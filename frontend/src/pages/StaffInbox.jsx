import { useCallback, useEffect, useMemo, useState } from 'react';
import api from '../api/axios';
import { getCurrentUser, ROLES } from '../config/rolePermissions';

const STATUS_OPTIONS = ['', 'open', 'in_progress', 'waiting_review', 'completed', 'dismissed'];
const PRIORITY_CLASSES = {
  low: 'bg-slate-100 text-slate-700',
  normal: 'bg-blue-50 text-blue-700',
  high: 'bg-amber-50 text-amber-700',
  urgent: 'bg-red-50 text-red-700',
};

function messageFromError(err, fallback) {
  const detail = err?.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (detail?.code === 'feature_disabled') return 'Staff Daily Inbox is not enabled for this bank.';
  return fallback;
}

function formatWhen(value) {
  if (!value) return 'No due date';
  return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value));
}

export default function StaffInbox() {
  const currentUser = getCurrentUser();
  const isAdmin = currentUser?.role === ROLES.SUPER_ADMIN || currentUser?.role === ROLES.BANK_ADMIN;
  const [items, setItems] = useState([]);
  const [status, setStatus] = useState('');
  const [scope, setScope] = useState('mine');
  const [loading, setLoading] = useState(false);
  const [notice, setNotice] = useState('');

  const openCount = useMemo(
    () => items.filter((item) => !['completed', 'dismissed'].includes(item.status)).length,
    [items]
  );
  const urgentCount = useMemo(
    () => items.filter((item) => item.priority === 'urgent' && !['completed', 'dismissed'].includes(item.status)).length,
    [items]
  );

  const fetchItems = useCallback(async () => {
    setLoading(true);
    setNotice('');
    try {
      const response = await api.get('/staff-work-items', {
        params: {
          scope: isAdmin ? scope : 'mine',
          status: status || undefined,
          include_closed: true,
        },
      });
      setItems(Array.isArray(response.data) ? response.data : []);
    } catch (err) {
      setItems([]);
      setNotice(messageFromError(err, 'Could not load staff inbox.'));
    } finally {
      setLoading(false);
    }
  }, [isAdmin, scope, status]);

  useEffect(() => {
    fetchItems();
  }, [fetchItems]);

  const updateStatus = async (itemId, nextStatus) => {
    try {
      const response = await api.patch(`/staff-work-items/${itemId}`, { status: nextStatus });
      setItems((current) => current.map((item) => item.id === itemId ? response.data : item));
    } catch (err) {
      setNotice(messageFromError(err, 'Could not update work item.'));
    }
  };

  return (
    <div className="p-xl max-w-container-max mx-auto">
      <header className="mb-lg flex flex-col gap-md xl:flex-row xl:items-end xl:justify-between">
        <div>
          <h1 className="text-h1 font-h1 text-on-surface">Staff Daily Inbox</h1>
          <p className="font-body-md text-on-surface-variant mt-sm max-w-3xl">
            Assigned follow-ups, acknowledgements, reviews, and internal banking work.
          </p>
        </div>
        <button
          type="button"
          onClick={fetchItems}
          disabled={loading}
          className="inline-flex items-center justify-center gap-xs rounded-lg border border-slate-300 px-md py-sm font-label-caps text-label-caps text-on-surface hover:bg-white disabled:opacity-50"
        >
          <span className="material-symbols-outlined text-[17px]">refresh</span>
          Refresh
        </button>
      </header>

      {notice && <div className="mb-md rounded-lg border border-slate-200 bg-white px-md py-sm text-body-sm text-slate-700">{notice}</div>}

      <section className="mb-lg grid grid-cols-1 gap-gutter lg:grid-cols-3">
        <div className="rounded-lg border border-slate-200 bg-white p-md">
          <p className="font-label-caps text-label-caps uppercase text-on-surface-variant">Open Items</p>
          <p className="mt-xs text-h2 font-h2 text-on-surface">{openCount}</p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-md">
          <p className="font-label-caps text-label-caps uppercase text-on-surface-variant">Urgent</p>
          <p className="mt-xs text-h2 font-h2 text-on-surface">{urgentCount}</p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-md">
          <p className="font-label-caps text-label-caps uppercase text-on-surface-variant">Filters</p>
          <div className="mt-sm grid grid-cols-1 gap-sm sm:grid-cols-2">
            <select value={status} onChange={(event) => setStatus(event.target.value)}
              className="rounded border border-slate-200 bg-slate-50 px-sm py-xs text-body-sm">
              {STATUS_OPTIONS.map((option) => <option key={option || 'all'} value={option}>{option || 'all statuses'}</option>)}
            </select>
            {isAdmin && (
              <select value={scope} onChange={(event) => setScope(event.target.value)}
                className="rounded border border-slate-200 bg-slate-50 px-sm py-xs text-body-sm">
                <option value="mine">my items</option>
                <option value="bank">bank-wide</option>
              </select>
            )}
          </div>
        </div>
      </section>

      <section className="rounded-lg border border-slate-200 bg-white">
        {loading ? (
          <div className="flex min-h-52 items-center justify-center text-body-sm text-on-surface-variant">Loading work items...</div>
        ) : items.length === 0 ? (
          <div className="flex min-h-52 flex-col items-center justify-center px-lg text-center">
            <div className="mb-md flex h-12 w-12 items-center justify-center rounded-lg bg-slate-100 text-slate-500">
              <span className="material-symbols-outlined text-[23px]">inbox</span>
            </div>
            <p className="text-body-md font-semibold text-on-surface">No work items</p>
            <p className="mt-xs max-w-md text-body-sm text-on-surface-variant">There is no assigned work for the current filter.</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {items.map((item) => (
              <article key={item.id} className="grid grid-cols-1 gap-md px-lg py-md xl:grid-cols-[1fr_auto] xl:items-start">
                <div className="min-w-0">
                  <div className="mb-xs flex flex-wrap items-center gap-sm">
                    <span className={`rounded px-2 py-0.5 text-[10px] font-bold uppercase ${PRIORITY_CLASSES[item.priority] || PRIORITY_CLASSES.normal}`}>{item.priority}</span>
                    <span className="rounded bg-slate-100 px-2 py-0.5 text-[10px] font-bold uppercase text-slate-600">{item.status}</span>
                    {item.source_type && <span className="rounded bg-white px-2 py-0.5 text-[10px] font-bold uppercase text-slate-500 ring-1 ring-slate-200">{item.source_type.replaceAll('_', ' ')}</span>}
                  </div>
                  <h2 className="text-body-md font-bold text-on-surface">{item.title}</h2>
                  {item.description && <p className="mt-xs text-body-sm text-on-surface-variant">{item.description}</p>}
                  <p className="mt-sm text-[11px] font-semibold uppercase text-slate-400">Due {formatWhen(item.due_at)}</p>
                </div>
                <div className="flex flex-wrap gap-sm xl:justify-end">
                  {!['completed', 'dismissed'].includes(item.status) && (
                    <>
                      <button type="button" onClick={() => updateStatus(item.id, 'in_progress')}
                        className="rounded-lg border border-slate-200 px-md py-sm font-label-caps text-label-caps text-on-surface hover:bg-slate-50">
                        Start
                      </button>
                      <button type="button" onClick={() => updateStatus(item.id, 'completed')}
                        className="rounded-lg bg-primary px-md py-sm font-label-caps text-label-caps text-white hover:opacity-90">
                        Complete
                      </button>
                    </>
                  )}
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
