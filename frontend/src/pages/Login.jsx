import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/axios';
import { useBranding } from '../contexts/BrandingContext';

export default function Login() {
  const navigate = useNavigate();
  const branding = useBranding();
  const [email, setEmail]       = useState('');
  const [password, setPassword] = useState('');
  const [error, setError]       = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    try {
      const formData = new FormData();
      formData.append('username', email);
      formData.append('password', password);
      await api.post('/auth/login', formData);
      // Fetch user profile and cache it (cookie is now set by the server)
      try {
        const me = await api.get('/auth/me');
        localStorage.setItem('user', JSON.stringify(me.data));
      } catch (_) {}
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Authentication failed. Check your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-surface flex">
      {/* Left panel — brand + info */}
      <div className="hidden lg:flex flex-col justify-between w-[480px] bg-primary-container p-12 text-white flex-shrink-0">
        <div>
          <div className="flex items-center gap-3 mb-16">
            <div className="h-10 w-10 bg-secondary flex items-center justify-center rounded">
              <span className="material-symbols-outlined text-white" style={{ fontVariationSettings: "'FILL' 1" }}>
                account_balance
              </span>
            </div>
            <div>
              <p className="font-black text-lg font-public-sans leading-none">{branding.product_name}</p>
              <p className="text-[10px] uppercase tracking-widest text-on-primary-container mt-0.5">Enterprise Intelligence</p>
            </div>
          </div>

          <h1 className="text-h1 font-h1 leading-tight mb-6">
            Secure Financial<br />Document Intelligence
          </h1>
          <p className="text-on-primary-container text-body-md leading-relaxed">
            {branding.welcome_message}
          </p>

          <div className="mt-12 space-y-4">
            {[
              { icon: 'lock', text: 'End-to-end encrypted document analysis' },
              { icon: 'verified_user', text: 'SOC2 Type II compliant environment' },
              { icon: 'policy', text: 'PII masked before any AI processing' },
              { icon: 'history_edu', text: 'Every AI action is fully auditable' },
            ].map(({ icon, text }) => (
              <div key={icon} className="flex items-center gap-3">
                <span className="material-symbols-outlined text-tertiary-fixed-dim text-[20px]">{icon}</span>
                <span className="text-body-sm text-on-primary-container">{text}</span>
              </div>
            ))}
          </div>
        </div>

        <p className="text-[11px] text-on-primary-container opacity-60">
          © {new Date().getFullYear()} {branding.product_name}. Authorized access only.
        </p>
      </div>

      {/* Right panel — login form */}
      <div className="flex-1 flex items-center justify-center p-8 bg-white">
        <div className="w-full max-w-sm">
          {/* Mobile brand */}
          <div className="lg:hidden flex items-center gap-3 mb-10">
            <div className="h-9 w-9 bg-primary flex items-center justify-center rounded">
              <span className="material-symbols-outlined text-white text-[18px]" style={{ fontVariationSettings: "'FILL' 1" }}>
                account_balance
              </span>
            </div>
            <span className="font-black text-lg text-slate-900 font-public-sans">{branding.product_name}</span>
          </div>

          <h2 className="text-h2 font-h2 text-on-surface mb-1">Sign in</h2>
          <p className="text-body-sm text-outline mb-8">
            Access {branding.bank_name}'s AI workspace
          </p>

          {error && (
            <div className="flex items-start gap-2 p-3 bg-error-container border border-red-100 rounded mb-6">
              <span className="material-symbols-outlined text-error text-[18px] flex-shrink-0 mt-0.5">error_outline</span>
              <p className="text-body-sm text-on-error-container">{error}</p>
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-5">
            <div>
              <label className="block font-label-caps text-label-caps text-slate-500 mb-1.5 uppercase">
                Work Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded px-4 py-2.5 text-on-surface text-body-sm
                           focus:outline-none focus:ring-2 focus:ring-secondary/30 focus:border-secondary focus:bg-white transition-all
                           placeholder:text-slate-400"
                placeholder="you@institution.com"
                required
                autoComplete="email"
              />
            </div>

            <div>
              <label className="block font-label-caps text-label-caps text-slate-500 mb-1.5 uppercase">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded px-4 py-2.5 text-on-surface text-body-sm
                           focus:outline-none focus:ring-2 focus:ring-secondary/30 focus:border-secondary focus:bg-white transition-all
                           placeholder:text-slate-400"
                placeholder="••••••••"
                required
                autoComplete="current-password"
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-primary text-white font-bold py-3 rounded shadow-sm hover:opacity-90 active:scale-95 transition-all
                         disabled:opacity-60 disabled:cursor-not-allowed mt-2 text-sm tracking-tight"
            >
              {isLoading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Authenticating...
                </span>
              ) : (
                'Sign In'
              )}
            </button>
          </form>

          <p className="text-[11px] text-slate-400 text-center mt-8 leading-relaxed">
            Authorized personnel only. All access is logged, encrypted,<br />and subject to institutional audit.
          </p>
        </div>
      </div>
    </div>
  );
}
