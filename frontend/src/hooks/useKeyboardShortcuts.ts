/**
 * Keyboard Shortcuts Hook (F12 - Polish)
 *
 * Global keyboard shortcut system for power users.
 * Implements shortcuts from Section 9 of the Frontend Design Document.
 */

import { useEffect, useCallback, useMemo } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useUIStore } from '../stores/uiStore';
import { useSwarmStore } from '../stores/swarmStore';

// ============================================================================
// Types
// ============================================================================

export interface KeyboardShortcut {
  key: string;
  ctrl?: boolean;
  meta?: boolean;
  shift?: boolean;
  alt?: boolean;
  description: string;
  category: 'navigation' | 'generation' | 'document' | 'view';
  handler: () => void;
  enabled?: () => boolean;
}

export interface ShortcutGroup {
  category: string;
  shortcuts: Array<{
    keys: string;
    description: string;
  }>;
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Check if an element is an input field that should capture keyboard events
 */
function isInputElement(element: EventTarget | null): boolean {
  if (!element || !(element instanceof HTMLElement)) return false;
  const tagName = element.tagName.toLowerCase();
  return (
    tagName === 'input' ||
    tagName === 'textarea' ||
    tagName === 'select' ||
    element.isContentEditable
  );
}

/**
 * Format a shortcut for display (e.g., "Ctrl+N" or "⌘N")
 */
export function formatShortcut(shortcut: KeyboardShortcut): string {
  const isMac = navigator.platform.toLowerCase().includes('mac');
  const parts: string[] = [];

  if (shortcut.ctrl || shortcut.meta) {
    parts.push(isMac ? '⌘' : 'Ctrl');
  }
  if (shortcut.shift) {
    parts.push(isMac ? '⇧' : 'Shift');
  }
  if (shortcut.alt) {
    parts.push(isMac ? '⌥' : 'Alt');
  }

  // Format the key
  let keyDisplay = shortcut.key.toUpperCase();
  if (shortcut.key === ' ') keyDisplay = 'Space';
  if (shortcut.key === 'Escape') keyDisplay = 'Esc';
  if (shortcut.key === 'Enter') keyDisplay = '↵';
  if (shortcut.key === 'Tab') keyDisplay = '⇥';
  if (shortcut.key === '[') keyDisplay = '[';
  if (shortcut.key === ']') keyDisplay = ']';

  parts.push(keyDisplay);

  return isMac ? parts.join('') : parts.join('+');
}

// ============================================================================
// Main Hook
// ============================================================================

export interface UseKeyboardShortcutsOptions {
  enabled?: boolean;
}

export interface UseKeyboardShortcutsReturn {
  shortcuts: KeyboardShortcut[];
  shortcutGroups: ShortcutGroup[];
}

export function useKeyboardShortcuts(
  options: UseKeyboardShortcutsOptions = {}
): UseKeyboardShortcutsReturn {
  const { enabled = true } = options;

  const navigate = useNavigate();
  const location = useLocation();
  const { setActiveTab, toggleSidebar } = useUIStore();
  const { status, pauseGeneration, resumeGeneration, cancelGeneration } =
    useSwarmStore();

  // Check if we're on the generation page
  const isGenerationPage = location.pathname.startsWith('/generate');
  const isGenerating = status === 'running';
  const isPaused = status === 'review';

  // Define all shortcuts
  const shortcuts: KeyboardShortcut[] = useMemo(
    () => [
      // Navigation shortcuts
      {
        key: 'n',
        ctrl: true,
        meta: true,
        description: 'New document',
        category: 'navigation',
        handler: () => navigate('/new'),
      },
      {
        key: 'b',
        ctrl: true,
        meta: true,
        description: 'Toggle sidebar',
        category: 'navigation',
        handler: toggleSidebar,
      },

      // Generation shortcuts (only on generation page)
      {
        key: ' ',
        description: 'Pause/resume generation',
        category: 'generation',
        handler: () => {
          if (isGenerating) {
            pauseGeneration();
          } else if (isPaused) {
            resumeGeneration();
          }
        },
        enabled: () => isGenerationPage && (isGenerating || isPaused),
      },
      {
        key: 'Escape',
        description: 'Cancel generation / close modal',
        category: 'generation',
        handler: () => {
          if (isGenerating || isPaused) {
            cancelGeneration();
          }
        },
        enabled: () => isGenerationPage && (isGenerating || isPaused),
      },
      {
        key: 'Enter',
        ctrl: true,
        meta: true,
        description: 'Start generation',
        category: 'generation',
        handler: () => {
          // This would be handled by the form component
          const submitButton = document.querySelector(
            '[data-generate-button]'
          ) as HTMLButtonElement;
          if (submitButton && !submitButton.disabled) {
            submitButton.click();
          }
        },
        enabled: () => location.pathname === '/new',
      },

      // View shortcuts (Tab switching in final output)
      {
        key: 'Tab',
        description: 'Switch between Debate Theater and Preview',
        category: 'view',
        handler: () => {
          // Toggle focus between debate theater and preview
          const debateTheater = document.querySelector(
            '[data-panel="debate-theater"]'
          ) as HTMLElement;
          const preview = document.querySelector(
            '[data-panel="document-preview"]'
          ) as HTMLElement;

          if (debateTheater && preview) {
            if (document.activeElement?.closest('[data-panel="debate-theater"]')) {
              preview.focus();
            } else {
              debateTheater.focus();
            }
          }
        },
        enabled: () => isGenerationPage,
      },
      {
        key: '1',
        description: 'Document tab',
        category: 'view',
        handler: () => setActiveTab('document'),
        enabled: () => isGenerationPage && status === 'complete',
      },
      {
        key: '2',
        description: 'Red Team Report tab',
        category: 'view',
        handler: () => setActiveTab('redteam'),
        enabled: () => isGenerationPage && status === 'complete',
      },
      {
        key: '3',
        description: 'Debate Log tab',
        category: 'view',
        handler: () => setActiveTab('debate'),
        enabled: () => isGenerationPage && status === 'complete',
      },
      {
        key: '4',
        description: 'Metrics tab',
        category: 'view',
        handler: () => setActiveTab('metrics'),
        enabled: () => isGenerationPage && status === 'complete',
      },

      // Document shortcuts
      {
        key: 'e',
        ctrl: true,
        meta: true,
        description: 'Export document',
        category: 'document',
        handler: () => {
          const exportButton = document.querySelector(
            '[data-export-button]'
          ) as HTMLButtonElement;
          if (exportButton) {
            exportButton.click();
          }
        },
        enabled: () => isGenerationPage && status === 'complete',
      },
      {
        key: 'c',
        ctrl: true,
        meta: true,
        shift: true,
        description: 'Copy document as markdown',
        category: 'document',
        handler: async () => {
          const content = document.querySelector(
            '[data-document-content]'
          )?.textContent;
          if (content) {
            try {
              await navigator.clipboard.writeText(content);
              // Could trigger a toast notification here
            } catch (err) {
              console.error('Failed to copy:', err);
            }
          }
        },
        enabled: () => isGenerationPage && status === 'complete',
      },
      {
        key: '[',
        description: 'Previous round in debate log',
        category: 'view',
        handler: () => {
          const prevButton = document.querySelector(
            '[data-round-prev]'
          ) as HTMLButtonElement;
          if (prevButton && !prevButton.disabled) {
            prevButton.click();
          }
        },
        enabled: () => isGenerationPage,
      },
      {
        key: ']',
        description: 'Next round in debate log',
        category: 'view',
        handler: () => {
          const nextButton = document.querySelector(
            '[data-round-next]'
          ) as HTMLButtonElement;
          if (nextButton && !nextButton.disabled) {
            nextButton.click();
          }
        },
        enabled: () => isGenerationPage,
      },
    ],
    [
      navigate,
      toggleSidebar,
      isGenerationPage,
      isGenerating,
      isPaused,
      pauseGeneration,
      resumeGeneration,
      cancelGeneration,
      setActiveTab,
      status,
      location.pathname,
    ]
  );

  // Group shortcuts for display in help modal
  const shortcutGroups: ShortcutGroup[] = useMemo(() => {
    const groups: Record<string, ShortcutGroup> = {};

    shortcuts.forEach((shortcut) => {
      const categoryLabel = {
        navigation: 'Navigation',
        generation: 'Generation',
        document: 'Document',
        view: 'View',
      }[shortcut.category];

      if (!groups[shortcut.category]) {
        groups[shortcut.category] = {
          category: categoryLabel,
          shortcuts: [],
        };
      }

      groups[shortcut.category].shortcuts.push({
        keys: formatShortcut(shortcut),
        description: shortcut.description,
      });
    });

    return Object.values(groups);
  }, [shortcuts]);

  // Event handler
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (!enabled) return;

      // Don't intercept shortcuts when typing in inputs
      if (isInputElement(event.target)) {
        // Still allow some shortcuts even in inputs
        const isMac = navigator.platform.toLowerCase().includes('mac');
        const modKey = isMac ? event.metaKey : event.ctrlKey;

        // Only allow Ctrl+N, Ctrl+B in inputs
        if (!(modKey && (event.key === 'n' || event.key === 'b'))) {
          return;
        }
      }

      // Find matching shortcut
      const isMac = navigator.platform.toLowerCase().includes('mac');

      for (const shortcut of shortcuts) {
        // Check if this shortcut is enabled
        if (shortcut.enabled && !shortcut.enabled()) {
          continue;
        }

        // Check key match
        if (shortcut.key.toLowerCase() !== event.key.toLowerCase()) {
          continue;
        }

        // Check modifier keys
        const wantsModifier = shortcut.ctrl || shortcut.meta;
        const hasModifier = isMac ? event.metaKey : event.ctrlKey;

        if (wantsModifier && !hasModifier) continue;
        if (!wantsModifier && hasModifier) continue;

        if (shortcut.shift && !event.shiftKey) continue;
        if (!shortcut.shift && event.shiftKey) continue;

        if (shortcut.alt && !event.altKey) continue;
        if (!shortcut.alt && event.altKey) continue;

        // Prevent default and execute handler
        event.preventDefault();
        event.stopPropagation();
        shortcut.handler();
        return;
      }
    },
    [enabled, shortcuts]
  );

  // Attach event listener
  useEffect(() => {
    if (!enabled) return;

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [enabled, handleKeyDown]);

  return { shortcuts, shortcutGroups };
}

// ============================================================================
// Shortcut Help Modal Hook
// ============================================================================

export function useShortcutHelp(): {
  isOpen: boolean;
  open: () => void;
  close: () => void;
  toggle: () => void;
} {
  const { shortcutHelpOpen, setShortcutHelpOpen } = useUIStore();

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Open help with ? key (Shift+/)
      if (event.key === '?' && !isInputElement(event.target)) {
        event.preventDefault();
        setShortcutHelpOpen(!shortcutHelpOpen);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [shortcutHelpOpen, setShortcutHelpOpen]);

  return {
    isOpen: shortcutHelpOpen,
    open: () => setShortcutHelpOpen(true),
    close: () => setShortcutHelpOpen(false),
    toggle: () => setShortcutHelpOpen(!shortcutHelpOpen),
  };
}

export default useKeyboardShortcuts;
