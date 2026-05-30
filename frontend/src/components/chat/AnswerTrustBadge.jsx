const TRUST_STATES = {
  official_source_backed: {
    label: 'Official source-backed',
    icon: 'verified',
    className: 'bg-emerald-50 text-emerald-800 border-emerald-200',
  },
  uploaded_file_answer: {
    label: 'Uploaded-file answer',
    icon: 'draft',
    className: 'bg-sky-50 text-sky-800 border-sky-200',
  },
  general_answer: {
    label: 'General answer',
    icon: 'info',
    className: 'bg-slate-50 text-slate-700 border-slate-200',
  },
  unsupported_source: {
    label: 'Source support incomplete',
    icon: 'rule',
    className: 'bg-amber-50 text-amber-800 border-amber-200',
  },
  not_found: {
    label: 'Not found in approved sources',
    icon: 'find_in_page',
    className: 'bg-amber-50 text-amber-800 border-amber-200',
  },
  escalate: {
    label: 'Escalate',
    icon: 'report',
    className: 'bg-rose-50 text-rose-800 border-rose-200',
  },
  capacity_busy: {
    label: 'Capacity busy',
    icon: 'hourglass_top',
    className: 'bg-amber-50 text-amber-800 border-amber-200',
  },
};

const CITATION_STATES = {
  supported: {
    label: 'Citations verified',
    icon: 'fact_check',
    className: 'bg-emerald-50 text-emerald-800 border-emerald-200',
  },
  partially_supported: {
    label: 'Partially supported',
    icon: 'rule',
    className: 'bg-amber-50 text-amber-800 border-amber-200',
  },
  not_enough_claims: {
    label: 'Low claim content',
    icon: 'notes',
    className: 'bg-slate-50 text-slate-700 border-slate-200',
  },
  no_sources: {
    label: 'No source verification',
    icon: 'info',
    className: 'bg-slate-50 text-slate-700 border-slate-200',
  },
};

const TRUST_LABEL_COPY = {
  source_supported: 'Source supported',
  partially_source_supported: 'Partially source supported',
  not_source_supported: 'Not source supported',
  no_sources: 'No sources',
  source_unverified: 'Source unverified',
};

function trustLabelState(label) {
  if (!label) return null;
  if (label === 'source_supported') {
    return {
      label: TRUST_LABEL_COPY[label],
      icon: 'verified',
      className: 'bg-emerald-50 text-emerald-800 border-emerald-200',
    };
  }
  if (label === 'not_source_supported') {
    return {
      label: TRUST_LABEL_COPY[label],
      icon: 'error',
      className: 'bg-rose-50 text-rose-800 border-rose-200',
    };
  }
  return {
    label: TRUST_LABEL_COPY[label] || label,
    icon: 'rule',
    className: 'bg-amber-50 text-amber-800 border-amber-200',
  };
}

function inferAnswerType(message) {
  if (message?.answer_metadata?.answer_type) return message.answer_metadata.answer_type;
  if (message?.sources?.length > 0) return 'official_source_backed';
  if (message?.id === 'welcome') return null;
  return 'general_answer';
}

function citationState(message) {
  const status = message?.answer_metadata?.citation_verification?.status;
  if (status) return CITATION_STATES[status] || null;
  const sourceStatus = message?.sources?.find(source => source?.citation_verification)?.citation_verification;
  return sourceStatus ? CITATION_STATES[sourceStatus] || null : null;
}

export default function AnswerTrustBadge({ message }) {
  const answerType = inferAnswerType(message);
  if (!answerType) return null;

  const state = TRUST_STATES[answerType] || TRUST_STATES.general_answer;
  const sourceCount = message?.answer_metadata?.source_count ?? message?.sources?.length ?? 0;
  const citation = citationState(message);
  const trustLabel = trustLabelState(message?.answer_metadata?.trust_label);

  return (
    <div className="flex flex-wrap items-center gap-1.5">
      <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded border text-[11px] font-semibold ${state.className}`}>
        <span className="material-symbols-outlined text-[14px]">{state.icon}</span>
        <span>{state.label}</span>
        {sourceCount > 0 && <span className="opacity-70">· {sourceCount} source{sourceCount === 1 ? '' : 's'}</span>}
      </div>
      {citation && sourceCount > 0 && (
        <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded border text-[11px] font-semibold ${citation.className}`}>
          <span className="material-symbols-outlined text-[14px]">{citation.icon}</span>
          <span>{citation.label}</span>
        </div>
      )}
      {trustLabel && (
        <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded border text-[11px] font-semibold ${trustLabel.className}`}>
          <span className="material-symbols-outlined text-[14px]">{trustLabel.icon}</span>
          <span>{trustLabel.label}</span>
        </div>
      )}
    </div>
  );
}
