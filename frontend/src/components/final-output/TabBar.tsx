/**
 * TabBar Component
 *
 * Tab navigation for the Final Output View, allowing users to switch between
 * Document, Red Team Report, Debate Log, and Metrics views.
 *
 * Based on Section 4.7 of the Frontend Design Document.
 */

import { memo, useCallback, useEffect } from 'react';
import type { OutputTab } from '../../types';
import './TabBar.css';

export interface TabBarProps {
  /** Currently active tab */
  activeTab: OutputTab;
  /** Callback when tab is changed */
  onTabChange: (tab: OutputTab) => void;
  /** Optional additional CSS class */
  className?: string;
}

interface TabConfig {
  id: OutputTab;
  label: string;
  shortcut: string;
}

const TABS: TabConfig[] = [
  { id: 'document', label: 'Document', shortcut: '1' },
  { id: 'redteam', label: 'Red Team Report', shortcut: '2' },
  { id: 'debate', label: 'Debate Log', shortcut: '3' },
  { id: 'metrics', label: 'Metrics', shortcut: '4' },
];

export const TabBar = memo(function TabBar({
  activeTab,
  onTabChange,
  className = '',
}: TabBarProps) {
  // Keyboard shortcuts (1-4) to switch tabs
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't capture if user is typing in an input
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement
      ) {
        return;
      }

      // Check for number keys 1-4
      const keyIndex = parseInt(e.key, 10) - 1;
      if (keyIndex >= 0 && keyIndex < TABS.length && !e.ctrlKey && !e.altKey && !e.metaKey) {
        e.preventDefault();
        onTabChange(TABS[keyIndex].id);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onTabChange]);

  const handleTabClick = useCallback(
    (tabId: OutputTab) => () => {
      onTabChange(tabId);
    },
    [onTabChange]
  );

  const handleKeyPress = useCallback(
    (tabId: OutputTab) => (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        onTabChange(tabId);
      }
    },
    [onTabChange]
  );

  return (
    <div
      className={`tab-bar ${className}`}
      role="tablist"
      aria-label="Output view tabs"
    >
      {TABS.map((tab) => (
        <button
          key={tab.id}
          className={`tab-bar__tab ${activeTab === tab.id ? 'tab-bar__tab--active' : ''}`}
          role="tab"
          aria-selected={activeTab === tab.id}
          aria-controls={`tabpanel-${tab.id}`}
          tabIndex={activeTab === tab.id ? 0 : -1}
          onClick={handleTabClick(tab.id)}
          onKeyDown={handleKeyPress(tab.id)}
          type="button"
        >
          <span className="tab-bar__tab-label">{tab.label}</span>
          <kbd className="tab-bar__tab-shortcut" aria-hidden="true">
            {tab.shortcut}
          </kbd>
        </button>
      ))}
    </div>
  );
});

export default TabBar;
