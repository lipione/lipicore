const BADGES = {
  official_source_backed: {
    icon: 'verified',
    label: 'Source-backed',
    className: 'border-emerald-200 bg-emerald-50 text-emerald-700',
  },
  uploaded_file_answer: {
    icon: 'attach_file',
    label: 'Uploaded file',
    className: 'border-blue-200 bg-blue-50 text-blue-700',
  },
  not_found: {
    icon: 'search_off',
    label: 'Not found in approved sources',
    className: 'border-amber-200 bg-amber-50 text-amber-800',
  },
  unsupported_source: {
    icon: 'report',
    label: 'Needs source review',
    className: 'border-red-200 bg-red-50 text-red-700',
  },
  general_answer: {
    icon: 'info',
    label: 'General answer',
    className: 'border-slate-200 bg-slate-50 text-slate-700',
  },
};

export default function AnswerTrustBadge({ answerType, trustLabel }) {
  const badge = BADGES[answerType] || BADGES.general_answer;
  const label = trustLabel && trustLabel !== 'source_supported'
    ? `${badge.label} · ${trustLabel.replaceAll('_', ' ')}`
    : badge.label;

  return (
    <span className={`inline-flex items-center gap-1 rounded border px-2 py-0.5 text-xs font-semibold ${badge.className}`}>
      <span className="material-symbols-outlined text-[14px]">{badge.icon}</span>
      {label}
    </span>
  );
}
