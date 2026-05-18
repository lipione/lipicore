import { useEffect, useMemo, useState } from 'react';
import api from '../api/axios';

const REPORT_TYPES = [
  {
    id: 'usage',
    title: 'AI Usage Report',
    icon: 'query_stats',
    description: 'Adoption, session volume, users, and AI request counts for management review.',
  },
  {
    id: 'audit',
    title: 'Audit Activity Report',
    icon: 'policy',
    description: 'Recent governance events, failed actions, and security-relevant activity.',
  },
  {
    id: 'documents',
    title: 'Document Inventory Report',
    icon: 'folder_managed',
    description: 'Knowledge-base inventory by status, department, type, and approval readiness.',
  },
  {
    id: 'quality',
    title: 'AI Answer Quality Report',
    icon: 'verified',
    description: 'Source-backed answer posture, no-source risk, and evaluation readiness indicators.',
  },
];

const EXPORT_FORMATS = [
  { fmt: 'txt', label: 'TXT' },
  { fmt: 'pdf', label: 'PDF' },
  { fmt: 'docx', label: 'DOCX' },
];

function groupCount(items, keyFn) {
  return items.reduce((acc, item) => {
    const key = keyFn(item) || 'Unspecified';
    acc[key] = (acc[key] || 0) + 1;
    return acc;
  }, {});
}

function parseMeta(log) {
  try { return JSON.parse(log.metadata_json || '{}'); } catch { return {}; }
}

function section(title, rows) {
  return [`## ${title}`, ...rows.map(row => `- ${row}`), ''].join('\n');
}

function table(title, object) {
  const rows = Object.entries(object);
  if (rows.length === 0) return section(title, ['No records available.']);
  return [`## ${title}`, '| Item | Count |', '| --- | ---: |', ...rows.map(([key, value]) => `| ${key} | ${value} |`), ''].join('\n');
}

