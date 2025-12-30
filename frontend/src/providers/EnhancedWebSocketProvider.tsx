/**
 * EnhancedWebSocketProvider
 *
 * Production-ready WebSocket provider with:
 * - Auto-reconnect with exponential backoff
 * - Message queue for offline handling
 * - Typed pub/sub message system
 * - Connection state tracking
 * - Heartbeat/ping-pong support
 */

import {
  createContext,
  useContext,
  useEffect,
  useRef,
  useState,
  useCallback,
} from 'react';
import type { ReactNode } from 'react';
import type {
  ConnectionStatus,
  ConnectionState,
  QueuedMessage,
  ClientEvents,
  WebSocketMessage,
} from '../types/websocket';

type MessageHandler = (payload: unknown) => void;

interface WebSocketContextValue {
  /** Current connection status */
  status: ConnectionStatus;
  /** Full connection state including history */
  connectionState: ConnectionState;
  /** Connection ID assigned by the server */
  connectionId: string | null;
  /** Send a message to the server */
  send: <K extends keyof ClientEvents>(type: K, payload: ClientEvents[K]) => void;
  /** Send raw message (for untyped events) */
  sendRaw: (type: string, payload: unknown) => void;
  /** Subscribe to a message type */
  subscribe: (type: string, handler: MessageHandler) => () => void;
  /** Force reconnection */
  reconnect: () => void;
  /** Number of queued messages waiting to be sent */
  queuedMessageCount: number;
  /** Clear the message queue */
  clearQueue: () => void;
}

const WebSocketContext = createContext<WebSocketContextValue | undefined>(
  undefined
);

interface WebSocketProviderProps {
  children: ReactNode;
  /** WebSocket server URL */
  url?: string;
  /** Base reconnect interval in ms */
  reconnectInterval?: number;
  /** Maximum reconnect attempts before giving up */
  maxReconnectAttempts?: number;
  /** Enable message queueing when disconnected */
  enableMessageQueue?: boolean;
  /** Maximum queued messages */
  maxQueueSize?: number;
  /** Heartbeat interval in ms (0 to disable) */
  heartbeatInterval?: number;
}

// Generate unique IDs for queued messages
let messageIdCounter = 0;
function generateMessageId(): string {
  return `msg_${Date.now()}_${++messageIdCounter}`;
}

