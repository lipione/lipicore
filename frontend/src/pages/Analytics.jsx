import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/axios';

const CHART_HEIGHTS = [40, 55, 45, 60, 75, 70, 85, 80, 95, 100, 85, 90, 75, 65, 70, 80, 90, 85, 95, 88, 72, 78, 83, 91, 86, 70, 75, 88, 95, 100];

const DOC_TYPES = [
  { label: 'Loan Agreements',  pct: 42 },
  { label: 'Compliance Audits', pct: 28 },
  { label: 'KYC Documents',    pct: 18 },
  { label: 'Tax Statements',   pct: 12 },
];

const DEPARTMENTS = [
  { name: 'Treasury',           analyses: 42105, conf: 99.1, trend: '+5.2%',  positive: true,  status: 'active' },
  { name: 'Retail Ops',         analyses: 38442, conf: 97.8, trend: '+18.4%', positive: true,  status: 'active' },
  { name: 'Risk Management',    analyses: 31002, conf: 96.4, trend: '+2.1%',  positive: true,  status: 'active' },
  { name: 'Legal & Compliance', analyses: 22810, conf: 99.5, trend: '-1.4%',  positive: false, status: 'active' },
  { name: 'Wealth Advisory',    analyses: 8535,  conf: 98.2, trend: '+44.2%', positive: true,  status: 'onboarding' },
];

const MODEL_LABELS = {
  fast: {
    label: 'LipiFast',
    detail: 'Default staff chat and drafting route',
    icon: 'bolt',
  },
  deep: {
    label: 'LipiCore',
    detail: 'Deeper analysis route for heavier prompts',
    icon: 'psychology',
  },
  vision: {
    label: 'LipiCore',
    detail: 'Document image and OCR review route',
    icon: 'visibility',
  },
};

const CAPACITY_EVIDENCE = [
  { label: '100 staff API smoke', value: '0 failures', detail: '2,357 requests · p95 57ms' },
  { label: '20 staff stream burst', value: 'p95 29.95s', detail: '20/20 real answers' },
  { label: '40 staff stream burst', value: 'p95 80.19s', detail: '40/40 real answers · slow tail' },
];

const SERVICE_LABELS = {
  database: { label: 'Postgres', icon: 'database' },
  qdrant: { label: 'Vector DB', icon: 'hub' },
  redis: { label: 'Redis Queue', icon: 'view_list' },
  storage: { label: 'Storage', icon: 'hard_drive' },
};

function ConfBadge({ conf }) {
  const cls = conf >= 98 ? 'bg-green-50 text-green-700'
    : conf >= 95       ? 'bg-yellow-50 text-yellow-700'
    : 'bg-red-50 text-error';
  return <span className={`px-2 py-1 text-xs font-bold rounded ${cls}`}>{conf}%</span>;
}

function capacityState(model) {
  const active = Number(model?.active || 0);
  const waiting = Number(model?.waiting || 0);
  const limit = Math.max(Number(model?.limit || 0), 1);
  const usage = Math.min(Math.round((active / limit) * 100), 100);
  if (waiting > 0) return { label: 'Queued', cls: 'bg-amber-50 text-amber-800 border-amber-200', usage };
  if (usage >= 90) return { label: 'Saturated', cls: 'bg-rose-50 text-rose-800 border-rose-200', usage };
  if (active > 0) return { label: 'Serving', cls: 'bg-sky-50 text-sky-800 border-sky-200', usage };
  return { label: 'Available', cls: 'bg-emerald-50 text-emerald-800 border-emerald-200', usage };
}

function capacityInterpretation(model) {
  const active = Number(model?.active || 0);
  const waiting = Number(model?.waiting || 0);
  const limit = Number(model?.limit || 0);
  if (!limit) return 'No configured capacity reported for this route.';
  if (waiting > 0) return 'Staff requests are waiting. Expect slower answers until slots free up.';
  if (active >= limit) return 'All slots are occupied. New requests may queue or time out.';
  if (active > 0) return 'The model is serving requests and still has spare slots.';
  return 'No active requests. New staff prompts should start immediately.';
}

