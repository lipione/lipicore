import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/axios';

const QUICK_START = [
  {
    icon: 'chat',
    title: 'Ask BankAi',
    desc: 'General staff chat that uses approved knowledge when available and keeps staff responsible for the final answer.',
    prompt: 'Help me answer a bank staff question. Use approved bank knowledge when available, cite sources, and say when no approved source supports the answer.',
  },
  {
    icon: 'policy',
    title: 'Ask Approved Knowledge',
    desc: 'Strict source-backed policy, circular, SOP, and product-document answers for branch and operations teams.',
    prompt: 'Answer only from approved bank policies, circulars, SOPs, and product documents. If the answer is not supported by approved knowledge, say that clearly.',
  },
  {
    icon: 'inventory_2',
    title: 'Analyze Large File',
    desc: 'Queue long PDF, scanned document, and Excel analysis instead of blocking staff chat.',
    route: '/documents',
  },
  {
    icon: 'document_scanner',
    title: 'OCR Text Extraction',
    desc: 'Upload PDFs, Office files, spreadsheets, CSV/TXT, or images and extract text without indexing them.',
    route: '/ocr',
  },
];

const FINAL_JOB_STATES = new Set(['completed', 'failed']);

function parseJson(value, fallback) {
  try {
    return value ? JSON.parse(value) : fallback;
  } catch {
    return fallback;
  }
}

function docIcon(type) {
  const normalized = (type || '').toLowerCase();
  if (normalized === 'pdf') return 'description';
  if (normalized === 'xlsx' || normalized === 'xls') return 'table_chart';
  if (normalized === 'docx' || normalized === 'doc') return 'article';
  if (normalized === 'pptx' || normalized === 'ppt') return 'slideshow';
  return 'insert_drive_file';
}

function formatLabel(value) {
  return String(value || 'unknown').replaceAll('_', ' ');
}

function formatNumber(value) {
  if (value === null || value === undefined) return '-';
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric.toLocaleString() : value;
}

function statusTone(status) {
  const tones = {
    queued: 'bg-blue-50 text-blue-700 border-blue-200',
    processing: 'bg-blue-50 text-blue-700 border-blue-200',
    packing_context: 'bg-blue-50 text-blue-700 border-blue-200',
    generating: 'bg-amber-50 text-amber-700 border-amber-200',
    completed: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    failed: 'bg-rose-50 text-rose-700 border-rose-200',
  };
  return tones[status] || 'bg-slate-50 text-slate-600 border-slate-200';
}

function MetricCard({ label, value, icon, detail }) {
  return (
    <div className="bg-white border border-slate-200 rounded-lg p-md flex items-center gap-md min-w-0">
      <div className="w-10 h-10 bg-surface-container-low rounded flex items-center justify-center flex-shrink-0">
        <span className="material-symbols-outlined text-secondary text-[20px]">{icon}</span>
      </div>
      <div className="min-w-0">
        <p className="font-label-caps text-label-caps text-outline uppercase">{label}</p>
        <p className="text-2xl font-bold text-on-surface mt-0.5">{value}</p>
        {detail && <p className="text-xs text-slate-500 truncate">{detail}</p>}
      </div>
    </div>
  );
}