export function WebSocketProvider({
  children,
  url = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws',
  reconnectInterval = 1000,
  maxReconnectAttempts = 10,
  enableMessageQueue = true,
  maxQueueSize = 100,
  heartbeatInterval = 30000,
}: WebSocketProviderProps) {
  const [connectionState, setConnectionState] = useState<ConnectionState>({
    status: 'disconnected',
    reconnectAttempts: 0,
    lastConnectedAt: null,
    lastDisconnectedAt: null,
    error: null,
  });

  const wsRef = useRef<WebSocket | null>(null);
  const handlersRef = useRef<Map<string, Set<MessageHandler>>>(new Map());
  const reconnectTimeoutRef = useRef<number | null>(null);
  const heartbeatIntervalRef = useRef<number | null>(null);
  const messageQueueRef = useRef<QueuedMessage[]>([]);
  const [queuedMessageCount, setQueuedMessageCount] = useState(0);
  const reconnectAttemptsRef = useRef(0);
  const [connectionId, setConnectionId] = useState<string | null>(null);

  // Update status helper
  const updateStatus = useCallback(
    (
      status: ConnectionStatus,
      updates?: Partial<Omit<ConnectionState, 'status'>>
    ) => {
      setConnectionState((prev) => ({
        ...prev,
        status,
        ...updates,
      }));
    },
    []
  );

  // Calculate backoff delay with jitter
  const getBackoffDelay = useCallback(
    (attempt: number): number => {
      const baseDelay = reconnectInterval;
      const maxDelay = 30000; // Cap at 30 seconds
      const exponentialDelay = Math.min(
        baseDelay * Math.pow(2, attempt),
        maxDelay
      );
      // Add jitter (0-25% of delay)
      const jitter = exponentialDelay * 0.25 * Math.random();
      return exponentialDelay + jitter;
    },
    [reconnectInterval]
  );

  // Process message queue after reconnection
  const processMessageQueue = useCallback(() => {
    if (wsRef.current?.readyState !== WebSocket.OPEN) return;

    const queue = [...messageQueueRef.current];
    messageQueueRef.current = [];
    setQueuedMessageCount(0);

    queue.forEach((msg) => {
      try {
        wsRef.current?.send(JSON.stringify({ type: msg.type, payload: msg.payload }));
      } catch (e) {
        console.error('Failed to send queued message:', e);
        // Re-queue failed messages
        if (messageQueueRef.current.length < maxQueueSize) {
          messageQueueRef.current.push({ ...msg, retries: msg.retries + 1 });
          setQueuedMessageCount((c) => c + 1);
        }
      }
    });
  }, [maxQueueSize]);

  // Start heartbeat
  const startHeartbeat = useCallback(() => {
    if (heartbeatInterval <= 0) return;

    heartbeatIntervalRef.current = window.setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping', payload: {} }));
      }
    }, heartbeatInterval);
  }, [heartbeatInterval]);

  // Stop heartbeat
  const stopHeartbeat = useCallback(() => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }
  }, []);

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    if (wsRef.current?.readyState === WebSocket.CONNECTING) return;

    updateStatus('connecting');

    try {
      const ws = new WebSocket(url);

      ws.onopen = () => {
        reconnectAttemptsRef.current = 0;
        updateStatus('connected', {
          lastConnectedAt: new Date(),
          reconnectAttempts: 0,
          error: null,
        });
        startHeartbeat();
        processMessageQueue();
      };

      ws.onclose = (event) => {
        stopHeartbeat();
        wsRef.current = null;

        const wasClean = event.wasClean;
        updateStatus('disconnected', {
          lastDisconnectedAt: new Date(),
        });

        // Attempt reconnection if not a clean close
        if (!wasClean) {
          const attempts = reconnectAttemptsRef.current;
          if (attempts < maxReconnectAttempts) {
            updateStatus('reconnecting', {
              reconnectAttempts: attempts + 1,
            });
            reconnectAttemptsRef.current = attempts + 1;

            const delay = getBackoffDelay(attempts);
            reconnectTimeoutRef.current = window.setTimeout(() => {
              connect();
            }, delay);
          } else {
            updateStatus('error', {
              error: `Failed to reconnect after ${maxReconnectAttempts} attempts`,
            });
          }
        }
      };

      ws.onerror = (event) => {
        console.error('WebSocket error:', event);
        updateStatus('error', {
          error: 'WebSocket connection error',
        });
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data) as WebSocketMessage;

          // Handle pong response
          if (message.type === 'pong') {
            return;
          }

          // Handle connected event - store the connection ID
          if (message.type === 'connected') {
            const payload = message.payload as { connectionId: string };
            if (payload.connectionId) {
              setConnectionId(payload.connectionId);
            }
          }

          // Dispatch to handlers
          const handlers = handlersRef.current.get(message.type);
          if (handlers) {
            handlers.forEach((handler) => {
              try {
                handler(message.payload);
              } catch (e) {
                console.error(`Error in handler for ${message.type}:`, e);
              }
            });
          }

          // Also dispatch to wildcard handlers
          const wildcardHandlers = handlersRef.current.get('*');
          if (wildcardHandlers) {
            wildcardHandlers.forEach((handler) => {
              try {
                handler(message);
              } catch (e) {
                console.error('Error in wildcard handler:', e);
              }
            });
          }
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e);
        }
      };

      wsRef.current = ws;
    } catch (e) {
      console.error('Failed to create WebSocket connection:', e);
      updateStatus('error', {
        error: 'Failed to create WebSocket connection',
      });
    }
  }, [
    url,
    maxReconnectAttempts,
    updateStatus,
    getBackoffDelay,
    startHeartbeat,
    stopHeartbeat,
    processMessageQueue,
  ]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    stopHeartbeat();
    if (wsRef.current) {
      wsRef.current.close(1000, 'Client disconnect');
      wsRef.current = null;
    }
    setConnectionId(null);
    updateStatus('disconnected');
  }, [stopHeartbeat, updateStatus]);

  // Send typed message
  const send = useCallback(
    <K extends keyof ClientEvents>(type: K, payload: ClientEvents[K]) => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type, payload }));
      } else if (enableMessageQueue) {
        // Queue message for later
        if (messageQueueRef.current.length < maxQueueSize) {
          messageQueueRef.current.push({
            id: generateMessageId(),
            type,
            payload,
            timestamp: Date.now(),
            retries: 0,
          });
          setQueuedMessageCount((c) => c + 1);
        } else {
          console.warn('Message queue full, message dropped:', type);
        }
      } else {
        console.warn('WebSocket not connected, message not sent:', type);
      }
    },
    [enableMessageQueue, maxQueueSize]
  );

  // Send raw/untyped message
  const sendRaw = useCallback(
    (type: string, payload: unknown) => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type, payload }));
      } else {
        console.warn('WebSocket not connected, message not sent:', type);
      }
    },
    []
  );

  // Subscribe to message type
  const subscribe = useCallback((type: string, handler: MessageHandler) => {
    if (!handlersRef.current.has(type)) {
      handlersRef.current.set(type, new Set());
    }
    handlersRef.current.get(type)!.add(handler);

    return () => {
      handlersRef.current.get(type)?.delete(handler);
      // Clean up empty sets
      if (handlersRef.current.get(type)?.size === 0) {
        handlersRef.current.delete(type);
      }
    };
  }, []);

  // Force reconnect
  const reconnect = useCallback(() => {
    disconnect();
    reconnectAttemptsRef.current = 0;
    setConnectionState((prev) => ({
      ...prev,
      reconnectAttempts: 0,
      error: null,
    }));
    // Small delay before reconnecting
    setTimeout(connect, 100);
  }, [connect, disconnect]);

  // Clear message queue
  const clearQueue = useCallback(() => {
    messageQueueRef.current = [];
    setQueuedMessageCount(0);
  }, []);

  // Auto-connect on mount
  useEffect(() => {
    connect();
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return (
    <WebSocketContext.Provider
      value={{
        status: connectionState.status,
        connectionState,
        connectionId,
        send,
        sendRaw,
        subscribe,
        reconnect,
        queuedMessageCount,
        clearQueue,
      }}
    >
      {children}
    </WebSocketContext.Provider>
  );
}

/**
 * Hook to access WebSocket context
 */
export function useWebSocket(): WebSocketContextValue {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
}

/**
 * Convenience hook for subscribing to specific message types
 */
export function useWebSocketMessage(type: string, handler: MessageHandler) {
  const { subscribe } = useWebSocket();

  useEffect(() => {
    return subscribe(type, handler);
  }, [type, handler, subscribe]);
}

/**
 * Hook to get connection status with additional helpers
 */
export function useConnectionStatus() {
  const { status, connectionState, reconnect, queuedMessageCount } =
    useWebSocket();

  return {
    status,
    isConnected: status === 'connected',
    isConnecting: status === 'connecting',
    isDisconnected: status === 'disconnected',
    isReconnecting: status === 'reconnecting',
    hasError: status === 'error',
    error: connectionState.error,
    reconnectAttempts: connectionState.reconnectAttempts,
    lastConnectedAt: connectionState.lastConnectedAt,
    queuedMessageCount,
    reconnect,
  };
}
