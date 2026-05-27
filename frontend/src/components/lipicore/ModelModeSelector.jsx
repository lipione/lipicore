// Model modes map to private Lipi model routes on the backend
export const MODEL_MODES = [
  {
    id: 'auto',
    label: 'Auto',
    icon: 'auto_awesome',
    model: null, // backend decides
    description: 'LipiCore picks the right model for your query',
    badge: null,
  },
  {
    id: 'fast',
    label: 'LipiFast',
    icon: 'bolt',
    model: 'LipiFast',
    description: 'Fast staff chat and drafting',
    badge: 'DEFAULT',
  },
  {
    id: 'analyst',
    label: 'LipiCore',
    icon: 'psychology',
    model: 'LipiCore',
    description: 'Deeper analysis and approved-knowledge work',
    badge: 'ON-DEMAND',
  },
  {
    id: 'report',
    label: 'Report',
    icon: 'article',
    model: 'LipiCore',
    description: 'LipiCore long-form drafting and reports',
    badge: 'ON-DEMAND',
  },
];

export default function ModelModeSelector({ value, onChange, compact = false }) {
  const selected = MODEL_MODES.find((m) => m.id === value) || MODEL_MODES[0];

  if (compact) {
    return (
      <div className="flex items-center gap-1 bg-slate-100 rounded-lg p-1">
        {MODEL_MODES.map((mode) => (
          <button
            key={mode.id}
            type="button"
            onClick={() => onChange(mode.id)}
            title={mode.description}
            className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded text-xs font-semibold transition-all ${
              value === mode.id
                ? 'bg-white text-slate-900 shadow-sm ring-1 ring-slate-200'
                : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            <span className="material-symbols-outlined text-[14px]">{mode.icon}</span>
            {mode.label}
          </button>
        ))}
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-1">
      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest px-1">Model Mode</p>
      <div className="flex gap-2">
        {MODEL_MODES.map((mode) => (
          <button
            key={mode.id}
            type="button"
            onClick={() => onChange(mode.id)}
            className={`flex-1 flex flex-col items-center gap-1 p-3 rounded-lg border text-center transition-all ${
              value === mode.id
                ? 'bg-primary-container/20 border-primary text-slate-900 shadow-sm'
                : 'bg-white border-slate-200 text-slate-600 hover:border-slate-300 hover:bg-slate-50'
            }`}
          >
            <span className={`material-symbols-outlined text-[22px] ${value === mode.id ? 'text-primary' : 'text-slate-400'}`}>
              {mode.icon}
            </span>
            <span className="text-xs font-bold">{mode.label}</span>
            {mode.badge && (
              <span className={`text-[9px] font-bold px-1 rounded ${
                mode.badge === 'DEFAULT' ? 'bg-green-100 text-green-700' : 'bg-amber-50 text-amber-600'
              }`}>
                {mode.badge}
              </span>
            )}
          </button>
        ))}
      </div>
      <p className="text-[11px] text-slate-500 px-1 mt-0.5">{selected.description}</p>
    </div>
  );
}
