import { useMemo, useState } from 'react';
import api from '../api/axios';
import SourceMetadataStrip from '../components/trust/SourceMetadataStrip';
import { hasCitationValue, sourcePdfPage } from '../utils/sourceCitation';

const SAMPLE_CASES = [
  {
    id: 'policy-source-check',
    question: 'What does the approved policy say about customer complaint escalation?',
    expected_source_titles: ['Customer Complaint Policy'],
    expected_section_labels: ['Complaint escalation'],
    required_citation_terms: ['complaint'],
    required_answer_terms: ['escalation'],
    source_required: true,
    citation_required: true,
  },
  {
    id: 'not-found-check',
    question: 'What is the bank policy for a topic that is not in the approved library?',
    not_found_required: true,
    no_general_policy_advice: true,
  },
  {
    id: 'unsupported-advice-check',
    question: 'Can staff approve this customer request?',
    source_required: true,
    no_general_policy_advice: true,
  },
];

function pct(value) {
  return `${Math.round(Number(value || 0) * 100)}%`;
}

function evaluationSourceLocation(source) {
  const pdfPage = sourcePdfPage(source);
  return [
    source.document_heading || source.section_label || source.section_number || 'Heading unknown',
    source.clause_number,
    hasCitationValue(pdfPage) ? `PDF p.${pdfPage}` : null,
    hasCitationValue(source.printed_page_number) ? `printed p.${source.printed_page_number}` : null,
  ].filter(Boolean).join(' · ');
}

function ScoreCard({ label, value, icon, tone = 'slate' }) {
  const tones = {
    emerald: 'bg-emerald-50 text-emerald-800 border-emerald-200',
    amber: 'bg-amber-50 text-amber-800 border-amber-200',
    rose: 'bg-rose-50 text-rose-800 border-rose-200',
    slate: 'bg-white text-slate-800 border-slate-200',
  };
  return (
    <div className={`border rounded-lg p-4 ${tones[tone] || tones.slate}`}>
      <div className="flex items-center justify-between gap-3">
        <span className="text-xs font-bold uppercase tracking-wide opacity-75">{label}</span>
        <span className="material-symbols-outlined text-[18px]">{icon}</span>
      </div>
      <p className="text-3xl font-bold mt-2">{value}</p>
    </div>
  );
}

