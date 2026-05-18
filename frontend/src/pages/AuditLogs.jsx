import { useState, useEffect } from 'react';
import api from '../api/axios';

const RISK_COLORS = {
  critical: 'border-l-error',
  high:     'border-l-error',
  medium:   'border-l-tertiary-fixed-dim',
  low:      'border-l-transparent',
  verified: 'border-l-tertiary-fixed-dim',
};

const CONF_COLOR = (conf) => {
  if (conf >= 90) return { text: 'text-on-tertiary-container', bar: 'bg-tertiary-fixed-dim' };
  if (conf >= 75) return { text: 'text-secondary',            bar: 'bg-secondary' };
  return                { text: 'text-error',                 bar: 'bg-error' };
};

const STATUS_BADGE = {
  critical:   'bg-red-50 text-error border-red-100',
  high:       'bg-red-50 text-error border-red-100',
  medium:     'bg-yellow-50 text-yellow-700 border-yellow-100',
  low:        'bg-slate-50 text-slate-600 border-slate-200',
  verified:   'bg-green-50 text-on-tertiary-container border-green-100',
  processing: 'bg-blue-50 text-secondary border-blue-100',
  approved:   'bg-green-50 text-on-tertiary-container border-green-100',
};

function parseSeverity(log) {
  try {
    const m = JSON.parse(log.metadata_json || '{}');
    return (m.severity || m.risk_level || 'low').toLowerCase();
  } catch { return 'low'; }
}

function parseConf(log) {
  try {
    const m = JSON.parse(log.metadata_json || '{}');
    return m.confidence ?? m.confidence_score ?? null;
  } catch { return null; }
}

function ActionDetail({ log, onClose }) {
  if (!log) {
    return (
      <div className="flex-1 bg-white border border-slate-200 rounded-lg flex flex-col items-center justify-center text-slate-400 p-8">
        <span className="material-symbols-outlined text-5xl mb-3">manage_search</span>
        <p className="text-body-sm font-medium">Select a log entry to inspect</p>
      </div>
    );
  }

  let meta = {};
  try { meta = JSON.parse(log.metadata_json || '{}'); } catch {}

  const conf = meta.confidence ?? meta.confidence_score ?? null;
  const severity = parseSeverity(log);
  const confColors = conf != null ? CONF_COLOR(conf) : null;

  return (
    <div className="flex-1 bg-white border border-slate-200 rounded-lg flex flex-col overflow-hidden">
      <div className="p-md border-b border-slate-200 flex justify-between items-center flex-shrink-0">
        <h3 className="text-body-md font-bold text-on-surface">Action Details</h3>
        <button onClick={onClose}
          className="material-symbols-outlined text-slate-400 hover:text-slate-900 transition-colors cursor-pointer">
          close
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-md space-y-lg">
        <div className="flex flex-col gap-sm">
          <span className="font-label-caps text-label-caps text-slate-500 uppercase tracking-widest">Log Entry ID</span>
          <p className="text-body-sm font-bold font-mono">EVT-{String(log.id).padStart(5, '0')}-LLM</p>
        </div>

        <div className="flex flex-col gap-sm">
          <span className="font-label-caps text-label-caps text-slate-500 uppercase tracking-widest">AI Reasoning Trace</span>
          <div className="bg-slate-50 border border-slate-200 p-md rounded-lg">
            <p className="text-body-sm italic text-slate-700 leading-relaxed mb-md">
              "{meta.reasoning || meta.description || log.action} — Resource: {log.resource_type}
              {log.resource_id ? ` #${log.resource_id}` : ''}."
            </p>
            {(severity === 'critical' || severity === 'high') ? (
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-error text-sm">warning</span>
                <span className="text-body-sm font-bold text-error">High sensitivity flag raised</span>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-on-tertiary-container text-sm"
                  style={{ fontVariationSettings: "'FILL' 1" }}>check_circle</span>
                <span className="text-body-sm font-bold text-on-tertiary-container">Within normal parameters</span>
              </div>
            )}
          </div>
        </div>

        <div className="space-y-md">
          <span className="font-label-caps text-label-caps text-slate-500 uppercase tracking-widest">Metadata</span>
          <div className="grid grid-cols-2 gap-md">
            {[
              { label: 'Model Version', value: meta.model_version || 'Local vLLM' },
              { label: 'Tokens Used',  value: meta.tokens_used   ? String(meta.tokens_used) : '—' },
              { label: 'Latency',      value: meta.latency_ms    ? `${meta.latency_ms}ms`   : '—' },
              { label: 'Source Hash',  value: meta.source_hash   || (log.resource_id ? `0x${log.resource_id.slice(0, 6)}` : '—') },
            ].map(({ label, value }) => (
              <div key={label} className="p-sm bg-slate-50 border border-slate-200 rounded">
                <p className="text-[10px] text-slate-500 uppercase font-bold tracking-wide">{label}</p>
                <p className="text-body-sm font-medium mt-0.5 font-mono truncate">{value}</p>
              </div>
            ))}
          </div>
        </div>

        {log.ip_address && (
          <div className="flex flex-col gap-sm">
            <span className="font-label-caps text-label-caps text-slate-500 uppercase tracking-widest">IP Address</span>
            <p className="text-body-sm font-mono font-medium">{log.ip_address}</p>
          </div>
        )}

        {conf != null && (
          <div className="flex flex-col gap-sm">
            <span className="font-label-caps text-label-caps text-slate-500 uppercase tracking-widest">Confidence Score</span>
            <div className="flex items-center gap-3">
              <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
                <div className={`h-full ${confColors.bar} rounded-full transition-all`} style={{ width: `${conf}%` }} />
              </div>
              <span className={`text-body-sm font-bold ${confColors.text}`}>{conf}%</span>
            </div>
          </div>
        )}

        <div className="flex flex-col gap-sm">
          <span className="font-label-caps text-label-caps text-slate-500 uppercase tracking-widest">Timestamp</span>
          <p className="text-body-sm font-medium">{new Date(log.created_at).toLocaleString()}</p>
        </div>
      </div>

      <div className="p-md border-t border-slate-200 bg-slate-50 flex flex-col gap-sm flex-shrink-0">
        <button className="w-full bg-secondary text-white py-2 font-bold text-body-sm rounded-lg hover:bg-secondary/90 transition-colors">
          Approve Action
        </button>
        <button className="w-full border border-slate-300 bg-white text-on-surface py-2 font-bold text-body-sm rounded-lg hover:bg-slate-50 transition-colors">
          Manual Override
        </button>
      </div>
    </div>
  );
}

