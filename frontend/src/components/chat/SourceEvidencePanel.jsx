import { useCallback, useEffect, useId, useRef, useState } from 'react';
import api from '../../api/axios';
import {
  confidenceLabel,
  formatSourceCitation,
  hasCitationValue,
  sourceLocationLabel,
  sourcePdfPage,
  sourceTitle,
} from '../../utils/sourceCitation';
import SourceMetadataStrip from '../trust/SourceMetadataStrip';

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
  unsupported: {
    label: 'Unsupported',
    icon: 'gpp_bad',
    className: 'bg-rose-50 text-rose-800 border-rose-200',
  },
  citation_incomplete: {
    label: 'Citation incomplete',
    icon: 'rule_settings',
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
  unknown: {
    label: 'Unknown',
    icon: 'help',
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

const FOCUSABLE_SELECTOR = [
  'a[href]',
  'button:not([disabled])',
  'input:not([disabled])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
].join(',');

function VerificationPill({ status }) {
  const state = VERIFICATION_STYLES[status] || VERIFICATION_STYLES.unknown;
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

function SourceRiskWarning({ source }) {
  if (!source.source_risk_level || source.source_risk_level === 'low') return null;
  return (
    <div className="mt-2">
      <span className="inline-flex items-center gap-1 rounded border border-amber-200 bg-amber-50 px-2 py-0.5 text-[10px] font-bold uppercase text-amber-800">
        <span className="material-symbols-outlined text-[12px]">gpp_maybe</span>
        Source warning: {source.source_risk_level}
      </span>
    </div>
  );
}

function sourcePath(source) {
  if (!source?.document_id) return null;
  const params = new URLSearchParams();
  const pdfPage = sourcePdfPage(source);
  if (hasCitationValue(pdfPage)) {
    params.set('page_number', pdfPage);
  }
  if (source.chunk_index !== null && source.chunk_index !== undefined) {
    params.set('chunk_index', source.chunk_index);
  }
  const query = params.toString();
  return `/documents/${source.document_id}/source${query ? `?${query}` : ''}`;
}

function sourceFileUrl(source) {
  if (!source?.document_id) return null;
  const baseUrl = source.source_file_url || `/api/documents/${source.document_id}/file`;
  const pdfPage = sourcePdfPage(source);
  const looksLikePdf = String(source.file_type || source.file_name || '').toLowerCase().includes('pdf');
  if (looksLikePdf && hasCitationValue(pdfPage)) {
    return `${baseUrl}#page=${pdfPage}`;
  }
  return baseUrl;
}

function sourceFileActionLabel(source) {
  const type = String(source?.file_type || source?.file_name || '').toLowerCase();
  if (type.includes('pdf')) return 'Open PDF';
  return 'Open file';
}

function copyTextToClipboard(text) {
  if (!text) return Promise.resolve();
  if (navigator.clipboard?.writeText) return navigator.clipboard.writeText(text);
  const textarea = document.createElement('textarea');
  textarea.value = text;
  textarea.setAttribute('readonly', '');
  textarea.style.position = 'fixed';
  textarea.style.opacity = '0';
  document.body.appendChild(textarea);
  textarea.select();
  document.execCommand('copy');
  document.body.removeChild(textarea);
  return Promise.resolve();
}

function SourceViewerModal({ viewer, onClose }) {
  const titleId = useId();
  const descriptionId = useId();
  const dialogRef = useRef(null);
  const closeButtonRef = useRef(null);
  const openerRef = useRef(null);

  const closeModal = useCallback(() => {
    const opener = openerRef.current;
    onClose();
    window.setTimeout(() => opener?.focus?.(), 0);
  }, [onClose]);

  useEffect(() => {
    if (!viewer.source) return undefined;
    openerRef.current = document.activeElement;

    const handleKeyDown = (event) => {
      if (event.key === 'Escape') {
        event.preventDefault();
        closeModal();
        return;
      }
      if (event.key !== 'Tab') return;

      const focusable = Array.from(dialogRef.current?.querySelectorAll(FOCUSABLE_SELECTOR) || [])
        .filter((element) => element.offsetParent !== null || element === document.activeElement);
      if (!focusable.length) {
        event.preventDefault();
        dialogRef.current?.focus();
        return;
      }

      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [closeModal, viewer.source]);

  useEffect(() => {
    if (viewer.source) closeButtonRef.current?.focus();
  }, [viewer.source]);

  if (!viewer.source) return null;
  const chunks = viewer.data?.chunks || [];
  const document = viewer.data?.document || viewer.source;
  const citationText = formatSourceCitation(viewer.source);
  const fileUrl = sourceFileUrl(viewer.source);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/30 px-4">
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={descriptionId}
        tabIndex={-1}
        className="w-full max-w-4xl max-h-[84vh] bg-white border border-slate-200 rounded-lg shadow-xl flex flex-col"
      >
        <div className="flex items-start justify-between gap-4 p-5 border-b border-slate-200 flex-shrink-0">
          <div className="min-w-0">
            <p id={titleId} className="text-sm font-bold text-slate-900 truncate">{document.title || document.document_title || sourceTitle(viewer.source)}</p>
            <p id={descriptionId} className="text-xs text-slate-500 truncate">
              {[document.file_name, sourceLocationLabel(viewer.source)].filter(Boolean).join(' · ')}
            </p>
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            {fileUrl && (
              <a
                href={fileUrl}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 rounded border border-slate-200 bg-white px-2.5 py-1 text-[11px] font-semibold text-slate-700 hover:border-secondary hover:text-secondary"
              >
                <span className="material-symbols-outlined text-[14px]">open_in_new</span>
                {sourceFileActionLabel(viewer.source)}
              </a>
            )}
            <button
              type="button"
              onClick={() => copyTextToClipboard(citationText)}
              className="inline-flex items-center gap-1.5 rounded border border-slate-200 bg-white px-2.5 py-1 text-[11px] font-semibold text-slate-700 hover:border-secondary hover:text-secondary"
            >
              <span className="material-symbols-outlined text-[14px]">content_copy</span>
              Copy citation
            </button>
            <button
              ref={closeButtonRef}
              type="button"
              onClick={closeModal}
              className="p-1 rounded text-slate-400 hover:text-slate-700 hover:bg-slate-100"
              aria-label="Close source viewer"
              title="Close"
            >
              <span className="material-symbols-outlined text-[20px]">close</span>
            </button>
          </div>
        </div>
        <div className="p-5 overflow-y-auto space-y-3">
          <div className="rounded border border-slate-200 bg-slate-50 px-3 py-2">
            <p className="font-label-caps text-[10px] uppercase tracking-wider text-slate-500">Citation line</p>
            <p className="mt-1 text-xs leading-5 text-slate-700 break-words">{citationText}</p>
          </div>
          {viewer.loading && (
            <div className="flex items-center gap-2 text-sm text-slate-500">
              <span className="w-4 h-4 border-2 border-slate-200 border-t-secondary rounded-full animate-spin" />
              Loading source
            </div>
          )}
          {viewer.error && (
            <div className="rounded border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
              {viewer.error}
            </div>
          )}
          {!viewer.loading && !viewer.error && chunks.length === 0 && (
            <div className="rounded border border-slate-200 bg-slate-50 p-3 text-sm text-slate-600">
              No source passage available for this citation.
            </div>
          )}
          {chunks.map((chunk) => {
            const pdfPage = sourcePdfPage(chunk);
            return (
              <article key={chunk.id || chunk.chunk_index} className="rounded border border-slate-200 bg-slate-50 p-4">
                <div className="mb-3 flex flex-wrap items-center gap-2 text-[10px] font-bold uppercase text-slate-500">
                  <span>Chunk {Number.isInteger(chunk.chunk_index) ? chunk.chunk_index + 1 : '—'}</span>
                  {hasCitationValue(pdfPage) ? <span>PDF page {pdfPage}</span> : null}
                  {hasCitationValue(chunk.printed_page_number) ? <span>Printed page {chunk.printed_page_number}</span> : null}
                  {chunk.document_heading ? <span>{chunk.document_heading}</span> : null}
                  {chunk.clause_number ? <span>{chunk.clause_number}</span> : null}
                  {chunk.document_status && chunk.version_state ? <span>Status {chunk.document_status}/{chunk.version_state}</span> : null}
                  {chunk.extraction_confidence !== null && chunk.extraction_confidence !== undefined && (
                    <span>Extract {confidenceLabel(chunk.extraction_confidence)}</span>
                  )}
                  {chunk.ocr_confidence !== null && chunk.ocr_confidence !== undefined && (
                    <span>OCR {confidenceLabel(chunk.ocr_confidence)}</span>
                  )}
                </div>
                <p className="whitespace-pre-wrap break-words text-sm leading-6 text-slate-800">
                  {chunk.text}
                </p>
              </article>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function SourceCard({ source, index, onOpenSource }) {
  const [copied, setCopied] = useState(false);
  const passage = source.passage || source.snippet || '';
  const preview = source.snippet || passage.slice(0, 180);
  const canExpand = passage && passage.length > preview.length;
  const relevance = Number(source.relevance_score || 0);
  const extractionConfidence = confidenceLabel(source.extraction_confidence);
  const ocrConfidence = confidenceLabel(source.ocr_confidence);
  const tableConfidence = confidenceLabel(source.table_confidence);
  const citationText = formatSourceCitation(source);
  const locationLabel = sourceLocationLabel(source);
  const fileUrl = sourceFileUrl(source);

  const copyCitation = async () => {
    await copyTextToClipboard(citationText);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1600);
  };

  return (
    <article key={`${source.document_id || source.title || 'source'}-${index}`} className="bg-white border border-slate-200 rounded p-3">
      <div className="flex items-start gap-2">
        <span className="material-symbols-outlined text-secondary text-[18px] mt-0.5">description</span>
        <div className="min-w-0 flex-1">
          <h3 className="text-xs font-semibold text-on-surface truncate">
            {sourceTitle(source)}
          </h3>
          {locationLabel && (
            <p className="text-[10px] text-slate-500 font-label-caps uppercase tracking-wider mt-0.5">
              {locationLabel}
            </p>
          )}
        </div>
        <VerificationPill status={source.citation_verification} />
      </div>
      <WarningPills warnings={source.source_warnings || []} />
      <SourceRiskWarning source={source} />
      <div className="mt-2">
        <SourceMetadataStrip source={source} />
      </div>
      <div className="mt-3 rounded border border-slate-200 bg-slate-50 px-2.5 py-2">
        <div className="flex items-center justify-between gap-2">
          <p className="font-label-caps text-[10px] uppercase tracking-wider text-slate-500">Citation</p>
          <button
            type="button"
            onClick={copyCitation}
            className="inline-flex items-center gap-1 rounded text-[10px] font-bold uppercase tracking-wider text-slate-500 hover:text-secondary"
          >
            <span className="material-symbols-outlined text-[13px]">{copied ? 'check' : 'content_copy'}</span>
            {copied ? 'Copied' : 'Copy'}
          </button>
        </div>
        <p className="mt-1 text-[11px] leading-5 text-slate-700 break-words">{citationText}</p>
      </div>
      {source.document_id && (
        <div className="mt-3 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => onOpenSource(source)}
            className="inline-flex items-center gap-1.5 rounded border border-slate-200 bg-white px-2.5 py-1 text-[11px] font-semibold text-slate-700 hover:border-secondary hover:text-secondary"
          >
            <span className="material-symbols-outlined text-[14px]">plagiarism</span>
            Open passage
          </button>
          {fileUrl && (
            <a
              href={fileUrl}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 rounded border border-slate-200 bg-white px-2.5 py-1 text-[11px] font-semibold text-slate-700 hover:border-secondary hover:text-secondary"
            >
              <span className="material-symbols-outlined text-[14px]">open_in_new</span>
              {sourceFileActionLabel(source)}
            </a>
          )}
        </div>
      )}
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
  const [viewer, setViewer] = useState({ source: null, data: null, loading: false, error: '' });

  const openSource = async (source) => {
    const path = sourcePath(source);
    if (!path) return;
    setViewer({ source, data: null, loading: true, error: '' });
    try {
      const response = await api.get(path);
      setViewer({ source, data: response.data, loading: false, error: '' });
    } catch (err) {
      setViewer({
        source,
        data: null,
        loading: false,
        error: err?.response?.data?.detail || 'Unable to open this source.',
      });
    }
  };

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
        {sources.map((source, index) => (
          <SourceCard
            key={`${source.document_id || source.title || 'source'}-${index}`}
            source={source}
            index={index}
            onOpenSource={openSource}
          />
        ))}
      </div>
      <SourceViewerModal viewer={viewer} onClose={() => setViewer({ source: null, data: null, loading: false, error: '' })} />
    </>
  );

  if (compact) {
    return <div className="mt-3 border border-slate-200 rounded bg-slate-50 overflow-hidden xl:hidden">{content}</div>;
  }

  return <aside className="hidden xl:flex w-80 flex-col bg-slate-50 border-l border-slate-200">{content}</aside>;
}
