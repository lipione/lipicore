import { useEffect, useState } from 'react';
import api from '../api/axios';

const EMPTY_FORM = {
  customer_issue: '',
  category: 'failed_transaction',
  channel: 'branch',
  priority: 'normal',
  escalation_target: '',
};

function formatLabel(value) {
  return String(value || 'unknown').replaceAll('_', ' ');
}

function safeJson(value, fallback) {
  try {
    return value ? JSON.parse(value) : fallback;
  } catch {
    return fallback;
  }
}

function toSourcePayload(value) {
  return String(value || '')
    .split(',')
    .map((item) => Number(item.trim()))
    .filter(Number.isFinite)
    .map((document_id) => ({ document_id }));
}

export default function SupportDesk() {
  const [cases, setCases] = useState([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [drafts, setDrafts] = useState({});
  const [error, setError] = useState('');

  const fetchCases = async () => {
    setLoading(true);
    try {
      const { data } = await api.get('/support-cases');
      setCases(data);
      setDrafts((previous) => {
        const next = { ...previous };
        data.forEach((item) => {
          if (!next[item.id]) {
            next[item.id] = {
              draft_response: item.draft_response || '',
              source_ids: safeJson(item.source_document_ids_json, []).join(', '),
            };
          }
        });
        return next;
      });
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to load support cases.');
      setCases([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCases();
  }, []);

  const createCase = async (event) => {
    event.preventDefault();
    if (!form.customer_issue.trim()) return;
    setSaving(true);
    setError('');
    try {
      await api.post('/support-cases', {
        ...form,
        escalation_target: form.escalation_target.trim() || null,
      });
      setForm(EMPTY_FORM);
      await fetchCases();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create support case.');
    } finally {
      setSaving(false);
    }
  };

  const saveDraft = async (caseId) => {
    const draft = drafts[caseId] || {};
    if (!draft.draft_response?.trim()) return;
    setSaving(true);
    setError('');
    try {
      await api.post(`/support-cases/${caseId}/draft`, {
        draft_response: draft.draft_response,
        sources: toSourcePayload(draft.source_ids),
      });
      await fetchCases();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save draft.');
    } finally {
      setSaving(false);
    }
  };

  const updateDraft = (caseId, patch) => {
    setDrafts((previous) => ({
      ...previous,
      [caseId]: { ...(previous[caseId] || {}), ...patch },
    }));
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Support Desk</h1>
          <p className="text-sm text-slate-500 mt-1">Customer-care and branch cases with review-required AI drafts.</p>
        </div>
        <span className="px-3 py-1 text-xs font-semibold rounded bg-amber-50 text-amber-700 border border-amber-200">
          Staff review required
        </span>
      </div>

      {error && (
        <div className="rounded border border-rose-100 bg-rose-50 px-3 py-2 text-sm font-semibold text-rose-700">
          {error}
        </div>
      )}

      <form onSubmit={createCase} className="bg-white border border-slate-200 rounded p-4 grid gap-4 lg:grid-cols-[1fr_180px_160px_120px]">
        <label className="text-sm font-medium text-slate-700">
          Customer issue
          <textarea
            className="mt-1 w-full min-h-24 rounded border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
            value={form.customer_issue}
            onChange={(event) => setForm({ ...form, customer_issue: event.target.value })}
          />
        </label>
        <label className="text-sm font-medium text-slate-700">
          Category
          <select
            className="mt-1 w-full rounded border border-slate-200 px-3 py-2 text-sm"
            value={form.category}
            onChange={(event) => setForm({ ...form, category: event.target.value })}
          >
            <option value="failed_transaction">Failed transaction</option>
            <option value="card_dispute">Card dispute</option>
            <option value="kyc_account_service">KYC/account service</option>
            <option value="complaint_escalation">Complaint escalation</option>
          </select>
        </label>
        <label className="text-sm font-medium text-slate-700">
          Channel
          <select
            className="mt-1 w-full rounded border border-slate-200 px-3 py-2 text-sm"
            value={form.channel}
            onChange={(event) => setForm({ ...form, channel: event.target.value })}
          >
            <option value="branch">Branch</option>
            <option value="call_center">Call center</option>
            <option value="email">Email</option>
            <option value="helpdesk">Helpdesk</option>
          </select>
        </label>
        <label className="text-sm font-medium text-slate-700">
          Priority
          <select
            className="mt-1 w-full rounded border border-slate-200 px-3 py-2 text-sm"
            value={form.priority}
            onChange={(event) => setForm({ ...form, priority: event.target.value })}
          >
            <option value="normal">Normal</option>
            <option value="high">High</option>
            <option value="urgent">Urgent</option>
          </select>
        </label>
        <label className="text-sm font-medium text-slate-700 lg:col-span-2">
          Escalation target
          <input
            className="mt-1 w-full rounded border border-slate-200 px-3 py-2 text-sm"
            value={form.escalation_target}
            onChange={(event) => setForm({ ...form, escalation_target: event.target.value })}
            placeholder="Branch operations, cards team, supervisor..."
          />
        </label>
        <div className="lg:col-span-4 flex justify-end">
          <button
            type="submit"
            disabled={saving}
            className="inline-flex items-center gap-2 rounded bg-primary px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
          >
            <span className="material-symbols-outlined text-[18px]">add</span>
            Create Case
          </button>
        </div>
      </form>

      <div className="grid gap-3">
        {loading ? (
          <div className="text-sm text-slate-500">Loading cases...</div>
        ) : cases.length === 0 ? (
          <div className="rounded border border-dashed border-slate-300 p-6 text-sm text-slate-500">No support cases yet.</div>
        ) : (
          cases.map((item) => (
            <div key={item.id} className="bg-white border border-slate-200 rounded p-4">
              <div className="flex flex-col xl:flex-row xl:items-start justify-between gap-4">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-xs font-semibold uppercase text-slate-500">{formatLabel(item.category)}</span>
                    <span className="text-xs px-2 py-0.5 rounded bg-slate-100 text-slate-700">{item.priority}</span>
                    <span className="text-xs px-2 py-0.5 rounded bg-blue-50 text-blue-700">{formatLabel(item.channel)}</span>
                    <span className="text-xs px-2 py-0.5 rounded bg-amber-50 text-amber-700">
                      {item.staff_review_required ? 'Review required' : 'Reviewed'}
                    </span>
                  </div>
                  <p className="mt-2 text-sm text-slate-900">{item.customer_issue}</p>
                  {item.escalation_target && (
                    <p className="mt-2 text-xs font-semibold text-slate-500">Escalate to: {item.escalation_target}</p>
                  )}
                  {item.draft_response && <p className="mt-3 text-sm text-slate-600">{item.draft_response}</p>}
                </div>
                <div className="xl:text-right">
                  <span className="text-xs font-medium text-slate-500">{formatLabel(item.status)}</span>
                  <p className="mt-1 text-[11px] text-slate-400">{new Date(item.updated_at).toLocaleString()}</p>
                </div>
              </div>

              <div className="mt-4 grid gap-3 lg:grid-cols-[1fr_220px_auto] border-t border-slate-100 pt-4">
                <label className="text-xs font-bold uppercase tracking-wide text-slate-500">
                  Staff-ready draft
                  <textarea
                    rows={4}
                    className="mt-1 w-full rounded border border-slate-200 px-3 py-2 text-sm normal-case font-normal text-slate-800 focus:outline-none focus:ring-2 focus:ring-primary/20"
                    value={drafts[item.id]?.draft_response || ''}
                    onChange={(event) => updateDraft(item.id, { draft_response: event.target.value })}
                    placeholder="Draft response for staff review..."
                  />
                </label>
                <label className="text-xs font-bold uppercase tracking-wide text-slate-500">
                  Source document IDs
                  <input
                    className="mt-1 w-full rounded border border-slate-200 px-3 py-2 text-sm normal-case font-normal text-slate-800"
                    value={drafts[item.id]?.source_ids || ''}
                    onChange={(event) => updateDraft(item.id, { source_ids: event.target.value })}
                    placeholder="12, 19"
                  />
                  <span className="mt-1 block text-[11px] font-normal normal-case text-slate-400">Optional evidence links for audit metadata.</span>
                </label>
                <div className="flex items-end">
                  <button
                    type="button"
                    disabled={saving || !drafts[item.id]?.draft_response?.trim()}
                    onClick={() => saveDraft(item.id)}
                    className="inline-flex w-full items-center justify-center gap-2 rounded bg-primary px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
                  >
                    <span className="material-symbols-outlined text-[18px]">save</span>
                    Save Draft
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
