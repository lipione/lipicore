import { useEffect, useMemo, useState } from 'react';
import api from '../api/axios';

const READINESS = {
  green: { label: 'Pilot ready', className: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
  yellow: { label: 'Needs watch', className: 'bg-amber-50 text-amber-700 border-amber-200' },
  red: { label: 'Do not claim', className: 'bg-rose-50 text-rose-700 border-rose-200' },
};

function ReadinessBadge({ value }) {
  const meta = READINESS[value] || { label: value || 'Not tested', className: 'bg-slate-50 text-slate-700 border-slate-200' };
  return <span className={`px-2 py-0.5 rounded border text-xs font-semibold ${meta.className}`}>{meta.label}</span>;
}

function formatLabel(value) {
  return String(value || 'unknown').replaceAll('_', ' ');
}

function formatMs(value) {
  if (value === null || value === undefined) return '-';
  return `${Math.round(Number(value)).toLocaleString()} ms`;
}

function formatNumber(value) {
  if (value === null || value === undefined) return '-';
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric.toLocaleString() : value;
}

function benchmarkForModel(model, benchmarks) {
  if (!model) return null;
  if (benchmarks[model.key]) return benchmarks[model.key];
  const entries = Object.entries(benchmarks);
  const key = String(model.key || '').toLowerCase();
  const modelName = String(model.model || '').toLowerCase();

  const match = entries.find(([name]) => {
    const normalized = name.toLowerCase();
    if (normalized.includes(key)) return true;
    if (key === 'fast') return normalized.includes('fast') || normalized.includes('e4b');
    if (key === 'deep') return normalized.includes('deep') || normalized.includes('26b');
    if (key === 'vision') return normalized.includes('vision') || normalized.includes('vl');
    return modelName && normalized.includes(modelName.split('/').pop());
  });
  return match?.[1] || null;
}

function RuntimeCard({ model, gate, benchmark }) {
  const limit = Number(gate?.limit || 0);
  const active = Number(gate?.active || 0);
  const waiting = Number(gate?.waiting || 0);
  const pct = limit > 0 ? Math.min(100, Math.round((active / limit) * 100)) : 0;

  return (
    <article className="bg-white border border-slate-200 rounded p-4">
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-sm font-semibold text-slate-900">{model.label}</h3>
            <span className="text-xs px-2 py-0.5 rounded bg-slate-100 text-slate-700">{model.key}</span>
          </div>
          <p className="mt-1 text-xs text-slate-500 break-all">{model.model}</p>
        </div>
        <ReadinessBadge value={benchmark?.claim_readiness} />
      </div>

      <div className="mt-4 grid grid-cols-3 gap-2 text-center">
        <div className="rounded border border-slate-100 bg-slate-50 px-2 py-2">
          <p className="text-sm font-bold text-slate-900">{formatNumber(model.context_window_tokens)}</p>
          <p className="text-[10px] font-semibold uppercase text-slate-500">Context</p>
        </div>
        <div className="rounded border border-slate-100 bg-slate-50 px-2 py-2">
          <p className="text-sm font-bold text-slate-900">{formatNumber(model.max_tokens)}</p>
          <p className="text-[10px] font-semibold uppercase text-slate-500">Output</p>
        </div>
        <div className="rounded border border-slate-100 bg-slate-50 px-2 py-2">
          <p className="text-sm font-bold text-slate-900">{formatNumber(limit)}</p>
          <p className="text-[10px] font-semibold uppercase text-slate-500">Slots</p>
        </div>
      </div>

      <div className="mt-4">
        <div className="flex items-center justify-between text-xs text-slate-500">
          <span>{active}/{limit || '-'} active</span>
          <span>{waiting} waiting</span>
        </div>
        <div className="mt-2 h-1.5 rounded-full bg-slate-100 overflow-hidden">
          <div className="h-full rounded-full bg-secondary" style={{ width: `${pct}%` }} />
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {(model.capabilities || []).map((capability) => (
          <span key={capability} className="text-xs px-2 py-1 rounded bg-blue-50 text-blue-700">
            {formatLabel(capability)}
          </span>
        ))}
      </div>
    </article>
  );
}

export default function ModelLab() {
  const [status, setStatus] = useState(null);
  const [candidates, setCandidates] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let mounted = true;
    Promise.all([
      api.get('/model-lab/status'),
      api.get('/model-lab/candidates'),
    ]).then(([statusResponse, candidateResponse]) => {
      if (!mounted) return;
      setStatus(statusResponse.data);
      setCandidates(candidateResponse.data);
    }).catch((err) => {
      if (!mounted) return;
      setError(err.response?.data?.detail || 'Unable to load model lab data.');
    }).finally(() => {
      if (mounted) setLoading(false);
    });
    return () => {
      mounted = false;
    };
  }, []);

  const registry = status?.registry || {};
  const modelGates = status?.models || {};
  const benchmarks = status?.latest_benchmark?.models || {};
  const candidateGroups = useMemo(() => {
    const groups = {};
    (candidates?.candidates || []).forEach((candidate) => {
      const tier = candidate.tier || 'unknown';
      if (!groups[tier]) groups[tier] = [];
      groups[tier].push(candidate);
    });
    return groups;
  }, [candidates]);

  const benchmarkRows = Object.entries(benchmarks);

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-4">
        <div>
          <p className="text-xs font-bold uppercase text-slate-400">Current upgrade</p>
          <h1 className="text-2xl font-bold text-slate-900 mt-1">Model Lab</h1>
          <p className="text-sm text-slate-500 mt-1 max-w-3xl">
            Runtime capacity, benchmark evidence, and candidate models for staff chat, approved knowledge, long context, embeddings, reranking, and vision OCR.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <span className="px-3 py-1 text-xs font-semibold rounded bg-slate-50 text-slate-700 border border-slate-200">
            {candidates?.total_candidates || 0} candidates
          </span>
          <span className="px-3 py-1 text-xs font-semibold rounded bg-amber-50 text-amber-700 border border-amber-200">
            No autonomous decisions
          </span>
        </div>
      </div>

      {error && (
        <div className="rounded border border-rose-100 bg-rose-50 px-3 py-2 text-sm font-semibold text-rose-700">
          {error}
        </div>
      )}

      {loading ? (
        <div className="rounded border border-dashed border-slate-300 p-8 text-center text-sm text-slate-500">
          Loading model lab...
        </div>
      ) : (
        <>
          <section>
            <div className="mb-3 flex flex-col sm:flex-row sm:items-end justify-between gap-2">
              <div>
                <h2 className="text-sm font-semibold text-slate-900">Runtime Registry</h2>
                <p className="text-xs text-slate-500 mt-1">The active routes used by the application today.</p>
              </div>
              <span className="text-xs text-slate-500">
                {Object.keys(modelGates).length} live admission gates
              </span>
            </div>
            <div className="grid gap-3 lg:grid-cols-3">
              {Object.values(registry).map((model) => (
                <RuntimeCard
                  key={model.key}
                  model={model}
                  gate={modelGates[model.key]}
                  benchmark={benchmarkForModel(model, benchmarks)}
                />
              ))}
            </div>
          </section>

          <section className="grid gap-4 lg:grid-cols-3">
            <div className="bg-white border border-slate-200 rounded p-4">
              <div className="flex items-center justify-between gap-3">
                <h2 className="text-sm font-semibold text-slate-900">Defensible Claim</h2>
                <span className="material-symbols-outlined text-[18px] text-emerald-600">verified</span>
              </div>
              <p className="mt-2 text-sm text-slate-600">
                LipiCore is better for private bank knowledge because it runs on bank-controlled infrastructure with citations, audit logs, and document governance.
              </p>
            </div>
            <div className="bg-white border border-slate-200 rounded p-4">
              <div className="flex items-center justify-between gap-3">
                <h2 className="text-sm font-semibold text-slate-900">Unsafe Claim</h2>
                <span className="material-symbols-outlined text-[18px] text-rose-600">block</span>
              </div>
              <p className="mt-2 text-sm text-slate-600">
                Do not claim it is generally better than GPT-4, makes lending decisions, or guarantees regulatory correctness.
              </p>
            </div>
            <div className="bg-white border border-slate-200 rounded p-4">
              <div className="flex items-center justify-between gap-3">
                <h2 className="text-sm font-semibold text-slate-900">Next Evidence</h2>
                <span className="material-symbols-outlined text-[18px] text-blue-600">science</span>
              </div>
              <p className="mt-2 text-sm text-slate-600">
                Run concurrency, Nepali, citation accuracy, OCR/table, and long-context tests before changing buyer-facing capacity claims.
              </p>
            </div>
          </section>

          <section>
            <div className="mb-3 flex flex-col sm:flex-row sm:items-end justify-between gap-2">
              <div>
                <h2 className="text-sm font-semibold text-slate-900">Latest Benchmark</h2>
                <p className="text-xs text-slate-500 mt-1">
                  {status?.latest_benchmark?.report_path || 'No benchmark report found.'}
                </p>
              </div>
              <span className="text-xs text-slate-500">{status?.latest_benchmark?.model_count || 0} models summarized</span>
            </div>
            <div className="bg-white border border-slate-200 rounded overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                  <tr>
                    <th className="text-left p-3">Model</th>
                    <th className="text-left p-3">Readiness</th>
                    <th className="text-right p-3">P95 first token</th>
                    <th className="text-right p-3">P95 total</th>
                    <th className="text-right p-3">Chars/sec</th>
                    <th className="text-right p-3">Errors</th>
                  </tr>
                </thead>
                <tbody>
                  {benchmarkRows.length === 0 ? (
                    <tr><td colSpan="6" className="p-4 text-slate-500">No benchmark report found.</td></tr>
                  ) : benchmarkRows.map(([key, item]) => (
                    <tr key={key} className="border-t border-slate-100">
                      <td className="p-3 font-medium text-slate-900">{key}</td>
                      <td className="p-3"><ReadinessBadge value={item.claim_readiness} /></td>
                      <td className="p-3 text-right text-slate-700">{formatMs(item.p95_first_token_latency_ms)}</td>
                      <td className="p-3 text-right text-slate-700">{formatMs(item.p95_total_latency_ms)}</td>
                      <td className="p-3 text-right text-slate-700">{formatNumber(item.chars_per_second_avg)}</td>
                      <td className="p-3 text-right text-slate-700">{formatNumber(item.failed_requests)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section>
            <div className="mb-3">
              <h2 className="text-sm font-semibold text-slate-900">Candidate Matrix</h2>
              <p className="text-xs text-slate-500 mt-1">{candidates?.policy}</p>
            </div>
            <div className="grid gap-4">
              {Object.entries(candidateGroups).map(([tier, items]) => (
                <div key={tier} className="bg-white border border-slate-200 rounded p-4">
                  <div className="flex items-center justify-between gap-3">
                    <h3 className="text-sm font-semibold text-slate-900">{formatLabel(tier)}</h3>
                    <span className="text-xs px-2 py-0.5 rounded bg-slate-100 text-slate-700">{items.length} models</span>
                  </div>
                  <div className="mt-3 grid gap-3 md:grid-cols-2">
                    {items.map((candidate) => (
                      <article key={candidate.key} className="rounded border border-slate-100 bg-slate-50 p-3">
                        <div className="flex flex-wrap items-start justify-between gap-2">
                          <div className="min-w-0">
                            <h4 className="text-sm font-bold text-slate-900">{candidate.key}</h4>
                            <p className="mt-1 text-xs text-slate-500 break-all">{candidate.model_id}</p>
                          </div>
                          <span className="text-xs px-2 py-0.5 rounded bg-white border border-slate-200 text-slate-600">
                            {candidate.min_vram_gb_estimate} GB VRAM
                          </span>
                        </div>
                        <div className="mt-3 flex flex-wrap gap-2">
                          <span className="text-xs px-2 py-0.5 rounded bg-white border border-slate-200 text-slate-600">
                            {formatNumber(candidate.context_tokens_claim)} context claim
                          </span>
                          {(candidate.runtime_priority || []).map((runtime) => (
                            <span key={runtime} className="text-xs px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-100">
                              {runtime}
                            </span>
                          ))}
                        </div>
                        <p className="mt-3 text-xs text-slate-600">{candidate.test_reason}</p>
                        {candidate.risk_notes && (
                          <p className="mt-2 text-xs text-amber-700 bg-amber-50 border border-amber-100 rounded p-2">
                            {candidate.risk_notes}
                          </p>
                        )}
                      </article>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </section>
        </>
      )}
    </div>
  );
}
