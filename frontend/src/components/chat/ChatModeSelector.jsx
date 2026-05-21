export const CHAT_MODES = [
  {
    value: 'ask_knowledge',
    label: 'Ask BankAi',
    icon: 'policy',
    description: 'General chat that cites approved knowledge when it matches.',
    prompt: 'Tell me about ',
  },
  {
    value: 'approved_knowledge',
    label: 'Approved Knowledge',
    icon: 'verified',
    description: 'Strict answers only from approved bank documents.',
    prompt: 'What do approved documents say about ',
  },
  {
    value: 'analyze_file',
    label: 'Analyze File',
    icon: 'plagiarism',
    description: 'Ask questions about uploaded session files.',
    prompt: 'Analyze this uploaded file and tell me ',
  },
  {
    value: 'summarize',
    label: 'Summarize',
    icon: 'summarize',
    description: 'Create concise staff-ready summaries.',
    prompt: 'Summarize the key points for staff: ',
  },
  {
    value: 'draft',
    label: 'Draft',
    icon: 'edit_note',
    description: 'Draft emails, notices, memos, and scripts.',
    prompt: 'Draft a staff-ready response for ',
  },
  {
    value: 'translate',
    label: 'Translate',
    icon: 'translate',
    description: 'Translate English and Nepali banking text.',
    prompt: 'Translate this while preserving banking terms: ',
  },
  {
    value: 'compare',
    label: 'Compare',
    icon: 'compare_arrows',
    description: 'Compare policies, circulars, or uploaded files.',
    prompt: 'Compare these documents and show the differences: ',
  },
];

export function modeByValue(value) {
  return CHAT_MODES.find(mode => mode.value === value) || CHAT_MODES[0];
}

export default function ChatModeSelector({ allowedModes = [], selectedMode, onChange, disabled }) {
  const visibleModes = CHAT_MODES.filter(mode => allowedModes.includes(mode.value));
  const modes = visibleModes.length ? visibleModes : CHAT_MODES;

  return (
    <div className="flex items-center gap-1 overflow-x-auto hide-scrollbar" aria-label="Chat modes">
      {modes.map(mode => {
        const active = mode.value === selectedMode;
        return (
          <button
            key={mode.value}
            type="button"
            onClick={() => onChange(mode.value)}
            disabled={disabled}
            title={mode.description}
            className={`h-9 inline-flex items-center gap-1.5 px-3 rounded border text-xs font-semibold whitespace-nowrap transition-colors ${
              active
                ? 'border-primary bg-primary text-white'
                : 'border-slate-200 bg-white text-slate-600 hover:border-secondary hover:text-secondary'
            } disabled:opacity-50`}
          >
            <span className="material-symbols-outlined text-[16px]">{mode.icon}</span>
            {mode.label}
          </button>
        );
      })}
    </div>
  );
}