function CapacityStrip({ modelStatus }) {
  const rows = ['fast', 'deep', 'vision'].map((key) => ({ key, ...(modelStatus?.[key] || {}) }));
  if (!modelStatus) {
    return (
      <div className="rounded border border-dashed border-slate-200 p-4 text-sm text-slate-500">
        Model capacity is available to analytics users from Model Lab.
      </div>
    );
  }

  return (
    <div className="grid gap-3">
      {rows.map((row) => {
        const limit = Number(row.limit || 0);
        const active = Number(row.active || 0);
        const pct = limit > 0 ? Math.min(100, Math.round((active / limit) * 100)) : 0;
        return (
          <div key={row.key} className="rounded border border-slate-200 bg-white p-3">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-slate-900 capitalize">{row.key}</p>
                <p className="text-xs text-slate-500">{active}/{limit || '-'} active, {row.waiting || 0} waiting</p>
              </div>
              <span className="material-symbols-outlined text-[18px] text-slate-400">
                {row.key === 'vision' ? 'document_scanner' : row.key === 'deep' ? 'psychology' : 'bolt'}
              </span>
            </div>
            <div className="mt-3 h-1.5 rounded-full bg-slate-100 overflow-hidden">
              <div className="h-full rounded-full bg-secondary" style={{ width: `${pct}%` }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default function Dashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [pinnedDocs, setPinnedDocs] = useState([]);
  const [analysisJobs, setAnalysisJobs] = useState([]);
  const [modelStatus, setModelStatus] = useState(null);

  const user = JSON.parse(localStorage.getItem('user') || '{}');

  useEffect(() => {
    let mounted = true;
    Promise.allSettled([
      api.get('/analytics/summary'),
      api.get('/chat/sessions?limit=5'),
      api.get('/documents?limit=3'),
      api.get('/long-document-analysis?limit=100'),
      api.get('/model-lab/status'),
    ]).then(([statsRes, sessRes, docsRes, jobsRes, modelRes]) => {
      if (!mounted) return;
      if (statsRes.status === 'fulfilled') setStats(statsRes.value.data);
      if (sessRes.status === 'fulfilled') setSessions(sessRes.value.data || []);
      if (docsRes.status === 'fulfilled') setPinnedDocs((docsRes.value.data || []).slice(0, 3));
      if (jobsRes.status === 'fulfilled') setAnalysisJobs(jobsRes.value.data || []);
      if (modelRes.status === 'fulfilled') setModelStatus(modelRes.value.data?.models || null);
    });
    return () => {
      mounted = false;
    };
  }, []);

  const longDocSummary = useMemo(() => {
    const active = analysisJobs.filter((job) => !FINAL_JOB_STATES.has(job.status)).length;
    return {
      active,
      completed: analysisJobs.filter((job) => job.status === 'completed').length,
      failed: analysisJobs.filter((job) => job.status === 'failed').length,
      total: analysisJobs.length,
    };
  }, [analysisJobs]);

  const recentJobs = analysisJobs.slice(0, 4);

  const startChatWith = async (prompt) => {
    try {
      const res = await api.post('/chat/sessions', { title: prompt.slice(0, 60) });
      navigate(`/chat?session=${res.data.id}&prompt=${encodeURIComponent(prompt)}`);
    } catch (_) {
      navigate('/chat');
    }
  };

  const runQuickStart = (item) => {
    if (item.route) {
      navigate(item.route);
      return;
    }
    startChatWith(item.prompt);
  };

  return (
    <div className="p-xl max-w-container-max mx-auto">
      <section className="mb-xl">
        <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-4">
          <div>
            <p className="font-label-caps text-label-caps text-outline uppercase mb-sm">Bank Staff AI Appliance</p>
            <h1 className="text-h1 font-h1 text-on-background mb-sm">
              Welcome back, {user.name?.split(' ')[0] || 'Administrator'}
            </h1>
            <p className="text-body-lg text-outline max-w-3xl">
              Secure staff assistance, approved-knowledge answers, queued large-file analysis, and human-reviewed decision support.
            </p>
          </div>
          <button
            type="button"
            onClick={() => navigate('/documents')}
            className="btn-primary inline-flex items-center justify-center gap-2"
          >
            <span className="material-symbols-outlined text-[18px]">inventory_2</span>
            Queue Document Analysis
          </button>
        </div>
      </section>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-gutter mb-xl">
        <MetricCard label="Documents Indexed" value={formatNumber(stats?.total_documents)} icon="description" detail="Approved and searchable knowledge" />
        <MetricCard label="Active Sessions" value={formatNumber(stats?.active_sessions)} icon="chat_bubble" detail="Staff assistant sessions" />
        <MetricCard label="Long Jobs Active" value={longDocSummary.active} icon="pending_actions" detail={`${longDocSummary.completed} completed, ${longDocSummary.failed} failed`} />
        <MetricCard label="OCR Extraction" value="Ready" icon="document_scanner" detail="Transient text extraction" />
      </div>

      <div className="grid grid-cols-12 gap-gutter">
        <section className="col-span-12 xl:col-span-8">
          <div className="mb-md flex justify-between items-end">
            <div>
              <h2 className="text-h2 font-h2 text-on-background">Staff Work Modes</h2>
              <p className="text-sm text-slate-500 mt-1">The product stays inside the bank and keeps final decisions with staff.</p>
            </div>
            <button
              type="button"
              onClick={() => navigate('/chat')}
              className="font-label-caps text-label-caps text-secondary font-bold hover:underline uppercase"
            >
              Open Chat
            </button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-md">
            {QUICK_START.map((item) => (
              <button
                key={item.title}
                type="button"
                onClick={() => runQuickStart(item)}
                className="text-left p-lg bg-white border border-slate-200 rounded-lg hover:border-secondary transition-colors group min-h-40"
              >
                <div className="flex items-start justify-between mb-md">
                  <div className="p-sm bg-surface-container rounded">
                    <span className="material-symbols-outlined text-secondary">{item.icon}</span>
                  </div>
                  <span className="material-symbols-outlined text-outline group-hover:text-secondary transition-colors">
                    arrow_forward
                  </span>
                </div>
                <h3 className="font-bold text-body-md text-on-surface mb-xs">{item.title}</h3>
                <p className="text-body-sm text-outline leading-relaxed">{item.desc}</p>
              </button>
            ))}
          </div>
        </section>

        <aside className="col-span-12 xl:col-span-4 space-y-lg">
          <section>
            <div className="mb-md flex justify-between items-end">
              <h2 className="text-h2 font-h2 text-on-background">Operational Queues</h2>
              <button
                type="button"
                onClick={() => navigate('/ocr')}
                className="text-sm text-outline hover:text-secondary"
              >
                Open OCR
              </button>
            </div>
            <div className="grid gap-sm">
              <button
                type="button"
                onClick={() => navigate('/documents')}
                className="text-left p-md bg-white border border-slate-200 rounded-lg hover:bg-slate-50"
              >
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-sm font-bold text-slate-900">Long-document analysis</p>
                    <p className="text-xs text-slate-500">{longDocSummary.total} recent jobs tracked</p>
                  </div>
                  <span className="text-2xl font-bold text-slate-900">{longDocSummary.active}</span>
                </div>
              </button>
              <button
                type="button"
                onClick={() => navigate('/ocr')}
                className="text-left p-md bg-white border border-slate-200 rounded-lg hover:bg-slate-50"
              >
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-sm font-bold text-slate-900">OCR extraction</p>
                    <p className="text-xs text-slate-500">Upload and extract text without indexing</p>
                  </div>
                  <span className="material-symbols-outlined text-2xl text-slate-900">document_scanner</span>
                </div>
              </button>
            </div>
          </section>

          <section>
            <div className="mb-md flex justify-between items-end">
              <h2 className="text-h2 font-h2 text-on-background">Model Capacity</h2>
              <button
                type="button"
                onClick={() => navigate('/model-lab')}
                className="text-sm text-outline hover:text-secondary"
              >
                Model Lab
              </button>
            </div>
            <CapacityStrip modelStatus={modelStatus} />
          </section>
        </aside>

        <section className="col-span-12 xl:col-span-8">
          <div className="mb-md flex justify-between items-end">
            <h2 className="text-h2 font-h2 text-on-background">Recent Long Analysis</h2>
            <button
              type="button"
              onClick={() => navigate('/documents')}
              className="text-sm text-outline hover:text-secondary"
            >
              Open documents
            </button>
          </div>
          {recentJobs.length > 0 ? (
            <div className="bg-white border border-slate-200 rounded-lg overflow-hidden">
              <table className="w-full text-left border-collapse">
                <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                  <tr>
                    <th className="px-lg py-md">Job</th>
                    <th className="px-lg py-md">Status</th>
                    <th className="px-lg py-md">Type</th>
                    <th className="px-lg py-md text-right">Updated</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {recentJobs.map((job) => (
                    <tr key={job.id} className="hover:bg-slate-50">
                      <td className="px-lg py-md">
                        <p className="font-semibold text-sm text-slate-900">Document #{job.document_id}</p>
                        <p className="text-xs text-slate-500 truncate max-w-md">{job.prompt}</p>
                      </td>
                      <td className="px-lg py-md">
                        <span className={`inline-flex px-2 py-0.5 rounded border text-[10px] font-bold uppercase ${statusTone(job.status)}`}>
                          {formatLabel(job.status)}
                        </span>
                      </td>
                      <td className="px-lg py-md text-sm text-slate-600">{formatLabel(job.analysis_type)}</td>
                      <td className="px-lg py-md text-right text-sm text-slate-500 whitespace-nowrap">
                        {job.updated_at ? new Date(job.updated_at).toLocaleString() : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="bg-white border border-dashed border-slate-300 rounded-lg p-8 text-center text-sm text-slate-500">
              No long-document analysis jobs yet. Open the document library to queue one.
            </div>
          )}
        </section>

        <aside className="col-span-12 xl:col-span-4">
          <div className="mb-md flex justify-between items-end">
            <h2 className="text-h2 font-h2 text-on-background">Pinned Documents</h2>
            <span className="material-symbols-outlined text-outline">push_pin</span>
          </div>
          <div className="space-y-sm">
            {pinnedDocs.length > 0 ? pinnedDocs.map((doc) => (
              <button
                key={doc.id}
                type="button"
                onClick={() => navigate('/documents')}
                className="w-full text-left p-md bg-white border border-slate-200 border-l-4 border-l-secondary rounded flex items-center gap-md hover:bg-slate-50 transition-colors"
              >
                <span className="material-symbols-outlined text-secondary">{docIcon(doc.file_type)}</span>
                <div className="flex-1 overflow-hidden">
                  <div className="font-bold text-body-sm truncate text-on-surface">{doc.file_name}</div>
                  <div className="font-label-caps text-[10px] text-outline uppercase mt-0.5">
                    {doc.status === 'approved' ? 'Approved knowledge' : `Status: ${doc.status}`}
                  </div>
                </div>
              </button>
            )) : (
              <div className="p-md bg-white border border-slate-200 rounded text-body-sm text-outline text-center py-8">
                No documents uploaded yet.
                <button type="button" onClick={() => navigate('/documents')} className="block mx-auto mt-2 text-secondary font-medium hover:underline">
                  Upload document
                </button>
              </div>
            )}
          </div>
        </aside>

        <section className="col-span-12 mt-lg">
          <div className="mb-md flex justify-between items-end">
            <h2 className="text-h2 font-h2 text-on-background">Recent Sessions</h2>
            <button
              type="button"
              onClick={() => navigate('/sessions')}
              className="flex items-center gap-1 text-body-sm text-outline hover:text-secondary transition-colors"
            >
              View history
              <span className="material-symbols-outlined text-[18px]">history</span>
            </button>
          </div>

          {sessions.length > 0 ? (
            <div className="bg-white border border-slate-200 rounded-lg overflow-hidden">
              <table className="w-full text-left border-collapse">
                <thead className="bg-slate-900 text-white">
                  <tr>
                    {['Session', 'Status', 'Documents', 'Timestamp', ''].map((heading) => (
                      <th key={heading} className="px-lg py-md font-label-caps text-label-caps">{heading}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {sessions.map((session) => {
                    const activeDocs = parseJson(session.active_document_ids_json, []);
                    return (
                      <tr
                        key={session.id}
                        onClick={() => navigate(`/chat?session=${session.id}`)}
                        className="hover:bg-slate-50 transition-colors cursor-pointer"
                      >
                        <td className="px-lg py-md">
                          <div className="flex items-center gap-3">
                            <span className="material-symbols-outlined text-outline text-[18px]">chat_bubble_outline</span>
                            <span className="font-semibold text-body-sm text-on-surface truncate max-w-xs">{session.title}</span>
                          </div>
                        </td>
                        <td className="px-lg py-md">
                          <span className="badge-verified">
                            <span className="w-1.5 h-1.5 rounded-full bg-on-tertiary-container"></span>
                            Completed
                          </span>
                        </td>
                        <td className="px-lg py-md text-body-sm text-outline">
                          {activeDocs.length} file{activeDocs.length !== 1 ? 's' : ''}
                        </td>
                        <td className="px-lg py-md text-body-sm text-outline whitespace-nowrap">
                          {session.created_at ? new Date(session.created_at).toLocaleString() : '-'}
                        </td>
                        <td className="px-lg py-md text-right">
                          <span className="material-symbols-outlined text-outline hover:text-on-surface cursor-pointer">chevron_right</span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="bg-white border border-slate-200 rounded-lg p-12 text-center">
              <span className="material-symbols-outlined text-slate-300 text-5xl">chat_bubble_outline</span>
              <p className="text-body-md text-outline mt-4">No sessions yet.</p>
              <button
                type="button"
                onClick={() => navigate('/chat')}
                className="mt-3 btn-primary inline-flex items-center gap-2"
              >
                <span className="material-symbols-outlined text-[18px]">add_comment</span>
                Start staff chat
              </button>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
