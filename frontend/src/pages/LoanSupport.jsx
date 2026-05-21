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

function parseList(value) {
  return String(value || '')
    .split(/\n|,/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function toSourcePayload(value) {
  return String(value || '')
    .split(',')
    .map((item) => Number(item.trim()))
    .filter(Number.isFinite)
    .map((document_id) => ({ document_id }));
}

export default function LoanSupport() {
  const [cases, setCases] = useState([]);
  const [form, setForm] = useState({
    applicant_name: '',
    loan_type: 'home_loan',
    requested_amount: '',
    required_documents: 'KYC, Income proof, Collateral valuation',
    received_documents: 'KYC',
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [drafts, setDrafts] = useState({});
  const [error, setError] = useState('');

  const fetchCases = async () => {
    setLoading(true);
    try {
      const { data } = await api.get('/loan-support');
      setCases(data);
      setDrafts((previous) => {
        const next = { ...previous };
        data.forEach((item) => {
          if (!next[item.id]) {
            next[item.id] = {
              memo_draft: item.credit_memo_draft || '',
              risk_factors: safeJson(item.risk_factors_json, []).join('\n'),
              source_ids: safeJson(item.source_document_ids_json, []).join(', '),
            };
          }
        });
        return next;
      });
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to load loan support cases.');
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
    if (!form.applicant_name.trim()) return;
    setSaving(true);
    setError('');
    try {
      await api.post('/loan-support', {
        applicant_name: form.applicant_name,
        loan_type: form.loan_type,
        requested_amount: form.requested_amount ? Number(form.requested_amount) : null,
        required_documents: parseList(form.required_documents),
        received_documents: parseList(form.received_documents),
      });
      setForm({ ...form, applicant_name: '', requested_amount: '' });
      await fetchCases();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create loan support case.');
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

  const saveMemo = async (caseId) => {
    const draft = drafts[caseId] || {};
    if (!draft.memo_draft?.trim()) return;
    setSaving(true);
    setError('');
    try {
      await api.post(`/loan-support/${caseId}/credit-memo`, {
        memo_draft: draft.memo_draft,
        risk_factors: parseList(draft.risk_factors),
        sources: toSourcePayload(draft.source_ids),
      });
      await fetchCases();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save credit memo draft.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Loan Support</h1>
          <p className="text-sm text-slate-500 mt-1">Checklist, risk-factor, and credit memo workspace for human lending officers.</p>
        </div>
        <span className="px-3 py-1 text-xs font-semibold rounded bg-amber-50 text-amber-700 border border-amber-200">
          No auto decision
        </span>
      </div>

      {error && (
        <div className="rounded border border-rose-100 bg-rose-50 px-3 py-2 text-sm font-semibold text-rose-700">
          {error}
        </div>
      )}

      <form onSubmit={createCase} className="bg-white border border-slate-200 rounded p-4 grid gap-4 lg:grid-cols-5">
        <label className="text-sm font-medium text-slate-700 lg:col-span-2">
          Applicant
          <input
            className="mt-1 w-full rounded border border-slate-200 px-3 py-2 text-sm"
            value={form.applicant_name}
            onChange={(event) => setForm({ ...form, applicant_name: event.target.value })}
          />
        </label>
        <label className="text-sm font-medium text-slate-700">
          Loan type
          <select
            className="mt-1 w-full rounded border border-slate-200 px-3 py-2 text-sm"
            value={form.loan_type}
            onChange={(event) => setForm({ ...form, loan_type: event.target.value })}
          >
            <option value="home_loan">Home loan</option>
            <option value="business_loan">Business loan</option>
            <option value="vehicle_loan">Vehicle loan</option>
          </select>
        </label>
        <label className="text-sm font-medium text-slate-700">
          Amount
          <input
            type="number"
            className="mt-1 w-full rounded border border-slate-200 px-3 py-2 text-sm"
            value={form.requested_amount}
            onChange={(event) => setForm({ ...form, requested_amount: event.target.value })}
          />
        </label>
        <div className="flex items-end">
          <button type="submit" disabled={saving} className="inline-flex w-full items-center justify-center gap-2 rounded bg-primary px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">
            <span className="material-symbols-outlined text-[18px]">note_add</span>
            Create
          </button>
        </div>
        <label className="text-sm font-medium text-slate-700 lg:col-span-3">
          Required documents
          <input
            className="mt-1 w-full rounded border border-slate-200 px-3 py-2 text-sm"
            value={form.required_documents}
            onChange={(event) => setForm({ ...form, required_documents: event.target.value })}
          />
        </label>
        <label className="text-sm font-medium text-slate-700 lg:col-span-2">
          Received documents
          <input
            className="mt-1 w-full rounded border border-slate-200 px-3 py-2 text-sm"
            value={form.received_documents}
            onChange={(event) => setForm({ ...form, received_documents: event.target.value })}
          />
        </label>
      </form>

      <div className="grid gap-3">
        {loading ? (
          <div className="text-sm text-slate-500">Loading loan support cases...</div>
        ) : cases.length === 0 ? (
          <div className="rounded border border-dashed border-slate-300 p-6 text-sm text-slate-500">No loan support cases yet.</div>
        ) : cases.map((item) => {
          const required = safeJson(item.required_documents_json, []);
          const received = safeJson(item.received_documents_json, []);
          const missing = safeJson(item.missing_documents_json, []);
          const riskFactors = safeJson(item.risk_factors_json, []);
          return (
            <div key={item.id} className="bg-white border border-slate-200 rounded p-4">
              <div className="flex flex-col xl:flex-row xl:items-start justify-between gap-4">
                <div>
                  <h2 className="text-sm font-semibold text-slate-900">{item.applicant_name}</h2>
                  <p className="mt-1 text-xs text-slate-500">{formatLabel(item.loan_type)} {item.requested_amount ? `- NPR ${Number(item.requested_amount).toLocaleString()}` : ''}</p>
                  <div className="mt-3 grid gap-3 md:grid-cols-3">
                    <div>
                      <p className="text-[10px] font-bold uppercase text-slate-400">Required</p>
                      <div className="mt-1 flex flex-wrap gap-1.5">
                        {required.map((doc) => (
                          <span key={doc} className="text-xs px-2 py-1 rounded bg-slate-100 text-slate-700">{doc}</span>
                        ))}
                      </div>
                    </div>
                    <div>
                      <p className="text-[10px] font-bold uppercase text-slate-400">Received</p>
                      <div className="mt-1 flex flex-wrap gap-1.5">
                        {received.map((doc) => (
                          <span key={doc} className="text-xs px-2 py-1 rounded bg-emerald-50 text-emerald-700 border border-emerald-100">{doc}</span>
                        ))}
                      </div>
                    </div>
                    <div>
                      <p className="text-[10px] font-bold uppercase text-slate-400">Missing</p>
                      <div className="mt-1 flex flex-wrap gap-1.5">
                        {missing.length === 0 ? (
                          <span className="text-xs px-2 py-1 rounded bg-emerald-50 text-emerald-700 border border-emerald-100">None detected</span>
                        ) : missing.map((doc) => (
                          <span key={doc} className="text-xs px-2 py-1 rounded bg-red-50 text-red-700 border border-red-100">{doc}</span>
                        ))}
                      </div>
                    </div>
                  </div>
                  {riskFactors.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-2">
                      {riskFactors.map((risk) => (
                        <span key={risk} className="text-xs px-2 py-1 rounded bg-amber-50 text-amber-700 border border-amber-100">{risk}</span>
                      ))}
                    </div>
                  )}
                  {item.credit_memo_draft && (
                    <p className="mt-3 text-sm text-slate-700">{item.credit_memo_draft}</p>
                  )}
                </div>
                <div className="xl:text-right">
                  <span className="text-xs font-medium text-slate-500">{formatLabel(item.status)}</span>
                  <p className="mt-1 text-xs text-amber-700">{item.human_review_required ? 'Human review required' : 'Reviewed'}</p>
                  {item.automated_decision && (
                    <p className="mt-1 text-xs text-rose-700">Unexpected decision: {item.automated_decision}</p>
                  )}
                </div>
              </div>

              <div className="mt-4 grid gap-3 border-t border-slate-100 pt-4">
                <label className="text-xs font-bold uppercase tracking-wide text-slate-500">
                  Credit memo draft
                  <textarea
                    rows={4}
                    className="mt-1 w-full rounded border border-slate-200 px-3 py-2 text-sm normal-case font-normal text-slate-800 focus:outline-none focus:ring-2 focus:ring-primary/20"
                    value={drafts[item.id]?.memo_draft || ''}
                    onChange={(event) => updateDraft(item.id, { memo_draft: event.target.value })}
                    placeholder="Borrower profile, facility request, policy checks, open risks, and staff review notes..."
                  />
                </label>
                <div className="grid gap-3 lg:grid-cols-[1fr_220px_auto]">
                  <label className="text-xs font-bold uppercase tracking-wide text-slate-500">
                    Risk factors
                    <textarea
                      rows={3}
                      className="mt-1 w-full rounded border border-slate-200 px-3 py-2 text-sm normal-case font-normal text-slate-800"
                      value={drafts[item.id]?.risk_factors || ''}
                      onChange={(event) => updateDraft(item.id, { risk_factors: event.target.value })}
                      placeholder="One risk per line"
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
                  </label>
                  <div className="flex items-end">
                    <button
                      type="button"
                      disabled={saving || !drafts[item.id]?.memo_draft?.trim()}
                      onClick={() => saveMemo(item.id)}
                      className="inline-flex w-full items-center justify-center gap-2 rounded bg-primary px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
                    >
                      <span className="material-symbols-outlined text-[18px]">save</span>
                      Save Memo
                    </button>
                  </div>
                </div>
                <p className="text-[11px] font-semibold text-slate-500">
                  LipiCore does not approve or reject loans. This memo is decision support for authorized officers.
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
