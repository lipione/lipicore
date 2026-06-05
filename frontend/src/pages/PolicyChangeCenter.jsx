import { useCallback, useEffect, useMemo, useState } from 'react';
import api from '../api/axios';
import { getCurrentUser, ROLES } from '../config/rolePermissions';

function messageFromError(err, fallback) {
  const detail = err?.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (detail?.code === 'feature_disabled') return 'Policy Change Center is not enabled for this bank.';
  return fallback;
}

function splitLines(value) {
  return value.split('\n').map((item) => item.trim()).filter(Boolean);
}

export default function PolicyChangeCenter() {
  const currentUser = getCurrentUser();
  const isAdmin = [ROLES.SUPER_ADMIN, ROLES.BANK_ADMIN, ROLES.COMPLIANCE_OFFICER].includes(currentUser?.role);
  const [changes, setChanges] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState('');
  const [form, setForm] = useState({ title: '', summary: '', impact_summary: '', affected_departments: '', action_items: '', create_work_items: false });

  const pendingAck = useMemo(() => changes.filter((change) => !change.acknowledged_at).length, [changes]);

  const fetchChanges = useCallback(async () => {
    setLoading(true);
    setNotice('');
    try {
      const response = await api.get('/policy-changes');
      setChanges(Array.isArray(response.data) ? response.data : []);
    } catch (err) {
      setChanges([]);
      setNotice(messageFromError(err, 'Could not load policy changes.'));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchChanges(); }, [fetchChanges]);

  const publish = async (event) => {
    event.preventDefault();
    setSaving(true);
    setNotice('');
    try {
      await api.post('/policy-changes', {
        title: form.title.trim(),
        summary: form.summary.trim(),
        impact_summary: form.impact_summary.trim() || null,
        affected_departments: splitLines(form.affected_departments),
        action_items: splitLines(form.action_items),
        create_work_items: form.create_work_items,
      });
      setForm({ title: '', summary: '', impact_summary: '', affected_departments: '', action_items: '', create_work_items: false });
      await fetchChanges();
      setNotice('Policy change published.');
    } catch (err) {
      setNotice(messageFromError(err, 'Could not publish policy change.'));
    } finally {
      setSaving(false);
    }
  };

  const acknowledge = async (changeId) => {
    try {
      const response = await api.patch(`/policy-changes/${changeId}/acknowledge`);
      setChanges((current) => current.map((change) => change.id === changeId ? response.data : change));
    } catch (err) {
      setNotice(messageFromError(err, 'Could not acknowledge policy change.'));
    }
  };

  return (
    <div className="p-xl max-w-container-max mx-auto">
      <header className="mb-lg flex flex-col gap-md xl:flex-row xl:items-end xl:justify-between">
        <div>
          <h1 className="text-h1 font-h1 text-on-surface">Policy Change Center</h1>
          <p className="font-body-md text-on-surface-variant mt-sm max-w-3xl">Publish digests, affected departments, action items, and acknowledgements.</p>
        </div>
        <button type="button" onClick={fetchChanges} disabled={loading}
          className="rounded-lg border border-slate-300 px-md py-sm font-label-caps text-label-caps text-on-surface hover:bg-white disabled:opacity-50">Refresh</button>
      </header>
      {notice && <div className="mb-md rounded-lg border border-slate-200 bg-white px-md py-sm text-body-sm text-slate-700">{notice}</div>}
      <section className="mb-lg grid grid-cols-1 gap-gutter lg:grid-cols-2">
        <div className="rounded-lg border border-slate-200 bg-white p-md">
          <p className="font-label-caps text-label-caps uppercase text-on-surface-variant">Visible Changes</p>
          <p className="mt-xs text-h2 font-h2 text-on-surface">{changes.length}</p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-md">
          <p className="font-label-caps text-label-caps uppercase text-on-surface-variant">Pending Acknowledgement</p>
          <p className="mt-xs text-h2 font-h2 text-on-surface">{pendingAck}</p>
        </div>
      </section>
      {isAdmin && (
        <form onSubmit={publish} className="mb-lg rounded-lg border border-slate-200 bg-white p-lg space-y-md">
          <input value={form.title} onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))} placeholder="Policy change title"
            className="w-full rounded-lg border border-slate-200 bg-slate-50 px-md py-sm text-body-sm" required />
          <textarea value={form.summary} onChange={(event) => setForm((current) => ({ ...current, summary: event.target.value }))} placeholder="Summary"
            className="min-h-20 w-full rounded-lg border border-slate-200 bg-slate-50 px-md py-sm text-body-sm" required />
          <textarea value={form.impact_summary} onChange={(event) => setForm((current) => ({ ...current, impact_summary: event.target.value }))} placeholder="Impact summary"
            className="min-h-20 w-full rounded-lg border border-slate-200 bg-slate-50 px-md py-sm text-body-sm" />
          <div className="grid grid-cols-1 gap-md lg:grid-cols-2">
            <textarea value={form.affected_departments} onChange={(event) => setForm((current) => ({ ...current, affected_departments: event.target.value }))} placeholder="Affected departments, one per line"
              className="min-h-24 rounded-lg border border-slate-200 bg-slate-50 px-md py-sm text-body-sm" />
            <textarea value={form.action_items} onChange={(event) => setForm((current) => ({ ...current, action_items: event.target.value }))} placeholder="Action items, one per line"
              className="min-h-24 rounded-lg border border-slate-200 bg-slate-50 px-md py-sm text-body-sm" />
          </div>
          <div className="flex flex-col gap-sm sm:flex-row sm:items-center sm:justify-between">
            <label className="flex items-center gap-sm text-body-sm font-medium text-on-surface">
              <input type="checkbox" checked={form.create_work_items} onChange={(event) => setForm((current) => ({ ...current, create_work_items: event.target.checked }))} />
              Create staff inbox items
            </label>
            <button type="submit" disabled={saving} className="rounded-lg bg-primary px-md py-sm font-label-caps text-label-caps text-white hover:opacity-90 disabled:opacity-50">
              {saving ? 'Publishing...' : 'Publish Change'}
            </button>
          </div>
        </form>
      )}
      <section className="rounded-lg border border-slate-200 bg-white">
        {loading ? <div className="flex min-h-52 items-center justify-center text-body-sm text-on-surface-variant">Loading changes...</div> : (
          changes.length === 0 ? <div className="flex min-h-52 items-center justify-center text-body-sm text-on-surface-variant">No policy changes found.</div> : (
            <div className="divide-y divide-slate-100">
              {changes.map((change) => (
                <article key={change.id} className="grid grid-cols-1 gap-md px-lg py-md xl:grid-cols-[1fr_auto]">
                  <div>
                    <h2 className="text-h2 font-h2 text-on-surface">{change.title}</h2>
                    <p className="mt-sm text-body-md text-on-surface-variant">{change.summary}</p>
                    {change.impact_summary && <p className="mt-sm text-body-sm text-slate-600">{change.impact_summary}</p>}
                    {change.action_items.length > 0 && <p className="mt-sm text-body-sm text-slate-500">Actions: {change.action_items.join(', ')}</p>}
                  </div>
                  {!change.acknowledged_at && (
                    <button type="button" onClick={() => acknowledge(change.id)}
                      className="rounded-lg bg-primary px-md py-sm font-label-caps text-label-caps text-white hover:opacity-90">
                      Acknowledge
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
