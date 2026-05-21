import { useEffect, useState } from 'react';
import api from '../api/axios';

function safeJson(value, fallback) {
  try {
    return value ? JSON.parse(value) : fallback;
  } catch {
    return fallback;
  }
}

function formatLabel(value) {
  return String(value || 'unknown').replaceAll('_', ' ');
}

function parseObligations(value) {
  return String(value || '')
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const [owner = 'Compliance', action = line, status = 'open'] = line.split('|').map((item) => item.trim());
      return { owner, action, status };
    });
}

function toSourcePayload(value) {
  return String(value || '')
    .split(',')
    .map((item) => Number(item.trim()))
    .filter(Number.isFinite)
    .map((document_id) => ({ document_id }));
}

export default function ComplianceWorkspace() {
  const [reviews, setReviews] = useState([]);
  const [form, setForm] = useState({ title: '', affected_departments: 'Operations, Compliance', circular_document_id: '' });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [drafts, setDrafts] = useState({});
  const [error, setError] = useState('');

  const fetchReviews = async () => {
    setLoading(true);
    try {
      const { data } = await api.get('/compliance-reviews');
      setReviews(data);
      setDrafts((previous) => {
        const next = { ...previous };
        data.forEach((item) => {
          if (!next[item.id]) {
            const obligations = safeJson(item.obligations_json, []);
            next[item.id] = {
              impact_summary: item.impact_summary || '',
              obligations_text: obligations.map((obligation) => (
                `${obligation.owner || 'Compliance'} | ${obligation.action || ''} | ${obligation.status || 'open'}`
              )).join('\n'),
              source_ids: safeJson(item.source_document_ids_json, []).join(', '),
            };
          }
        });
        return next;
      });
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to load compliance reviews.');
      setReviews([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReviews();
  }, []);

  const createReview = async (event) => {
    event.preventDefault();
    if (!form.title.trim()) return;
    setSaving(true);
    setError('');
    try {
      await api.post('/compliance-reviews', {
        title: form.title,
        circular_document_id: form.circular_document_id ? Number(form.circular_document_id) : null,
        affected_departments: form.affected_departments.split(',').map((item) => item.trim()).filter(Boolean),
      });
      setForm({ title: '', affected_departments: 'Operations, Compliance', circular_document_id: '' });
      await fetchReviews();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create compliance review.');
    } finally {
      setSaving(false);
    }
  };

  const updateDraft = (reviewId, patch) => {
    setDrafts((previous) => ({
      ...previous,
      [reviewId]: { ...(previous[reviewId] || {}), ...patch },
    }));
  };

  const saveSummary = async (reviewId) => {
    const draft = drafts[reviewId] || {};
    if (!draft.impact_summary?.trim()) return;
    setSaving(true);
    setError('');
    try {
      await api.post(`/compliance-reviews/${reviewId}/summary`, {
        impact_summary: draft.impact_summary,
        obligations: parseObligations(draft.obligations_text),
        sources: toSourcePayload(draft.source_ids),
      });
      await fetchReviews();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save compliance summary.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Compliance Workspace</h1>
          <p className="text-sm text-slate-500 mt-1">Circular impact summaries, obligation tracking, and officer review state.</p>
        </div>
        <span className="px-3 py-1 text-xs font-semibold rounded bg-blue-50 text-blue-700 border border-blue-200">
          Officer review
        </span>
      </div>

      {error && (
        <div className="rounded border border-rose-100 bg-rose-50 px-3 py-2 text-sm font-semibold text-rose-700">
          {error}
        </div>
      )}

      <form onSubmit={createReview} className="bg-white border border-slate-200 rounded p-4 grid gap-4 lg:grid-cols-[1fr_220px_320px_auto]">
        <label className="text-sm font-medium text-slate-700">
          Review title
          <input
            className="mt-1 w-full rounded border border-slate-200 px-3 py-2 text-sm"
            value={form.title}
            onChange={(event) => setForm({ ...form, title: event.target.value })}
          />
        </label>
        <label className="text-sm font-medium text-slate-700">
          Circular doc ID
          <input
            type="number"
            className="mt-1 w-full rounded border border-slate-200 px-3 py-2 text-sm"
            value={form.circular_document_id}
            onChange={(event) => setForm({ ...form, circular_document_id: event.target.value })}
            placeholder="Optional"
          />
        </label>
        <label className="text-sm font-medium text-slate-700">
          Departments
          <input
            className="mt-1 w-full rounded border border-slate-200 px-3 py-2 text-sm"
            value={form.affected_departments}
            onChange={(event) => setForm({ ...form, affected_departments: event.target.value })}
          />
        </label>
        <div className="flex items-end">
          <button type="submit" disabled={saving} className="inline-flex items-center gap-2 rounded bg-primary px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">
            <span className="material-symbols-outlined text-[18px]">playlist_add</span>
            Create Review
          </button>
        </div>
      </form>

      <div className="grid gap-3">
        {loading ? (
          <div className="text-sm text-slate-500">Loading reviews...</div>
        ) : reviews.length === 0 ? (
          <div className="rounded border border-dashed border-slate-300 p-6 text-sm text-slate-500">No compliance reviews yet.</div>
        ) : (
          reviews.map((review) => (
            <div key={review.id} className="bg-white border border-slate-200 rounded p-4">
              <div className="flex flex-col xl:flex-row xl:items-start justify-between gap-4">
                <div>
                  <h2 className="text-sm font-semibold text-slate-900">{review.title}</h2>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {safeJson(review.affected_departments_json, []).map((department) => (
                      <span key={department} className="text-xs px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-100">{department}</span>
                    ))}
                    {review.circular_document_id && (
                      <span className="text-xs px-2 py-0.5 rounded bg-slate-100 text-slate-700">Circular #{review.circular_document_id}</span>
                    )}
                  </div>
                  <p className="mt-1 text-xs text-slate-500">{review.disclaimer}</p>
                  {review.impact_summary && <p className="mt-3 text-sm text-slate-700">{review.impact_summary}</p>}
                  {safeJson(review.obligations_json, []).length > 0 && (
                    <div className="mt-3 grid gap-2">
                      {safeJson(review.obligations_json, []).map((obligation, index) => (
                        <div key={`${obligation.action}-${index}`} className="rounded border border-slate-100 bg-slate-50 px-3 py-2 text-xs">
                          <span className="font-bold text-slate-800">{obligation.owner || 'Owner'}</span>
                          <span className="mx-2 text-slate-400">/</span>
                          <span className="text-slate-700">{obligation.action}</span>
                          <span className="ml-2 rounded bg-white px-1.5 py-0.5 font-semibold text-slate-500">{obligation.status || 'open'}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                <div className="text-right">
                  <span className="text-xs font-medium text-slate-500">{formatLabel(review.status)}</span>
                  <p className="mt-1 text-xs text-blue-700">{formatLabel(review.approval_status)}</p>
                </div>
              </div>

              <div className="mt-4 grid gap-3 border-t border-slate-100 pt-4">
                <label className="text-xs font-bold uppercase tracking-wide text-slate-500">
                  Impact summary
                  <textarea
                    rows={4}
                    className="mt-1 w-full rounded border border-slate-200 px-3 py-2 text-sm normal-case font-normal text-slate-800 focus:outline-none focus:ring-2 focus:ring-primary/20"
                    value={drafts[review.id]?.impact_summary || ''}
                    onChange={(event) => updateDraft(review.id, { impact_summary: event.target.value })}
                    placeholder="What changed, who is affected, what staff must do..."
                  />
                </label>
                <div className="grid gap-3 lg:grid-cols-[1fr_220px_auto]">
                  <label className="text-xs font-bold uppercase tracking-wide text-slate-500">
                    Obligations
                    <textarea
                      rows={3}
                      className="mt-1 w-full rounded border border-slate-200 px-3 py-2 text-sm normal-case font-normal text-slate-800"
                      value={drafts[review.id]?.obligations_text || ''}
                      onChange={(event) => updateDraft(review.id, { obligations_text: event.target.value })}
                      placeholder="Owner | Action | Status"
                    />
                  </label>
                  <label className="text-xs font-bold uppercase tracking-wide text-slate-500">
                    Source document IDs
                    <input
                      className="mt-1 w-full rounded border border-slate-200 px-3 py-2 text-sm normal-case font-normal text-slate-800"
                      value={drafts[review.id]?.source_ids || ''}
                      onChange={(event) => updateDraft(review.id, { source_ids: event.target.value })}
                      placeholder="12, 19"
                    />
                  </label>
                  <div className="flex items-end">
                    <button
                      type="button"
                      disabled={saving || !drafts[review.id]?.impact_summary?.trim()}
                      onClick={() => saveSummary(review.id)}
                      className="inline-flex w-full items-center justify-center gap-2 rounded bg-primary px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
                    >
                      <span className="material-symbols-outlined text-[18px]">save</span>
                      Save Summary
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
