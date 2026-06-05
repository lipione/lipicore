import { useCallback, useEffect, useState } from 'react';
import api from '../api/axios';

function messageFromError(err, fallback) {
  const detail = err?.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (detail?.code === 'feature_disabled') return 'This workflow is not enabled for this bank.';
  return fallback;
}

export default function BankingWorkflowWorkspace({ title, description, endpoint, checklist = false }) {
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState('');
  const [form, setForm] = useState({
    title: '',
    prompt: '',
    customer_reference: '',
    priority: 'normal',
    required_items: '',
    provided_items: '',
  });

  const fetchCases = useCallback(async () => {
    setLoading(true);
    setNotice('');
    try {
      const response = await api.get(`${endpoint}/cases`);
      setCases(Array.isArray(response.data) ? response.data : []);
    } catch (err) {
      setCases([]);
      setNotice(messageFromError(err, 'Could not load workflow cases.'));
    } finally {
      setLoading(false);
    }
  }, [endpoint]);

  useEffect(() => { fetchCases(); }, [fetchCases]);

  const submit = async (event) => {
    event.preventDefault();
    setSaving(true);
    setNotice('');
    try {
      if (checklist) {
        await api.post(`${endpoint}/validate`, {
          title: form.title.trim(),
          prompt: form.prompt.trim(),
          required_items: form.required_items.split('\n').map((item) => item.trim()).filter(Boolean),
          provided_items: form.provided_items.split('\n').map((item) => item.trim()).filter(Boolean),
        });
      } else {
        await api.post(`${endpoint}/cases`, {
          title: form.title.trim(),
          prompt: form.prompt.trim(),
          customer_reference: form.customer_reference.trim() || null,
          priority: form.priority,
        });
      }
      setForm({ title: '', prompt: '', customer_reference: '', priority: 'normal', required_items: '', provided_items: '' });
      await fetchCases();
      setNotice('Workflow case created.');
    } catch (err) {
      setNotice(messageFromError(err, 'Could not create workflow case.'));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="p-xl max-w-container-max mx-auto">
      <header className="mb-lg flex flex-col gap-md xl:flex-row xl:items-end xl:justify-between">
        <div>
          <h1 className="text-h1 font-h1 text-on-surface">{title}</h1>
          <p className="font-body-md text-on-surface-variant mt-sm max-w-3xl">{description}</p>
        </div>
        <button type="button" onClick={fetchCases} disabled={loading}
          className="rounded-lg border border-slate-300 px-md py-sm font-label-caps text-label-caps text-on-surface hover:bg-white disabled:opacity-50">
          Refresh
        </button>
      </header>

      {notice && <div className="mb-md rounded-lg border border-slate-200 bg-white px-md py-sm text-body-sm text-slate-700">{notice}</div>}

      <form onSubmit={submit} className="mb-lg rounded-lg border border-slate-200 bg-white p-lg space-y-md">
        <input value={form.title} onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))} placeholder="Case title"
          className="w-full rounded-lg border border-slate-200 bg-slate-50 px-md py-sm text-body-sm" required />
        {!checklist && (
          <div className="grid grid-cols-1 gap-md lg:grid-cols-[1fr_180px]">
            <input value={form.customer_reference} onChange={(event) => setForm((current) => ({ ...current, customer_reference: event.target.value }))} placeholder="Customer/reference number"
              className="w-full rounded-lg border border-slate-200 bg-slate-50 px-md py-sm text-body-sm" />
            <select value={form.priority} onChange={(event) => setForm((current) => ({ ...current, priority: event.target.value }))}
              className="w-full rounded-lg border border-slate-200 bg-slate-50 px-md py-sm text-body-sm">
              <option value="low">Low priority</option>
              <option value="normal">Normal priority</option>
              <option value="high">High priority</option>
              <option value="urgent">Urgent priority</option>
            </select>
          </div>
        )}
        <textarea value={form.prompt} onChange={(event) => setForm((current) => ({ ...current, prompt: event.target.value }))} placeholder={checklist ? 'Checklist context or file notes' : 'Facts, request, circular, complaint, or case notes'}
          className="min-h-28 w-full rounded-lg border border-slate-200 bg-slate-50 px-md py-sm text-body-sm" required={!checklist} />
        {checklist && (
          <div className="grid grid-cols-1 gap-md lg:grid-cols-2">
            <textarea value={form.required_items} onChange={(event) => setForm((current) => ({ ...current, required_items: event.target.value }))} placeholder="Required items, one per line"
              className="min-h-28 rounded-lg border border-slate-200 bg-slate-50 px-md py-sm text-body-sm" required />
            <textarea value={form.provided_items} onChange={(event) => setForm((current) => ({ ...current, provided_items: event.target.value }))} placeholder="Provided items, one per line"
              className="min-h-28 rounded-lg border border-slate-200 bg-slate-50 px-md py-sm text-body-sm" required />
          </div>
        )}
        <button type="submit" disabled={saving} className="rounded-lg bg-primary px-md py-sm font-label-caps text-label-caps text-white hover:opacity-90 disabled:opacity-50">
          {saving ? 'Creating...' : checklist ? 'Validate Checklist' : 'Create Draft'}
        </button>
      </form>

      <section className="rounded-lg border border-slate-200 bg-white">
        {loading ? <div className="flex min-h-52 items-center justify-center text-body-sm text-on-surface-variant">Loading cases...</div> : (
          cases.length === 0 ? <div className="flex min-h-52 items-center justify-center text-body-sm text-on-surface-variant">No cases yet.</div> : (
            <div className="divide-y divide-slate-100">
              {cases.map((item) => (
                <article key={item.id} className="px-lg py-md">
                  <div className="mb-xs flex flex-wrap gap-sm">
                    <span className="rounded bg-slate-100 px-2 py-0.5 text-[10px] font-bold uppercase text-slate-600">{item.status}</span>
                    <span className="rounded bg-white px-2 py-0.5 text-[10px] font-bold uppercase text-slate-500 ring-1 ring-slate-200">{item.priority}</span>
                    {item.customer_reference && <span className="rounded bg-white px-2 py-0.5 text-[10px] font-bold uppercase text-slate-500 ring-1 ring-slate-200">{item.customer_reference}</span>}
                  </div>
                  <h2 className="text-body-md font-bold text-on-surface">{item.title}</h2>
                  <p className="mt-sm whitespace-pre-wrap text-body-sm text-on-surface-variant">{item.output_summary}</p>
                  {item.metadata?.missing_items?.length > 0 && <p className="mt-sm text-body-sm font-semibold text-amber-700">Missing: {item.metadata.missing_items.join(', ')}</p>}
                </article>
              ))}
            </div>
          )
        )}
      </section>
    </div>
  );
}
