import type { ReactNode } from 'react';
import './MainWorkspace.css';

interface MainWorkspaceProps {
  children: ReactNode;
  title?: string;
  /** When true, removes padding and allows content to fill the full space */
  fullWidth?: boolean;
  /** Hide the header title bar */
  hideHeader?: boolean;
}

export function MainWorkspace({
  children,
  title,
  fullWidth = false,
  hideHeader = false,
}: MainWorkspaceProps) {
  return (
    <div className="main-workspace-content">
      {title && !hideHeader && (
        <header className="workspace-header">
          <h1 className="workspace-title">{title}</h1>
        </header>
      )}
      <div className={`workspace-body ${fullWidth ? 'workspace-body--full-width' : ''}`}>
        {children}
      </div>
    </div>
  );
}
