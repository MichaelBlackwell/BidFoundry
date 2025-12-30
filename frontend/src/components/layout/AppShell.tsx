import type { ReactNode } from 'react';
import { Sidebar } from './Sidebar';
import { useUIStore } from '../../stores/uiStore';
import { useKeyboardShortcuts } from '../../hooks';
import { KeyboardShortcutsModal } from '../ui';
import { useAccessibility } from '../../providers';
import './AppShell.css';

interface AppShellProps {
  children: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const sidebarCollapsed = useUIStore((state) => state.sidebarCollapsed);
  const { isMobile, isTablet, reducedMotion } = useAccessibility();

  // Enable global keyboard shortcuts (inside Router context)
  useKeyboardShortcuts();

  // Build class names for responsive and motion preferences
  const classNames = [
    'app-shell',
    sidebarCollapsed ? 'sidebar-collapsed' : '',
    isMobile ? 'is-mobile' : '',
    isTablet ? 'is-tablet' : '',
    reducedMotion ? 'reduce-motion' : '',
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div className={classNames}>
      <Sidebar />
      <main
        id="main-content"
        className="main-workspace"
        role="main"
        aria-label="Main content"
        tabIndex={-1}
      >
        {children}
      </main>
      <KeyboardShortcutsModal />
    </div>
  );
}
