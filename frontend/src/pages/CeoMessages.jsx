import { useCallback, useEffect, useMemo, useState } from 'react';
import api from '../api/axios';
import { getCurrentUser, ROLES } from '../config/rolePermissions';

const PRIORITY_OPTIONS = ['normal', 'important', 'urgent', 'critical'];
const AUDIENCE_OPTIONS = [
  { value: 'bank', label: 'All active users' },
  { value: 'role', label: 'Role' },
  { value: 'department', label: 'Department' },
];
const ROLE_OPTIONS = [
  { value: 'staff_user', label: 'Staff' },
  { value: 'compliance_user', label: 'Compliance' },
  { value: 'compliance_officer', label: 'Compliance Officer' },
  { value: 'document_reviewer', label: 'Reviewer' },
  { value: 'auditor', label: 'Auditor' },
  { value: 'data_auditor', label: 'Data Auditor' },
  { value: 'bank_admin', label: 'Bank Admin' },
];

function messageFromError(err, fallback) {
  const detail = err?.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (detail?.code === 'feature_disabled') return "CEO's Message is not enabled for this bank.";
  return fallback;
}

function priorityClass(priority) {
  const classes = {
    normal: 'bg-slate-100 text-slate-700 border-slate-200',
    important: 'bg-amber-50 text-amber-700 border-amber-200',
    urgent: 'bg-red-50 text-red-700 border-red-200',
    critical: 'bg-slate-900 text-white border-slate-900',
  };
  return classes[priority] || classes.normal;
}

function formatWhen(value) {
  if (!value) return '';
  return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value));
}

