import { NavLink } from 'react-router-dom';
import { useUIStore } from '../../stores/uiStore';
import './Sidebar.css';

interface NavItemProps {
  to: string;
  icon: string;
  label: string;
  onClose?: () => void;
}

function NavItem({ to, icon, label, onClose }: NavItemProps) {
  const sidebarCollapsed = useUIStore((state) => state.sidebarCollapsed);

  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `nav-item ${isActive ? 'nav-item--active' : ''}`
      }
      title={sidebarCollapsed ? label : undefined}
    >
      <span className="nav-item__icon">{icon}</span>
      <span className="nav-item__label">{label}</span>
      {onClose && (
        <button
          className="nav-item__close"
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            onClose();
          }}
          title="Close tab"
        >
          ×
        </button>
      )}
    </NavLink>
  );
}

export function Sidebar() {
  const { sidebarCollapsed, toggleSidebar, documentTabs, removeDocumentTab } = useUIStore();

  return (
    <aside className={`sidebar ${sidebarCollapsed ? 'sidebar--collapsed' : ''}`}>
      <div className="sidebar__header">
        <div className="sidebar__logo">
          {sidebarCollapsed ? 'AS' : 'Adversarial Swarm'}
        </div>
        <button
          className="sidebar__toggle"
          onClick={toggleSidebar}
          aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {sidebarCollapsed ? '\u25B6' : '\u25C0'}
        </button>
      </div>

      <nav className="sidebar__nav">
        <NavItem to="/new" icon="➕" label="New Document" />

        {documentTabs.length > 0 && (
          <div className="sidebar__section">
            <div className="sidebar__section-label">
              {!sidebarCollapsed && 'In Progress'}
            </div>
            {documentTabs.map((tab) => (
              <NavItem
                key={tab.id}
                to={tab.path}
                icon="📝"
                label={tab.label}
                onClose={() => removeDocumentTab(tab.id)}
              />
            ))}
          </div>
        )}

        <NavItem to="/history" icon="📄" label="History" />
        <NavItem to="/profiles" icon="🏢" label="Company Profiles" />
        <NavItem to="/settings" icon="⚙️" label="Settings" />
      </nav>

      <div className="sidebar__footer">
        <div className="sidebar__version">v1.0.0</div>
      </div>
    </aside>
  );
}
