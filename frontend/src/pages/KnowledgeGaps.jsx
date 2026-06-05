import { useCallback, useEffect, useMemo, useState } from 'react';
import api from '../api/axios';
import { getCurrentUser, ROLES } from '../config/rolePermissions';

const STATUS_OPTIONS = ['', 'open', 'in_review', 'resolved', 'dismissed'];

function messageFromError(err, fallback) {
  const detail = err?.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (detail?.code === 'feature_disabled') return 'Knowledge Gaps are not enabled for this bank.';
  return fallback;
}

export default function KnowledgeGaps() {
  const currentUser = getCurrentUser();
  const isAdmin = [ROLES.SUPER_ADMIN, ROLES.BANK_ADMIN, ROLES.COMPLIANCE_OFFICER].includes(currentUser?.role);
  const [gaps, setGaps] = useState([]);
  const [scope, setScope] = useState(isAdmin ? 'bank' : 'mine');
  const [status, setStatus] = useState('');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState('');
  const [form, setForm] = useState({ question: '', priority: 'normal', source_type: 'manual' });

  const openCount = useMemo(() => gaps.filter((gap) => !['resolved', 'dismissed'].includes(gap.status)).length, [gaps]);

  const fetchGaps = useCallback(async () => {
    setLoading(true);
    setNotice('');
    try {
      const response = await api.get('/knowledge-gaps', {
        params: { scope: isAdmin ? scope : 'mine', status: status || undefined },
      });
      setGaps(Array.isArray(response.data) ? response.data : []);
    } catch (err) {
      setGaps([]);
      setNotice(messageFromError(err, 'Could not load knowledge gaps.'));
    } finally {
      setLoading(false);
    }
  }, [isAdmin, scope, status]);

  useEffect(() => { fetchGaps(); }, [fetchGaps]);

  const createGap = async (event) => {
    event.preventDefault();
    setSaving(true);
    setNotice('');
    try {
      await api.post('/knowledge-gaps', form);
      setForm({ question: '', priority: 'normal', source_type: 'manual' });
      await fetchGaps();
      setNotice('Knowledge gap captured.');
    } catch (err) {
      setNotice(messageFromError(err, 'Could not create knowledge gap.'));
    } finally {
      setSaving(false);
    }
  };

  const updateGap = async (gapId, payload) => {
    try {
      const response = await api.patch(`/knowledge-gaps/${gapId}`, payload);
      setGaps((current) => current.map((gap) => gap.id === gapId ? response.data : gap));
    } catch (err) {
      setNotice(messageFromError(err, 'Could not update knowledge gap.'));
    }
  };

  return (
    <div className="p-xl max-w-container-max mx-auto">
      <header className="mb-lg flex flex-col gap-md xl:flex-row xl:items-end xl:justify-between">
        <div>
          <h1 className="text-h1 font-h1 text-on-surface">Knowledge Gaps</h1>
          <p className="font-body-md text-on-surface-variant mt-sm max-w-3xl">Capture unanswered staff questions and track missing policy/document coverage.</p>
        </div>
        <button type="button" onClick={fetchGaps} disabled={loading}
          className="inline-flex items-center justify-center gap-xs rounded-lg border border-slate-300 px-md py-sm font-label-caps text-label-caps text-on-surface hover:bg-white disabled:opacity-50">
          <span className="material-symbols-outlined text-[17px]">refresh</span>
          Refresh
        </button>
      </header>

      {notice && <div className="mb-md rounded-lg border border-slate-200 bg-white px-md py-sm text-body-sm text-slate-700">{notice}</div>}

      <section className="mb-lg grid grid-cols-1 gap-gutter lg:grid-cols-3">
        <div className="rounded-lg border border-slate-200 bg-white p-md">
          <p className="font-label-caps text-label-caps uppercase text-on-surface-variant">Open Gaps</p>
          <p className="mt-xs text-h2 font-h2 text-on-surface">{openCount}</p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-md lg:col-span-2">
          <p className="font-label-caps text-label-caps uppercase text-on-surface-variant">Filters</p>
          <div className="mt-sm grid grid-cols-1 gap-sm sm:grid-cols-2">
            <select value={status} onChange={(event) => setStatus(event.target.value)} className="rounded border border-slate-200 bg-slate-50 px-sm py-xs text-body-sm">
              {STATUS_OPTIONS.map((option) => <option key={option || 'all'} value={option}>{option || 'all statuses'}</option>)}
            </select>
            {isAdmin && (
              <select value={scope} onChange={(event) => setScope(event.target.value)} className="rounded border border-slate-200 bg-slate-50 px-sm py-xs text-body-sm">
                <option value="bank">bank-wide</option>
                <option value="mine">my submissions</option>
              </select>
            )}
          </div>
        </div>
      </section>

      <form onSubmit={createGap} className="mb-lg rounded-lg border border-slate-200 bg-white p-lg">
        <label className="mb-xs block font-label-caps text-label-caps uppercase text-on-surface-variant">Question or Missing Knowledge</label>
        <textarea value={form.question} onChange={(event) => setForm((current) => ({ ...current, question: event.target.value }))}
          className="min-h-24 w-full resize-y rounded-lg border border-slate-200 bg-slate-50 px-md py-sm text-body-sm focus:border-secondary focus:outline-none" required />
        <div className="mt-md flex flex-col gap-sm sm:flex-row sm:items-center sm:justify-between">
          <select value={form.priority} onChange={(event) => setForm((current) => ({ ...current, priority: event.target.value }))}
            className="rounded-lg border border-slate-200 bg-slate-50 px-md py-sm text-body-sm">
            <option value="low">low</option><option value="normal">normal</option><option value="high">high</option><option value="urgent">urgent</option>
          </select>
          <button type="submit" disabled={saving} className="rounded-lg bg-primary px-md py-sm font-label-caps text-label-caps text-white hover:opacity-90 disabled:opacity-50">
            {saving ? 'Capturing...' : 'Capture Gap'}
          </button>
        </div>
      </form>

      <section className="rounded-lg border border-slate-200 bg-white">
        {loading ? <div className="flex min-h-52 items-center justify-center text-body-sm text-on-surface-variant">Loading gaps...</div> : (
          gaps.length === 0 ? <div className="flex min-h-52 items-center justify-center text-body-sm text-on-surface-variant">No knowledge gaps found.</div> : (
            <div className="divide-y divide-slate-100">
              {gaps.map((gap) => (
                <article key={gap.id} className="grid grid-cols-1 gap-md px-lg py-md xl:grid-cols-[1fr_auto]">
                  <div>
                    <div className="mb-xs flex flex-wrap gap-sm">
                      <span className="rounded bg-slate-100 px-2 py-0.5 text-[10px] font-bold uppercase text-slate-600">{gap.status}</span>
                      <span className="rounded bg-amber-50 px-2 py-0.5 text-[10px] font-bold uppercase text-amber-700">{gap.priority}</span>
                    </div>
                    <h2 className="text-body-md font-bold text-on-surface">{gap.question}</h2>
                    {gap.resolution_notes && <p className="mt-xs text-body-sm text-on-surface-variant">{gap.resolution_notes}</p>}
                  </div>
                  {isAdmin && gap.status !== 'resolved' && (
                    <button type="button" onClick={() => updateGap(gap.id, { status: 'resolved', resolution_notes: 'Resolved by knowledge owner.' })}
                      className="rounded-lg bg-primary px-md py-sm font-label-caps text-label-caps text-white hover:opacity-90">
                      Resolve
                    </button>
                  )}
                </article>
              ))}
            </div>
          )
        )}
      </section>
    </div>
  );
}
