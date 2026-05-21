function sourceLocation(source) {
  const parts = [];
  if (source.section_label || source.section_number) parts.push(source.section_label || source.section_number);
  if (source.page_number) parts.push(`p.${source.page_number}`);
  if (!parts.length && Number.isInteger(source.chunk_index)) parts.push(`chunk ${source.chunk_index + 1}`);
  return parts.join(' · ');
}

const VERIFICATION_STYLES = {
  supported: {
    label: 'Verified',
    icon: 'verified',
    className: 'bg-emerald-50 text-emerald-800 border-emerald-200',
  },
  partially_supported: {
    label: 'Partial',
    icon: 'rule',
    className: 'bg-amber-50 text-amber-800 border-amber-200',
  },
  no_sources: {
    label: 'Unchecked',
    icon: 'info',
    className: 'bg-slate-50 text-slate-700 border-slate-200',
  },
  not_enough_claims: {
    label: 'Low claims',
    icon: 'notes',
    className: 'bg-slate-50 text-slate-700 border-slate-200',
  },
};

const WARNING_STYLES = {
  expired_source: {
    label: 'Expired',
    icon: 'event_busy',
    className: 'bg-rose-50 text-rose-800 border-rose-200',
  },
  review_due: {
    label: 'Review due',
    icon: 'pending_actions',
    className: 'bg-amber-50 text-amber-800 border-amber-200',
  },
  superseded_source: {
    label: 'Superseded',
    icon: 'history',
    className: 'bg-slate-100 text-slate-700 border-slate-200',
  },
  not_yet_effective: {
    label: 'Not effective yet',
    icon: 'event_upcoming',
    className: 'bg-sky-50 text-sky-800 border-sky-200',
  },
};