export default function Reports() {
  const [selectedType, setSelectedType] = useState('usage');
  const [stats, setStats] = useState({});
  const [documents, setDocuments] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    const load = async () => {
      setLoading(true);
      setError('');
      try {
        const [summaryRes, docsRes, auditRes, usersRes] = await Promise.allSettled([
          api.get('/analytics/summary'),
          api.get('/documents?limit=500'),
          api.get('/audit?limit=500'),
          api.get('/users?limit=500'),
        ]);
        if (!active) return;
        setStats(summaryRes.status === 'fulfilled' ? summaryRes.value.data || {} : {});
        setDocuments(docsRes.status === 'fulfilled' && Array.isArray(docsRes.value.data) ? docsRes.value.data : []);
        setAuditLogs(auditRes.status === 'fulfilled' && Array.isArray(auditRes.value.data) ? auditRes.value.data : []);
        setUsers(usersRes.status === 'fulfilled' && Array.isArray(usersRes.value.data) ? usersRes.value.data : []);
        if ([summaryRes, docsRes, auditRes, usersRes].some(result => result.status === 'rejected')) {
          setError('Some data sources are unavailable. Report uses the data that could be loaded.');
        }
      } finally {
        if (active) setLoading(false);
      }
    };
    load();
    return () => { active = false; };
  }, []);

  const report = useMemo(() => {
    const byStatus = groupCount(documents, doc => doc.status);
    const byDepartment = groupCount(documents, doc => doc.department);
    const byType = groupCount(documents, doc => doc.document_type || doc.file_type);
    const activeUsers = users.filter(user => user.is_active !== false).length;
    const failedDocs = documents.filter(doc => doc.status === 'failed').length;
    const approvedDocs = documents.filter(doc => ['approved', 'indexed', 'ready'].includes(doc.status)).length;
    const sourceBackedEvents = auditLogs.filter(log => {
      const meta = parseMeta(log);
      return Number(meta.source_count || 0) > 0 || meta.answer_type === 'official_source_backed';
    }).length;
    const riskyLogs = auditLogs.filter(log => {
      const meta = parseMeta(log);
      return ['high', 'critical'].includes(String(meta.severity || meta.risk_level || '').toLowerCase()) || String(log.action || '').includes('failed');
    });

    const generatedAt = new Date().toLocaleString();
    const selected = REPORT_TYPES.find(type => type.id === selectedType) || REPORT_TYPES[0];

    const commonHeader = [
      `# ${selected.title}`,
      `Generated: ${generatedAt}`,
      `Scope: Current bank workspace`,
      '',
    ].join('\n');

    if (selectedType === 'audit') {
      return {
        title: selected.title,
        content: commonHeader + [
          section('Executive Summary', [
            `${auditLogs.length} audit events loaded.`,
            `${riskyLogs.length} events need review based on severity/action metadata.`,
            `${activeUsers} active users are currently visible to this report.`,
          ]),
          section('Recent Events', auditLogs.slice(0, 12).map(log => `${new Date(log.created_at).toLocaleString()} - ${log.action} on ${log.resource_type || 'resource'} by user ${log.user_id || 'system'}`)),
          section('Review Queue', riskyLogs.slice(0, 12).map(log => `${log.action} - ${parseMeta(log).severity || parseMeta(log).risk_level || 'review'} - ${log.resource_type || 'resource'}`)),
        ].join('\n'),
      };
    }

    if (selectedType === 'documents') {
      return {
        title: selected.title,
        content: commonHeader + [
          section('Executive Summary', [
            `${documents.length} documents loaded.`,
            `${approvedDocs} documents are ready/approved/indexed for knowledge use.`,
            `${failedDocs} documents failed processing and require operator review.`,
          ]),
          table('Documents by Status', byStatus),
          table('Documents by Department', byDepartment),
          table('Documents by Type', byType),
        ].join('\n'),
      };
    }

    if (selectedType === 'quality') {
      const sourceBackedRatio = auditLogs.length ? Math.round((sourceBackedEvents / auditLogs.length) * 100) : 0;
      return {
        title: selected.title,
        content: commonHeader + [
          section('Executive Summary', [
            `${sourceBackedRatio}% of loaded audit events show source-backed answer metadata where available.`,
            `${approvedDocs} documents are usable as approved/indexed knowledge.`,
            `${failedDocs} failed documents reduce retrieval coverage and should be fixed before a pilot review.`,
          ]),
          section('Quality Signals', [
            `Trust score from analytics: ${stats.trust_score ?? 'not available'}%.`,
            `Average confidence from analytics: ${stats.avg_confidence ?? 'not available'}%.`,
            `Source-backed events detected: ${sourceBackedEvents}.`,
            `Total audit events inspected: ${auditLogs.length}.`,
          ]),
          section('Recommended Release Gate', [
            'Run a 50-question customer-care and policy evaluation set.',
            'Require exact citation title recall for source-backed answers.',
            'Review every answer marked as general knowledge before customer-facing use.',
          ]),
        ].join('\n'),
      };
    }

    return {
      title: selected.title,
      content: commonHeader + [
        section('Executive Summary', [
          `${stats.total_queries ?? 0} total staff questions recorded.`,
          `${stats.total_sessions ?? 0} total chat sessions recorded.`,
          `${activeUsers} active users loaded.`,
          `${documents.length} documents available in the workspace.`,
        ]),
        section('Usage Metrics', [
          `Queries this week: ${stats.queries_this_week ?? 0}.`,
          `Active sessions this week: ${stats.active_sessions ?? 0}.`,
          `Security/audit events: ${stats.security_events ?? auditLogs.length}.`,
          `Average latency: ${stats.avg_latency_ms ?? 'not available'} ms.`,
        ]),
        table('Users by Role', groupCount(users, user => user.role)),
      ].join('\n'),
    };
  }, [auditLogs, documents, selectedType, stats, users]);

  const exportReport = async (fmt) => {
    setExporting(fmt);
    try {
      const res = await api.post('/export', {
        title: report.title,
        content: report.content,
        fmt,
      }, { responseType: 'blob' });
      const url = URL.createObjectURL(res.data);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${report.title.toLowerCase().replace(/[^a-z0-9]+/g, '-')}.${fmt}`;
      link.click();
      URL.revokeObjectURL(url);
    } finally {
      setExporting(null);
    }
  };

  return (
    <div className="p-xl max-w-container-max mx-auto">
      <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-md mb-xl">
        <div>
          <span className="font-label-caps text-label-caps text-secondary uppercase tracking-widest mb-sm block">Reports</span>
          <h1 className="font-h1 text-h1 text-on-surface">Management Report Workspace</h1>
          <p className="text-outline font-body-md text-body-md mt-2 max-w-3xl">
            Generate practical reports from current workspace data for usage reviews, audits, document governance, and AI quality checks.
          </p>
        </div>
        <div className="flex flex-wrap gap-sm">
          {EXPORT_FORMATS.map(format => (
            <button key={format.fmt} onClick={() => exportReport(format.fmt)} disabled={loading || !!exporting}
              className="flex items-center gap-2 px-md py-sm border border-slate-300 rounded-lg bg-white text-sm font-bold hover:bg-slate-50 disabled:opacity-50">
              <span className="material-symbols-outlined text-[16px]">file_download</span>
              {exporting === format.fmt ? 'Exporting...' : format.label}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="mb-md p-md bg-amber-50 border border-amber-200 text-amber-800 rounded-lg text-body-sm">
          {error}
        </div>
      )}

      <div className="grid grid-cols-12 gap-gutter">
        <section className="col-span-12 lg:col-span-4 space-y-sm">
          {REPORT_TYPES.map(type => (
            <button key={type.id} onClick={() => setSelectedType(type.id)}
              className={`w-full p-md border rounded-lg text-left transition-all ${
                selectedType === type.id
                  ? 'bg-white border-secondary shadow-sm'
                  : 'bg-slate-50 border-slate-200 hover:bg-white'
              }`}>
              <div className="flex items-start gap-md">
                <span className="material-symbols-outlined text-secondary">{type.icon}</span>
                <div>
                  <h2 className="font-bold text-on-surface">{type.title}</h2>
                  <p className="text-body-sm text-on-surface-variant mt-xs">{type.description}</p>
                </div>
              </div>
            </button>
          ))}
        </section>

        <section className="col-span-12 lg:col-span-8 bg-white border border-slate-200 rounded-lg overflow-hidden">
          <div className="p-lg border-b border-slate-100 flex items-center justify-between">
            <div>
              <h2 className="font-h2 text-h2 text-on-surface">{report.title}</h2>
              <p className="text-body-sm text-on-surface-variant">Preview before export</p>
            </div>
            <span className="text-xs font-bold text-slate-500 bg-slate-100 px-2 py-1 rounded">
              {loading ? 'Loading' : 'Current Data'}
            </span>
          </div>
          <pre className="p-lg whitespace-pre-wrap text-body-sm leading-relaxed text-slate-700 font-sans max-h-[650px] overflow-y-auto">
            {loading ? 'Loading report data...' : report.content}
          </pre>
        </section>
      </div>
    </div>
  );
}
