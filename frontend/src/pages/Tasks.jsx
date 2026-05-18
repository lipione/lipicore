import { useEffect, useMemo, useRef, useState } from 'react';
import api from '../api/axios';

const CATEGORY_COLORS = {
  Documents:  'bg-blue-50 text-blue-700 border-blue-100',
  Writing:    'bg-violet-50 text-violet-700 border-violet-100',
  Data:       'bg-emerald-50 text-emerald-700 border-emerald-100',
  Language:   'bg-amber-50 text-amber-700 border-amber-100',
  Compliance: 'bg-red-50 text-red-700 border-red-100',
};

const FORMAT_LABELS = {
  pdf:  { label: 'PDF',        icon: 'picture_as_pdf' },
  docx: { label: 'Word',       icon: 'description' },
  xlsx: { label: 'Excel',      icon: 'table_chart' },
  pptx: { label: 'PowerPoint', icon: 'slideshow' },
  txt:  { label: 'Text',       icon: 'article' },
};

const TASK_GUIDANCE = {
  summarize: {
    starter: 'Summarize this for branch staff and highlight action items, deadlines, and decisions.',
    sourceLabel: 'Upload or paste the document to summarize',
    contextLabel: 'What should the summary focus on?',
    examples: ['Branch staff summary', 'Executive summary', 'Action item list'],
    audiences: ['Branch staff', 'Management', 'Compliance team'],
  },
  draft_letter: {
    starter: 'Draft a formal bank letter with clear subject, recipient, body, and closing.',
    sourceLabel: 'Describe the letter you need',
    contextLabel: 'Recipient, tone, and must-include details',
    examples: ['Customer notice', 'Regulator response', 'Internal approval letter'],
    audiences: ['Customer', 'Regulator', 'Internal staff'],
  },
  meeting_minutes: {
    starter: 'Convert these rough notes into formal meeting minutes with decisions and owners.',
    sourceLabel: 'Upload or paste notes, transcript, or agenda',
    contextLabel: 'Meeting title, date, attendees, and expected format',
    examples: ['Credit committee minutes', 'ALCO minutes', 'Operations review'],
    audiences: ['Committee members', 'Management', 'Audit team'],
  },
  analyze_data: {
    starter: 'Analyze this data and identify trends, anomalies, risks, and recommended actions.',
    sourceLabel: 'Upload a spreadsheet or paste tabular data',
    contextLabel: 'What question should the analysis answer?',
    examples: ['Customer complaint trends', 'Branch performance', 'Loan portfolio summary'],
    audiences: ['Management', 'Risk team', 'Operations team'],
  },
  translate: {
    starter: 'Translate accurately while preserving banking terms, names, numbers, and formatting.',
    sourceLabel: 'Upload or paste the text to translate',
    contextLabel: 'Target language and style',
    examples: ['Translate to Nepali', 'Translate to English', 'Simplify after translation'],
    audiences: ['Customer', 'Branch staff', 'Management'],
  },
  write_report: {
    starter: 'Write a structured report with executive summary, findings, risks, and recommendations.',
    sourceLabel: 'Upload supporting data or paste notes',
    contextLabel: 'Report type, audience, period, and expected decision',
    examples: ['Compliance report', 'Monthly performance report', 'Board memo'],
    audiences: ['Board', 'Management', 'Regulator'],
  },
  compose_email: {
    starter: 'Compose a clear professional email with subject, greeting, body, and closing.',
    sourceLabel: 'Describe what the email must communicate',
    contextLabel: 'Recipient type, tone, and key points',
    examples: ['Customer care reply', 'Internal follow-up', 'Escalation response'],
    audiences: ['Customer', 'Internal staff', 'Regulator'],
  },
  explain_circular: {
    starter: 'Explain this circular in plain language and list who is affected, what changed, and what staff must do.',
    sourceLabel: 'Upload or paste the circular or policy',
    contextLabel: 'Department, staff role, or compliance focus',
    examples: ['Staff briefing', 'Compliance checklist', 'Customer impact note'],
    audiences: ['Branch staff', 'Compliance team', 'Customer care'],
  },
};