function VerificationPill({ status }) {
  const state = VERIFICATION_STYLES[status] || VERIFICATION_STYLES.no_sources;
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded border text-[10px] font-bold uppercase ${state.className}`}>
      <span className="material-symbols-outlined text-[12px]">{state.icon}</span>
      {state.label}
    </span>
  );
}

function WarningPills({ warnings = [] }) {
  if (!warnings.length) return null;
  return (
    <div className="mt-2 flex flex-wrap gap-1.5">
      {warnings.map((warning) => {
        const state = WARNING_STYLES[warning] || {
          label: warning,
          icon: 'warning',
          className: 'bg-amber-50 text-amber-800 border-amber-200',
        };
        return (
          <span key={warning} className={`inline-flex items-center gap-1 px-2 py-0.5 rounded border text-[10px] font-bold uppercase ${state.className}`}>
            <span className="material-symbols-outlined text-[12px]">{state.icon}</span>
            {state.label}
          </span>
        );
      })}
    </div>
  );
}

function confidenceLabel(value) {
  if (value === null || value === undefined || value === '') return null;
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return null;
  return `${Math.round(Math.max(0, Math.min(numeric, 1)) * 100)}%`;
}

function SourceCard({ source, index }) {
  const passage = source.passage || source.snippet || '';
  const preview = source.snippet || passage.slice(0, 180);
  const canExpand = passage && passage.length > preview.length;
  const relevance = Number(source.relevance_score || 0);
  const extractionConfidence = confidenceLabel(source.extraction_confidence);
  const ocrConfidence = confidenceLabel(source.ocr_confidence);
  const tableConfidence = confidenceLabel(source.table_confidence);

  return (
    <article key={`${source.document_id || source.title || 'source'}-${index}`} className="bg-white border border-slate-200 rounded p-3">
      <div className="flex items-start gap-2">
        <span className="material-symbols-outlined text-secondary text-[18px] mt-0.5">description</span>
        <div className="min-w-0 flex-1">
          <h3 className="text-xs font-semibold text-on-surface truncate">
            {source.document_title || source.title || 'Source'}
          </h3>
          {sourceLocation(source) && (
            <p className="text-[10px] text-slate-500 font-label-caps uppercase tracking-wider mt-0.5">
              {sourceLocation(source)}
            </p>
          )}
        </div>
        <VerificationPill status={source.citation_verification} />
      </div>
      <WarningPills warnings={source.source_warnings || []} />
      <div className="mt-3 grid grid-cols-2 gap-2 text-[10px] text-slate-500">
        <div className="rounded bg-slate-50 border border-slate-100 px-2 py-1">
          <span className="font-bold text-slate-700">Doc ID:</span> {source.document_id || '—'}
        </div>
        <div className="rounded bg-slate-50 border border-slate-100 px-2 py-1">
          <span className="font-bold text-slate-700">Score:</span> {relevance ? relevance.toFixed(2) : '—'}
        </div>
        {(source.regulator || source.jurisdiction) && (
          <div className="rounded bg-slate-50 border border-slate-100 px-2 py-1 col-span-2">
            <span className="font-bold text-slate-700">Scope:</span> {[source.regulator, source.jurisdiction].filter(Boolean).join(' · ')}
          </div>
        )}
        {(extractionConfidence || ocrConfidence || tableConfidence) && (
          <div className="rounded bg-slate-50 border border-slate-100 px-2 py-1 col-span-2">
            <span className="font-bold text-slate-700">Confidence:</span>{' '}
            {[
              extractionConfidence && `extract ${extractionConfidence}`,
              ocrConfidence && `ocr ${ocrConfidence}`,
              tableConfidence && `table ${tableConfidence}`,
            ].filter(Boolean).join(' · ')}
          </div>
        )}
      </div>
      {passage && (
        <details className="mt-3 group">
          <summary className="cursor-pointer list-none text-xs leading-relaxed text-slate-600 border-l-2 border-slate-200 pl-3">
            <span>{preview}</span>
            {canExpand && (
              <span className="mt-2 inline-flex items-center gap-1 text-[10px] font-semibold uppercase tracking-wider text-secondary">
                <span className="group-open:hidden">View passage</span>
                <span className="hidden group-open:inline">Hide passage</span>
                <span className="material-symbols-outlined text-[14px] group-open:rotate-180 transition-transform">expand_more</span>
              </span>
            )}
          </summary>
          {canExpand && (
            <p className="mt-2 text-xs leading-relaxed text-slate-700 bg-slate-50 border border-slate-200 rounded p-3 whitespace-pre-wrap">
              {passage}
            </p>
          )}
          {!canExpand && passage && (
            <p className="mt-2 text-xs leading-relaxed text-slate-700 bg-slate-50 border border-slate-200 rounded p-3 whitespace-pre-wrap">
              {passage}
            </p>
          )}
        </details>
      )}
    </article>
  );
}

export default function SourceEvidencePanel({ sources = [], compact = false }) {
  if (!sources.length) {
    return (
      <aside className={compact ? 'hidden' : 'hidden xl:flex w-80 flex-col bg-slate-50 border-l border-slate-200'}>
        <div className="p-4 border-b border-slate-200 bg-white">
          <h2 className="text-sm font-semibold text-on-surface">Evidence</h2>
          <p className="text-xs text-slate-500 mt-1">Sources from the selected answer appear here.</p>
        </div>
        <div className="p-4 text-xs text-slate-500">No source-backed answer selected.</div>
      </aside>
    );
  }

  const content = (
    <>
      <div className="p-4 border-b border-slate-200 bg-white">
        <h2 className="text-sm font-semibold text-on-surface">Evidence</h2>
        <p className="text-xs text-slate-500 mt-1">{sources.length} cited source{sources.length === 1 ? '' : 's'}</p>
      </div>
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {sources.map((source, index) => <SourceCard key={`${source.document_id || source.title || 'source'}-${index}`} source={source} index={index} />)}
      </div>
    </>
  );

  if (compact) {
    return <div className="mt-3 border border-slate-200 rounded bg-slate-50 overflow-hidden xl:hidden">{content}</div>;
  }

  return <aside className="hidden xl:flex w-80 flex-col bg-slate-50 border-l border-slate-200">{content}</aside>;
}