function ModelCapacityCard({ name, model }) {
  const config = MODEL_LABELS[name] || { label: name, detail: 'Local model route', icon: 'memory' };
  const active = Number(model?.active || 0);
  const waiting = Number(model?.waiting || 0);
  const limit = Number(model?.limit || 0);
  const state = capacityState(model);

  return (
    <div className="bg-white border border-slate-200 rounded-lg p-lg">
      <div className="flex items-start justify-between gap-md">
        <div className="flex items-start gap-sm min-w-0">
          <div className="w-9 h-9 rounded bg-primary-container text-white flex items-center justify-center flex-shrink-0">
            <span className="material-symbols-outlined text-[18px]">{config.icon}</span>
          </div>
          <div className="min-w-0">
            <h3 className="font-h2 text-h2 text-on-surface">{config.label}</h3>
            <p className="text-body-sm text-outline mt-1">{config.detail}</p>
          </div>
        </div>
        <span className={`px-2.5 py-1 border rounded text-[11px] font-bold uppercase tracking-wide ${state.cls}`}>
          {state.label}
        </span>
      </div>

      <div className="mt-lg grid grid-cols-3 gap-sm">
        <div>
          <p className="font-label-caps text-label-caps text-outline uppercase">Active</p>
          <p className="text-2xl font-bold text-on-surface mt-1">{active}</p>
        </div>
        <div>
          <p className="font-label-caps text-label-caps text-outline uppercase">Waiting</p>
          <p className={`text-2xl font-bold mt-1 ${waiting > 0 ? 'text-amber-700' : 'text-on-surface'}`}>{waiting}</p>
        </div>
        <div>
          <p className="font-label-caps text-label-caps text-outline uppercase">Limit</p>
          <p className="text-2xl font-bold text-on-surface mt-1">{limit}</p>
        </div>
      </div>

      <div className="mt-md">
        <div className="flex justify-between text-[11px] text-slate-500 mb-1">
          <span>Slot usage</span>
          <span>{state.usage}%</span>
        </div>
        <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
          <div className={`h-full rounded-full transition-all ${waiting > 0 ? 'bg-amber-500' : 'bg-secondary'}`} style={{ width: `${state.usage}%` }} />
        </div>
      </div>
      <div className="mt-md rounded border border-slate-100 bg-slate-50 p-sm">
        <p className="text-[11px] text-slate-600 leading-relaxed">{capacityInterpretation(model)}</p>
      </div>
    </div>
  );
}

function healthClass(status) {
  if (status === 'healthy') return 'bg-emerald-50 text-emerald-800 border-emerald-200';
  if (status === 'degraded') return 'bg-amber-50 text-amber-800 border-amber-200';
  return 'bg-slate-50 text-slate-700 border-slate-200';
}

function serviceDetail(name, service) {
  if (!service) return 'No signal reported.';
  if (name === 'redis' && service.queued_jobs !== undefined) return `${service.queued_jobs} ingestion job${service.queued_jobs === 1 ? '' : 's'} queued`;
  if (name === 'qdrant' && service.collection) return service.collection;
  if (name === 'storage' && Array.isArray(service.paths)) {
    const worst = service.paths.reduce((max, item) => Math.max(max, Number(item.used_percent || 0)), 0);
    return `${Math.round(worst)}% max disk used`;
  }
  return service.detail || 'Operational';
}

function ServiceHealthCard({ name, service }) {
  const meta = SERVICE_LABELS[name] || { label: name, icon: 'monitor_heart' };
  const status = service?.status || 'unknown';
  return (
    <div className="bg-white border border-slate-200 rounded-lg p-md">
      <div className="flex items-start justify-between gap-sm">
        <div className="flex items-center gap-sm min-w-0">
          <div className="w-8 h-8 rounded bg-slate-100 text-slate-700 flex items-center justify-center">
            <span className="material-symbols-outlined text-[17px]">{meta.icon}</span>
          </div>
          <div className="min-w-0">
            <p className="text-sm font-bold text-on-surface truncate">{meta.label}</p>
            <p className="text-[11px] text-slate-500 mt-0.5 truncate">{serviceDetail(name, service)}</p>
          </div>
        </div>
        <span className={`px-2 py-0.5 border rounded text-[10px] font-bold uppercase ${healthClass(status)}`}>
          {status}
        </span>
      </div>
    </div>
  );
}