const IMPROVEMENTS = [
  'Make it shorter and easier for branch staff.',
  'Use a formal banking tone.',
  'Add a checklist of required actions.',
  'Highlight risks, exceptions, and missing information.',
  'Make it suitable for customer care staff.',
];

const STEPS = [
  { id: 1, label: 'Choose', icon: 'apps' },
  { id: 2, label: 'Source', icon: 'upload_file' },
  { id: 3, label: 'Prompt', icon: 'tune' },
  { id: 4, label: 'Generate', icon: 'auto_awesome' },
  { id: 5, label: 'Review', icon: 'fact_check' },
];

function templateGuidance(template) {
  return TASK_GUIDANCE[template?.id] || {
    starter: 'Complete this banking task clearly and professionally.',
    sourceLabel: 'Add source material or instructions',
    contextLabel: 'Additional context',
    examples: ['Professional output', 'Management summary', 'Action checklist'],
    audiences: ['Bank staff', 'Management', 'Customer'],
  };
}

function ExportDropdown({ content, title, formats = ['txt'] }) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(null);
  const ref = useRef(null);

  useEffect(() => {
    const handler = (event) => {
      if (ref.current && !ref.current.contains(event.target)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const handleExport = async (fmt) => {
    setLoading(fmt);
    setOpen(false);
    try {
      const res = await api.post('/export', { content, fmt, title }, { responseType: 'blob' });
      const url = URL.createObjectURL(res.data);
      const anchor = document.createElement('a');
      const disposition = res.headers['content-disposition'] || '';
      const name = disposition.match(/filename="(.+?)"/);
      anchor.href = url;
      anchor.download = name ? name[1] : `task-output.${fmt}`;
      anchor.click();
      URL.revokeObjectURL(url);
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(value => !value)}
        disabled={!!loading || !content}
        className="inline-flex items-center gap-1.5 px-3 py-2 bg-primary text-white text-xs font-semibold rounded hover:opacity-90 disabled:opacity-50 transition-all"
      >
        {loading
          ? <span className="h-3.5 w-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          : <span className="material-symbols-outlined text-[15px]">download</span>}
        Export
      </button>
      {open && (
        <div className="absolute right-0 top-10 w-44 bg-white border border-slate-200 rounded shadow-lg py-1 z-30">
          {formats.map(fmt => {
            const format = FORMAT_LABELS[fmt] || { label: fmt.toUpperCase(), icon: 'download' };
            return (
              <button
                key={fmt}
                onClick={() => handleExport(fmt)}
                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
              >
                <span className="material-symbols-outlined text-[16px] text-slate-400">{format.icon}</span>
                {format.label}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

function StepRail({ step, setStep, canGenerate, hasResult }) {
  return (
    <div className="flex flex-wrap gap-2">
      {STEPS.map(item => {
        const disabled = item.id === 4 ? !canGenerate : item.id === 5 ? !hasResult : false;
        return (
          <button
            key={item.id}
            type="button"
            disabled={disabled}
            onClick={() => setStep(item.id)}
            className={`flex items-center gap-2 px-3 py-2 rounded border text-xs font-semibold transition-all ${
              step === item.id
                ? 'bg-primary text-white border-primary'
                : 'bg-white text-slate-600 border-slate-200 hover:border-primary/40 disabled:opacity-40 disabled:hover:border-slate-200'
            }`}
          >
            <span className="material-symbols-outlined text-[15px]">{item.icon}</span>
            {item.label}
          </button>
        );
      })}
    </div>
  );
}

function TaskCard({ template, active, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`w-full text-left border rounded p-4 transition-all ${
        active ? 'border-primary bg-primary/5 ring-1 ring-primary/20' : 'border-slate-200 bg-white hover:border-primary/40'
      }`}
    >
      <div className="flex items-start gap-3">
        <div className="h-10 w-10 bg-primary/10 rounded flex items-center justify-center flex-shrink-0">
          <span className="material-symbols-outlined text-primary text-[22px]">{template.icon}</span>
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="text-sm font-bold text-slate-900">{template.name}</h3>
            <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border uppercase ${CATEGORY_COLORS[template.category] || 'bg-slate-50 text-slate-500 border-slate-100'}`}>
              {template.category}
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1 leading-relaxed">{template.description}</p>
        </div>
      </div>
    </button>
  );
}

function SourceDrop({ file, setFile, acceptsFile }) {
  const fileRef = useRef(null);
  const [dragging, setDragging] = useState(false);

  const setSelectedFile = (selected) => {
    setFile(selected || null);
    setDragging(false);
  };

  if (!acceptsFile) {
    return (
      <div className="rounded border border-slate-200 bg-slate-50 p-4 text-sm text-slate-500">
        This task uses written instructions instead of a required upload.
      </div>
    );
  }

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => fileRef.current?.click()}
      onKeyDown={(event) => { if (event.key === 'Enter') fileRef.current?.click(); }}
      onDragOver={(event) => { event.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={(event) => {
        event.preventDefault();
        setSelectedFile(event.dataTransfer.files?.[0]);
      }}
      className={`border-2 border-dashed rounded p-5 cursor-pointer transition-all ${
        dragging ? 'border-primary bg-primary/5' : 'border-slate-200 bg-white hover:border-primary/50'
      }`}
    >
      <input
        ref={fileRef}
        type="file"
        className="hidden"
        accept=".pdf,.docx,.txt,.xlsx,.xls,.csv,.pptx,.ppt"
        onChange={event => setSelectedFile(event.target.files?.[0])}
      />
      <div className="flex items-center gap-3">
        <div className="h-11 w-11 rounded bg-slate-100 flex items-center justify-center">
          <span className="material-symbols-outlined text-slate-500">upload_file</span>
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold text-slate-800 truncate">
            {file ? file.name : 'Drop a file here or choose from computer'}
          </p>
          <p className="text-xs text-slate-500 mt-0.5">PDF, Word, Excel, PowerPoint, CSV, or text up to 20 MB</p>
        </div>
        {file && (
          <button
            type="button"
            onClick={(event) => {
              event.stopPropagation();
              setFile(null);
              if (fileRef.current) fileRef.current.value = '';
            }}
            className="p-1.5 text-slate-400 hover:text-error hover:bg-red-50 rounded"
          >
            <span className="material-symbols-outlined text-[18px]">close</span>
          </button>
        )}
      </div>
    </div>
  );
}

function PromptQualityPanel({ file, content, extra, audience, tone }) {
  const checks = [
    { label: 'Source material added', pass: Boolean(file || content.trim()) },
    { label: 'Audience selected', pass: Boolean(audience) },
    { label: 'Tone selected', pass: Boolean(tone) },
    { label: 'Specific instructions included', pass: extra.trim().length >= 40 },
  ];
  const passed = checks.filter(check => check.pass).length;

  return (
    <div className="bg-white border border-slate-200 rounded p-4">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-sm font-bold text-slate-900">Prompt readiness</h3>
        <span className={`text-xs font-bold px-2 py-1 rounded border ${
          passed === checks.length ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-amber-50 text-amber-700 border-amber-200'
        }`}>
          {passed}/{checks.length}
        </span>
      </div>
      <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-2">
        {checks.map(check => (
          <div key={check.label} className="flex items-center gap-2 text-xs text-slate-600">
            <span className={`material-symbols-outlined text-[16px] ${check.pass ? 'text-emerald-600' : 'text-slate-300'}`}>
              {check.pass ? 'check_circle' : 'radio_button_unchecked'}
            </span>
            {check.label}
          </div>
        ))}
      </div>
    </div>
  );
}

function ResultPanel({ result, editableResult, setEditableResult, onReset }) {
  const [editing, setEditing] = useState(false);
  if (!result) return null;
  const wordCount = editableResult.trim() ? editableResult.trim().split(/\s+/).length : 0;

  return (
    <div className="bg-white border border-slate-200 rounded p-5 space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-emerald-50 text-emerald-700 rounded-full text-xs font-semibold">
            <span className="material-symbols-outlined text-[15px]">check_circle</span>
            Generated
          </div>
          <h2 className="text-base font-bold text-slate-900 mt-2">{result.template_name}</h2>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setEditing(value => !value)}
            className="inline-flex items-center gap-1.5 px-3 py-2 border border-slate-200 text-xs font-semibold text-slate-600 rounded hover:bg-slate-50"
          >
            <span className="material-symbols-outlined text-[15px]">{editing ? 'visibility' : 'edit'}</span>
            {editing ? 'Preview' : 'Edit'}
          </button>
          <button
            type="button"
            onClick={onReset}
            className="inline-flex items-center gap-1.5 px-3 py-2 border border-slate-200 text-xs font-semibold text-slate-600 rounded hover:bg-slate-50"
          >
            <span className="material-symbols-outlined text-[15px]">refresh</span>
            New run
          </button>
          <ExportDropdown content={editableResult} title={result.template_name} formats={result.suggested_formats} />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div className="rounded border border-slate-200 bg-slate-50 p-3">
          <p className="text-[10px] font-bold text-slate-500 uppercase">Length</p>
          <p className="text-lg font-bold text-slate-900 mt-1">{wordCount} words</p>
        </div>
        <div className="rounded border border-slate-200 bg-slate-50 p-3">
          <p className="text-[10px] font-bold text-slate-500 uppercase">Review status</p>
          <p className="text-sm font-bold text-amber-700 mt-1">Human review required</p>
        </div>
        <div className="rounded border border-slate-200 bg-slate-50 p-3">
          <p className="text-[10px] font-bold text-slate-500 uppercase">Export formats</p>
          <p className="text-sm font-bold text-slate-900 mt-1">{(result.suggested_formats || []).join(', ').toUpperCase()}</p>
        </div>
      </div>

      {editing ? (
        <textarea
          value={editableResult}
          onChange={event => setEditableResult(event.target.value)}
          rows={16}
          className="w-full border border-slate-200 rounded px-3 py-3 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-primary/20 resize-y"
        />
      ) : (
        <div className="max-h-[520px] overflow-y-auto border border-slate-200 rounded bg-slate-50 p-4 text-sm text-slate-800 leading-relaxed whitespace-pre-wrap">
          {editableResult}
        </div>
      )}
    </div>
  );
}

export default function Tasks() {
  const [templates, setTemplates] = useState([]);
  const [active, setActive] = useState(null);
  const [filterCat, setFilterCat] = useState('All');
  const [step, setStep] = useState(1);
  const [content, setContent] = useState('');
  const [extra, setExtra] = useState('');
  const [file, setFile] = useState(null);
  const [audience, setAudience] = useState('');
  const [tone, setTone] = useState('Professional');
  const [result, setResult] = useState(null);
  const [editableResult, setEditableResult] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    api.get('/tasks/templates').then(response => {
      setTemplates(response.data);
      setActive(current => current || response.data[0] || null);
    }).catch(() => setError('Could not load AI tasks. Check your session and backend access.'));
  }, []);

  const guidance = templateGuidance(active);
  const categories = useMemo(() => ['All', ...new Set(templates.map(template => template.category))], [templates]);
  const filtered = filterCat === 'All' ? templates : templates.filter(template => template.category === filterCat);
  const generatedPrompt = useMemo(() => {
    const parts = [
      guidance.starter,
      audience ? `Audience: ${audience}.` : '',
      tone ? `Tone: ${tone}.` : '',
      extra ? `Specific instructions: ${extra}` : '',
    ].filter(Boolean);
    return parts.join('\n');
  }, [audience, extra, guidance.starter, tone]);
  const hasInput = Boolean(file || content.trim() || (!active?.accepts_file && extra.trim()));
  const canGenerate = Boolean(active && hasInput && !loading);

  const chooseTemplate = (template) => {
    setActive(template);
    setStep(2);
    setFile(null);
    setResult(null);
    setEditableResult('');
    setError('');
    const nextGuidance = templateGuidance(template);
    setExtra(nextGuidance.starter);
    setAudience(nextGuidance.audiences[0] || '');
  };

  const appendInstruction = (instruction) => {
    setExtra(current => current ? `${current}\n${instruction}` : instruction);
  };

  const runTask = async () => {
    if (!canGenerate) {
      setError('Add a file, pasted content, or clear instructions before generating.');
      setStep(2);
      return;
    }

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const fd = new FormData();
      fd.append('template_id', active.id);
      fd.append('content', content.trim() || extra.trim());
      fd.append('extra', generatedPrompt);
      if (file) fd.append('file', file);

      const response = await api.post('/tasks/run', fd);
      setResult(response.data);
      setEditableResult(response.data.result || '');
      setStep(5);
    } catch (err) {
      setError(err.response?.data?.detail || 'Task failed. Please revise the input and try again.');
      setStep(4);
    } finally {
      setLoading(false);
    }
  };

  const resetRun = () => {
    setResult(null);
    setEditableResult('');
    setStep(2);
  };

  return (
    <div className="h-full overflow-y-auto bg-slate-50">
      <div className="max-w-7xl mx-auto p-4 sm:p-6 lg:p-8 space-y-6">
        <header className="flex flex-col lg:flex-row lg:items-end justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 font-public-sans">AI Tasks</h1>
            <p className="text-sm text-slate-500 mt-1 max-w-2xl">
              Guided workflows for bank staff. Choose the job, add the source, refine the prompt, then export the result.
            </p>
          </div>
          <StepRail step={step} setStep={setStep} canGenerate={canGenerate} hasResult={!!result} />
        </header>

        {error && (
          <div className="flex items-start gap-2 bg-red-50 border border-red-100 text-red-700 rounded p-3 text-sm">
            <span className="material-symbols-outlined text-[18px] mt-0.5">error_outline</span>
            <span>{error}</span>
          </div>
        )}

        <div className="grid grid-cols-1 xl:grid-cols-[360px_1fr] gap-6">
          <aside className="space-y-4">
            <div className="bg-white border border-slate-200 rounded p-4 space-y-3">
              <div className="flex items-center justify-between gap-3">
                <h2 className="text-sm font-bold text-slate-900">Task library</h2>
                <span className="text-xs text-slate-400">{filtered.length} shown</span>
              </div>
              <div className="flex gap-1.5 flex-wrap">
                {categories.map(category => (
                  <button
                    key={category}
                    type="button"
                    onClick={() => setFilterCat(category)}
                    className={`px-2.5 py-1.5 rounded text-xs font-semibold transition-colors ${
                      filterCat === category ? 'bg-primary text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    {category}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-3">
              {filtered.map(template => (
                <TaskCard
                  key={template.id}
                  template={template}
                  active={active?.id === template.id}
                  onClick={() => chooseTemplate(template)}
                />
              ))}
            </div>
          </aside>

          <main className="space-y-6">
            <section className="bg-white border border-slate-200 rounded p-5">
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-3">
                  <div className="h-11 w-11 bg-primary/10 rounded flex items-center justify-center flex-shrink-0">
                    <span className="material-symbols-outlined text-primary text-[24px]">{active?.icon || 'auto_awesome'}</span>
                  </div>
                  <div>
                    <h2 className="text-lg font-bold text-slate-900">{active?.name || 'Select a task'}</h2>
                    <p className="text-sm text-slate-500 mt-1">{active?.description || 'Choose a task from the library to begin.'}</p>
                  </div>
                </div>
                {active?.category && (
                  <span className={`text-[10px] font-bold px-2 py-1 rounded-full border uppercase ${CATEGORY_COLORS[active.category] || 'bg-slate-50 text-slate-500 border-slate-100'}`}>
                    {active.category}
                  </span>
                )}
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-3 mt-5">
                {guidance.examples.map(example => (
                  <button
                    key={example}
                    type="button"
                    onClick={() => {
                      setExtra(`${guidance.starter}\nUse case: ${example}.`);
                      setStep(3);
                    }}
                    className="text-left border border-slate-200 rounded p-3 hover:border-primary/40 hover:bg-primary/5 transition-colors"
                  >
                    <span className="text-xs font-semibold text-slate-800">{example}</span>
                  </button>
                ))}
              </div>
            </section>

            <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white border border-slate-200 rounded p-5 space-y-4">
                <div>
                  <h2 className="text-sm font-bold text-slate-900">1. Add source material</h2>
                  <p className="text-xs text-slate-500 mt-1">{guidance.sourceLabel}</p>
                </div>
                <SourceDrop file={file} setFile={setFile} acceptsFile={!!active?.accepts_file} />
                <textarea
                  value={content}
                  onChange={event => setContent(event.target.value)}
                  rows={8}
                  placeholder={active?.accepts_file ? 'Paste text here if there is no file, or add notes that should be included.' : 'Write what you want the AI to create.'}
                  className="w-full border border-slate-200 rounded px-3 py-3 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-primary/20 resize-y"
                />
              </div>

              <div className="bg-white border border-slate-200 rounded p-5 space-y-4">
                <div>
                  <h2 className="text-sm font-bold text-slate-900">2. Shape the output</h2>
                  <p className="text-xs text-slate-500 mt-1">{guidance.contextLabel}</p>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <label className="space-y-1.5">
                    <span className="text-xs font-semibold text-slate-500 uppercase">Audience</span>
                    <select
                      value={audience}
                      onChange={event => setAudience(event.target.value)}
                      className="w-full border border-slate-200 rounded px-3 py-2.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-primary/20"
                    >
                      {guidance.audiences.map(option => <option key={option}>{option}</option>)}
                      <option>Customer care staff</option>
                      <option>Branch operations</option>
                    </select>
                  </label>
                  <label className="space-y-1.5">
                    <span className="text-xs font-semibold text-slate-500 uppercase">Tone</span>
                    <select
                      value={tone}
                      onChange={event => setTone(event.target.value)}
                      className="w-full border border-slate-200 rounded px-3 py-2.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-primary/20"
                    >
                      <option>Professional</option>
                      <option>Simple</option>
                      <option>Formal</option>
                      <option>Customer friendly</option>
                    </select>
                  </label>
                </div>
                <textarea
                  value={extra}
                  onChange={event => setExtra(event.target.value)}
                  rows={6}
                  placeholder={guidance.starter}
                  className="w-full border border-slate-200 rounded px-3 py-3 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-primary/20 resize-y"
                />
                <div className="flex flex-wrap gap-2">
                  {IMPROVEMENTS.map(item => (
                    <button
                      key={item}
                      type="button"
                      onClick={() => appendInstruction(item)}
                      className="inline-flex items-center gap-1 px-2.5 py-1.5 bg-slate-50 border border-slate-200 rounded text-xs text-slate-600 hover:border-primary/40 hover:text-primary"
                    >
                      <span className="material-symbols-outlined text-[14px]">add</span>
                      {item}
                    </button>
                  ))}
                </div>
              </div>
            </section>

            <PromptQualityPanel
              file={file}
              content={content}
              extra={extra}
              audience={audience}
              tone={tone}
            />

            <section className="bg-white border border-slate-200 rounded p-5 space-y-4">
              <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-4">
                <div>
                  <h2 className="text-sm font-bold text-slate-900">3. Review generated prompt</h2>
                  <p className="text-xs text-slate-500 mt-1">This is what will guide the private model. Edit the fields above to improve it.</p>
                </div>
                <button
                  type="button"
                  onClick={runTask}
                  disabled={!canGenerate}
                  className="inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-primary text-white text-sm font-semibold rounded shadow-sm hover:opacity-90 disabled:opacity-50 transition-all"
                >
                  {loading
                    ? <><span className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Generating</>
                    : <><span className="material-symbols-outlined text-[18px]">auto_awesome</span> Generate output</>}
                </button>
              </div>
              <pre className="whitespace-pre-wrap bg-slate-950 text-slate-100 rounded p-4 text-xs leading-relaxed overflow-x-auto">
                {generatedPrompt}
              </pre>
            </section>

            <ResultPanel
              result={result}
              editableResult={editableResult}
              setEditableResult={setEditableResult}
              onReset={resetRun}
            />
          </main>
        </div>
      </div>
    </div>
  );
}
