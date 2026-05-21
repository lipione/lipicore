import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/axios';
import { useBranding } from '../contexts/BrandingContext';

function Toggle({ on, onChange }) {
  return (
    <button
      onClick={() => onChange(!on)}
      className={`relative w-10 h-5 rounded-full transition-colors flex-shrink-0 ${on ? 'bg-secondary-container' : 'bg-slate-200'}`}
    >
      <div className={`absolute top-1 w-3 h-3 bg-white rounded-full shadow transition-all ${on ? 'left-6' : 'left-1'}`} />
    </button>
  );
}

const NOTIFICATIONS = [
  { key: 'analysis_complete', label: 'Analysis Completion',   desc: 'Get notified when document auditing is finished.',              defaultApp: true,  defaultEmail: true },
  { key: 'anomaly_detected',  label: 'Anomalies Detected',    desc: 'Immediate alerts for high-risk financial discrepancies.',       defaultApp: true,  defaultEmail: false },
  { key: 'weekly_summary',    label: 'Weekly Summary',        desc: 'Aggregated report of all analysis performed.',                   defaultApp: false, defaultEmail: true },
];

const MODE_OPTIONS = [
  { value: 'ask_knowledge', label: 'Ask Bank Knowledge' },
  { value: 'approved_knowledge', label: 'Ask Approved Knowledge' },
  { value: 'analyze_file', label: 'Analyze Uploaded File' },
  { value: 'summarize', label: 'Summarize' },
  { value: 'draft', label: 'Draft' },
  { value: 'translate', label: 'Translate' },
  { value: 'compare', label: 'Compare Documents' },
];