function CaseResult({ item }) {
  return (
    <article className="bg-white border border-slate-200 rounded-lg p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded border text-[10px] font-bold uppercase ${
              item.passed ? 'bg-emerald-50 text-emerald-800 border-emerald-200' : 'bg-rose-50 text-rose-800 border-rose-200'
            }`}>
              <span className="material-symbols-outlined text-[12px]">{item.passed ? 'check_circle' : 'error'}</span>
              {item.passed ? 'Passed' : 'Failed'}
            </span>
            <span className="text-xs text-slate-500">{item.id}</span>
          </div>
          <h3 className="text-sm font-bold text-slate-900 mt-2">{item.question}</h3>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center text-xs">
          <div className="rounded bg-slate-50 border border-slate-100 px-2 py-1">
            <p className="font-bold text-slate-900">{pct(item.source_recall)}</p>
            <p className="text-slate-500">Source</p>
          </div>
          <div className="rounded bg-slate-50 border border-slate-100 px-2 py-1">
            <p className="font-bold text-slate-900">{pct(item.location_recall)}</p>
            <p className="text-slate-500">Location</p>
          </div>
          <div className="rounded bg-slate-50 border border-slate-100 px-2 py-1">
            <p className="font-bold text-slate-900">{pct(item.citation_term_recall)}</p>
            <p className="text-slate-500">Citation</p>
          </div>
          <div className="rounded bg-slate-50 border border-slate-100 px-2 py-1">
            <p className="font-bold text-slate-900">{pct(item.answer_term_recall)}</p>
            <p className="text-slate-500">Answer</p>
          </div>
        </div>
      </div>

      {item.failures?.length > 0 && (
        <div className="mt-3 bg-rose-50 border border-rose-100 rounded p-3">
          <p className="text-xs font-bold text-rose-800 uppercase mb-1">Failures</p>
          <ul className="space-y-1 text-xs text-rose-700">
            {item.failures.map((failure, index) => <li key={`${failure}-${index}`}>{failure}</li>)}
          </ul>
        </div>
      )}

      <details className="mt-3">
        <summary className="cursor-pointer text-xs font-semibold text-slate-600">Answer and sources</summary>
        <div className="mt-3 grid grid-cols-1 lg:grid-cols-2 gap-3">
          <pre className="whitespace-pre-wrap bg-slate-950 text-slate-100 rounded p-3 text-xs leading-relaxed overflow-x-auto max-h-72">
            {item.answer || 'No answer'}
          </pre>
          <div className="space-y-2 max-h-72 overflow-y-auto">
            {(item.sources || []).length === 0 ? (
              <p className="text-xs text-slate-500 border border-slate-200 rounded p-3">No sources returned.</p>
            ) : item.sources.map((source, index) => (
              <div key={`${source.document_id || index}`} className="border border-slate-200 rounded p-3 text-xs">
                <div className="flex flex-wrap items-center gap-1.5">
                  <p className="font-bold text-slate-900">{source.document_title || source.title || 'Source'}</p>
                  {source.citation_verification && (
                    <span className="px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 font-bold uppercase text-[9px]">
                      {source.citation_verification}
                    </span>
                  )}
                  {(source.source_warnings || []).map(warning => (
                    <span key={warning} className="px-1.5 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-100 font-bold uppercase text-[9px]">
                      {warning.replaceAll('_', ' ')}
                    </span>
                  ))}
                </div>
                <p className="text-slate-500 mt-1">{evaluationSourceLocation(source)}</p>
                <div className="mt-2">
                  <SourceMetadataStrip source={source} />
                </div>
                <p className="text-slate-700 mt-2 whitespace-pre-wrap">{source.snippet || source.passage || ''}</p>
              </div>
            ))}
          </div>
        </div>
      </details>
    </article>
  );
}

export default function EvaluationCenter() {
  const [caseText, setCaseText] = useState(JSON.stringify(SAMPLE_CASES, null, 2));
  const [threshold, setThreshold] = useState(0.8);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const parsedCases = useMemo(() => {
    try {
      const parsed = JSON.parse(caseText);
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return null;
    }
  }, [caseText]);

  const runEvaluation = async () => {
    if (!parsedCases || parsedCases.length === 0) {
      setError('Evaluation cases must be a non-empty JSON array.');
      return;
    }
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const response = await api.post('/evaluations/rag', {
        cases: parsedCases,
        pass_threshold: Number(threshold),
      });
      setResult(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Evaluation failed. Check case format and admin permissions.');
    } finally {
      setLoading(false);
    }
  };

  const summary = result?.summary;
  const gateTone = summary?.gate_passed ? 'emerald' : summary ? 'rose' : 'slate';

  return (
    <div className="h-full overflow-y-auto bg-slate-50">
      <div className="max-w-7xl mx-auto p-4 sm:p-6 lg:p-8 space-y-6">
        <header className="flex flex-col lg:flex-row lg:items-end justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">RAG Evaluation Center</h1>
            <p className="text-sm text-slate-500 mt-1 max-w-2xl">
              Test retrieval, citation, and answer quality before claiming a document library is reliable.
            </p>
          </div>
          <button
            type="button"
            onClick={runEvaluation}
            disabled={loading || !parsedCases}
            className="inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-primary text-white text-sm font-semibold rounded shadow-sm hover:opacity-90 disabled:opacity-50"
          >
            {loading
              ? <><span className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Running</>
              : <><span className="material-symbols-outlined text-[18px]">science</span> Run evaluation</>}
          </button>
        </header>

        {error && (
          <div className="flex items-start gap-2 bg-rose-50 border border-rose-100 text-rose-700 rounded p-3 text-sm">
            <span className="material-symbols-outlined text-[18px] mt-0.5">error</span>
            <span>{error}</span>
          </div>
        )}

        <section className="grid grid-cols-1 xl:grid-cols-[420px_1fr] gap-6">
          <aside className="bg-white border border-slate-200 rounded-lg p-5 space-y-4">
            <div>
              <h2 className="text-sm font-bold text-slate-900">Evaluation cases</h2>
              <p className="text-xs text-slate-500 mt-1">
                Use expected sources, section/page expectations, citation terms, and gate flags such as source_required, citation_required, and no_general_policy_advice.
              </p>
            </div>
            <label className="space-y-1.5 block">
              <span className="text-xs font-semibold text-slate-500 uppercase">Pass threshold</span>
              <input
                type="number"
                min="0"
                max="1"
                step="0.05"
                value={threshold}
                onChange={event => setThreshold(event.target.value)}
                className="w-full border border-slate-200 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
              />
            </label>
            <textarea
              value={caseText}
              onChange={event => setCaseText(event.target.value)}
              rows={24}
              spellCheck={false}
              className={`w-full font-mono text-xs border rounded px-3 py-3 focus:outline-none focus:ring-2 resize-y ${
                parsedCases ? 'border-slate-200 focus:ring-primary/20' : 'border-rose-200 focus:ring-rose-100'
              }`}
            />
          </aside>

          <main className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
              <ScoreCard label="Gate" value={summary ? (summary.gate_passed ? 'Pass' : 'Fail') : '—'} icon="rule" tone={gateTone} />
              <ScoreCard label="Pass rate" value={summary ? pct(summary.pass_rate) : '—'} icon="fact_check" tone="slate" />
              <ScoreCard label="Source recall" value={summary ? pct(summary.source_recall_avg) : '—'} icon="source" tone="slate" />
              <ScoreCard label="Location recall" value={summary ? pct(summary.location_recall_avg) : '—'} icon="pin_drop" tone="slate" />
              <ScoreCard label="Citation recall" value={summary ? pct(summary.citation_term_recall_avg) : '—'} icon="format_quote" tone="slate" />
            </div>

            <section className="bg-white border border-slate-200 rounded-lg p-5">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <h2 className="text-sm font-bold text-slate-900">Evaluation results</h2>
                  <p className="text-xs text-slate-500 mt-1">
                    Failed cases are the questions most likely to embarrass you in a bank pilot.
                  </p>
                </div>
                {summary && (
                  <span className="text-xs text-slate-500">
                    {summary.passed_cases}/{summary.total_cases} passed
                  </span>
                )}
              </div>
              <div className="mt-4 space-y-3">
                {!result ? (
                  <div className="border border-dashed border-slate-200 rounded-lg p-8 text-center text-sm text-slate-500">
                    Run an evaluation to see source and citation quality.
                  </div>
                ) : result.cases.map(item => <CaseResult key={item.id} item={item} />)}
              </div>
            </section>
          </main>
        </section>
      </div>
    </div>
  );
}
