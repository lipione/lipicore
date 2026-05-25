import { NavLink } from 'react-router-dom';
import { PERMISSIONS, getCurrentUserRole, hasPermission } from '../../config/rolePermissions';
import RoleBadge from '../lipicore/RoleBadge';
import { getCurrentUser } from '../../config/rolePermissions';
import { useBranding } from '../../contexts/BrandingContext';

const NAV_SECTIONS = [
  {
    label: null,
    items: [
      { icon: 'chat',           label: 'Chat Assistant',      to: '/chat',               permission: PERMISSIONS.USE_CHAT },
      { icon: 'account_tree',   label: 'Process Navigator',   to: '/process-navigator',  permission: PERMISSIONS.VIEW_PROCESS_NAVIGATOR },
      { icon: 'document_scanner', label: 'OCR Extraction',     to: '/ocr',                permission: PERMISSIONS.USE_CHAT_FILE_UPLOAD },
    ],
  },
  {
    label: 'KNOWLEDGE',
    items: [
      { icon: 'folder_managed', label: 'Document Library',    to: '/documents',          permission: PERMISSIONS.VIEW_DOCUMENTS },
      { icon: 'gpp_maybe',      label: 'Compliance Monitor',  to: '/regulatory',         permission: PERMISSIONS.VIEW_REGULATORY_LIBRARY },
      { icon: 'rule',           label: 'Compliance Workspace', to: '/compliance-workspace', permission: PERMISSIONS.MANAGE_COMPLIANCE },
    ],
  },
  {
    label: 'INSIGHTS',
    items: [
      { icon: 'bar_chart',      label: 'Analytics',           to: '/analytics',          permission: PERMISSIONS.VIEW_ANALYTICS },
      { icon: 'science',        label: 'Evaluations',         to: '/evaluations',        permission: PERMISSIONS.VIEW_EVALUATIONS },
      { icon: 'speed',          label: 'Model Lab',           to: '/model-lab',          permission: PERMISSIONS.VIEW_EVALUATIONS },
      { icon: 'summarize',      label: 'Reports',             to: '/reports',            permission: PERMISSIONS.VIEW_REPORTS },
      { icon: 'auto_awesome',   label: 'AI Tasks',            to: '/tasks',              permission: PERMISSIONS.VIEW_TASKS },
    ],
  },
  {
    label: 'GOVERNANCE',
    items: [
      { icon: 'policy',         label: 'Audit Logs',          to: '/audit',              permission: PERMISSIONS.VIEW_AUDIT_LOGS },
      { icon: 'manage_accounts', label: 'Users & Roles',      to: '/admin/users',        permission: PERMISSIONS.MANAGE_USERS },
      { icon: 'settings',       label: 'Settings',            to: '/admin/settings',     permission: PERMISSIONS.VIEW_SYSTEM_SETTINGS },
    ],
  },
];

const FOOTER_ITEMS = [
  { icon: 'help_outline', label: 'Help Center', to: '/help' },
];

function NavItem({ icon, label, to }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `flex items-center gap-3 px-3 py-2.5 rounded text-[13px] font-medium transition-all duration-150 ${
          isActive
            ? 'bg-white text-slate-900 shadow-sm ring-1 ring-slate-200'
            : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
        }`
      }
    >
      <span className="material-symbols-outlined text-[20px]">{icon}</span>
      {label}
    </NavLink>
  );
}

export default function Sidebar({ onUpload, open = false, onClose }) {
  const userRole = getCurrentUserRole();
  const user = getCurrentUser();
  const branding = useBranding();

  return (
    <aside
      className={`fixed left-0 top-0 h-screen w-64 flex flex-col py-4 px-3 bg-slate-50 border-r border-slate-200 z-40 transition-transform duration-200 lg:translate-x-0 ${
        open ? 'translate-x-0 shadow-panel' : '-translate-x-full'
      }`}
    >
      {/* Brand */}
      <div className="px-3 py-3 mb-4 flex items-center gap-3">
        <div className="h-9 w-9 bg-primary flex items-center justify-center rounded-lg flex-shrink-0">
          <span className="material-symbols-outlined text-white text-[18px]" style={{ fontVariationSettings: "'FILL' 1" }}>
            account_balance
          </span>
        </div>
        <div>
          <h2 className="text-base font-black text-slate-900 font-public-sans leading-none">{branding.product_name}</h2>
          <p className="text-[10px] uppercase tracking-widest text-slate-500 font-bold mt-0.5">{branding.bank_name}</p>
        </div>
        <button
          type="button"
          aria-label="Close navigation"
          onClick={onClose}
          className="ml-auto p-1.5 text-slate-500 hover:text-slate-900 hover:bg-slate-100 rounded lg:hidden"
        >
          <span className="material-symbols-outlined text-[18px]">close</span>
        </button>
      </div>

      {/* Upload CTA */}
      {hasPermission(userRole, PERMISSIONS.UPLOAD_DOCUMENTS) && (
        <button
          onClick={onUpload}
          className="flex items-center justify-center gap-2 px-4 py-2.5 mb-4 bg-primary text-white text-sm font-semibold rounded shadow-sm hover:opacity-90 active:scale-95 transition-all"
        >
          <span className="material-symbols-outlined text-[18px]">upload_file</span>
          Upload Document
        </button>
      )}

      {/* Chat CTA for users without upload permission */}
      {!hasPermission(userRole, PERMISSIONS.UPLOAD_DOCUMENTS) && hasPermission(userRole, PERMISSIONS.USE_CHAT) && (
        <NavLink
          to="/chat"
          className="flex items-center justify-center gap-2 px-4 py-2.5 mb-4 bg-primary text-white text-sm font-semibold rounded shadow-sm hover:opacity-90 active:scale-95 transition-all"
        >
          <span className="material-symbols-outlined text-[18px]">add_comment</span>
          New Chat
        </NavLink>
      )}

      {/* Main Nav */}
      <nav className="flex-1 overflow-y-auto space-y-4 pr-1">
        {NAV_SECTIONS.map((section) => {
          const visibleItems = section.items.filter(
            (item) => !item.permission || hasPermission(userRole, item.permission)
          );
          if (visibleItems.length === 0) return null;
          return (
            <div key={section.label || 'main'}>
              {section.label && (
                <p className="px-3 text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">{section.label}</p>
              )}
              <div className="space-y-0.5">
                {visibleItems.map(({ icon, label, to }) => (
                  <NavItem key={to} icon={icon} label={label} to={to} />
                ))}
              </div>
            </div>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="border-t border-slate-200 pt-3 mt-3 space-y-0.5">
        {FOOTER_ITEMS.map(({ icon, label, to }) => (
          <NavItem key={to} icon={icon} label={label} to={to} />
        ))}

        {/* User identity */}
        {user && (
          <div className="mt-3 px-3 py-2.5 rounded bg-white border border-slate-100 flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-full bg-primary-container flex items-center justify-center flex-shrink-0">
              <span className="material-symbols-outlined text-[14px]">person</span>
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-[12px] font-semibold text-slate-800 truncate">{user.email}</p>
              <RoleBadge role={userRole} size="xs" />
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}