const PAGE_SIZE = 15;

export default function AuditLogs() {
  const [logs,       setLogs]       = useState([]);
  const [total,      setTotal]      = useState(0);
  const [page,       setPage]       = useState(0);
  const [search,     setSearch]     = useState('');
  const [riskFilter, setRiskFilter] = useState('all');
  const [dateFilter, setDateFilter] = useState('24h');
  const [selected,   setSelected]   = useState(null);
  const [loading,    setLoading]    = useState(true);
  const [alerts,     setAlerts]     = useState(0);

  useEffect(() => { fetchLogs(); }, [page]);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const res  = await api.get(`/audit?skip=${page * PAGE_SIZE}&limit=${PAGE_SIZE}`);
      const data = Array.isArray(res.data) ? res.data : [];
      setLogs(data);
      if (page === 0) {
        setTotal(data.length >= PAGE_SIZE ? data.length * 3 : data.length);
        const highRisk = data.filter(l => {
          const s = parseSeverity(l);
          return s === 'critical' || s === 'high';
        }).length;
        setAlerts(highRisk);
      }
    } catch {
      setLogs([]);
    } finally {
      setLoading(false);
    }
  };

  const filtered = logs.filter(log => {
    if (search) {
      const q = search.toLowerCase();
      const hit = [log.action, log.resource_type, String(log.resource_id || ''), String(log.user_id || '')]
        .some(f => f.toLowerCase().includes(q));
      if (!hit) return false;
    }
    if (riskFilter !== 'all') {
      const sev = parseSeverity(log);
      if (riskFilter === 'high'   && sev !== 'critical' && sev !== 'high')   return false;
      if (riskFilter === 'medium' && sev !== 'medium')                        return false;
      if (riskFilter === 'low'    && sev !== 'low' && sev !== 'verified')     return false;
    }
    return true;
  });

  const handleExport = () => {
    const rows = [
      ['ID', 'Action', 'Resource', 'Resource ID', 'IP', 'Created At'],
      ...logs.map(l => [l.id, l.action, l.resource_type, l.resource_id || '', l.ip_address || '', l.created_at]),
    ];
    const csv  = rows.map(r => r.map(v => `"${v}"`).join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href = url; a.download = 'audit_log.csv'; a.click();
    URL.revokeObjectURL(url);
  };

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div className="p-xl max-w-container-max mx-auto">
      {/* Header */}
      <div className="mb-lg flex justify-between items-end">
        <div>
          <h1 className="text-h1 font-h1 text-on-surface mb-xs">Audit Forensics</h1>
          <p className="text-on-surface-variant font-body-md">
            Real-time immutable log of AI decision paths and investigator interactions.
          </p>
        </div>
        <div className="flex gap-sm">
          <button onClick={handleExport}
            className="flex items-center gap-2 border border-slate-300 px-md py-sm bg-white hover:bg-slate-50 transition-colors font-label-caps text-label-caps text-on-surface rounded-lg">
            <span className="material-symbols-outlined text-sm">download</span> Export CSV
          </button>
          <button onClick={() => window.print()}
            className="flex items-center gap-2 border border-slate-300 px-md py-sm bg-white hover:bg-slate-50 transition-colors font-label-caps text-label-caps text-on-surface rounded-lg">
            <span className="material-symbols-outlined text-sm">print</span> Print Report
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white border border-slate-200 p-md mb-lg flex flex-wrap gap-md items-center rounded-lg">
        <div className="flex-1 relative min-w-[260px]">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 material-symbols-outlined text-slate-400 text-[18px]">
            search
          </span>
          <input
            className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 focus:outline-none focus:ring-2 focus:ring-secondary focus:bg-white transition-all text-body-sm rounded-lg"
            placeholder="Search logs by user, action, or document ID..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && fetchLogs()}
          />
        </div>
        <div className="flex gap-sm">
          <select
            className="border border-slate-200 bg-slate-50 px-3 py-2 text-body-sm rounded-lg focus:outline-none focus:ring-2 focus:ring-secondary"
            value={riskFilter}
            onChange={e => setRiskFilter(e.target.value)}
          >
            <option value="all">Risk Level: All</option>
            <option value="high">High Risk</option>
            <option value="medium">Medium Risk</option>
            <option value="low">Low Risk</option>
          </select>
          <select
            className="border border-slate-200 bg-slate-50 px-3 py-2 text-body-sm rounded-lg focus:outline-none focus:ring-2 focus:ring-secondary"
            value={dateFilter}
            onChange={e => setDateFilter(e.target.value)}
          >
            <option value="24h">Date: Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
            <option value="custom">Custom Range</option>
          </select>
          <button onClick={fetchLogs}
            className="bg-slate-900 text-white px-md py-2 text-body-sm font-bold flex items-center gap-2 rounded-lg hover:bg-slate-800 transition-colors">
            <span className="material-symbols-outlined text-sm">filter_alt</span> Apply Filters
          </button>
        </div>
      </div>

      {/* Table + Detail */}
      <div className="flex gap-lg" style={{ height: 'calc(100vh - 400px)', minHeight: '400px' }}>
        <div className="flex-[3] bg-white border border-slate-200 rounded-lg overflow-hidden flex flex-col">
          <div className="overflow-y-auto flex-1">
            <table className="w-full text-left border-collapse">
              <thead className="sticky top-0 bg-primary-container text-white z-10">
                <tr>
                  {['Timestamp', 'User Identity', 'AI Action', 'Confidence', 'Status', ''].map(h => (
                    <th key={h} className="px-md py-4 font-label-caps text-label-caps whitespace-nowrap">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {loading ? (
                  <tr>
                    <td colSpan={6} className="px-md py-12 text-center">
                      <span className="material-symbols-outlined text-slate-300 text-4xl">hourglass_empty</span>
                      <p className="text-body-sm text-slate-400 mt-2">Loading audit logs...</p>
                    </td>
                  </tr>
                ) : filtered.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-md py-12 text-center">
                      <span className="material-symbols-outlined text-slate-300 text-4xl">search_off</span>
                      <p className="text-body-sm text-slate-400 mt-2">No audit logs found.</p>
                    </td>
                  </tr>
                ) : filtered.map(log => {
                  const severity    = parseSeverity(log);
                  const conf        = parseConf(log);
                  const confColors  = conf != null ? CONF_COLOR(conf) : null;
                  const borderClass = RISK_COLORS[severity] || 'border-l-transparent';
                  const badgeClass  = STATUS_BADGE[severity]  || STATUS_BADGE.low;
                  const isSelected  = selected?.id === log.id;
                  let meta = {};
                  try { meta = JSON.parse(log.metadata_json || '{}'); } catch {}

                  return (
                    <tr key={log.id}
                      onClick={() => setSelected(isSelected ? null : log)}
                      className={`cursor-pointer border-l-4 ${borderClass} transition-colors ${isSelected ? 'bg-surface-container-low' : 'hover:bg-slate-50'}`}>
                      <td className="px-md py-4 text-body-sm text-slate-500 whitespace-nowrap">
                        {new Date(log.created_at).toLocaleString()}
                      </td>
                      <td className="px-md py-4">
                        <div className="flex items-center gap-2">
                          <div className="w-6 h-6 rounded-full bg-slate-200 flex items-center justify-center text-[10px] font-bold flex-shrink-0">
                            {log.user_id ? `U${log.user_id}` : 'AI'}
                          </div>
                          <span className="text-body-sm font-medium whitespace-nowrap">
                            {meta.user_name || (log.user_id ? `User #${log.user_id}` : 'AI System')}
                          </span>
                        </div>
                      </td>
                      <td className="px-md py-4 text-body-sm text-slate-900 max-w-[200px] truncate" title={log.action}>
                        {log.action}
                        {log.resource_type && <span className="text-slate-400"> — {log.resource_type}</span>}
                      </td>
                      <td className="px-md py-4">
                        {conf != null ? (
                          <div className="flex items-center gap-2">
                            <span className={`text-body-sm font-semibold ${confColors.text}`}>{conf}%</span>
                            <div className="w-16 h-1 bg-slate-100 rounded-full overflow-hidden">
                              <div className={`${confColors.bar} h-full`} style={{ width: `${conf}%` }} />
                            </div>
                          </div>
                        ) : (
                          <span className="text-slate-300">—</span>
                        )}
                      </td>
                      <td className="px-md py-4">
                        <span className={`px-2 py-1 border rounded text-[10px] font-bold uppercase ${badgeClass}`}>
                          {severity}
                        </span>
                      </td>
                      <td className="px-md py-4 text-right">
                        <span className="material-symbols-outlined text-slate-400">chevron_right</span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination footer */}
          <div className="border-t border-slate-200 px-md py-4 flex justify-between items-center bg-slate-50 flex-shrink-0">
            <p className="text-body-sm text-slate-500">
              Showing {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, total || filtered.length)} of {total || filtered.length} entries
            </p>
            <div className="flex gap-2">
              <button onClick={() => setPage(p => Math.max(0, p - 1))} disabled={page === 0}
                className="px-3 py-1 border border-slate-300 rounded hover:bg-white disabled:opacity-40 text-body-sm">
                Previous
              </button>
              {[0, 1, 2].filter(p => p < totalPages).map(p => (
                <button key={p} onClick={() => setPage(p)}
                  className={`px-3 py-1 rounded text-body-sm border ${page === p ? 'border-slate-900 bg-slate-900 text-white' : 'border-slate-300 hover:bg-white'}`}>
                  {p + 1}
                </button>
              ))}
              <button onClick={() => setPage(p => Math.min(p + 1, totalPages - 1))} disabled={page >= totalPages - 1}
                className="px-3 py-1 border border-slate-300 rounded hover:bg-white disabled:opacity-40 text-body-sm">
                Next
              </button>
            </div>
          </div>
        </div>

        <ActionDetail log={selected} onClose={() => setSelected(null)} />
      </div>

      {/* Forensic Trends */}
      <div className="mt-lg grid grid-cols-1 md:grid-cols-3 gap-lg">
        <div className="bg-white border-l-4 border-secondary p-md border border-slate-200 flex items-center gap-md rounded-lg">
          <div className="w-12 h-12 bg-blue-50 rounded-full flex items-center justify-center text-secondary flex-shrink-0">
            <span className="material-symbols-outlined">security</span>
          </div>
          <div>
            <p className="font-label-caps text-label-caps text-slate-500 uppercase tracking-widest">Compliance Integrity</p>
            <p className="text-h2 font-h2 text-on-surface">99.8%</p>
          </div>
        </div>
        <div className="bg-white border-l-4 border-error p-md border border-slate-200 flex items-center gap-md rounded-lg">
          <div className="w-12 h-12 bg-red-50 rounded-full flex items-center justify-center text-error flex-shrink-0">
            <span className="material-symbols-outlined">gpp_maybe</span>
          </div>
          <div>
            <p className="font-label-caps text-label-caps text-slate-500 uppercase tracking-widest">Low Confidence Alerts</p>
            <p className="text-h2 font-h2 text-on-surface">
              {alerts} {alerts > 0 && <span className="text-body-sm font-medium text-error">↑ {alerts}</span>}
            </p>
          </div>
        </div>
        <div className="bg-white border-l-4 border-tertiary-fixed-dim p-md border border-slate-200 flex items-center gap-md rounded-lg">
          <div className="w-12 h-12 bg-green-50 rounded-full flex items-center justify-center text-on-tertiary-container flex-shrink-0">
            <span className="material-symbols-outlined">rule</span>
          </div>
          <div>
            <p className="font-label-caps text-label-caps text-slate-500 uppercase tracking-widest">Avg. Human Review Time</p>
            <p className="text-h2 font-h2 text-on-surface">4.2m</p>
          </div>
        </div>
      </div>
    </div>
  );
}
