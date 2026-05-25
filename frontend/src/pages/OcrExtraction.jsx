import { useMemo, useRef, useState } from 'react';
import api from '../api/axios';

const ACCEPTED_TYPES = '.pdf,.docx,.txt,.csv,.jpg,.jpeg,.png,.xlsx,.xls,.pptx,.ppt';
const SUPPORTED_LABEL = 'PDF, Word, Excel, PowerPoint, CSV, TXT, JPG, PNG';

function formatBytes(value) {
  if (!value) return '-';
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

function confidenceLabel(value) {
  if (value === null || value === undefined) return null;
  return `${Math.round(Number(value) * 100)}%`;
}

function confidenceTone(value) {
  if (value === null || value === undefined) return 'bg-slate-100 text-slate-500 border-slate-200';
  if (Number(value) >= 0.85) return 'bg-emerald-50 text-emerald-700 border-emerald-200';
  if (Number(value) >= 0.65) return 'bg-amber-50 text-amber-700 border-amber-200';
  return 'bg-rose-50 text-rose-700 border-rose-200';
}

function PageResult({ page }) {
  const confidenceItems = [
    ['Extract', page.extraction_confidence],
    ['OCR', page.ocr_confidence],
    ['Table', page.table_confidence],
  ].filter(([, value]) => value !== null && value !== undefined);

  return (
    <article className="bg-white border border-slate-200 rounded-lg p-4">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-sm font-bold text-slate-900">{page.label}</p>
          <p className="text-xs text-slate-500 mt-0.5">{page.character_count.toLocaleString()} characters</p>
        </div>
        {confidenceItems.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {confidenceItems.map(([label, value]) => (
              <span key={label} className={`inline-flex rounded border px-2 py-1 text-[11px] font-semibold ${confidenceTone(value)}`}>
                {label} {confidenceLabel(value)}
              </span>
            ))}
          </div>
        )}
      </div>
      <pre className="mt-3 max-h-72 overflow-auto whitespace-pre-wrap rounded border border-slate-100 bg-slate-50 p-3 text-xs leading-relaxed text-slate-700">
        {page.text}
      </pre>
      {page.vision_review && (
        <div className="mt-3 rounded border border-sky-200 bg-sky-50 p-3">
          <div className="flex items-center gap-2 text-xs font-bold uppercase text-sky-800">
            <span className="material-symbols-outlined text-[16px]">visibility</span>
            Vision Review
          </div>
          <p className="mt-2 whitespace-pre-wrap text-sm leading-relaxed text-sky-900">{page.vision_review}</p>
        </div>
      )}
    </article>
  );
}

