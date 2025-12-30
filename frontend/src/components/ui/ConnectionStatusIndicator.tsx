/**
 * ConnectionStatusIndicator
 *
 * Shows the current WebSocket connection status in a compact format.
 * Useful for displaying in the header or status bar.
 */

import { useConnectionStatus } from '../../providers';
import './ConnectionStatusIndicator.css';

interface ConnectionStatusIndicatorProps {
  /** Show text label next to the indicator */
  showLabel?: boolean;
  /** Additional CSS class */
  className?: string;
}

export function ConnectionStatusIndicator({
  showLabel = false,
  className = '',
}: ConnectionStatusIndicatorProps) {
  const {
    status,
    isConnected,
    isConnecting,
    isReconnecting,
    hasError,
    reconnectAttempts,
    queuedMessageCount,
    reconnect,
  } = useConnectionStatus();

  const getStatusLabel = () => {
    switch (status) {
      case 'connected':
        return 'Connected';
      case 'connecting':
        return 'Connecting...';
      case 'reconnecting':
        return `Reconnecting (${reconnectAttempts})...`;
      case 'disconnected':
        return 'Disconnected';
      case 'error':
        return 'Connection Error';
      default:
        return 'Unknown';
    }
  };

  const getStatusClass = () => {
    if (isConnected) return 'status-connected';
    if (isConnecting || isReconnecting) return 'status-connecting';
    if (hasError) return 'status-error';
    return 'status-disconnected';
  };

  return (
    <div className={`connection-status-indicator ${className}`}>
      <div className={`status-dot ${getStatusClass()}`} title={getStatusLabel()}>
        {(isConnecting || isReconnecting) && (
          <span className="status-pulse" />
        )}
      </div>

      {showLabel && (
        <span className="status-label">{getStatusLabel()}</span>
      )}

      {queuedMessageCount > 0 && (
        <span className="queued-badge" title={`${queuedMessageCount} messages queued`}>
          {queuedMessageCount}
        </span>
      )}

      {(hasError || status === 'disconnected') && (
        <button
          className="reconnect-button"
          onClick={reconnect}
          title="Click to reconnect"
        >
          Retry
        </button>
      )}
    </div>
  );
}