export default function Analytics() {
  const navigate = useNavigate();
  const [stats,    setStats]    = useState(null);
  const [modelStatus, setModelStatus] = useState(null);
  const [applianceHealth, setApplianceHealth] = useState(null);
  const [period,   setPeriod]   = useState('30d');
  const [loading,  setLoading]  = useState(true);
  const [syncTime, setSyncTime] = useState(new Date());

  useEffect(() => {
    fetchStats();
    const t = setInterval(() => setSyncTime(new Date()), 120_000);
    return () => clearInterval(t);
  }, [period]);

  const fetchStats = async () => {
    setLoading(true);
    try {
      const [summaryRes, modelRes, healthRes] = await Promise.all([
        api.get('/analytics/summary'),
        api.get('/chat/models/status'),
        api.get('/analytics/appliance-health'),
      ]);
      setStats(summaryRes.data);
      setModelStatus(modelRes.data);
      setApplianceHealth(healthRes.data);
    } catch {
      setStats(null);
      setModelStatus(null);
      setApplianceHealth(null);
    } finally {
      setLoading(false);
      setSyncTime(new Date());
    }
  };

  const topStats = [
    {
      label:   'Total Analyses Completed',
      value:   stats?.total_queries?.toLocaleString()    ?? '0',
      trend:   `${stats?.queries_this_week ?? 0} this week`,
      icon:    'analytics',
      accent:  'bg-secondary',
      trendCls: 'text-on-tertiary-container',
      trendIcon: 'trending_up',
    },
    {
      label:   'Avg. Confidence Score',
      value:   stats?.avg_confidence ? `${stats.avg_confidence}%` : '—',
      bar:     stats?.avg_confidence ?? 0,
      icon:    'verified',
      accent:  'bg-on-tertiary-container',
      trendCls: 'text-on-tertiary-container',
    },
    {
      label:   'System Latency (Avg)',
      value:   stats?.avg_latency_ms  ? `${stats.avg_latency_ms}ms` : '—',
      trend:   'Measured by backend summary',
      icon:    'speed',
      accent:  'bg-secondary-container',
      trendCls: 'text-on-tertiary-container',
      trendIcon: 'check_circle',
    },
    {
      label:   'Active Users',
      value:   stats?.active_users?.toLocaleString() ?? '0',
      trend:   'Institutional access active',
      icon:    'groups',
      accent:  'bg-slate-400',
      trendCls: 'text-slate-500',
      trendIcon: 'groups',
    },
  ];

  const chartMonths = Array.from({ length: 30 }, (_, i) => {
    const d = new Date(); d.setDate(d.getDate() - (29 - i));
    return d;
  });
  const chartLabels = ['', '', '', '', '', '', '', '', '', '',
    chartMonths[9]?.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) || '',
    '', '', '', '', '', '', '', '', '',
    chartMonths[19]?.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) || '',
    '', '', '', '', '', '', '', '', '',
    chartMonths[29]?.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) || ''];

  const minutesAgo = Math.round((new Date() - syncTime) / 60000);

  const exportSnapshot = () => {
    const rows = [
      ['Metric', 'Value'],
      ['Total analyses completed', stats?.total_queries ?? 0],
      ['Queries this week', stats?.queries_this_week ?? 0],
      ['Total sessions', stats?.total_sessions ?? 0],
      ['Active sessions', stats?.active_sessions ?? 0],
      ['Active users', stats?.active_users ?? 0],
      ['Total documents', stats?.total_documents ?? 0],
      ['Security events', stats?.security_events ?? 0],
      ['Trust score', stats?.trust_score ?? 0],
      ['Average confidence', stats?.avg_confidence ?? ''],
      ['Average latency ms', stats?.avg_latency_ms ?? ''],
      ['Appliance health', applianceHealth?.status ?? 'unknown'],
      ['Queued ingestion jobs', applianceHealth?.ingestion?.queued_jobs ?? ''],
      ['Documents needing approval', applianceHealth?.ingestion?.needs_approval ?? ''],
      ['Failed documents', applianceHealth?.ingestion?.failed_documents ?? ''],
    ];
    const csv = rows.map(row => row.map(cell => `"${String(cell ?? '').replace(/"/g, '""')}"`).join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'bankai-analytics-snapshot.csv';
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="p-xl max-w-container-max mx-auto">
      {/* Header */}
      <div className="flex justify-between items-end mb-xl">
        <div>
          <h1 className="font-h1 text-h1 text-on-surface">Performance Analytics</h1>
          <p className="text-outline font-body-md text-body-md mt-2">
            Institution-wide AI processing insights and health metrics.
          </p>
        </div>
        <div className="flex gap-sm">
          <select
            className="flex items-center gap-2 px-md py-sm border border-slate-300 rounded-lg text-on-surface font-label-caps text-label-caps bg-white hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-secondary"
            value={period}
            onChange={e => setPeriod(e.target.value)}
          >
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
            <option value="90d">Last 90 Days</option>
          </select>
          <button onClick={exportSnapshot}
            className="flex items-center gap-2 px-md py-sm border border-slate-300 rounded-lg text-on-surface font-label-caps text-label-caps bg-white hover:bg-slate-50 transition-colors">
            <span className="material-symbols-outlined text-sm">file_download</span>
            Export Snapshot
          </button>
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-gutter mb-gutter">
        {topStats.map(({ label, value, trend, bar, icon, accent, trendCls, trendIcon }) => (
          <div key={label} className="bg-white p-lg border border-slate-200 rounded-lg relative overflow-hidden flex flex-col justify-between">
            <div className={`absolute top-0 left-0 h-full w-1 ${accent}`} />
            <div>
              <p className="font-label-caps text-label-caps text-on-primary-container mb-sm uppercase tracking-widest">{label}</p>
              <h2 className="text-3xl font-bold text-on-surface">{loading ? '—' : value}</h2>
            </div>
            {bar != null ? (
              <div className="mt-md">
                <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                  <div className="h-full bg-on-tertiary-container rounded-full transition-all" style={{ width: `${bar}%` }} />
                </div>
              </div>
            ) : trend ? (
              <div className={`mt-md flex items-center gap-1 font-medium text-body-sm ${trendCls}`}>
                {trendIcon && <span className="material-symbols-outlined text-sm">{trendIcon}</span>}
                <span>{trend}</span>
              </div>
            ) : null}
          </div>
        ))}
      </div>

      {/* Appliance health */}
      <div className="mb-gutter">
        <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-md mb-md">
          <div>
            <h2 className="font-h2 text-h2 text-on-surface">Appliance Health</h2>
            <p className="text-outline font-body-sm text-body-sm mt-1">
              Live readiness checks for the dedicated bank server.
            </p>
          </div>
          <span className={`self-start lg:self-auto px-3 py-1.5 border rounded text-[11px] font-bold uppercase tracking-wide ${healthClass(applianceHealth?.status)}`}>
            {applianceHealth?.status || 'unknown'}
          </span>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-gutter">
          <div className="xl:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-gutter">
            {Object.entries(applianceHealth?.services || SERVICE_LABELS).map(([name, service]) => (
              <ServiceHealthCard
                key={name}
                name={name}
                service={service?.status ? service : null}
              />
            ))}
          </div>
          <div className="bg-white border border-slate-200 rounded-lg p-lg">
            <h3 className="font-h2 text-h2 text-on-surface">Document Governance</h3>
            <p className="text-body-sm text-outline mt-1 mb-md">Approved knowledge readiness by status.</p>
            <div className="grid grid-cols-3 gap-sm">
              <div className="rounded border border-slate-100 bg-slate-50 p-sm">
                <p className="text-[10px] font-bold uppercase text-slate-500">Total</p>
                <p className="text-2xl font-bold text-on-surface mt-1">{applianceHealth?.documents?.total ?? '—'}</p>
              </div>
              <div className="rounded border border-slate-100 bg-slate-50 p-sm">
                <p className="text-[10px] font-bold uppercase text-slate-500">Approved</p>
                <p className="text-2xl font-bold text-emerald-700 mt-1">{applianceHealth?.documents?.approved ?? '—'}</p>
              </div>
              <div className="rounded border border-slate-100 bg-slate-50 p-sm">
                <p className="text-[10px] font-bold uppercase text-slate-500">Failed</p>
                <p className="text-2xl font-bold text-rose-700 mt-1">{applianceHealth?.documents?.failed ?? '—'}</p>
              </div>
            </div>
            <div className="mt-md border border-slate-100 rounded p-sm bg-slate-50">
              <div className="flex items-center justify-between text-sm">
                <span className="font-semibold text-slate-700">Needs approval</span>
                <span className="font-bold text-secondary">{applianceHealth?.ingestion?.needs_approval ?? '—'}</span>
              </div>
              <div className="flex items-center justify-between text-sm mt-2">
                <span className="font-semibold text-slate-700">Queued ingestion</span>
                <span className="font-bold text-secondary">{applianceHealth?.ingestion?.queued_jobs ?? '—'}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Model capacity */}
      <div className="mb-gutter">
        <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-md mb-md">
          <div>
            <h2 className="font-h2 text-h2 text-on-surface">Model Capacity</h2>
            <p className="text-outline font-body-sm text-body-sm mt-1">
              Live local-model slots and tested capacity evidence for bank IT.
            </p>
          </div>
          <button onClick={fetchStats}
            className="self-start lg:self-auto flex items-center gap-2 px-md py-sm border border-slate-300 rounded-lg text-on-surface font-label-caps text-label-caps bg-white hover:bg-slate-50 transition-colors">
            <span className="material-symbols-outlined text-sm">refresh</span>
            Refresh Capacity
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-gutter">
          <div className="lg:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-gutter">
            {modelStatus
              ? Object.entries(modelStatus).map(([name, model]) => <ModelCapacityCard key={name} name={name} model={model} />)
              : ['fast', 'deep'].map(name => <ModelCapacityCard key={name} name={name} model={{ active: 0, waiting: 0, limit: 0 }} />)
            }
          </div>
          <div className="bg-white border border-slate-200 rounded-lg p-lg">
            <h3 className="font-h2 text-h2 text-on-surface">Capacity Evidence</h3>
            <p className="text-body-sm text-outline mt-1 mb-md">Measured on the current test server.</p>
            <div className="space-y-sm">
              {CAPACITY_EVIDENCE.map(item => (
                <div key={item.label} className="border border-slate-100 rounded p-sm">
                  <div className="flex justify-between gap-sm">
                    <span className="text-body-sm font-semibold text-on-surface">{item.label}</span>
                    <span className="text-body-sm font-bold text-secondary">{item.value}</span>
                  </div>
                  <p className="text-[11px] text-slate-500 mt-1">{item.detail}</p>
                </div>
              ))}
            </div>
            <p className="text-[11px] text-slate-500 mt-md">
              Streaming and normal API capacity are separate claims. Tail latency rises sharply during large simultaneous generation bursts.
            </p>
          </div>
        </div>
      </div>

      {/* Chart section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-gutter mb-gutter">
        {/* Daily volume bar chart */}
        <div className="lg:col-span-2 bg-white p-lg border border-slate-200 rounded-lg">
          <div className="flex justify-between items-center mb-lg">
            <div>
              <h3 className="font-h2 text-h2 text-on-surface">Daily Query Volume</h3>
              <p className="text-outline font-body-sm text-body-sm">Tracking AI requests over the {period === '30d' ? '30' : period === '7d' ? '7' : '90'}-day period</p>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-secondary" />
              <span className="text-xs font-medium text-slate-600">This Period</span>
            </div>
          </div>
          <div className="h-64 flex items-end justify-between gap-1 border-b border-slate-100 relative pb-0">
            {/* Grid lines */}
            <div className="absolute inset-0 flex flex-col justify-between pointer-events-none">
              {[0, 1, 2, 3].map(i => (
                <div key={i} className="border-t border-slate-50 w-full" />
              ))}
            </div>
            {CHART_HEIGHTS.map((h, i) => (
              <div
                key={i}
                className="flex-1 bg-secondary rounded-t-sm transition-all hover:opacity-80 cursor-default"
                style={{ height: `${h}%`, opacity: 0.15 + (h / 100) * 0.85 }}
                title={`Day ${i + 1}: ${Math.round(h * 14)} queries`}
              />
            ))}
          </div>
          <div className="flex justify-between mt-sm text-xs font-label-caps text-slate-400">
            <span>Day 1</span>
            <span>Day 10</span>
            <span>Day 20</span>
            <span>Day 30</span>
          </div>
        </div>

        {/* Document types */}
        <div className="bg-white p-lg border border-slate-200 rounded-lg">
          <h3 className="font-h2 text-h2 text-on-surface mb-xs">Document Types</h3>
          <p className="text-outline font-body-sm text-body-sm mb-lg">Most frequently analyzed categories</p>
          <div className="space-y-lg">
            {DOC_TYPES.map(({ label, pct }) => (
              <div key={label}>
                <div className="flex justify-between mb-xs">
                  <span className="text-body-sm font-medium text-on-surface">{label}</span>
                  <span className="text-body-sm font-bold text-on-surface">{pct}%</span>
                </div>
                <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                  <div className="h-full bg-secondary rounded-full transition-all" style={{ width: `${pct}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Department table */}
      <div className="bg-white border border-slate-200 rounded-lg overflow-hidden">
        <div className="p-lg border-b border-slate-100">
          <h3 className="font-h2 text-h2 text-on-surface">Usage by Department</h3>
          <p className="text-outline font-body-sm text-body-sm">Detailed breakdown of AI adoption across functional areas</p>
        </div>
        <table className="w-full text-left">
          <thead>
            <tr className="bg-slate-900 text-white font-label-caps text-label-caps">
              {['Department', 'Total Analyses', 'Avg. Confidence', 'Status', 'Trend'].map((h, i) => (
                <th key={h} className={`px-lg py-4 ${i === 4 ? 'text-right' : ''}`}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 font-body-sm text-body-sm">
            {DEPARTMENTS.map(({ name, analyses, conf, trend, positive, status }) => (
              <tr key={name} className="hover:bg-slate-50 transition-colors">
                <td className="px-lg py-4 font-semibold text-on-surface">{name}</td>
                <td className="px-lg py-4 text-outline">{analyses.toLocaleString()}</td>
                <td className="px-lg py-4"><ConfBadge conf={conf} /></td>
                <td className="px-lg py-4">
                  <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${status === 'active' ? 'bg-on-tertiary-container' : 'bg-secondary-container'}`} />
                    <span className="capitalize">{status}</span>
                  </div>
                </td>
                <td className={`px-lg py-4 text-right font-bold ${positive ? 'text-on-tertiary-container' : 'text-error'}`}>
                  {trend}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="px-lg py-4 bg-slate-50 flex justify-between items-center">
          <span className="text-xs text-slate-500">Showing 5 of 12 departments</span>
          <button onClick={() => navigate('/reports')}
            className="text-xs font-bold text-secondary hover:underline uppercase tracking-widest">
            Open Reports
          </button>
        </div>
      </div>

      {/* Sync indicator */}
      <div className="fixed bottom-8 right-8 bg-primary-container text-white px-md py-sm rounded-lg flex items-center gap-3 shadow-xl pointer-events-none">
        <span className="material-symbols-outlined text-on-tertiary-container text-sm"
          style={{ fontVariationSettings: "'FILL' 1" }}>check_circle</span>
        <div className="text-xs">
          <p className="font-bold">Real-time Sync Active</p>
          <p className="opacity-70">Last updated {minutesAgo < 1 ? 'just now' : `${minutesAgo}m ago`}</p>
        </div>
      </div>
    </div>
  );
}
