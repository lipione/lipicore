import { NavLink, useNavigate } from 'react-router-dom';
import api from '../../api/axios';
import RoleBadge from '../lipicore/RoleBadge';
import { getCurrentUserRole } from '../../config/rolePermissions';
import { useBranding } from '../../contexts/BrandingContext';

const TOP_NAV = [
  { label: 'Chat',       to: '/chat' },
  { label: 'Audit Log',  to: '/audit' },
  { label: 'Compliance', to: '/regulatory' },
];

export default function TopBar({ language, onLanguageChange, onMenuClick }) {
  const navigate = useNavigate();
  const branding = useBranding();
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  const initials = (user.name || user.email || 'U').split(/[\s@]/)[0].slice(0, 2).toUpperCase();
  const userRole = getCurrentUserRole();

  const handleLogout = async () => {
    try { await api.post('/auth/logout'); } catch (_) {}
    localStorage.removeItem('user');
    navigate('/login');
  };

  return (
    <header className="fixed top-0 left-0 lg:left-64 right-0 h-16 flex justify-between items-center px-3 sm:px-6 bg-white border-b border-slate-200 z-30">
      {/* Left: wordmark + top nav */}
      <div className="flex items-center gap-3 sm:gap-8 min-w-0">
        <button
          type="button"
          aria-label="Open navigation"
          onClick={onMenuClick}
          className="p-2 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded lg:hidden"
        >
          <span className="material-symbols-outlined text-[21px]">menu</span>
        </button>
        <div className="flex items-center gap-1.5">
          <span className="text-xl font-bold tracking-tighter text-slate-900 font-public-sans">
            {branding.product_name}
          </span>
          <span className="text-[10px] font-semibold text-slate-400 border border-slate-200 px-1.5 py-0.5 rounded hidden sm:inline">
            Enterprise
          </span>
        </div>
        <nav className="hidden lg:flex items-center h-16">
          {TOP_NAV.map(({ label, to }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `h-full flex items-center px-1 mr-6 text-sm font-medium font-public-sans tracking-tight transition-colors border-b-2 ${
                  isActive
                    ? 'text-slate-900 border-slate-900'
                    : 'text-slate-500 border-transparent hover:text-slate-900'
                }`
              }
            >
              {label}
            </NavLink>
          ))}
        </nav>
      </div>

      {/* Right: bilingual toggle + icons + avatar */}
      <div className="flex items-center gap-2 sm:gap-4">
        {/* Bilingual switcher */}
        <div className="flex items-center bg-slate-100 rounded p-1 gap-1">
          <button
            type="button"
            onClick={(e) => { e.preventDefault(); onLanguageChange('en'); }}
            className={`px-3 py-1 text-xs font-bold rounded transition-all cursor-pointer ${
              language === 'en'
                ? 'bg-white shadow-sm text-slate-900'
                : 'text-slate-500 hover:text-slate-700 hover:bg-slate-200'
            }`}
          >
            EN
          </button>
          <button
            type="button"
            onClick={(e) => { e.preventDefault(); onLanguageChange('np'); }}
            className={`px-3 py-1 text-xs font-bold rounded transition-all cursor-pointer ${
              language === 'np'
                ? 'bg-white shadow-sm text-slate-900'
                : 'text-slate-500 hover:text-slate-700 hover:bg-slate-200'
            }`}
          >
            ने
          </button>
        </div>

        {/* Icon cluster */}
        <div className="hidden sm:flex items-center gap-1 border-l border-slate-200 pl-4">
          <button
            className="p-2 text-slate-500 hover:text-slate-900 rounded hover:bg-slate-100 transition-colors"
            title="Security Status"
          >
            <span className="material-symbols-outlined text-[20px]">enhanced_encryption</span>
          </button>
          <button
            className="p-2 text-slate-500 hover:text-slate-900 rounded hover:bg-slate-100 transition-colors relative"
            title="Notifications"
          >
            <span className="material-symbols-outlined text-[20px]">notifications</span>
          </button>
          <NavLink
            to="/admin/settings"
            className="p-2 text-slate-500 hover:text-slate-900 rounded hover:bg-slate-100 transition-colors"
            title="Settings"
          >
            <span className="material-symbols-outlined text-[20px]">settings</span>
          </NavLink>

          {/* Avatar + dropdown */}
          <div className="relative group ml-1">
            <button className="h-8 w-8 rounded-full bg-primary-container text-white flex items-center justify-center text-xs font-bold ring-2 ring-slate-200">
              {initials}
            </button>
            <div className="absolute right-0 top-10 w-52 bg-white border border-slate-200 rounded-lg shadow-floating py-1 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50">
              <div className="px-3 py-2 border-b border-slate-100">
                <p className="text-sm font-semibold text-slate-900 truncate">{user.name || 'User'}</p>
                <p className="text-xs text-slate-500 truncate mb-1">{user.email || ''}</p>
                <RoleBadge role={userRole} size="xs" />
              </div>
              <NavLink to="/admin/settings" className="flex items-center gap-2 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50">
                <span className="material-symbols-outlined text-[16px]">person</span> Account Settings
              </NavLink>
              <button
                onClick={handleLogout}
                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-error hover:bg-red-50"
              >
                <span className="material-symbols-outlined text-[16px]">logout</span> Sign Out
              </button>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