export default function OcrExtraction() {
  const inputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);
  const [visionReview, setVisionReview] = useState(false);

  const totalPages = result?.page_count || 0;
  const totalCharacters = result?.character_count || 0;
  const hasResult = Boolean(result?.full_text);

  const outputName = useMemo(() => {
    if (!result?.file_name) return 'ocr-extracted-text.txt';
    return `${result.file_name.replace(/\.[^.]+$/, '') || 'ocr'}-extracted-text.txt`;
  }, [result?.file_name]);

  const handleFileChange = (event) => {
    const selected = event.target.files?.[0] || null;
    setFile(selected);
    setResult(null);
    setError('');
    setCopied(false);
  };

  const extractText = async () => {
    if (!file) {
      setError('Choose a file to extract text.');
      return;
    }
    setLoading(true);
    setError('');
    setCopied(false);
    setResult(null);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('vision_review', visionReview ? 'true' : 'false');
    try {
      const { data } = await api.post('/ocr/extract', formData);
      setResult(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Text extraction failed.');
    } finally {
      setLoading(false);
    }
  };

  const copyText = async () => {
    if (!result?.full_text) return;
    await navigator.clipboard.writeText(result.full_text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  };

  const downloadText = () => {
    if (!result?.full_text) return;
    const blob = new Blob([result.full_text], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = outputName;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="p-xl max-w-container-max mx-auto space-y-xl">
      <section className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="font-label-caps text-label-caps text-outline uppercase mb-sm">Document OCR</p>
          <h1 className="text-h1 font-h1 text-on-background">OCR Text Extraction</h1>
          <p className="mt-2 max-w-3xl text-body-md text-outline">
            Upload a document, image, spreadsheet, or presentation and extract text without adding it to the approved knowledge base.
          </p>
        </div>
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          className="btn-primary inline-flex items-center justify-center gap-2"
        >
          <span className="material-symbols-outlined text-[18px]">upload_file</span>
          Choose File
        </button>
      </section>

      <section className="grid grid-cols-1 gap-gutter xl:grid-cols-12">
        <div className="xl:col-span-4 space-y-md">
          <div className="bg-white border border-slate-200 rounded-lg p-lg">
            <input
              ref={inputRef}
              type="file"
              accept={ACCEPTED_TYPES}
              onChange={handleFileChange}
              className="hidden"
            />
            <button
              type="button"
              onClick={() => inputRef.current?.click()}
              className="w-full min-h-56 rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 px-5 py-8 text-center hover:border-secondary hover:bg-blue-50/30 transition-colors"
            >
              <span className="material-symbols-outlined text-5xl text-secondary">document_scanner</span>
              <span className="mt-4 block text-base font-bold text-slate-900">
                {file ? file.name : 'Select document'}
              </span>
              <span className="mt-1 block text-sm text-slate-500">
                {file ? formatBytes(file.size) : SUPPORTED_LABEL}
              </span>
            </button>

            <label className="mt-4 flex cursor-pointer items-center justify-between gap-4 rounded-lg border border-slate-200 bg-white p-3">
              <span className="flex min-w-0 items-center gap-3">
                <span className="material-symbols-outlined text-[20px] text-secondary">visibility</span>
                <span className="min-w-0">
                  <span className="block text-sm font-bold text-slate-900">Vision Review</span>
                  <span className="block text-xs leading-snug text-slate-500">Qwen-VL notes for PDF/image pages after OCR.</span>
                </span>
              </span>
              <input
                type="checkbox"
                checked={visionReview}
                onChange={(event) => setVisionReview(event.target.checked)}
                className="sr-only"
              />
              <span className={`relative h-6 w-11 shrink-0 rounded-full transition ${visionReview ? 'bg-secondary' : 'bg-slate-300'}`}>
                <span className={`absolute left-1 top-1 h-4 w-4 rounded-full bg-white transition ${visionReview ? 'translate-x-5' : ''}`} />
              </span>
            </label>

            <button
              type="button"
              disabled={loading || !file}
              onClick={extractText}
              className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded bg-primary px-4 py-3 text-sm font-semibold text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <span className="material-symbols-outlined text-[18px]">{loading ? 'hourglass_top' : 'text_snippet'}</span>
              {loading ? (visionReview ? 'Reviewing...' : 'Extracting...') : 'Extract Text'}
            </button>
          </div>

          <div className="grid grid-cols-2 gap-sm">
            <div className="bg-white border border-slate-200 rounded-lg p-md">
              <p className="font-label-caps text-label-caps text-outline uppercase">Pages</p>
              <p className="mt-1 text-2xl font-bold text-slate-900">{totalPages}</p>
            </div>
            <div className="bg-white border border-slate-200 rounded-lg p-md">
              <p className="font-label-caps text-label-caps text-outline uppercase">Characters</p>
              <p className="mt-1 text-2xl font-bold text-slate-900">{totalCharacters.toLocaleString()}</p>
            </div>
          </div>

          {result?.warnings?.length > 0 && (
            <div className="rounded-lg border border-amber-200 bg-amber-50 p-md text-sm text-amber-800">
              {result.warnings.map((warning) => (
                <p key={warning}>{warning}</p>
              ))}
            </div>
          )}

          {error && (
            <div className="rounded-lg border border-rose-200 bg-rose-50 p-md text-sm font-semibold text-rose-700">
              {error}
            </div>
          )}
        </div>

        <div className="xl:col-span-8 space-y-md">
          <div className="bg-white border border-slate-200 rounded-lg">
            <div className="flex flex-col gap-3 border-b border-slate-100 p-md md:flex-row md:items-center md:justify-between">
              <div>
                <h2 className="text-h2 font-h2 text-on-surface">Extracted Text</h2>
                <p className="text-sm text-slate-500">
                  {hasResult ? result.file_name : 'No extraction result yet'}
                  {result?.vision_review_requested && result.vision_review_pages > 0
                    ? ` · Vision reviewed ${result.vision_review_pages} page${result.vision_review_pages === 1 ? '' : 's'}`
                    : ''}
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  disabled={!hasResult}
                  onClick={copyText}
                  className="inline-flex items-center gap-2 rounded border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50"
                >
                  <span className="material-symbols-outlined text-[18px]">{copied ? 'check' : 'content_copy'}</span>
                  {copied ? 'Copied' : 'Copy'}
                </button>
                <button
                  type="button"
                  disabled={!hasResult}
                  onClick={downloadText}
                  className="inline-flex items-center gap-2 rounded border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50"
                >
                  <span className="material-symbols-outlined text-[18px]">download</span>
                  TXT
                </button>
              </div>
            </div>
            <pre className="min-h-[26rem] max-h-[34rem] overflow-auto whitespace-pre-wrap p-md text-sm leading-relaxed text-slate-800">
              {hasResult ? result.full_text : 'Extracted text will appear here.'}
            </pre>
          </div>

          {result?.pages?.length > 0 && (
            <div className="space-y-sm">
              {result.pages.map((page) => (
                <PageResult key={`${page.index}-${page.label}`} page={page} />
              ))}
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
