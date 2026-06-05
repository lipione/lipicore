import { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/axios';
import { getCurrentUser, ROLES } from '../config/rolePermissions';

const CATEGORY_OPTIONS = ['system', 'policy', 'work_item', 'ceo_message', 'document', 'model', 'security', 'compliance'];
const SEVERITY_OPTIONS = ['info', 'warning', 'urgent', 'critical'];
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
  if (detail?.code === 'feature_disabled') return 'Notifications are not enabled for this bank.';
  return fallback;
}

function severityClass(severity) {
  const classes = {
    info: 'bg-blue-50 text-blue-700 border-blue-200',
    warning: 'bg-amber-50 text-amber-700 border-amber-200',
    urgent: 'bg-red-50 text-red-700 border-red-200',
    critical: 'bg-slate-900 text-white border-slate-900',
  };
  return classes[severity] || classes.info;
}

function formatWhen(value) {
  if (!value) return '';
  return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value));
}

export default function Notifications() {
  const navigate = useNavigate();
  const currentUser = getCurrentUser();
  const isAdmin = currentUser?.role === ROLES.SUPER_ADMIN || currentUser?.role === ROLES.BANK_ADMIN;
  const [notifications, setNotifications] = useState([]);
  const [includeRead, setIncludeRead] = useState(true);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState('');
  const [form, setForm] = useState({
    title: '',
    body: '',
    category: 'system',
    severity: 'info',
    audience_type: 'bank',
    role: 'staff_user',
    department: '',
    action_url: '',
    requires_acknowledgement: false,
  });

  const unreadCount = useMemo(
    () => notifications.filter((notification) => !notification.read_at).length,
    [notifications]
  );
  const ackRequiredCount = useMemo(
    () => notifications.filter((notification) => notification.requires_acknowledgement && !notification.acknowledged_at).length,
    [notifications]
  );

  const fetchNotifications = useCallback(async () => {
    setLoading(true);
    setNotice('');
    try {
      const response = await api.get('/notifications', {
        params: { include_read: includeRead, limit: 100 },
      });
      setNotifications(Array.isArray(response.data) ? response.data : []);
    } catch (err) {
      setNotifications([]);
      setNotice(messageFromError(err, 'Could not load notifications.'));
    } finally {
      setLoading(false);
    }
  }, [includeRead]);

  useEffect(() => {
    fetchNotifications();
  }, [fetchNotifications]);

  const updateForm = (key, value) => {
    setForm((current) => ({ ...current, [key]: value }));
  };

  const createNotification = async (event) => {
    event.preventDefault();
    setSaving(true);
    setNotice('');
    try {
      const payload = {
        title: form.title.trim(),
        body: form.body.trim(),
        category: form.category,
        severity: form.severity,
        audience_type: form.audience_type,
        role: form.audience_type === 'role' ? form.role : null,
        department: form.audience_type === 'department' ? form.department.trim() : null,
        action_url: form.action_url.trim() || null,
        requires_acknowledgement: form.requires_acknowledgement,
      };
      const response = await api.post('/notifications', payload);
      setForm({
        title: '',
        body: '',
        category: 'system',
        severity: 'info',
        audience_type: 'bank',
        role: 'staff_user',
        department: '',
        action_url: '',
        requires_acknowledgement: false,
      });
      await fetchNotifications();
      setNotice(`Notification sent to ${response.data.created_count} user${response.data.created_count === 1 ? '' : 's'}.`);
    } catch (err) {
      setNotice(messageFromError(err, 'Could not send notification.'));
    } finally {
      setSaving(false);
    }
  };

  const markRead = async (notificationId) => {
    try {
      const response = await api.patch(`/notifications/${notificationId}/read`);
      setNotifications((current) => current.map((item) => item.id === notificationId ? response.data : item));
    } catch (err) {
      setNotice(messageFromError(err, 'Could not mark notification read.'));
    }
  };

  const acknowledge = async (notificationId) => {
    try {
      const response = await api.patch(`/notifications/${notificationId}/acknowledge`);
      setNotifications((current) => current.map((item) => item.id === notificationId ? response.data : item));
    } catch (err) {
      setNotice(messageFromError(err, 'Could not acknowledge notification.'));
    }
  };

  return (
    <div className="p-xl max-w-container-max mx-auto">
      <header className="mb-lg flex flex-col gap-md xl:flex-row xl:items-end xl:justify-between">
        <div>
          <h1 className="text-h1 font-h1 text-on-surface">Notifications & Alerts</h1>
          <p className="font-body-md text-on-surface-variant mt-sm max-w-3xl">
            Bank alerts, acknowledgements, assigned-work notices, and operational updates.
          </p>
        </div>
        <button
          type="button"
          onClick={fetchNotifications}
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
          <p className="font-label-caps text-label-caps uppercase text-on-surface-variant">Unread</p>
          <p className="mt-xs text-h2 font-h2 text-on-surface">{unreadCount}</p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-md">
          <p className="font-label-caps text-label-caps uppercase text-on-surface-variant">Acknowledgements</p>
          <p className="mt-xs text-h2 font-h2 text-on-surface">{ackRequiredCount}</p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-md">
          <p className="font-label-caps text-label-caps uppercase text-on-surface-variant">Filter</p>
          <label className="mt-sm flex items-center gap-sm text-body-sm font-medium text-on-surface">
            <input
              type="checkbox"
              checked={includeRead}
              onChange={(event) => setIncludeRead(event.target.checked)}
              className="h-4 w-4 rounded border-slate-300 text-secondary focus:ring-0"
            />
            Show read notifications
          </label>
        </div>
      </section>

      {isAdmin && (
        <section className="mb-lg rounded-lg border border-slate-200 bg-white p-lg">
          <div className="mb-md">
            <h2 className="text-h2 font-h2 text-on-surface">Send Alert</h2>
            <p className="text-body-sm text-on-surface-variant">Alerts are delivered only to active users in this bank.</p>
          </div>

          <form onSubmit={createNotification} className="space-y-md">
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
                <label className="mb-xs block font-label-caps text-label-caps uppercase text-on-surface-variant">Action URL</label>
                <input
                  value={form.action_url}
                  onChange={(event) => updateForm('action_url', event.target.value)}
                  placeholder="/market-time"
                  className="w-full rounded-lg border border-slate-200 bg-slate-50 px-md py-sm text-body-sm text-on-surface focus:border-secondary focus:outline-none"
                />
              </div>
              <div className="lg:col-span-2">
                <label className="mb-xs block font-label-caps text-label-caps uppercase text-on-surface-variant">Body</label>
                <textarea
                  value={form.body}
                  onChange={(event) => updateForm('body', event.target.value)}
                  className="min-h-24 w-full resize-y rounded-lg border border-slate-200 bg-slate-50 px-md py-sm text-body-sm text-on-surface focus:border-secondary focus:outline-none"
                  required
                />
              </div>
              <div>
                <label className="mb-xs block font-label-caps text-label-caps uppercase text-on-surface-variant">Category</label>
                <select
                  value={form.category}
                  onChange={(event) => updateForm('category', event.target.value)}
                  className="w-full rounded-lg border border-slate-200 bg-slate-50 px-md py-sm text-body-sm text-on-surface focus:border-secondary focus:outline-none"
                >
                  {CATEGORY_OPTIONS.map((category) => (
                    <option key={category} value={category}>{category.replaceAll('_', ' ')}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="mb-xs block font-label-caps text-label-caps uppercase text-on-surface-variant">Severity</label>
                <select
                  value={form.severity}
                  onChange={(event) => updateForm('severity', event.target.value)}
                  className="w-full rounded-lg border border-slate-200 bg-slate-50 px-md py-sm text-body-sm text-on-surface focus:border-secondary focus:outline-none"
                >
                  {SEVERITY_OPTIONS.map((severity) => (
                    <option key={severity} value={severity}>{severity}</option>
                  ))}
                </select>
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
              <label className="flex items-center gap-sm text-body-sm font-medium text-on-surface">
                <input
                  type="checkbox"
                  checked={form.requires_acknowledgement}
                  onChange={(event) => updateForm('requires_acknowledgement', event.target.checked)}
                  className="h-4 w-4 rounded border-slate-300 text-secondary focus:ring-0"
                />
                Require acknowledgement
              </label>
              <button
                type="submit"
                disabled={saving}
                className="inline-flex items-center justify-center gap-xs rounded-lg bg-primary px-md py-sm font-label-caps text-label-caps text-white hover:opacity-90 disabled:opacity-50"
              >
                <span className="material-symbols-outlined text-[17px]">send</span>
                {saving ? 'Sending...' : 'Send Alert'}
              </button>
            </div>
          </form>
        </section>
      )}

      <section className="rounded-lg border border-slate-200 bg-white">
        {loading ? (
          <div className="flex min-h-52 items-center justify-center text-body-sm text-on-surface-variant">
            Loading notifications...
          </div>
        ) : notifications.length === 0 ? (
          <div className="flex min-h-52 flex-col items-center justify-center px-lg text-center">
            <div className="mb-md flex h-12 w-12 items-center justify-center rounded-lg bg-slate-100 text-slate-500">
              <span className="material-symbols-outlined text-[23px]">notifications_off</span>
            </div>
            <p className="text-body-md font-semibold text-on-surface">No notifications</p>
            <p className="mt-xs max-w-md text-body-sm text-on-surface-variant">There are no alerts matching the current filter.</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {notifications.map((notification) => (
              <article key={notification.id} className="grid grid-cols-1 gap-md px-lg py-md xl:grid-cols-[1fr_auto] xl:items-start">
                <div className="min-w-0">
                  <div className="mb-xs flex flex-wrap items-center gap-sm">
                    <span className={`rounded border px-2 py-0.5 text-[10px] font-bold uppercase ${severityClass(notification.severity)}`}>
                      {notification.severity}
                    </span>
                    <span className="rounded bg-slate-100 px-2 py-0.5 text-[10px] font-bold uppercase text-slate-600">
                      {notification.category.replaceAll('_', ' ')}
                    </span>
                    {!notification.read_at && (
                      <span className="rounded bg-green-100 px-2 py-0.5 text-[10px] font-bold uppercase text-green-800">Unread</span>
                    )}
                    {notification.requires_acknowledgement && !notification.acknowledged_at && (
                      <span className="rounded bg-amber-100 px-2 py-0.5 text-[10px] font-bold uppercase text-amber-800">Ack Required</span>
                    )}
                  </div>
                  <h2 className="text-body-md font-bold text-on-surface">{notification.title}</h2>
                  <p className="mt-xs text-body-sm text-on-surface-variant">{notification.body}</p>
                  <p className="mt-sm text-[11px] font-semibold uppercase text-slate-400">
                    {formatWhen(notification.created_at)}
                  </p>
                </div>
                <div className="flex flex-wrap gap-sm xl:justify-end">
                  {notification.action_url && (
                    <button
                      type="button"
                      onClick={() => navigate(notification.action_url)}
                      className="inline-flex items-center gap-xs rounded-lg border border-slate-200 px-md py-sm font-label-caps text-label-caps text-on-surface hover:bg-slate-50"
                    >
                      <span className="material-symbols-outlined text-[17px]">open_in_new</span>
                      Open
                    </button>
                  )}
                  {!notification.read_at && (
                    <button
                      type="button"
                      onClick={() => markRead(notification.id)}
                      className="inline-flex items-center gap-xs rounded-lg border border-slate-200 px-md py-sm font-label-caps text-label-caps text-on-surface hover:bg-slate-50"
                    >
                      <span className="material-symbols-outlined text-[17px]">done</span>
                      Mark Read
                    </button>
                  )}
                  {notification.requires_acknowledgement && !notification.acknowledged_at && (
                    <button
                      type="button"
                      onClick={() => acknowledge(notification.id)}
                      className="inline-flex items-center gap-xs rounded-lg bg-primary px-md py-sm font-label-caps text-label-caps text-white hover:opacity-90"
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