export default function CeoMessages() {
  const currentUser = getCurrentUser();
  const isAdmin = currentUser?.role === ROLES.SUPER_ADMIN || currentUser?.role === ROLES.BANK_ADMIN;
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState('');
  const [form, setForm] = useState({
    title: '',
    body: '',
    audience_type: 'bank',
    role: 'staff_user',
    department: '',
    priority: 'normal',
    requires_acknowledgement: false,
    notify: true,
  });

  const unreadAckCount = useMemo(
    () => messages.filter((message) => message.requires_acknowledgement && !message.acknowledged_at).length,
    [messages]
  );

  const fetchMessages = useCallback(async () => {
    setLoading(true);
    setNotice('');
    try {
      const response = await api.get('/ceo-messages');
      setMessages(Array.isArray(response.data) ? response.data : []);
    } catch (err) {
      setMessages([]);
      setNotice(messageFromError(err, 'Could not load CEO messages.'));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMessages();
  }, [fetchMessages]);

  const updateForm = (key, value) => {
    setForm((current) => ({ ...current, [key]: value }));
  };

  const publishMessage = async (event) => {
    event.preventDefault();
    setSaving(true);
    setNotice('');
    try {
      const payload = {
        title: form.title.trim(),
        body: form.body.trim(),
        audience_type: form.audience_type,
        role: form.audience_type === 'role' ? form.role : null,
        department: form.audience_type === 'department' ? form.department.trim() : null,
        priority: form.priority,
        requires_acknowledgement: form.requires_acknowledgement,
        notify: form.notify,
      };
      await api.post('/ceo-messages', payload);
      setForm({
        title: '',
        body: '',
        audience_type: 'bank',
        role: 'staff_user',
        department: '',
        priority: 'normal',
        requires_acknowledgement: false,
        notify: true,
      });
      await fetchMessages();
      setNotice('CEO message published.');
    } catch (err) {
      setNotice(messageFromError(err, 'Could not publish CEO message.'));
    } finally {
      setSaving(false);
    }
  };

  const acknowledge = async (messageId) => {
    try {
      const response = await api.patch(`/ceo-messages/${messageId}/acknowledge`);
      setMessages((current) => current.map((message) => message.id === messageId ? response.data : message));
    } catch (err) {
      setNotice(messageFromError(err, 'Could not acknowledge this message.'));
    }
  };

  return (
    <div className="p-xl max-w-container-max mx-auto">
      <header className="mb-lg flex flex-col gap-md xl:flex-row xl:items-end xl:justify-between">
        <div>
          <h1 className="text-h1 font-h1 text-on-surface">CEO's Message</h1>
          <p className="font-body-md text-on-surface-variant mt-sm max-w-3xl">
            Executive announcements for employees, departments, and bank roles.
          </p>
        </div>
        <button
          type="button"
          onClick={fetchMessages}
          disabled={loading}
          className="inline-flex items-center justify-center gap-xs rounded-lg border border-slate-300 px-md py-sm font-label-caps text-label-caps text-on-surface hover:bg-white disabled:opacity-50"
        >
          <span className="material-symbols-outlined text-[17px]">refresh</span>
          Refresh
        </button>
      </header>

      {notice && (
        <div className="mb-md rounded-lg border border-slate-200 bg-white px-md py-sm text-body-sm text-slate-700">
          {notice}
        </div>
      )}

      <section className="mb-lg grid grid-cols-1 gap-gutter lg:grid-cols-3">
        <div className="rounded-lg border border-slate-200 bg-white p-md">
          <p className="font-label-caps text-label-caps uppercase text-on-surface-variant">Visible Messages</p>
          <p className="mt-xs text-h2 font-h2 text-on-surface">{messages.length}</p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-md">
          <p className="font-label-caps text-label-caps uppercase text-on-surface-variant">Pending Acks</p>
          <p className="mt-xs text-h2 font-h2 text-on-surface">{unreadAckCount}</p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-md">
          <p className="font-label-caps text-label-caps uppercase text-on-surface-variant">Audience</p>
          <p className="mt-xs text-body-md font-semibold text-on-surface">Bank-scoped</p>
        </div>
      </section>

      {isAdmin && (
        <section className="mb-lg rounded-lg border border-slate-200 bg-white p-lg">
          <div className="mb-md">
            <h2 className="text-h2 font-h2 text-on-surface">Publish Message</h2>
            <p className="text-body-sm text-on-surface-variant">Messages are visible only to matching active users in this bank.</p>
          </div>

          <form onSubmit={publishMessage} className="space-y-md">
            <div className="grid grid-cols-1 gap-md lg:grid-cols-2">
              <div>
                <label className="mb-xs block font-label-caps text-label-caps uppercase text-on-surface-variant">Title</label>
                <input
                  value={form.title}
                  onChange={(event) => updateForm('title', event.target.value)}
                  className="w-full rounded-lg border border-slate-200 bg-slate-50 px-md py-sm text-body-sm text-on-surface focus:border-secondary focus:outline-none"
                  required
                />
              </div>
              <div>
                <label className="mb-xs block font-label-caps text-label-caps uppercase text-on-surface-variant">Priority</label>
                <select
                  value={form.priority}
                  onChange={(event) => updateForm('priority', event.target.value)}
                  className="w-full rounded-lg border border-slate-200 bg-slate-50 px-md py-sm text-body-sm text-on-surface focus:border-secondary focus:outline-none"
                >
                  {PRIORITY_OPTIONS.map((priority) => (
                    <option key={priority} value={priority}>{priority}</option>
                  ))}
                </select>
              </div>
              <div className="lg:col-span-2">
                <label className="mb-xs block font-label-caps text-label-caps uppercase text-on-surface-variant">Message</label>
                <textarea
                  value={form.body}
                  onChange={(event) => updateForm('body', event.target.value)}
                  className="min-h-28 w-full resize-y rounded-lg border border-slate-200 bg-slate-50 px-md py-sm text-body-sm text-on-surface focus:border-secondary focus:outline-none"
                  required
                />
              </div>
              <div>
                <label className="mb-xs block font-label-caps text-label-caps uppercase text-on-surface-variant">Audience</label>
                <select
                  value={form.audience_type}
                  onChange={(event) => updateForm('audience_type', event.target.value)}
                  className="w-full rounded-lg border border-slate-200 bg-slate-50 px-md py-sm text-body-sm text-on-surface focus:border-secondary focus:outline-none"
                >
                  {AUDIENCE_OPTIONS.map((audience) => (
                    <option key={audience.value} value={audience.value}>{audience.label}</option>
                  ))}
                </select>
              </div>
              {form.audience_type === 'role' && (
                <div>
                  <label className="mb-xs block font-label-caps text-label-caps uppercase text-on-surface-variant">Role</label>
                  <select
                    value={form.role}
                    onChange={(event) => updateForm('role', event.target.value)}
                    className="w-full rounded-lg border border-slate-200 bg-slate-50 px-md py-sm text-body-sm text-on-surface focus:border-secondary focus:outline-none"
                  >
                    {ROLE_OPTIONS.map((role) => (
                      <option key={role.value} value={role.value}>{role.label}</option>
                    ))}
                  </select>
                </div>
              )}
              {form.audience_type === 'department' && (
                <div>
                  <label className="mb-xs block font-label-caps text-label-caps uppercase text-on-surface-variant">Department</label>
                  <input
                    value={form.department}
                    onChange={(event) => updateForm('department', event.target.value)}
                    className="w-full rounded-lg border border-slate-200 bg-slate-50 px-md py-sm text-body-sm text-on-surface focus:border-secondary focus:outline-none"
                    required
                  />
                </div>
              )}
            </div>

            <div className="flex flex-col gap-sm sm:flex-row sm:items-center sm:justify-between">
              <div className="flex flex-col gap-sm sm:flex-row sm:items-center">
                <label className="flex items-center gap-sm text-body-sm font-medium text-on-surface">
                  <input
                    type="checkbox"
                    checked={form.requires_acknowledgement}
                    onChange={(event) => updateForm('requires_acknowledgement', event.target.checked)}
                    className="h-4 w-4 rounded border-slate-300 text-secondary focus:ring-0"
                  />
                  Require acknowledgement
                </label>
                <label className="flex items-center gap-sm text-body-sm font-medium text-on-surface">
                  <input
                    type="checkbox"
                    checked={form.notify}
                    onChange={(event) => updateForm('notify', event.target.checked)}
                    className="h-4 w-4 rounded border-slate-300 text-secondary focus:ring-0"
                  />
                  Send notification
                </label>
              </div>
              <button
                type="submit"
                disabled={saving}
                className="inline-flex items-center justify-center gap-xs rounded-lg bg-primary px-md py-sm font-label-caps text-label-caps text-white hover:opacity-90 disabled:opacity-50"
              >
                <span className="material-symbols-outlined text-[17px]">campaign</span>
                {saving ? 'Publishing...' : 'Publish Message'}
              </button>
            </div>
          </form>
        </section>
      )}

      <section className="rounded-lg border border-slate-200 bg-white">
        {loading ? (
          <div className="flex min-h-52 items-center justify-center text-body-sm text-on-surface-variant">
            Loading messages...
          </div>
        ) : messages.length === 0 ? (
          <div className="flex min-h-52 flex-col items-center justify-center px-lg text-center">
            <div className="mb-md flex h-12 w-12 items-center justify-center rounded-lg bg-slate-100 text-slate-500">
              <span className="material-symbols-outlined text-[23px]">campaign</span>
            </div>
            <p className="text-body-md font-semibold text-on-surface">No CEO messages</p>
            <p className="mt-xs max-w-md text-body-sm text-on-surface-variant">There are no visible executive announcements right now.</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {messages.map((message) => (
              <article key={message.id} className="px-lg py-md">
                <div className="mb-sm flex flex-wrap items-center gap-sm">
                  <span className={`rounded border px-2 py-0.5 text-[10px] font-bold uppercase ${priorityClass(message.priority)}`}>
                    {message.priority}
                  </span>
                  <span className="rounded bg-slate-100 px-2 py-0.5 text-[10px] font-bold uppercase text-slate-600">
                    {message.audience_type}
                  </span>
                  {message.requires_acknowledgement && !message.acknowledged_at && (
                    <span className="rounded bg-amber-100 px-2 py-0.5 text-[10px] font-bold uppercase text-amber-800">Ack Required</span>
                  )}
                  {message.acknowledged_at && (
                    <span className="rounded bg-green-100 px-2 py-0.5 text-[10px] font-bold uppercase text-green-800">Acknowledged</span>
                  )}
                </div>
                <div className="grid grid-cols-1 gap-md xl:grid-cols-[1fr_auto] xl:items-start">
                  <div>
                    <h2 className="text-h2 font-h2 text-on-surface">{message.title}</h2>
                    <p className="mt-sm whitespace-pre-wrap text-body-md text-on-surface-variant">{message.body}</p>
                    <p className="mt-md text-[11px] font-semibold uppercase text-slate-400">
                      Published {formatWhen(message.published_at)}
                    </p>
                  </div>
                  {message.requires_acknowledgement && !message.acknowledged_at && (
                    <button
                      type="button"
                      onClick={() => acknowledge(message.id)}
                      className="inline-flex items-center justify-center gap-xs rounded-lg bg-primary px-md py-sm font-label-caps text-label-caps text-white hover:opacity-90"
                    >
                      <span className="material-symbols-outlined text-[17px]">task_alt</span>
                      Acknowledge
                    </button>
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
