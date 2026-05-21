import { useEffect, useState } from 'react';
import api from '../api/axios';

function safeJson(value, fallback) {
  try {
    return value ? JSON.parse(value) : fallback;
  } catch {
    return fallback;
  }
}

function confidenceLabel(value) {
  if (value === null || value === undefined) return 'n/a';
  return `${Math.round(Number(value) * 100)}%`;
}

function confidenceTone(value) {
  if (value === null || value === undefined) return 'bg-slate-100 text-slate-500';
  if (Number(value) >= 0.85) return 'bg-emerald-50 text-emerald-700 border-emerald-100';
  if (Number(value) >= 0.65) return 'bg-amber-50 text-amber-700 border-amber-100';
  return 'bg-rose-50 text-rose-700 border-rose-100';
}

export default function DocumentReview() {
  const [queue, setQueue] = useState([]);
  const [loading, setLoading] = useState(true);
  const [corrections, setCorrections] = useState({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const fetchQueue = async () => {
    setLoading(true);
    try {
      const { data } = await api.get('/document-review/queue');
      setQueue(data);
      setCorrections((previous) => {
        const next = { ...previous };
        data.forEach((page) => {
          if (next[page.id] === undefined) {
            next[page.id] = page.corrected_text || page.extracted_text || '';
          }
        });
        return next;
      });
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to load document review queue.');
      setQueue([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueue();
  }, []);

  const markReviewed = async (pageId, reviewStatus) => {
    setSaving(true);
    setError('');
    try {
      await api.patch(`/document-review/pages/${pageId}/review`, {
        review_status: reviewStatus,
        corrected_text: reviewStatus === 'corrected' ? corrections[pageId] : undefined,
      });
      await fetchQueue();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update extraction review.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Document Review</h1>
          <p className="text-sm text-slate-500 mt-1">Low-confidence OCR, table, handwriting, stamp, and signature-like extraction queue.</p>
        </div>
        <span className="px-3 py-1 text-xs font-semibold rounded bg-amber-50 text-amber-700 border border-amber-200">
          {queue.length} pending
        </span>
      </div>

      {error && (
        <div className="rounded border border-rose-100 bg-rose-50 px-3 py-2 text-sm font-semibold text-rose-700">
          {error}
        </div>
      )}

      <div className="grid gap-3">
        {loading ? (
          <div className="text-sm text-slate-500">Loading queue...</div>
        ) : queue.length === 0 ? (
          <div className="rounded border border-dashed border-slate-300 p-6 text-sm text-slate-500">No low-confidence pages waiting for review.</div>
        ) : queue.map((page) => {
          const flags = safeJson(page.flags_json, []);
          return (
            <div key={page.id} className="bg-white border border-slate-200 rounded p-4">
              <div className="flex flex-col xl:flex-row xl:items-start justify-between gap-4">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-xs font-semibold text-slate-500">Document #{page.document_id} page {page.page_number}</span>
                    <span className="text-xs px-2 py-0.5 rounded bg-slate-100 text-slate-700">{page.parser}</span>
                    <span className={`text-xs px-2 py-0.5 rounded border ${confidenceTone(page.ocr_confidence)}`}>
                      OCR {confidenceLabel(page.ocr_confidence)}
                    </span>
                    <span className={`text-xs px-2 py-0.5 rounded border ${confidenceTone(page.table_confidence)}`}>
                      Table {confidenceLabel(page.table_confidence)}
                    </span>
                    <span className={`text-xs px-2 py-0.5 rounded border ${confidenceTone(page.layout_confidence)}`}>
                      Layout {confidenceLabel(page.layout_confidence)}
                    </span>
                  </div>
                  <div className="mt-3 grid gap-3 lg:grid-cols-2">
                    <div>
                      <p className="text-[10px] font-bold uppercase text-slate-400">Extracted text</p>
                      <pre className="mt-1 max-h-44 overflow-y-auto whitespace-pre-wrap rounded bg-slate-50 border border-slate-100 p-3 text-xs text-slate-700">
                        {page.extracted_text || 'No extracted text captured.'}
                      </pre>
                    </div>
                    <label className="text-[10px] font-bold uppercase text-slate-400">
                      Correction
                      <textarea
                        rows={7}
                        className="mt-1 w-full rounded border border-slate-200 px-3 py-2 text-xs normal-case font-normal text-slate-800 focus:outline-none focus:ring-2 focus:ring-primary/20"
                        value={corrections[page.id] || ''}
                        onChange={(event) => setCorrections((previous) => ({ ...previous, [page.id]: event.target.value }))}
                      />
                    </label>
                  </div>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {flags.length === 0 ? (
                      <span className="text-xs px-2 py-1 rounded bg-slate-100 text-slate-600">No flags</span>
                    ) : flags.map((flag) => (
                      <span key={flag} className="text-xs px-2 py-1 rounded bg-amber-50 text-amber-700 border border-amber-100">
                        {flag.replaceAll('_', ' ')}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="flex flex-col gap-2 xl:w-36">
                  <button
                    type="button"
                    disabled={saving}
                    onClick={() => markReviewed(page.id, 'verified')}
                    className="inline-flex items-center justify-center gap-2 rounded border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                  >
                    <span className="material-symbols-outlined text-[16px]">check</span>
                    Verify
                  </button>
                  <button
                    type="button"
                    disabled={saving || !corrections[page.id]?.trim()}
                    onClick={() => markReviewed(page.id, 'corrected')}
                    className="inline-flex items-center justify-center gap-2 rounded border border-blue-200 px-3 py-2 text-xs font-semibold text-blue-700 hover:bg-blue-50 disabled:opacity-50"
                  >
                    <span className="material-symbols-outlined text-[16px]">edit_note</span>
                    Corrected
                  </button>
                  <button
                    type="button"
                    disabled={saving}
                    onClick={() => markReviewed(page.id, 'unreliable')}
                    className="inline-flex items-center justify-center gap-2 rounded border border-red-200 px-3 py-2 text-xs font-semibold text-red-700 hover:bg-red-50"
                  >
                    <span className="material-symbols-outlined text-[16px]">report</span>
                    Unreliable
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
