import { useEffect, useMemo, useState } from 'react';
import api from '../api/axios';

function parseMeta(log) {
  try { return JSON.parse(log.metadata_json || '{}'); } catch { return {}; }
}

function pct(part, total) {
  if (!total) return 0;
  return Math.round((part / total) * 100);
}

function riskBadge(level) {
  const normalized = String(level || 'low').toLowerCase();
  if (normalized === 'critical' || normalized === 'high') return 'bg-red-50 text-error border-red-100';
  if (normalized === 'medium') return 'bg-yellow-50 text-yellow-700 border-yellow-100';
  return 'bg-green-50 text-on-tertiary-container border-green-100';
}

function statusTone(status) {
  if (['failed', 'disabled'].includes(status)) return 'bg-red-50 text-error border-red-100';
  if (['uploaded', 'processing', 'extracting_text', 'chunking', 'embedding', 'indexing'].includes(status)) {
    return 'bg-blue-50 text-secondary border-blue-100';
  }
  return 'bg-green-50 text-on-tertiary-container border-green-100';
}

export default function ComplianceRisk() {
  const [stats, setStats] = useState({});
  const [documents, setDocuments] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
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
          setError('Some compliance data could not be loaded. Showing available signals only.');
        }
      } finally {
        if (active) setLoading(false);
      }
    };
    load();
    return () => { active = false; };
  }, []);

  const derived = useMemo(() => {
    const totalDocs = documents.length;
    const approvedDocs = documents.filter(doc => ['approved', 'ready', 'indexed'].includes(doc.status)).length;
    const failedDocs = documents.filter(doc => doc.status === 'failed').length;
    const inProgressDocs = documents.filter(doc => ['uploaded', 'processing', 'extracting_text', 'chunking', 'embedding', 'indexing'].includes(doc.status)).length;
    const activeUsers = users.filter(user => user.is_active !== false).length;
    const inactiveUsers = users.length - activeUsers;
    const highRiskLogs = auditLogs.filter(log => {
      const meta = parseMeta(log);
      const severity = String(meta.severity || meta.risk_level || '').toLowerCase();
      return ['critical', 'high'].includes(severity) || String(log.action || '').includes('failed');
    });
    const reviewQueue = [
      ...documents
        .filter(doc => ['failed', 'disabled'].includes(doc.status))
        .map(doc => ({
          type: 'Document',
          title: doc.title || doc.file_name,
          detail: `Status: ${doc.status}. ${doc.processing_message || 'Operator review required.'}`,
          severity: doc.status === 'failed' ? 'high' : 'medium',
          created_at: doc.created_at,
        })),
      ...highRiskLogs.map(log => {
        const meta = parseMeta(log);
        return {
          type: 'Audit',
          title: log.action,
          detail: `${log.resource_type || 'resource'} ${log.resource_id || ''}`.trim() || 'Audit event requires review.',
          severity: meta.severity || meta.risk_level || 'high',
          created_at: log.created_at,
        };
      }),
    ].sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0));

    const governanceScore = Math.max(0, Math.min(100,
      Math.round(
        (stats.trust_score ?? pct(approvedDocs, totalDocs) ?? 0)
        - (failedDocs * 8)
        - (highRiskLogs.length * 3)
        - (inactiveUsers > 0 ? 2 : 0)
      )
    ));

    return {
      totalDocs,
      approvedDocs,
      failedDocs,
      inProgressDocs,
      activeUsers,
      inactiveUsers,
      highRiskLogs,
      reviewQueue,
      governanceScore,
      approvalRate: pct(approvedDocs, totalDocs),
      auditEvents: auditLogs.length,
    };
  }, [auditLogs, documents, stats.trust_score, users]);

  const exportCsv = () => {
    const rows = [
      ['Metric', 'Value'],
      ['Governance score', derived.governanceScore],
      ['Document approval rate', `${derived.approvalRate}%`],
      ['Approved documents', derived.approvedDocs],
      ['Failed documents', derived.failedDocs],
      ['In-progress documents', derived.inProgressDocs],
      ['Audit events', derived.auditEvents],
      ['High-risk audit events', derived.highRiskLogs.length],
      ['Active users', derived.activeUsers],
      ['Inactive users', derived.inactiveUsers],
      [],
      ['Review Type', 'Title', 'Severity', 'Detail'],
      ...derived.reviewQueue.map(item => [item.type, item.title, item.severity, item.detail]),
    ];
    const csv = rows.map(row => row.map(cell => `"${String(cell ?? '').replace(/"/g, '""')}"`).join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'compliance-monitor-snapshot.csv';
    link.click();
    URL.revokeObjectURL(url);
  };

  const cards = [
    {
      title: 'Knowledge Approval',
      subtitle: 'Documents ready for staff answers',
      value: `${derived.approvalRate}%`,
      detail: `${derived.approvedDocs} of ${derived.totalDocs} documents approved/ready/indexed`,
      icon: 'folder_managed',
    },
    {
      title: 'Processing Exceptions',
      subtitle: 'Failed or blocked document ingestion',
      value: derived.failedDocs,
      detail: `${derived.inProgressDocs} documents still processing`,
      icon: 'report',
    },
    {
      title: 'Audit Review Load',
      subtitle: 'Events requiring compliance review',
      value: derived.highRiskLogs.length,
      detail: `${derived.auditEvents} audit events inspected`,
      icon: 'policy',
    },
    {
      title: 'Access Posture',
      subtitle: 'Visible active users',
      value: derived.activeUsers,
      detail: `${derived.inactiveUsers} inactive users`,
      icon: 'manage_accounts',
    },
  ];

  return (
    <div className="p-xl max-w-container-max mx-auto">
      <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-md mb-xl">
        <div>
          <span className="font-label-caps text-label-caps text-secondary uppercase tracking-widest mb-sm block">
            Compliance Monitor
          </span>
          <h1 className="font-h1 text-h1 text-on-surface">Governance & Risk Review</h1>
          <p className="text-outline font-body-md text-body-md mt-2 max-w-3xl">
            Data-backed compliance snapshot derived from document governance, audit activity, and user access signals.
          </p>
        </div>
        <button onClick={exportCsv} disabled={loading}
          className="bg-primary text-white px-lg py-sm rounded-lg text-sm font-bold flex items-center gap-2 hover:opacity-90 disabled:opacity-50">
          <span className="material-symbols-outlined text-sm">download</span>
          Export Snapshot
        </button>
      </div>

      {error && (
        <div className="mb-md p-md bg-amber-50 border border-amber-200 text-amber-800 rounded-lg text-body-sm">
          {error}
        </div>
      )}

      <div className="grid grid-cols-12 gap-gutter">
        <section className="col-span-12 lg:col-span-4 bg-white border border-outline-variant p-lg rounded-lg flex flex-col items-center justify-center relative overflow-hidden">
          <div className="absolute top-0 left-0 w-1 h-full bg-secondary" />
          <h2 className="font-h2 text-h2 mb-lg text-center">Governance Score</h2>
          <div className="relative w-48 h-48 flex items-center justify-center">
            <svg className="w-full h-full -rotate-90">
              <circle className="text-slate-100" cx="96" cy="96" fill="transparent" r="88" stroke="currentColor" strokeWidth="12" />
              <circle className="text-secondary" cx="96" cy="96" fill="transparent" r="88" stroke="currentColor"
                strokeDasharray="552.92" strokeDashoffset={552.92 - (552.92 * derived.governanceScore / 100)} strokeWidth="12" />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-5xl font-black text-on-surface">{loading ? '—' : derived.governanceScore}</span>
              <span className="font-label-caps text-label-caps text-outline uppercase">
                {derived.governanceScore >= 85 ? 'Strong' : derived.governanceScore >= 65 ? 'Needs Review' : 'At Risk'}
              </span>
            </div>
          </div>
          <div className="mt-lg grid grid-cols-2 gap-lg w-full text-center">
            <div><p className="text-sm text-outline mb-1">Trust Score</p><p className="font-bold text-lg">{stats.trust_score ?? '—'}%</p></div>
            <div><p className="text-sm text-outline mb-1">Target</p><p className="font-bold text-lg text-on-tertiary-container">90+</p></div>
          </div>
        </section>

        <section className="col-span-12 lg:col-span-8 grid grid-cols-1 md:grid-cols-2 gap-gutter">
          {cards.map(card => (
            <article key={card.title} className="bg-white border border-outline-variant p-md rounded-lg relative">
              <div className="absolute top-0 left-0 w-1 h-full bg-secondary" />
              <div className="flex justify-between items-start mb-md">
                <div>
                  <h3 className="font-bold text-lg">{card.title}</h3>
                  <p className="text-xs text-outline">{card.subtitle}</p>
                </div>
                <span className="material-symbols-outlined text-secondary">{card.icon}</span>
              </div>
              <p className="text-2xl font-bold text-on-surface">{loading ? '—' : card.value}</p>
              <p className="text-body-sm text-outline mt-sm">{card.detail}</p>
            </article>
          ))}
        </section>

        <section className="col-span-12 lg:col-span-7 bg-white border border-outline-variant p-lg rounded-lg">
          <div className="flex justify-between items-center mb-lg">
            <div>
              <h2 className="font-h2 text-h2">Document Governance</h2>
              <p className="text-body-sm text-outline">Knowledge readiness by document status</p>
            </div>
          </div>
          <div className="space-y-sm">
            {documents.length === 0 && !loading ? (
              <div className="py-12 text-center text-slate-400">
                <span className="material-symbols-outlined text-4xl mb-sm">folder_off</span>
                <p>No documents available for compliance review.</p>
              </div>
            ) : documents.slice(0, 8).map(doc => (
              <div key={doc.id} className="flex items-center justify-between p-sm border border-slate-100 rounded bg-slate-50">
                <div className="min-w-0">
                  <p className="font-bold text-body-sm text-on-surface truncate">{doc.title || doc.file_name}</p>
                  <p className="text-xs text-outline truncate">{doc.department || 'No department'} · {doc.document_type || doc.file_type}</p>
                </div>
                <span className={`text-[10px] font-bold uppercase border px-2 py-1 rounded ${statusTone(doc.status)}`}>{doc.status}</span>
              </div>
            ))}
          </div>
        </section>

        <section className="col-span-12 lg:col-span-5 bg-white border border-outline-variant rounded-lg flex flex-col overflow-hidden">
          <div className="p-md border-b border-outline-variant bg-primary-container text-white flex justify-between items-center">
            <h2 className="font-bold">Compliance Review Queue</h2>
            <span className="text-xs bg-white/10 px-2 py-1 rounded">{derived.reviewQueue.length} items</span>
          </div>
          <div className="divide-y divide-slate-100 max-h-[460px] overflow-y-auto">
            {derived.reviewQueue.length === 0 && !loading ? (
              <div className="p-xl text-center text-slate-400">
                <span className="material-symbols-outlined text-4xl mb-sm">verified</span>
                <p>No high-risk review items found in loaded data.</p>
              </div>
            ) : derived.reviewQueue.slice(0, 12).map((item, index) => (
              <article key={`${item.type}-${item.title}-${index}`} className="p-md hover:bg-slate-50 transition-colors">
                <div className="flex gap-md">
                  <div className="w-2 h-12 bg-secondary rounded-full mt-1 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="flex justify-between items-start mb-xs gap-sm">
                      <h3 className="font-bold text-sm truncate">{item.title}</h3>
                      <span className={`text-[10px] font-bold uppercase border px-2 py-0.5 rounded ${riskBadge(item.severity)}`}>{item.severity}</span>
                    </div>
                    <p className="text-xs text-outline">{item.detail}</p>
                    <div className="flex justify-between items-center mt-sm">
                      <span className="text-[10px] text-slate-400">{item.type}</span>
                      <span className="text-[10px] text-slate-400">{item.created_at ? new Date(item.created_at).toLocaleDateString() : 'No date'}</span>
                    </div>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
