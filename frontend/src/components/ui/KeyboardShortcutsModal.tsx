/**
 * Keyboard Shortcuts Help Modal (F12 - Polish)
 *
 * Displays available keyboard shortcuts in a modal dialog.
 * Opened by pressing '?' key.
 */

import { useEffect, useRef } from 'react';
import { Modal } from './Modal';
import { useShortcutHelp, useKeyboardShortcuts, type ShortcutGroup } from '../../hooks/useKeyboardShortcuts';
import './KeyboardShortcutsModal.css';

interface ShortcutRowProps {
  keys: string;
  description: string;
}

function ShortcutRow({ keys, description }: ShortcutRowProps) {
  return (
    <div className="shortcut-row" role="listitem">
      <kbd className="shortcut-keys" aria-label={`Press ${keys}`}>
        {keys}
      </kbd>
      <span className="shortcut-description">{description}</span>
    </div>
  );
}

interface ShortcutGroupSectionProps {
  group: ShortcutGroup;
}

function ShortcutGroupSection({ group }: ShortcutGroupSectionProps) {
  return (
    <div className="shortcut-group">
      <h3 className="shortcut-group__title">{group.category}</h3>
      <div className="shortcut-group__list" role="list">
        {group.shortcuts.map((shortcut, index) => (
          <ShortcutRow
            key={index}
            keys={shortcut.keys}
            description={shortcut.description}
          />
        ))}
      </div>
    </div>
  );
}

export function KeyboardShortcutsModal() {
  const { isOpen, close } = useShortcutHelp();
  const { shortcutGroups } = useKeyboardShortcuts({ enabled: false });
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  // Focus management for accessibility
  useEffect(() => {
    if (isOpen && closeButtonRef.current) {
      closeButtonRef.current.focus();
    }
  }, [isOpen]);

  return (
    <Modal
      isOpen={isOpen}
      onClose={close}
      title="Keyboard Shortcuts"
      className="keyboard-shortcuts-modal"
      aria-labelledby="shortcuts-modal-title"
    >
      <div className="keyboard-shortcuts-content" role="document">
        <div className="keyboard-shortcuts-grid">
          {shortcutGroups.map((group) => (
            <ShortcutGroupSection key={group.category} group={group} />
          ))}
        </div>
        <div className="keyboard-shortcuts-footer">
          <p className="keyboard-shortcuts-hint">
            Press <kbd>?</kbd> to toggle this help menu
          </p>
          <button
            ref={closeButtonRef}
            className="keyboard-shortcuts-close"
            onClick={close}
            aria-label="Close shortcuts help"
          >
            Close
          </button>
        </div>
      </div>
    </Modal>
  );
}

export default KeyboardShortcutsModal;
