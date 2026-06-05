import { useCallback, useEffect, useState } from 'react';
import api from '../api/axios';

function messageFromError(err, fallback) {
  const detail = err?.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (detail?.code === 'feature_disabled') return 'Audit Evidence Packs are not enabled for this bank.';
  return fallback;
}

export default function AuditEvidence() {
  const [packs, setPacks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState('');
  const [form, setForm] = useState({ title: '', source_type: '', source_id: '', summary: '', included_items: '' });

  const fetchPacks = useCallback(async () => {
    setLoading(true);
    setNotice('');
    try {
      const response = await api.get('/audit-evidence/packs');
      setPacks(Array.isArray(response.data) ? response.data : []);
    } catch (err) {
      setPacks([]);
      setNotice(messageFromError(err, 'Could not load evidence packs.'));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchPacks(); }, [fetchPacks]);

  const createPack = async (event) => {
    event.preventDefault();
    setSaving(true);
    setNotice('');
    try {
      await api.post('/audit-evidence/packs', {
        title: form.title.trim(),
        source_type: form.source_type.trim() || null,
        source_id: form.source_id.trim() || null,
        summary: form.summary.trim() || null,
        included_items: form.included_items.split('\n').map((item) => item.trim()).filter(Boolean),
      });
      setForm({ title: '', source_type: '', source_id: '', summary: '', included_items: '' });
      await fetchPacks();
      setNotice('Evidence pack created.');
    } catch (err) {
      setNotice(messageFromError(err, 'Could not create evidence pack.'));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="p-xl max-w-container-max mx-auto">
      <header className="mb-lg">
        <h1 className="text-h1 font-h1 text-on-surface">Audit Evidence Packs</h1>
        <p className="font-body-md text-on-surface-variant mt-sm max-w-3xl">Prepare source-backed bundles for audit review and internal evidence handoff.</p>
      </header>
      {notice && <div className="mb-md rounded-lg border border-slate-200 bg-white px-md py-sm text-body-sm text-slate-700">{notice}</div>}
      <form onSubmit={createPack} className="mb-lg rounded-lg border border-slate-200 bg-white p-lg space-y-md">
        <input value={form.title} onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))} placeholder="Evidence pack title"
          className="w-full rounded-lg border border-slate-200 bg-slate-50 px-md py-sm text-body-sm" required />
        <div className="grid grid-cols-1 gap-md lg:grid-cols-2">
          <input value={form.source_type} onChange={(event) => setForm((current) => ({ ...current, source_type: event.target.value }))} placeholder="Source type"
            className="rounded-lg border border-slate-200 bg-slate-50 px-md py-sm text-body-sm" />
          <input value={form.source_id} onChange={(event) => setForm((current) => ({ ...current, source_id: event.target.value }))} placeholder="Source ID"
            className="rounded-lg border border-slate-200 bg-slate-50 px-md py-sm text-body-sm" />
        </div>
        <textarea value={form.summary} onChange={(event) => setForm((current) => ({ ...current, summary: event.target.value }))} placeholder="Summary"
          className="min-h-24 w-full rounded-lg border border-slate-200 bg-slate-50 px-md py-sm text-body-sm" />
        <textarea value={form.included_items} onChange={(event) => setForm((current) => ({ ...current, included_items: event.target.value }))} placeholder="Included items, one per line"
          className="min-h-24 w-full rounded-lg border border-slate-200 bg-slate-50 px-md py-sm text-body-sm" />
        <button type="submit" disabled={saving} className="rounded-lg bg-primary px-md py-sm font-label-caps text-label-caps text-white hover:opacity-90 disabled:opacity-50">
          {saving ? 'Creating...' : 'Create Evidence Pack'}
        </button>
      </form>
      <section className="rounded-lg border border-slate-200 bg-white">
        {loading ? <div className="flex min-h-52 items-center justify-center text-body-sm text-on-surface-variant">Loading packs...</div> : (
          packs.length === 0 ? <div className="flex min-h-52 items-center justify-center text-body-sm text-on-surface-variant">No evidence packs yet.</div> : (
            <div className="divide-y divide-slate-100">
              {packs.map((pack) => (
                <article key={pack.id} className="px-lg py-md">
                  <h2 className="text-body-md font-bold text-on-surface">{pack.title}</h2>
                  {pack.summary && <p className="mt-xs text-body-sm text-on-surface-variant">{pack.summary}</p>}
                  {pack.included_items.length > 0 && <p className="mt-sm text-body-sm text-slate-500">Includes: {pack.included_items.join(', ')}</p>}
                </article>
              ))}
            </div>
          )
        )}
      </section>
    </div>
  );
}