export default function Settings() {
  const navigate  = useNavigate();
  const storedUser = JSON.parse(localStorage.getItem('user') || '{}');
  const branding = useBranding();

  const [form, setForm] = useState({
    name:       storedUser.name  || '',
    email:      storedUser.email || '',
    department: 'Financial Audit & Compliance',
  });
  const [language,      setLanguage]     = useState(localStorage.getItem('language') || 'en');
  const [notifs,        setNotifs]       = useState(() => {
    const s = {};
    NOTIFICATIONS.forEach(n => { s[`${n.key}_app`] = n.defaultApp; s[`${n.key}_email`] = n.defaultEmail; });
    return s;
  });
  const [saving,        setSaving]       = useState(false);
  const [saveMsg,       setSaveMsg]      = useState('');
  const [brandingSaving, setBrandingSaving] = useState(false);
  const [brandingMsg, setBrandingMsg] = useState('');
  const [brandingForm, setBrandingForm] = useState({
    product_name: 'BankAi',
    bank_name: 'Your Bank',
    logo_url: '',
    primary_color: '#17324d',
    accent_color: '#c7902c',
    welcome_message: '',
    support_contact: '',
    disclaimer: '',
    allowed_modes: MODE_OPTIONS.map(mode => mode.value),
  });
  const [showPwdModal,  setShowPwdModal] = useState(false);
  const [pwdForm,       setPwdForm]      = useState({ current: '', next: '', confirm: '' });
  const [apiKeys,       setApiKeys]      = useState([
    { id: 1, name: 'Production Analytics Key', key: 'bk_live_8392_xxxx_xxxx_7721', status: 'active',  lastUsed: '14 mins ago',   created: 'Jan 12, 2024' },
    { id: 2, name: 'Development Sandbox',       key: 'bk_test_0019_xxxx_xxxx_1109', status: 'expired', lastUsed: 'Dec 30, 2023',  created: 'Oct 01, 2023' },
  ]);

  useEffect(() => {
    setBrandingForm({
      product_name: branding.product_name || 'BankAi',
      bank_name: branding.bank_name || 'Your Bank',
      logo_url: branding.logo_url || '',
      primary_color: branding.primary_color || '#17324d',
      accent_color: branding.accent_color || '#c7902c',
      welcome_message: branding.welcome_message || '',
      support_contact: branding.support_contact || '',
      disclaimer: branding.disclaimer || '',
      allowed_modes: branding.allowed_modes || MODE_OPTIONS.map(mode => mode.value),
    });
  }, [branding.product_name, branding.bank_name, branding.logo_url, branding.primary_color, branding.accent_color, branding.welcome_message, branding.support_contact, branding.disclaimer, branding.allowed_modes]);

  const handleSaveProfile = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.put('/auth/me', { name: form.name });
      const updated = { ...storedUser, name: form.name };
      localStorage.setItem('user', JSON.stringify(updated));
      localStorage.setItem('language', language);
      setSaveMsg('Profile saved successfully.');
      setTimeout(() => setSaveMsg(''), 3000);
    } catch {
      setSaveMsg('Failed to save changes.');
      setTimeout(() => setSaveMsg(''), 3000);
    } finally {
      setSaving(false);
    }
  };

  const handleSignOut = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  const handleSaveBranding = async (e) => {
    e.preventDefault();
    if (!storedUser.bank_id) {
      setBrandingMsg('No bank is attached to this user.');
      return;
    }
    setBrandingSaving(true);
    setBrandingMsg('');
    try {
      const response = await api.patch(`/config/branding/${storedUser.bank_id}`, brandingForm);
      branding.setBranding?.(response.data);
      setBrandingMsg('Branding saved.');
      setTimeout(() => setBrandingMsg(''), 3000);
    } catch (err) {
      setBrandingMsg(err.response?.data?.detail || 'Failed to save branding.');
      setTimeout(() => setBrandingMsg(''), 3000);
    } finally {
      setBrandingSaving(false);
    }
  };

  const toggleMode = (mode) => {
    setBrandingForm(current => {
      const selected = current.allowed_modes.includes(mode)
        ? current.allowed_modes.filter(item => item !== mode)
        : [...current.allowed_modes, mode];
      return { ...current, allowed_modes: selected.length ? selected : current.allowed_modes };
    });
  };

  const copyKey = (key) => {
    navigator.clipboard.writeText(key).catch(() => {});
  };

  const deleteKey = (id) => {
    setApiKeys(k => k.filter(x => x.id !== id));
  };

  const generateKey = () => {
    const rand = Math.random().toString(36).slice(2, 8);
    setApiKeys(k => [...k, {
      id:       Date.now(),
      name:     `API Key ${rand.toUpperCase()}`,
      key:      `bk_live_${rand}_xxxx_xxxx_${Math.floor(Math.random() * 9999)}`,
      status:   'active',
      lastUsed: 'Just now',
      created:  new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }),
    }]);
  };

  return (
    <div className="p-xl max-w-container-max mx-auto">
      <header className="mb-xl">
        <h1 className="font-h1 text-h1 text-on-surface mb-xs">Account Settings</h1>
        <p className="font-body-md text-body-md text-on-surface-variant">
          Manage your enterprise profile, security protocols, and API integrations.
        </p>
      </header>

      <div className="grid grid-cols-12 gap-gutter">
        {/* White-label branding */}
        <section className="col-span-12 bg-white border border-slate-200 rounded-lg p-lg relative overflow-hidden">
          <div className="absolute left-0 top-0 bottom-0 w-1 bg-secondary" />
          <form onSubmit={handleSaveBranding}>
            <div className="flex flex-col gap-md lg:flex-row lg:items-start lg:justify-between mb-lg">
              <div>
                <h2 className="font-h2 text-h2 text-on-surface mb-xs">White-Label Branding</h2>
                <p className="font-body-sm text-body-sm text-on-surface-variant">
                  Configure the bank-facing identity used across login, navigation, and chat.
                </p>
              </div>
              <div className="flex items-center gap-md">
                {brandingMsg && (
                  <span className={`text-body-sm font-medium ${brandingMsg.includes('Failed') || brandingMsg.includes('No bank') ? 'text-error' : 'text-on-tertiary-container'}`}>
                    {brandingMsg}
                  </span>
                )}
                <button type="submit" disabled={brandingSaving}
                  className="bg-primary text-white font-label-caps text-label-caps px-md py-sm rounded hover:opacity-90 transition-all disabled:opacity-50">
                  {brandingSaving ? 'Saving...' : 'Save Branding'}
                </button>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-md">
              <div className="space-y-xs">
                <label className="font-label-caps text-label-caps text-on-surface-variant uppercase block">Product Name</label>
                <input className="w-full bg-slate-50 border border-slate-200 rounded-lg text-body-md px-md py-sm focus:outline-none focus:border-secondary"
                  value={brandingForm.product_name}
                  onChange={e => setBrandingForm(f => ({ ...f, product_name: e.target.value }))}
                  required />
              </div>
              <div className="space-y-xs">
                <label className="font-label-caps text-label-caps text-on-surface-variant uppercase block">Bank Name</label>
                <input className="w-full bg-slate-50 border border-slate-200 rounded-lg text-body-md px-md py-sm focus:outline-none focus:border-secondary"
                  value={brandingForm.bank_name}
                  onChange={e => setBrandingForm(f => ({ ...f, bank_name: e.target.value }))}
                  required />
              </div>
              <div className="space-y-xs">
                <label className="font-label-caps text-label-caps text-on-surface-variant uppercase block">Primary Color</label>
                <input type="color" className="w-full h-11 bg-slate-50 border border-slate-200 rounded-lg px-sm py-xs"
                  value={brandingForm.primary_color}
                  onChange={e => setBrandingForm(f => ({ ...f, primary_color: e.target.value }))} />
              </div>
              <div className="space-y-xs">
                <label className="font-label-caps text-label-caps text-on-surface-variant uppercase block">Accent Color</label>
                <input type="color" className="w-full h-11 bg-slate-50 border border-slate-200 rounded-lg px-sm py-xs"
                  value={brandingForm.accent_color}
                  onChange={e => setBrandingForm(f => ({ ...f, accent_color: e.target.value }))} />
              </div>
              <div className="space-y-xs md:col-span-2">
                <label className="font-label-caps text-label-caps text-on-surface-variant uppercase block">Logo URL</label>
                <input className="w-full bg-slate-50 border border-slate-200 rounded-lg text-body-md px-md py-sm focus:outline-none focus:border-secondary"
                  value={brandingForm.logo_url}
                  onChange={e => setBrandingForm(f => ({ ...f, logo_url: e.target.value }))}
                  placeholder="/assets/bank-logo.png" />
              </div>
              <div className="space-y-xs md:col-span-2">
                <label className="font-label-caps text-label-caps text-on-surface-variant uppercase block">Support Contact</label>
                <input className="w-full bg-slate-50 border border-slate-200 rounded-lg text-body-md px-md py-sm focus:outline-none focus:border-secondary"
                  value={brandingForm.support_contact}
                  onChange={e => setBrandingForm(f => ({ ...f, support_contact: e.target.value }))}
                  placeholder="it-helpdesk@bank.local" />
              </div>
              <div className="space-y-xs md:col-span-2">
                <label className="font-label-caps text-label-caps text-on-surface-variant uppercase block">Welcome Message</label>
                <textarea className="w-full min-h-24 bg-slate-50 border border-slate-200 rounded-lg text-body-md px-md py-sm focus:outline-none focus:border-secondary resize-y"
                  value={brandingForm.welcome_message}
                  onChange={e => setBrandingForm(f => ({ ...f, welcome_message: e.target.value }))}
                  required />
              </div>
              <div className="space-y-xs md:col-span-2">
                <label className="font-label-caps text-label-caps text-on-surface-variant uppercase block">Disclaimer</label>
                <textarea className="w-full min-h-24 bg-slate-50 border border-slate-200 rounded-lg text-body-md px-md py-sm focus:outline-none focus:border-secondary resize-y"
                  value={brandingForm.disclaimer}
                  onChange={e => setBrandingForm(f => ({ ...f, disclaimer: e.target.value }))}
                  required />
              </div>
            </div>

            <div className="mt-lg">
              <p className="font-label-caps text-label-caps text-on-surface-variant uppercase mb-sm">Enabled Assistant Modes</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-sm">
                {MODE_OPTIONS.map(mode => (
                  <label key={mode.value} className="flex items-center gap-sm p-sm border border-slate-200 rounded-lg bg-slate-50 cursor-pointer">
                    <input type="checkbox"
                      checked={brandingForm.allowed_modes.includes(mode.value)}
                      onChange={() => toggleMode(mode.value)}
                      className="rounded-sm border-slate-300 text-secondary focus:ring-0 w-4 h-4" />
                    <span className="text-body-sm font-medium text-on-surface">{mode.label}</span>
                  </label>
                ))}
              </div>
            </div>
          </form>
        </section>

        {/* Profile card */}
        <section className="col-span-12 lg:col-span-8 bg-white border border-slate-200 rounded-lg p-lg relative overflow-hidden">
          <div className="absolute left-0 top-0 bottom-0 w-1 bg-secondary" />
          <form onSubmit={handleSaveProfile}>
            <div className="flex items-start justify-between mb-lg">
              <div>
                <h2 className="font-h2 text-h2 text-on-surface mb-xs">Profile Information</h2>
                <p className="font-body-sm text-body-sm text-on-surface-variant">
                  Update your personal details and organizational role.
                </p>
              </div>
              <div className="flex items-center gap-md">
                {saveMsg && (
                  <span className={`text-body-sm font-medium ${saveMsg.includes('Failed') ? 'text-error' : 'text-on-tertiary-container'}`}>
                    {saveMsg}
                  </span>
                )}
                <button type="submit" disabled={saving}
                  className="bg-primary text-white font-label-caps text-label-caps px-md py-sm rounded hover:opacity-90 transition-all disabled:opacity-50">
                  {saving ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </div>

            <div className="flex flex-col md:flex-row gap-xl items-start">
              {/* Avatar */}
              <div className="relative group flex-shrink-0">
                <div className="w-32 h-32 rounded-lg bg-primary-container flex items-center justify-center text-white text-4xl font-bold border-2 border-slate-100">
                  {form.name ? form.name.split(' ').map(p => p[0]).join('').slice(0, 2).toUpperCase() : 'U'}
                </div>
                <button type="button"
                  className="absolute -bottom-2 -right-2 bg-white shadow-sm border border-slate-200 p-xs rounded-full text-slate-600 hover:text-secondary transition-colors">
                  <span className="material-symbols-outlined text-[20px]">edit</span>
                </button>
              </div>

              {/* Form fields */}
              <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-md w-full">
                <div className="space-y-xs">
                  <label className="font-label-caps text-label-caps text-on-surface-variant uppercase block">Full Name</label>
                  <input
                    className="w-full bg-slate-50 border border-slate-200 focus:border-secondary focus:ring-0 focus:outline-none rounded-lg text-body-md px-md py-sm"
                    value={form.name}
                    onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                  />
                </div>
                <div className="space-y-xs">
                  <label className="font-label-caps text-label-caps text-on-surface-variant uppercase block">Email Address</label>
                  <input type="email" readOnly
                    className="w-full bg-slate-100 border border-slate-200 rounded-lg text-body-md px-md py-sm text-slate-500 cursor-not-allowed"
                    value={form.email}
                  />
                </div>
                <div className="space-y-xs">
                  <label className="font-label-caps text-label-caps text-on-surface-variant uppercase block">Department</label>
                  <select
                    className="w-full bg-slate-50 border border-slate-200 focus:border-secondary focus:ring-0 focus:outline-none rounded-lg text-body-md px-md py-sm"
                    value={form.department}
                    onChange={e => setForm(f => ({ ...f, department: e.target.value }))}
                  >
                    <option>Financial Audit & Compliance</option>
                    <option>Risk Management</option>
                    <option>Data Engineering</option>
                    <option>Treasury</option>
                    <option>Retail Operations</option>
                  </select>
                </div>
                <div className="space-y-xs">
                  <label className="font-label-caps text-label-caps text-on-surface-variant uppercase block">Language Preference</label>
                  <div className="flex items-center gap-sm mt-xs">
                    <span className={`font-body-sm text-body-sm ${language === 'en' ? 'text-on-surface font-semibold' : 'text-on-surface-variant'}`}>
                      English
                    </span>
                    <Toggle on={language === 'ne'} onChange={val => setLanguage(val ? 'ne' : 'en')} />
                    <span className={`font-body-sm text-body-sm ${language === 'ne' ? 'text-on-surface font-semibold' : 'text-on-surface-variant'}`}>
                      नेपाली
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </form>
        </section>

        {/* Security card */}
        <section className="col-span-12 lg:col-span-4 bg-white border border-slate-200 rounded-lg p-lg relative overflow-hidden flex flex-col">
          <div className="absolute left-0 top-0 bottom-0 w-1 bg-primary" />
          <h2 className="font-h2 text-h2 text-on-surface mb-xs">Security</h2>
          <p className="font-body-sm text-body-sm text-on-surface-variant mb-lg">
            Manage access and authentication protocols.
          </p>
          <div className="space-y-md flex-1">
            <div className="p-md bg-surface-container rounded-lg flex items-center justify-between border border-surface-variant">
              <div className="flex items-center gap-md">
                <span className="material-symbols-outlined text-secondary">verified_user</span>
                <div>
                  <p className="font-body-md font-semibold text-on-surface">2FA Status</p>
                  <p className="text-[10px] text-on-tertiary-container font-bold uppercase tracking-widest">Active & Verified</p>
                </div>
              </div>
              <span className="material-symbols-outlined text-on-tertiary-container"
                style={{ fontVariationSettings: "'FILL' 1" }}>check_circle</span>
            </div>
            <button onClick={() => setShowPwdModal(true)}
              className="w-full flex items-center justify-between p-md border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors text-left group">
              <div className="flex items-center gap-md">
                <span className="material-symbols-outlined text-slate-500 group-hover:text-primary transition-colors">key</span>
                <span className="font-body-md text-on-surface">Change Password</span>
              </div>
              <span className="material-symbols-outlined text-slate-400">chevron_right</span>
            </button>
            <button className="w-full flex items-center justify-between p-md border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors text-left group">
              <div className="flex items-center gap-md">
                <span className="material-symbols-outlined text-slate-500 group-hover:text-primary transition-colors">devices</span>
                <span className="font-body-md text-on-surface">Trusted Devices</span>
              </div>
              <span className="material-symbols-outlined text-slate-400">chevron_right</span>
            </button>
            <button onClick={handleSignOut}
              className="w-full flex items-center justify-between p-md border border-red-100 bg-red-50 rounded-lg hover:bg-error-container transition-colors text-left group">
              <div className="flex items-center gap-md">
                <span className="material-symbols-outlined text-error">logout</span>
                <span className="font-body-md text-error font-medium">Sign Out</span>
              </div>
              <span className="material-symbols-outlined text-red-300">chevron_right</span>
            </button>
          </div>
        </section>

        {/* Notifications */}
        <section className="col-span-12 lg:col-span-6 bg-white border border-slate-200 rounded-lg p-lg relative overflow-hidden">
          <div className="absolute left-0 top-0 bottom-0 w-1 bg-on-tertiary-container" />
          <h2 className="font-h2 text-h2 text-on-surface mb-xs">Notifications</h2>
          <p className="font-body-sm text-body-sm text-on-surface-variant mb-lg">
            Configure how and when you receive AI analysis updates.
          </p>
          <div className="space-y-lg">
            {NOTIFICATIONS.map((notif, i) => (
              <div key={notif.key} className={`flex items-center justify-between ${i < NOTIFICATIONS.length - 1 ? 'pb-md border-b border-slate-100' : ''}`}>
                <div>
                  <p className="font-body-md font-semibold text-on-surface">{notif.label}</p>
                  <p className="text-xs text-on-surface-variant">{notif.desc}</p>
                </div>
                <div className="flex gap-md flex-shrink-0 ml-4">
                  {['app', 'email'].map(channel => (
                    <div key={channel} className="flex flex-col items-center gap-xs">
                      <span className="text-[10px] font-bold text-slate-400 uppercase">{channel}</span>
                      <input
                        type="checkbox"
                        checked={notifs[`${notif.key}_${channel}`] || false}
                        onChange={e => setNotifs(n => ({ ...n, [`${notif.key}_${channel}`]: e.target.checked }))}
                        className="rounded-sm border-slate-300 text-secondary focus:ring-0 w-4 h-4 cursor-pointer"
                      />
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* API Keys */}
        <section className="col-span-12 lg:col-span-6 bg-white border border-slate-200 rounded-lg p-lg relative overflow-hidden">
          <div className="absolute left-0 top-0 bottom-0 w-1 bg-surface-tint" />
          <div className="flex items-start justify-between mb-lg">
            <div>
              <h2 className="font-h2 text-h2 text-on-surface mb-xs">Personal API Keys</h2>
              <p className="font-body-sm text-body-sm text-on-surface-variant">
                Connect BankAi engine to your local scripts and tools.
              </p>
            </div>
            <button onClick={generateKey}
              className="border border-slate-300 text-slate-700 font-label-caps text-label-caps px-md py-sm rounded hover:bg-slate-50 transition-all flex items-center gap-xs">
              <span className="material-symbols-outlined text-[18px]">add</span>
              Generate New
            </button>
          </div>
          <div className="space-y-md">
            {apiKeys.map(apiKey => (
              <div key={apiKey.id} className={`p-md border border-slate-100 rounded-lg ${apiKey.status === 'expired' ? 'opacity-50 grayscale' : 'bg-slate-50'}`}>
                <div className="flex items-center justify-between mb-sm">
                  <span className="font-body-sm font-semibold text-on-surface">{apiKey.name}</span>
                  <span className={`px-sm py-xs rounded text-[10px] font-bold uppercase ${
                    apiKey.status === 'active'
                      ? 'bg-on-tertiary-container/10 text-on-tertiary-container'
                      : 'bg-slate-200 text-slate-600'
                  }`}>
                    {apiKey.status}
                  </span>
                </div>
                <div className="flex items-center gap-md">
                  <code className="flex-1 font-mono text-xs text-slate-600 bg-white p-sm rounded border border-slate-200 select-all overflow-hidden">
                    {apiKey.key}
                  </code>
                  <button onClick={() => copyKey(apiKey.key)}
                    className="text-slate-400 hover:text-secondary transition-colors flex-shrink-0">
                    <span className="material-symbols-outlined text-[20px]">content_copy</span>
                  </button>
                  <button onClick={() => deleteKey(apiKey.id)}
                    className="text-slate-400 hover:text-error transition-colors flex-shrink-0">
                    <span className="material-symbols-outlined text-[20px]">delete</span>
                  </button>
                </div>
                <p className="mt-sm text-[11px] text-slate-400">
                  {apiKey.status === 'expired'
                    ? `Expired: ${apiKey.lastUsed}`
                    : `Last used: ${apiKey.lastUsed} • Created: ${apiKey.created}`}
                </p>
              </div>
            ))}
          </div>
        </section>
      </div>

      {/* Footer */}
      <footer className="mt-xl pt-lg border-t border-slate-200 flex flex-col md:flex-row justify-between items-center gap-md text-on-surface-variant font-body-sm">
        <p>© 2024 BankAi Enterprise Solutions. All rights reserved.</p>
        <div className="flex gap-lg">
          <button type="button" onClick={() => navigate('/admin/security')} className="hover:text-primary transition-colors">
            Security Policy
          </button>
          <button type="button" onClick={() => navigate('/help')} className="hover:text-primary transition-colors">
            API Documentation
          </button>
          <button type="button" onClick={() => navigate('/audit')} className="hover:text-primary transition-colors">
            Audit Log Export
          </button>
        </div>
      </footer>

      {/* Password change modal */}
      {showPwdModal && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-sm p-lg">
            <div className="flex justify-between items-center mb-lg">
              <h3 className="text-h2 font-h2 text-on-surface">Change Password</h3>
              <button onClick={() => setShowPwdModal(false)}
                className="material-symbols-outlined text-slate-400 hover:text-slate-900 cursor-pointer">
                close
              </button>
            </div>
            <form onSubmit={e => { e.preventDefault(); setShowPwdModal(false); }} className="space-y-md">
              {[
                { key: 'current', label: 'Current Password' },
                { key: 'next',    label: 'New Password' },
                { key: 'confirm', label: 'Confirm New Password' },
              ].map(({ key, label }) => (
                <div key={key}>
                  <label className="font-label-caps text-label-caps text-on-surface-variant uppercase block mb-xs">{label}</label>
                  <input type="password" required
                    className="w-full bg-slate-50 border border-slate-200 rounded-lg px-md py-sm text-body-sm focus:outline-none focus:ring-2 focus:ring-secondary"
                    value={pwdForm[key]}
                    onChange={e => setPwdForm(f => ({ ...f, [key]: e.target.value }))}
                  />
                </div>
              ))}
              <div className="flex gap-md pt-md">
                <button type="button" onClick={() => setShowPwdModal(false)}
                  className="flex-1 py-sm border border-slate-300 rounded-lg font-label-caps text-label-caps text-on-surface hover:bg-slate-50 transition-colors">
                  Cancel
                </button>
                <button type="submit"
                  className="flex-1 py-sm bg-primary text-white rounded-lg font-label-caps text-label-caps hover:bg-slate-800 transition-colors">
                  Update Password
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
