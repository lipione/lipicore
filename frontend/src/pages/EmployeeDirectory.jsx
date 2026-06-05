import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/axios';
import { createDirectConversation } from '../api/messenger';
import { getCurrentUser, ROLES } from '../config/rolePermissions';
import { useFeatureFlags } from '../contexts/FeatureFlagContext';

const ROLE_OPTIONS = [
  { value: '', label: 'All roles' },
  { value: 'staff_user', label: 'Staff' },
  { value: 'compliance_user', label: 'Compliance' },
  { value: 'compliance_officer', label: 'Compliance Officer' },
  { value: 'document_reviewer', label: 'Reviewer' },
  { value: 'auditor', label: 'Auditor' },
  { value: 'data_auditor', label: 'Data Auditor' },
  { value: 'bank_admin', label: 'Bank Admin' },
];

function roleLabel(role) {
  return ROLE_OPTIONS.find((option) => option.value === role)?.label || role;
}

function messageFromError(err, fallback) {
  const detail = err?.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (detail?.code === 'feature_disabled') return 'Employee Directory is not enabled for this bank.';
  return fallback;
}

export default function EmployeeDirectory() {
  const navigate = useNavigate();
  const currentUser = getCurrentUser();
  const { isFeatureEnabled } = useFeatureFlags();
  const canUseStaffInbox = isFeatureEnabled('staff_inbox');
  const isAdmin = currentUser?.role === ROLES.SUPER_ADMIN || currentUser?.role === ROLES.BANK_ADMIN;

  const [filters, setFilters] = useState({
    q: '',
    department: '',
    role: '',
    branch: '',
    expertise: '',
    includeDisabled: false,
  });
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [notice, setNotice] = useState('');
  const [messagingId, setMessagingId] = useState(null);

  const activeCount = useMemo(
    () => results.filter((employee) => employee.is_active).length,
    [results]
  );

  const fetchEmployees = async () => {
    setLoading(true);
    setNotice('');
    try {
      const response = await api.get('/employee-directory', {
        params: {
          q: filters.q || undefined,
          department: filters.department || undefined,
          role: filters.role || undefined,
          branch: filters.branch || undefined,
          expertise: filters.expertise || undefined,
          include_disabled: isAdmin ? filters.includeDisabled : undefined,
          limit: 50,
        },
      });
      setResults(Array.isArray(response.data) ? response.data : []);
    } catch (err) {
      setResults([]);
      setNotice(messageFromError(err, 'Could not load the employee directory.'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEmployees();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const updateFilter = (key, value) => {
    setFilters((current) => ({ ...current, [key]: value }));
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    fetchEmployees();
  };

  const handleMessage = async (employee) => {
    if (!employee.can_message || !canUseStaffInbox) return;
    setMessagingId(employee.id);
    setNotice('');
    try {
      await createDirectConversation(employee.id);
      navigate('/messenger');
    } catch (err) {
      setNotice(messageFromError(err, 'Could not open a direct message.'));
    } finally {
      setMessagingId(null);
    }
  };

  return (
    <div className="p-xl max-w-container-max mx-auto">
      <header className="mb-lg flex flex-col gap-md xl:flex-row xl:items-end xl:justify-between">
        <div>
          <h1 className="text-h1 font-h1 text-on-surface">Employee Directory</h1>
          <p className="font-body-md text-on-surface-variant mt-sm max-w-3xl">
            Find employees by department, branch, role, expertise, and escalation area.
          </p>
        </div>
        <div className="grid grid-cols-2 gap-sm sm:flex sm:items-center">
          <div className="rounded-lg border border-slate-200 bg-white px-md py-sm">
            <p className="font-label-caps text-label-caps uppercase text-on-surface-variant">Results</p>
            <p className="text-body-md font-bold text-on-surface">{results.length}</p>
          </div>
          <div className="rounded-lg border border-slate-200 bg-white px-md py-sm">
            <p className="font-label-caps text-label-caps uppercase text-on-surface-variant">Active</p>
            <p className="text-body-md font-bold text-on-surface">{activeCount}</p>
          </div>
        </div>
      </header>

      {notice && (
        <div className="mb-md rounded-lg border border-slate-200 bg-white px-md py-sm text-body-sm text-slate-700">
          {notice}
        </div>
      )}

      <form onSubmit={handleSubmit} className="mb-lg rounded-lg border border-slate-200 bg-white p-lg">
        <div className="grid grid-cols-1 gap-md lg:grid-cols-12">
          <div className="lg:col-span-4">
            <label className="mb-xs block font-label-caps text-label-caps uppercase text-on-surface-variant">Search</label>
            <div className="relative">
              <span className="material-symbols-outlined pointer-events-none absolute left-3 top-2.5 text-[18px] text-slate-400">search</span>
              <input
                value={filters.q}
                onChange={(event) => updateFilter('q', event.target.value)}
                placeholder="Name, email, expertise, escalation"
                className="w-full rounded-lg border border-slate-200 bg-slate-50 py-sm pl-10 pr-md text-body-sm text-on-surface focus:border-secondary focus:outline-none"
              />
            </div>
          </div>

          <div className="lg:col-span-2">
            <label className="mb-xs block font-label-caps text-label-caps uppercase text-on-surface-variant">Department</label>
            <input
              value={filters.department}
              onChange={(event) => updateFilter('department', event.target.value)}
              className="w-full rounded-lg border border-slate-200 bg-slate-50 px-md py-sm text-body-sm text-on-surface focus:border-secondary focus:outline-none"
            />
          </div>

          <div className="lg:col-span-2">
            <label className="mb-xs block font-label-caps text-label-caps uppercase text-on-surface-variant">Role</label>
            <select
              value={filters.role}
              onChange={(event) => updateFilter('role', event.target.value)}
              className="w-full rounded-lg border border-slate-200 bg-slate-50 px-md py-sm text-body-sm text-on-surface focus:border-secondary focus:outline-none"
            >
              {ROLE_OPTIONS.map((option) => (
                <option key={option.value || 'all'} value={option.value}>{option.label}</option>
              ))}
            </select>
          </div>

          <div className="lg:col-span-2">
            <label className="mb-xs block font-label-caps text-label-caps uppercase text-on-surface-variant">Branch</label>
            <input
              value={filters.branch}
              onChange={(event) => updateFilter('branch', event.target.value)}
              className="w-full rounded-lg border border-slate-200 bg-slate-50 px-md py-sm text-body-sm text-on-surface focus:border-secondary focus:outline-none"
            />
          </div>

          <div className="lg:col-span-2">
            <label className="mb-xs block font-label-caps text-label-caps uppercase text-on-surface-variant">Expertise</label>
            <input
              value={filters.expertise}
              onChange={(event) => updateFilter('expertise', event.target.value)}
              className="w-full rounded-lg border border-slate-200 bg-slate-50 px-md py-sm text-body-sm text-on-surface focus:border-secondary focus:outline-none"
            />
          </div>
        </div>

        <div className="mt-md flex flex-col gap-md sm:flex-row sm:items-center sm:justify-between">
          {isAdmin ? (
            <label className="flex items-center gap-sm text-body-sm font-medium text-on-surface">
              <input
                type="checkbox"
                checked={filters.includeDisabled}
                onChange={(event) => updateFilter('includeDisabled', event.target.checked)}
                className="h-4 w-4 rounded border-slate-300 text-secondary focus:ring-0"
              />
              Include disabled employees
            </label>
          ) : (
            <span className="text-body-sm text-on-surface-variant">Active employees only</span>
          )}
          <button
            type="submit"
            disabled={loading}
            className="inline-flex items-center justify-center gap-xs rounded-lg bg-primary px-md py-sm font-label-caps text-label-caps text-white transition-colors hover:opacity-90 disabled:opacity-50"
          >
            <span className="material-symbols-outlined text-[17px]">manage_search</span>
            {loading ? 'Searching...' : 'Search Directory'}
          </button>
        </div>
      </form>

      <section className="rounded-lg border border-slate-200 bg-white">
        <div className="grid grid-cols-[1.5fr_1fr_1fr_160px] gap-md border-b border-slate-100 px-lg py-sm text-[11px] font-bold uppercase text-slate-400 max-xl:hidden">
          <span>Employee</span>
          <span>Branch & Role</span>
          <span>Expertise</span>
          <span className="text-right">Action</span>
        </div>

        {loading ? (
          <div className="flex min-h-52 items-center justify-center text-body-sm text-on-surface-variant">
            Loading directory...
          </div>
        ) : results.length === 0 ? (
          <div className="flex min-h-52 flex-col items-center justify-center px-lg text-center">
            <div className="mb-md flex h-12 w-12 items-center justify-center rounded-lg bg-slate-100 text-slate-500">
              <span className="material-symbols-outlined text-[23px]">person_search</span>
            </div>
            <p className="text-body-md font-semibold text-on-surface">No employees found</p>
            <p className="mt-xs max-w-md text-body-sm text-on-surface-variant">
              Try a different name, branch, department, or expertise filter.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {results.map((employee) => (
              <div key={employee.id} className="grid grid-cols-1 gap-md px-lg py-md xl:grid-cols-[1.5fr_1fr_1fr_160px] xl:items-center">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-sm">
                    <h2 className="truncate text-body-md font-bold text-on-surface">{employee.name}</h2>
                    <span className={`rounded px-2 py-0.5 text-[10px] font-bold uppercase ${
                      employee.is_active ? 'bg-green-100 text-green-800' : 'bg-slate-100 text-slate-600'
                    }`}>
                      {employee.is_active ? employee.availability_status : 'Disabled'}
                    </span>
                  </div>
                  <p className="truncate text-body-sm text-on-surface-variant">{employee.email}</p>
                  {employee.department && (
                    <p className="mt-xs text-[12px] font-semibold uppercase text-slate-400">{employee.department}</p>
                  )}
                </div>

                <div className="min-w-0 text-body-sm text-on-surface">
                  <p className="font-semibold">{employee.branch || 'No branch'}</p>
                  <p className="text-on-surface-variant">{employee.job_title || roleLabel(employee.role)}</p>
                  {employee.phone_extension && (
                    <p className="mt-xs text-[12px] text-slate-500">Ext. {employee.phone_extension}</p>
                  )}
                </div>

                <div className="min-w-0">
                  <div className="flex flex-wrap gap-xs">
                    {employee.expertise_tags.length ? employee.expertise_tags.map((tag) => (
                      <span key={`${employee.id}-${tag}`} className="rounded bg-slate-100 px-2 py-1 text-[11px] font-semibold text-slate-700">
                        {tag}
                      </span>
                    )) : (
                      <span className="text-body-sm text-on-surface-variant">No tags</span>
                    )}
                  </div>
                  {employee.escalation_areas.length > 0 && (
                    <p className="mt-xs truncate text-[12px] text-slate-500">
                      Escalation: {employee.escalation_areas.join(', ')}
                    </p>
                  )}
                </div>

                <div className="flex justify-start xl:justify-end">
                  <button
                    type="button"
                    disabled={!employee.can_message || !canUseStaffInbox || messagingId === employee.id}
                    onClick={() => handleMessage(employee)}
                    className="inline-flex min-w-32 items-center justify-center gap-xs rounded-lg border border-slate-200 px-md py-sm font-label-caps text-label-caps text-on-surface transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
                    title={canUseStaffInbox ? 'Message employee' : 'Staff Inbox is disabled'}
                  >
                    <span className="material-symbols-outlined text-[17px]">forum</span>
                    {messagingId === employee.id ? 'Opening...' : 'Message'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
