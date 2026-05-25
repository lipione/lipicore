import { useState, useRef, useEffect, useCallback } from 'react';
import { useSearchParams, useOutletContext, useNavigate } from 'react-router-dom';
import api from '../api/axios';
import FilePreviewCard from '../components/chat/FilePreviewCard';
import AnswerTrustBadge from '../components/chat/AnswerTrustBadge';
import ChatModeSelector, { CHAT_MODES, modeByValue } from '../components/chat/ChatModeSelector';
import SourceEvidencePanel from '../components/chat/SourceEvidencePanel';
import useDropZone from '../hooks/useDropZone';
import { useBranding } from '../contexts/BrandingContext';

const EXPORT_FORMATS = [
  { fmt: 'pdf',  label: 'PDF',         icon: 'picture_as_pdf' },
  { fmt: 'docx', label: 'Word',        icon: 'description' },
  { fmt: 'xlsx', label: 'Excel',       icon: 'table_chart' },
  { fmt: 'pptx', label: 'PowerPoint',  icon: 'slideshow' },
  { fmt: 'txt',  label: 'Text',        icon: 'article' },
];

const LAST_CHAT_SESSION_KEY = 'bankai:lastChatSessionId';

function ChatExportButton({ content }) {
  const [open, setOpen]     = useState(false);
  const [loading, setLoading] = useState(null);
  const ref = useRef(null);

  useEffect(() => {
    const h = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener('mousedown', h);
    return () => document.removeEventListener('mousedown', h);
  }, []);

  const handleExport = async (fmt) => {
    setLoading(fmt); setOpen(false);
    try {
      const res = await api.post('/export', { content, fmt, title: 'LipiCore Response' }, { responseType: 'blob' });
      const url = URL.createObjectURL(res.data);
      const a = document.createElement('a');
      a.href = url;
      const cd = res.headers['content-disposition'] || '';
      const fn = cd.match(/filename="(.+?)"/);
      a.download = fn ? fn[1] : `response.${fmt}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (_) {
      // Export failures leave the response visible; the user can retry.
    }
    finally { setLoading(null); }
  };

  return (
    <div className="relative" ref={ref}>
      <button onClick={() => setOpen(v => !v)} disabled={!!loading}
        className="flex items-center gap-1 text-slate-400 hover:text-slate-900 text-[12px] transition-colors disabled:opacity-40">
        {loading
          ? <span className="w-3 h-3 border border-slate-300 border-t-slate-600 rounded-full animate-spin" />
          : <span className="material-symbols-outlined text-[15px]">download</span>
        }
        Export
      </button>
      {open && (
        <div className="absolute left-0 bottom-6 w-40 bg-white border border-slate-200 rounded-lg shadow-lg py-1 z-50">
          {EXPORT_FORMATS.map(({ fmt, label, icon }) => (
            <button key={fmt} onClick={() => handleExport(fmt)}
              className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-slate-700 hover:bg-slate-50 transition-colors">
              <span className="material-symbols-outlined text-[14px] text-slate-400">{icon}</span>
              {label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

const FILE_ACCEPT = '.pdf,.docx,.txt,.xlsx,.xls,.pptx,.ppt,.jpg,.jpeg,.png';

const MODEL_OPTIONS = [
  { value: null, label: 'Auto', icon: 'auto_awesome', description: 'Backend routes to the best local vLLM tier' },
  { value: 'gemma-4', label: 'Fast', icon: 'bolt', description: 'Gemma 4 4B on local vLLM' },
  { value: 'gemma-4-26b-4bit', label: 'Analyst', icon: 'psychology', description: 'Gemma 4 26B on local vLLM' },
];

// ── Markdown renderer ─────────────────────────────────────────────────────────
function inlineFormat(text) {
  if (!text) return null;
  const parts = [];
  let last = 0;
  const re = /(\*\*(.+?)\*\*|\*(.+?)\*|`(.+?)`)/g;
  let m;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) parts.push(<span key={last}>{text.slice(last, m.index).replace(/\*+/g, '')}</span>);
    if (m[2]) parts.push(<strong key={m.index} className="font-semibold">{m[2]}</strong>);
    else if (m[3]) parts.push(<em key={m.index}>{m[3]}</em>);
    else if (m[4]) parts.push(<code key={m.index} className="bg-slate-100 text-secondary px-1 rounded text-xs font-mono">{m[4]}</code>);
    last = m.index + m[0].length;
  }
  if (last < text.length) {
    const remaining = text.slice(last).replace(/\*+/g, '');
    if (remaining) parts.push(<span key={last}>{remaining}</span>);
  }
  return parts.length ? parts : text;
}

function renderMarkdown(text) {
  if (!text) return null;
  return text.split('\n').map((line, i) => {
    const t = line.trim();
    if (t.startsWith('### ')) return <h3 key={i} className="font-bold text-on-surface mt-3 mb-1 text-sm">{t.slice(4)}</h3>;
    if (t.startsWith('## '))  return <h2 key={i} className="font-bold text-on-surface mt-4 mb-1">{t.slice(3)}</h2>;
    if (t === '---')           return <hr key={i} className="border-slate-100 my-3" />;
    if (t.startsWith('• ') || t.startsWith('- ') || t.startsWith('* ')) {
      return <div key={i} className="flex items-start gap-2 ml-3 my-0.5 text-body-sm"><span className="text-secondary mt-0.5 flex-shrink-0">•</span><span>{inlineFormat(t.slice(2))}</span></div>;
    }
    if (/^\d+\.\s/.test(t)) {
      const num = t.match(/^(\d+)\./)[1];
      return <div key={i} className="flex items-start gap-2 ml-3 my-0.5 text-body-sm"><span className="text-secondary font-medium flex-shrink-0 w-4">{num}.</span><span>{inlineFormat(t.replace(/^\d+\.\s/, ''))}</span></div>;
    }
    if (t === '') return <div key={i} className="h-2" />;
    return <div key={i} className="text-body-sm leading-relaxed">{inlineFormat(line)}</div>;
  });
}

function safeJson(str, fallback) {
  try { return JSON.parse(str || 'null') ?? fallback; } catch { return fallback; }
}

function formatMessageTime(value) {
  const date = value ? new Date(value) : new Date();
  if (Number.isNaN(date.getTime())) return '';
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function documentLabel(doc) {
  return doc?.name || doc?.file_name || doc?.title || 'Document';
}

function activeDocumentId(doc) {
  const id = Number(doc?.document_id || doc?.id);
  return Number.isInteger(id) ? id : null;
}

function isExtractTextPrompt(text) {
  return /\b(?:extract|show|display|give|copy|read)\s+(?:me\s+)?(?:the\s+)?(?:raw\s+|full\s+|all\s+)?text\b|\b(?:ocr|text extraction|extracted text|raw text|full text)\b|(?:टेक्स्ट|पाठ|अक्षर)\s*(?:निकाल|देखा|देऊ)/i.test(text || '');
}

function deriveClientAnswerMetadata(message) {
  if (message?.answer_metadata) return message.answer_metadata;
  const sourceCount = message?.sources?.length || 0;
  const sourceVerification = message?.sources?.find(source => source?.citation_verification)?.citation_verification;
  if (sourceCount > 0) {
    return {
      mode: 'ask_knowledge',
      answer_type: 'official_source_backed',
      source_count: sourceCount,
      requires_sources: true,
      citation_verification: {
        status: sourceVerification || 'no_sources',
      },
    };
  }
  return null;
}

const CAPACITY_ERROR_MARKERS = [
  'AI engine is busy',
  'Error connecting to AI engine',
  'AI engine returned error',
];

function classifyStreamStatus(message) {
  if (!message) return null;
  const text = String(message);
  if (/queued behind/i.test(text)) {
    return {
      kind: 'queued',
      icon: 'pending_actions',
      label: text,
      detail: 'Your request is waiting for a local model slot.',
    };
  }
  if (/model workers are busy|request is queued/i.test(text)) {
    return {
      kind: 'busy',
      icon: 'hourglass_top',
      label: 'All model workers are busy',
      detail: 'BankAi will start when a local model slot is available.',
    };
  }
  if (/generating response/i.test(text)) {
    return {
      kind: 'generating',
      icon: 'bolt',
      label: 'Generating response',
      detail: 'The local model is writing the answer.',
    };
  }
  return {
    kind: 'status',
    icon: 'sync',
    label: text,
    detail: '',
  };
}

function isCapacityErrorText(text) {
  return CAPACITY_ERROR_MARKERS.some(marker => String(text || '').includes(marker));
}

function formatCapacityFailure(text) {
  if (String(text || '').includes('returned error')) {
    return '**AI capacity error.** The local model returned an error while generating the answer. Please retry, or choose the Fast model if the Analyst model is busy.';
  }
  if (String(text || '').includes('Error connecting')) {
    return '**AI connection error.** BankAi could not reach the local model worker. Please retry shortly.';
  }
  return '**AI capacity is busy.** The local model queue is full right now. Please retry shortly or use a shorter prompt.';
}

function capacityFailureMetadata(mode, reason) {
  return {
    mode,
    answer_type: 'capacity_busy',
    source_count: 0,
    requires_sources: false,
    failure_reason: reason,
    citation_verification: {
      status: 'no_sources',
      supported_sentence_count: 0,
      unsupported_sentence_count: 0,
      unsupported_sentences: [],
    },
  };
}

function welcomeMsg(branding) {
  return {
    id: 'welcome', role: 'assistant',
    content: `नमस्ते! I am **${branding.product_name}** — ${branding.welcome_message}\n\nUpload a document using the attachment icon below, or ask me anything about approved bank knowledge.`,
    sources: [], suggestions: [],
  };
}

// ── Main component ────────────────────────────────────────────────────────────
export default function ChatAssistant() {
  const [searchParams]  = useSearchParams();
  const navigate        = useNavigate();
  const outletCtx       = useOutletContext() || {};
  const language        = outletCtx.language || localStorage.getItem('language') || 'en';
  const branding        = useBranding();

  const [messages, setMessages]               = useState([]);
  const [input, setInput]                     = useState('');
  const [isLoading, setIsLoading]             = useState(false);
  const [sessionId, setSessionId]             = useState(null);
  const [sessions, setSessions]               = useState([]);
  const [activeDocuments, setActiveDocuments] = useState([]);
  const [streamingText, setStreamingText]     = useState('');
  const [statusMsg, setStatusMsg]             = useState('');
  const [queueState, setQueueState]           = useState(null);
  const [elapsedSeconds, setElapsedSeconds]   = useState(0);
  const [sidebarOpen, setSidebarOpen]         = useState(false);
  const [editingId, setEditingId]             = useState(null);
  const [editText, setEditText]               = useState('');
  const [userScrolled, setUserScrolled]       = useState(false);
  const [abortCtrl, setAbortCtrl]             = useState(null);
  const [selectedLLM, setSelectedLLM]         = useState(null);
  const [selectedMode, setSelectedMode]       = useState('ask_knowledge');

  const endRef      = useRef(null);
  const bodyRef     = useRef(null);
  const fileRef     = useRef(null);
  const textareaRef = useRef(null);
  const streamingTextRef = useRef('');
  const streamStartedAtRef = useRef(null);

  const allowedModes = branding.allowed_modes || CHAT_MODES.map(mode => mode.value);
  const selectedModeOption = modeByValue(selectedMode);
  const sourceMessage = [...messages].reverse().find(
    message => message.role === 'assistant' && (message.sources?.length || 0) > 0
  );
  const evidenceSources = sourceMessage?.sources || [];
  const showPromptChips = messages.length <= 1 && !isLoading;
  const promptChips = [
    { label: 'Policy answer', mode: 'ask_knowledge', text: 'What is the approved policy for ' },
    { label: 'Customer reply', mode: 'draft', text: 'Draft a customer care reply for ' },
    { label: 'Summarize circular', mode: 'summarize', text: 'Summarize this circular for branch staff: ' },
    { label: 'Translate to Nepali', mode: 'translate', text: 'Translate this into Nepali using banking terms: ' },
  ].filter(chip => allowedModes.includes(chip.mode));

  useEffect(() => {
    if (allowedModes.length > 0 && !allowedModes.includes(selectedMode)) {
      setSelectedMode(allowedModes[0]);
    }
  }, [allowedModes, selectedMode]);

  const scrollBottom = useCallback(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => { if (!userScrolled) scrollBottom(); }, [messages, streamingText, userScrolled, scrollBottom]);

  useEffect(() => {
    if (!isLoading || !streamStartedAtRef.current) return undefined;
    const timer = window.setInterval(() => {
      setElapsedSeconds(Math.floor((Date.now() - streamStartedAtRef.current) / 1000));
    }, 1000);
    return () => window.clearInterval(timer);
  }, [isLoading]);

  // ── Fetch sessions list ──────────────────────────────────────────────────
  const fetchSessions = useCallback(async () => {
    try { const r = await api.get('/chat/sessions'); setSessions(r.data); } catch (_) {
      // Session refresh failures are non-blocking for the active chat.
    }
  }, []);

  // ── Load a session ───────────────────────────────────────────────────────
  const loadSession = useCallback(async (id) => {
    try {
      setSessionId(id);
      localStorage.setItem(LAST_CHAT_SESSION_KEY, String(id));
      setSidebarOpen(false);
      setActiveDocuments([]);  // Clear stale documents immediately

      const [msgR, sessR] = await Promise.all([
        api.get(`/chat/sessions/${id}/messages`),
        api.get(`/chat/sessions/${id}`),
      ]);
      const loaded = msgR.data.map(m => ({
        id: m.id, role: m.role, content: m.content,
        sources: safeJson(m.sources_json, []),
        suggestions: safeJson(m.suggestions_json, []),
        answer_metadata: deriveClientAnswerMetadata({
          sources: safeJson(m.sources_json, []),
          answer_metadata: safeJson(m.answer_metadata_json, null),
        }),
        created_at: m.created_at,
      }));
      if (loaded.length === 0) loaded.unshift(welcomeMsg(branding));
      setMessages(loaded);

      // Restore active session documents (only for this session)
      const activeIds = safeJson(sessR.data.active_document_ids_json, []);
      if (activeIds.length > 0 && sessR.data.id === id) {
        try {
          const docsR = await api.get('/documents?limit=200');
          const sessionDocs = docsR.data.filter(d =>
            activeIds.includes(d.id) && d.session_id === id && d.document_scope === 'session_upload'
          );
          setActiveDocuments(sessionDocs);
        } catch (_) {
          // Missing document metadata should not block loading chat history.
        }
      } else {
        setActiveDocuments([]);
      }
    } catch (err) { console.error('loadSession', err); }
  }, [branding]);

  const createNewSession = useCallback(async () => {
    try {
      const r = await api.post('/chat/sessions', { title: 'New Analysis' });
      setSessionId(r.data.id);
      localStorage.setItem(LAST_CHAT_SESSION_KEY, String(r.data.id));
      setActiveDocuments([]);
      setMessages([welcomeMsg(branding)]);
      navigate(`?session=${r.data.id}`);
      fetchSessions();
    } catch (_) {
      // The bootstrap flow will leave the existing screen in place on failure.
    }
  }, [branding, fetchSessions, navigate]);

  // ── Poll document status ────────────────────────────────────────────────
  useEffect(() => {
    if (activeDocuments.length === 0) return;

    const hasProcessing = activeDocuments.some(d =>
      !['ready','approved','indexed','failed'].includes(d.status)
    );
    if (!hasProcessing) {
      // All documents ready - clear any stale processing warnings
      setMessages(prev => prev.filter(m =>
        !m.content?.includes('is still being processed')
      ));
      return;
    }

    const pollInterval = setInterval(async () => {
      try {
        const ids = activeDocuments.map(d => d.id).join(',');
        const res = await api.get(`/documents?ids=${ids}&limit=200`);
        const updated = res.data.filter(d => activeDocuments.some(ad => ad.id === d.id));
        if (updated.length > 0) {
          setActiveDocuments(prev =>
            prev.map(d => updated.find(u => u.id === d.id) || d)
          );
          setMessages(prev => prev.map(message => {
            if (!message.attachments?.length) return message;
            return {
              ...message,
              attachments: message.attachments.map(file =>
                updated.find(u => activeDocumentId(u) === activeDocumentId(file)) || file
              ),
            };
          }));

          // Clear stale warnings if documents are now ready
          const allReady = updated.every(d => ['ready','approved','indexed'].includes(d.status));
          if (allReady) {
            setMessages(prev => prev.filter(m =>
              !m.content?.includes('is still being processed')
            ));
          }
        }
      } catch (err) {
        console.error('Failed to poll document status:', err.message);
      }
    }, 2000);

    return () => clearInterval(pollInterval);
  }, [activeDocuments]);

  // ── Bootstrap ────────────────────────────────────────────────────────────
  useEffect(() => {
    let cancelled = false;

    const init = async () => {
      const r = await api.get('/chat/sessions').catch(() => ({ data: [] }));
      const availableSessions = r.data || [];
      if (cancelled) return;
      setSessions(availableSessions);

      const sid = searchParams.get('session');
      const prompt = searchParams.get('prompt');
      if (sid) {
        await loadSession(Number(sid));
        if (prompt) setInput(decodeURIComponent(prompt));
        return;
      }

      const storedSessionId = Number(localStorage.getItem(LAST_CHAT_SESSION_KEY));
      const storedStillExists = availableSessions.some(session => session.id === storedSessionId);
      const nextSessionId = storedStillExists ? storedSessionId : availableSessions[0]?.id;

      if (nextSessionId) {
        navigate(`?session=${nextSessionId}`, { replace: true });
        await loadSession(nextSessionId);
        return;
      }

      await createNewSession();
    };

    init();
    return () => { cancelled = true; };
  }, [createNewSession, loadSession, navigate, searchParams]);

  // ── File upload ──────────────────────────────────────────────────────────
  const handleFileSelect = useCallback(async (file, sid = null) => {
    if (!file) return;

    let uploadSessionId = sid || sessionId;

    // Create session if needed
    if (!uploadSessionId) {
      try {
        const r = await api.post('/chat/sessions', { title: 'New Analysis' });
        uploadSessionId = r.data.id;
        setSessionId(uploadSessionId);
        navigate(`?session=${uploadSessionId}`);
      } catch (err) {
        console.error('Failed to create session:', err.response?.data || err.message);
        setActiveDocuments(prev => [...prev, {
          id: `tmp-${Date.now()}`, name: file.name, status: 'failed',
          processing_message: `Failed to create session: ${err.response?.data?.detail || err.message}`,
        }]);
        return;
      }
    }

    const tmpId = `tmp-${Date.now()}-${Math.random()}`;
    const tmpDoc = {
      id: tmpId, name: file.name, status: 'uploading',
      processing_progress: 0, processing_message: 'Uploading document...',
    };
    const uploadMessageId = `upload-${tmpId}`;
    setActiveDocuments(prev => [...prev, tmpDoc]);
    setMessages(prev => [...prev, {
      id: uploadMessageId,
      role: 'user',
      content: '',
      attachments: [tmpDoc],
      sources: [],
      suggestions: [],
      created_at: new Date().toISOString(),
    }]);

    try {
      const fd = new FormData();
      fd.append('file', file);
      const r = await api.post(`/chat/sessions/${uploadSessionId}/files`, fd);
      const uploadedDoc = { ...r.data, name: file.name, status: r.data.status || 'uploaded' };
      setActiveDocuments(prev =>
        prev.map(d => d.id === tmpId ? uploadedDoc : d)
      );
      setMessages(prev => prev.map(message =>
        message.id === uploadMessageId
          ? { ...message, attachments: [uploadedDoc] }
          : message
      ));
      setSelectedMode(current => current === 'ask_knowledge' ? 'analyze_file' : current);
      setInput(current => current || 'extract text');
      textareaRef.current?.focus();
    } catch (err) {
      const errorDetail = err.response?.data?.detail || err.message;
      const failedDoc = {
        ...tmpDoc,
        status: 'failed',
        processing_message: `Upload failed: ${errorDetail}`,
      };
      setActiveDocuments(prev =>
        prev.map(d => d.id === tmpId ? failedDoc : d)
      );
      setMessages(prev => prev.map(message =>
        message.id === uploadMessageId
          ? { ...message, attachments: [failedDoc] }
          : message
      ));
    }
  }, [sessionId, navigate]);

  // ── Handle drop zone files (parallel uploads) ────────────────────────────
  const handleDropZoneFiles = useCallback(async (files) => {
    const fileArray = Array.from(files);
    if (fileArray.length === 0) return;

    // Create session once if needed
    let uploadSessionId = sessionId;
    if (!uploadSessionId) {
      try {
        const r = await api.post('/chat/sessions', { title: 'New Analysis' });
        uploadSessionId = r.data.id;
        setSessionId(uploadSessionId);
        navigate(`?session=${uploadSessionId}`);
      } catch (err) {
        console.error('Failed to create session:', err.response?.data || err.message);
        return;
      }
    }

    // Upload with concurrency limit of 3
    const CONCURRENCY = 3;
    for (let i = 0; i < fileArray.length; i += CONCURRENCY) {
      const batch = fileArray.slice(i, i + CONCURRENCY);
      await Promise.all(batch.map(file => handleFileSelect(file, uploadSessionId)));
    }
  }, [sessionId, handleFileSelect, navigate]);

  // ── Handle file input ────────────────────────────────────────────────────
  const handleFileInput = useCallback(async (e) => {
    const files = Array.from(e.target.files || []);
    if (files.length > 0) {
      await handleDropZoneFiles(files);
    }
    if (fileRef.current) fileRef.current.value = '';
  }, [handleDropZoneFiles]);

  const { isDragging, dropHandlers } = useDropZone(handleDropZoneFiles);

  // ── Send / Stream ────────────────────────────────────────────────────────
  const handleSend = async (e, override) => {
    e?.preventDefault();
    const content = (override ?? input).trim();
    if (!content || isLoading || !sessionId) return;

    // Block only when every attached real document is still processing. Ready
    // documents remain queryable while other uploads finish in the background.
    const extractTextRequested = isExtractTextPrompt(content);
    const busy = activeDocuments.filter(
      d => !['ready','approved','indexed'].includes(d.status) && !String(d.id).startsWith('tmp')
    );
    const readyDocs = activeDocuments.filter(
      d => ['ready','approved','indexed'].includes(d.status) && !String(d.id).startsWith('tmp')
    );
    const queryDocs = extractTextRequested
      ? activeDocuments.filter(d => d.status !== 'failed' && !String(d.id).startsWith('tmp'))
      : readyDocs;
    const usedDocs = queryDocs.map(d => ({
      id: activeDocumentId(d),
      name: documentLabel(d),
      file_name: d.file_name,
      document_type: d.document_type,
      department: d.department,
    })).filter(d => d.id);
    if (busy.length && readyDocs.length === 0 && !extractTextRequested) {
      setMessages(prev => [...prev, {
        id: Date.now(), role: 'assistant', created_at: new Date().toISOString(),
        content: `⚠️ **${busy[0].name || busy[0].file_name}** is still being processed. Please wait for "Ready" status before asking questions about it.`,
        sources: [], suggestions: [],
      }]);
      return;
    }

    setMessages(prev => [...prev, {
      id: Date.now(),
      role: 'user',
      content,
      sources: [],
      suggestions: [],
      usedDocuments: usedDocs,
      created_at: new Date().toISOString(),
    }]);
    setInput('');
    if (textareaRef.current) { textareaRef.current.style.height = 'auto'; }
    setIsLoading(true);
    setStreamingText('');
    streamingTextRef.current = '';
    streamStartedAtRef.current = Date.now();
    setStatusMsg('');
    setQueueState(null);
    setElapsedSeconds(0);
    setUserScrolled(false);

    const ctrl = new AbortController();
    setAbortCtrl(ctrl);

    try {
      const resp = await fetch(`/api/chat/sessions/${sessionId}/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          message: content,
          language,
          active_document_ids: usedDocs.map(d => d.id),
          mode: selectedMode,
          ...(selectedLLM ? { model_override: selectedLLM } : {}),
        }),
        signal: ctrl.signal,
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);

      const reader  = resp.body.getReader();
      const decoder = new TextDecoder();
      let fullText = '';
      let buffer   = '';
      let sources  = [];
      let suggestions = [];
      let answerMetadata = null;
      let capacityFailureReason = null;

      // eslint-disable-next-line no-constant-condition
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        for (const line of lines) {
          const t = line.trim();
          if (!t.startsWith('data: ')) continue;
          try {
            const data = JSON.parse(t.slice(6));
            if (data.type === 'status') {
              const message = data.message || '';
              setStatusMsg(message);
              setQueueState(classifyStreamStatus(message));
            }
            else if (data.token) {
              if (isCapacityErrorText(data.token)) {
                capacityFailureReason = data.token;
                fullText = formatCapacityFailure(data.token);
              } else {
                fullText += data.token;
              }
              streamingTextRef.current = fullText;
              setStreamingText(fullText);
              setStatusMsg('');
            }
            if (data.sources)     sources     = data.sources;
            if (data.suggestions) suggestions = data.suggestions;
            if (data.answer_metadata) answerMetadata = data.answer_metadata;
          } catch (_) {
            // Ignore malformed SSE lines and continue reading the stream.
          }
        }
      }

      setMessages(prev => [...prev, {
        id: Date.now() + 1, role: 'assistant',
        content: fullText || 'No response received.',
        sources, suggestions,
        answer_metadata: capacityFailureReason
          ? capacityFailureMetadata(selectedMode, capacityFailureReason)
          : answerMetadata || deriveClientAnswerMetadata({ sources }),
        created_at: new Date().toISOString(),
      }]);
      fetchSessions();
    } catch (err) {
      if (err.name === 'AbortError') {
        setMessages(prev => [...prev, {
          id: Date.now() + 1, role: 'assistant',
          content: (streamingTextRef.current || '') + '\n\n*(Generation stopped)*',
          sources: [], suggestions: [],
          created_at: new Date().toISOString(),
        }]);
      } else {
        setMessages(prev => [...prev, {
          id: Date.now() + 1, role: 'assistant',
          content: 'Connection error. Please check the AI engine and try again.',
          sources: [], suggestions: [],
          created_at: new Date().toISOString(),
        }]);
      }
    } finally {
      setIsLoading(false); setStreamingText(''); streamingTextRef.current = ''; streamStartedAtRef.current = null; setStatusMsg(''); setQueueState(null); setElapsedSeconds(0); setAbortCtrl(null);
    }
  };

  const stopGeneration = () => abortCtrl?.abort();

  const regenerate = async (idx) => {
    const prevUser = [...messages].slice(0, idx).reverse().find(m => m.role === 'user');
    if (!prevUser) return;
    setMessages(prev => prev.slice(0, idx));
    await handleSend(null, prevUser.content);
  };

  const startEdit = (msg) => { setEditingId(msg.id); setEditText(msg.content); };
  const submitEdit = async (idx) => {
    if (!editText.trim()) return;
    setMessages(prev => prev.slice(0, idx));
    setEditingId(null);
    await handleSend(null, editText.trim());
  };

  const selectedModelOption = MODEL_OPTIONS.find(option => option.value === selectedLLM) || MODEL_OPTIONS[0];

  return (
    <div className="flex h-full overflow-hidden">
      {/* Main chat */}
      <div className="flex-1 flex flex-col bg-white border-r border-slate-200 min-w-0">

        {/* Sub-header */}
        <div className="flex items-center justify-between px-3 sm:px-6 py-2 border-b border-slate-200 flex-shrink-0 gap-2 lg:gap-4 flex-wrap">
          <div className="flex items-center gap-2 min-w-0">
            <div className="w-7 h-7 bg-primary-container rounded flex items-center justify-center flex-shrink-0">
              <span className="material-symbols-outlined text-white text-[15px]" style={{ fontVariationSettings: "'FILL' 1" }}>{selectedModeOption.icon}</span>
            </div>
            <div className="min-w-0">
              <span className="font-semibold text-on-surface text-sm truncate max-w-xs block">
                {sessions.find(s => s.id === sessionId)?.title || 'New Analysis'}
              </span>
              <span className="text-[10px] text-slate-500 font-label-caps uppercase tracking-wider">{selectedModeOption.label}</span>
            </div>
          </div>
          <div className="flex items-center gap-2 lg:gap-3 flex-wrap justify-end">
            {/* LLM Model Selector */}
            <div className="flex items-center gap-1">
              <div className="relative group">
                <button className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:text-slate-900 hover:bg-slate-100 rounded border border-slate-200 transition-colors">
                  <span className="material-symbols-outlined text-[14px]">{selectedModelOption.icon}</span>
                  <span className="max-w-[150px] truncate">{selectedModelOption.label}</span>
                  <span className="material-symbols-outlined text-[12px]">expand_more</span>
                </button>
                <div className="absolute right-0 top-8 w-64 bg-white border border-slate-200 rounded-lg shadow-lg py-1 z-50 hidden group-hover:block">
                  {MODEL_OPTIONS.map(option => (
                    <button key={option.label} onClick={() => setSelectedLLM(option.value)}
                      className={`w-full flex items-start gap-2 px-3 py-2.5 text-xs transition-colors ${selectedLLM === option.value ? 'bg-primary/10 text-primary font-semibold' : 'text-slate-700 hover:bg-slate-50'}`}>
                      <span className="material-symbols-outlined text-[14px] mt-0.5">{option.icon}</span>
                      <div className="flex-1 text-left">
                        <div className="font-semibold">{option.label}</div>
                        <div className="text-[10px] text-slate-500 mt-0.5">{option.description}</div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-1 border-l border-slate-200 pl-3">
              <button onClick={createNewSession} className="flex items-center gap-1 text-xs border border-slate-200 px-3 py-1.5 rounded hover:bg-slate-50 transition-colors text-slate-600">
                <span className="material-symbols-outlined text-[15px]">add_comment</span> New
              </button>
              <button onClick={() => setSidebarOpen(v => !v)} className="p-1.5 text-slate-500 hover:text-on-surface hover:bg-slate-100 rounded">
                <span className="material-symbols-outlined text-[20px]">history</span>
              </button>
            </div>
          </div>
        </div>

        {/* Messages */}
        <div
          ref={bodyRef}
          {...dropHandlers}
          onScroll={() => {
            const el = bodyRef.current;
            if (el) setUserScrolled(el.scrollHeight - el.scrollTop - el.clientHeight > 80);
          }}
          className={`flex-1 overflow-y-auto px-3 sm:px-gutter py-lg sm:py-xl hide-scrollbar relative transition-colors ${isDragging ? 'bg-primary/5' : ''}`}
        >
          {isDragging && (
            <div className="absolute inset-0 flex items-center justify-center bg-primary/10 backdrop-blur-sm pointer-events-none z-40 rounded-lg border-2 border-dashed border-primary">
              <div className="flex flex-col items-center gap-2">
                <span className="material-symbols-outlined text-primary text-5xl">attach_file</span>
                <p className="text-primary font-semibold">Drop document to attach</p>
              </div>
            </div>
          )}
          <div className="max-w-3xl mx-auto space-y-6 sm:space-y-8">
            {messages.map((msg, idx) => (
              <MsgBubble key={msg.id} msg={msg} idx={idx}
                isLast={idx === messages.length - 1} isLoading={isLoading}
                editingId={editingId} editText={editText} setEditText={setEditText}
                onCopy={(t) => navigator.clipboard.writeText(t)}
                onRegenerate={regenerate}
                onEdit={startEdit}
                onSubmitEdit={submitEdit}
                onCancelEdit={() => setEditingId(null)}
                onSuggestion={(s) => handleSend(null, s)}
              />
            ))}

            {isLoading && statusMsg && !streamingText && (
              <div className="flex gap-4 items-center">
                <AiBadge />
                <QueueStatusIndicator
                  status={queueState}
                  fallback={statusMsg}
                  elapsedSeconds={elapsedSeconds}
                />
              </div>
            )}

            {isLoading && streamingText && (
              <div className="flex gap-4">
                <AiBadge />
                <div className="flex-1 text-body-sm text-on-surface leading-relaxed">
                  {renderMarkdown(streamingText)}
                  <span className="streaming-cursor" />
                </div>
              </div>
            )}

            {isLoading && !streamingText && !statusMsg && (
              <div className="flex gap-4 items-center">
                <AiBadge />
                <div className="flex items-center gap-2">
                  <span className="text-body-sm text-slate-500 italic">{branding.product_name} is analyzing your documents…</span>
                  <ThinkingDots />
                </div>
              </div>
            )}

            <div ref={endRef} className="h-4" />
          </div>
        </div>

        {/* Jump-to-bottom */}
        {userScrolled && (
          <button onClick={() => { setUserScrolled(false); scrollBottom(); }}
            className="absolute bottom-28 right-4 lg:right-96 p-2 bg-white border border-slate-200 rounded-full shadow-floating text-slate-500 hover:text-on-surface z-10">
            <span className="material-symbols-outlined text-[20px]">keyboard_arrow_down</span>
          </button>
        )}

        {/* Footer input */}
        <footer className="p-3 sm:p-6 bg-white border-t border-slate-200 flex-shrink-0">
          <div className="max-w-3xl mx-auto space-y-3">
            <ChatModeSelector
              allowedModes={allowedModes}
              selectedMode={selectedMode}
              onChange={setSelectedMode}
              disabled={isLoading}
            />

            {showPromptChips && promptChips.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {promptChips.map(chip => (
                  <button
                    key={chip.label}
                    type="button"
                    onClick={() => {
                      setSelectedMode(chip.mode);
                      setInput(chip.text);
                      textareaRef.current?.focus();
                    }}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-50 border border-slate-200 rounded text-xs text-slate-600 hover:border-secondary hover:text-secondary transition-colors"
                  >
                    <span className="material-symbols-outlined text-[14px]">{modeByValue(chip.mode).icon}</span>
                    {chip.label}
                  </button>
                ))}
              </div>
            )}

            <div className="relative">
              <button type="button" onClick={() => {
                fileRef.current?.click();
              }}
                className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-900 transition-colors p-1"
                disabled={isLoading}>
                <span className="material-symbols-outlined text-[22px]">attachment</span>
              </button>
              <input type="file" ref={fileRef} onChange={handleFileInput} className="hidden" accept={FILE_ACCEPT} data-testid="file-upload" multiple />
              <textarea
                data-testid="chat-input"
                ref={textareaRef}
                value={input}
                onChange={(e) => {
                  setInput(e.target.value);
                  e.target.style.height = 'auto';
                  e.target.style.height = Math.min(e.target.scrollHeight, 160) + 'px';
                }}
                onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(e); } }}
                placeholder={activeDocuments.length > 0
                  ? `Ask about ${activeDocuments.map(d => d.name || d.file_name).slice(0, 2).join(', ')} in English or नेपाली...`
                  : `${selectedModeOption.prompt || `Ask ${branding.product_name}...`}`}
                className="w-full pl-12 pr-20 sm:pr-28 py-4 bg-slate-100 border-none focus:ring-2 focus:ring-secondary/20 rounded font-body-sm text-on-surface placeholder:text-slate-400 resize-none min-h-[56px] max-h-[160px] leading-relaxed outline-none"
                rows={1}
                disabled={isLoading && !abortCtrl}
              />
              <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1">
                {isLoading ? (
                  <button onClick={stopGeneration}
                    className="flex items-center gap-1.5 px-3 py-1.5 border border-error/20 text-error hover:bg-error/5 rounded text-xs font-bold transition-colors">
                    <span className="material-symbols-outlined text-[16px]">stop_circle</span> STOP
                  </button>
                ) : (
                  <button onClick={handleSend} disabled={!input.trim()}
                    className="bg-primary text-white p-2.5 rounded shadow-sm hover:opacity-90 active:scale-95 transition-all disabled:opacity-40">
                    <span className="material-symbols-outlined text-[20px]">send</span>
                  </button>
                )}
              </div>
            </div>

            <p className="text-center text-[10px] text-slate-400 font-label-caps tracking-widest uppercase">
              Encrypted in transit · Private cloud environment
            </p>
          </div>
        </footer>
      </div>

      <SourceEvidencePanel sources={evidenceSources} />

      {/* History sidebar */}
      {sidebarOpen && (
        <div className="w-72 flex flex-col bg-slate-50 border-l border-slate-200 flex-shrink-0 animate-slide-in">
          <div className="h-14 flex items-center justify-between px-4 border-b border-slate-200 bg-white">
            <h3 className="font-semibold text-on-surface text-sm">Chat History</h3>
            <button onClick={() => setSidebarOpen(false)} className="p-1 text-slate-400 hover:text-on-surface rounded hover:bg-slate-100">
              <span className="material-symbols-outlined text-[18px]">close</span>
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-2 space-y-0.5">
            {sessions.map(sess => {
              const activeDocs = safeJson(sess.active_document_ids_json, []);
              return (
                <button key={sess.id} onClick={() => loadSession(sess.id)}
                  className={`w-full text-left p-3 rounded transition-colors ${sessionId === sess.id ? 'bg-white ring-1 ring-slate-200 shadow-sm text-on-surface' : 'text-slate-600 hover:bg-white hover:text-on-surface'}`}>
                  <div className="flex items-start gap-2">
                    <span className="material-symbols-outlined text-[15px] mt-0.5 text-outline flex-shrink-0">chat_bubble_outline</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-semibold truncate">{sess.title}</p>
                      {activeDocs.length > 0 && (
                        <p className="text-[10px] text-outline mt-0.5">{activeDocs.length} file{activeDocs.length !== 1 ? 's' : ''} attached</p>
                      )}
                      <p className="text-[10px] text-outline mt-0.5">{new Date(sess.created_at).toLocaleDateString()}</p>
                    </div>
                  </div>
                </button>
              );
            })}
            {sessions.length === 0 && <p className="text-xs text-slate-400 text-center mt-6">No history yet</p>}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Sub-components ────────────────────────────────────────────────────────────
function AiBadge() {
  return (
    <div className="w-9 h-9 flex-shrink-0 bg-primary-container rounded flex items-center justify-center mt-1">
      <span className="material-symbols-outlined text-white text-[18px]" style={{ fontVariationSettings: "'FILL' 1" }}>bolt</span>
    </div>
  );
}

function ThinkingDots() {
  return (
    <div className="flex gap-1">
      <div className="w-1.5 h-1.5 bg-slate-400 rounded-full typing-dot" />
      <div className="w-1.5 h-1.5 bg-slate-400 rounded-full typing-dot" />
      <div className="w-1.5 h-1.5 bg-slate-400 rounded-full typing-dot" />
    </div>
  );
}

function QueueStatusIndicator({ status, fallback, elapsedSeconds }) {
  const active = status || classifyStreamStatus(fallback);
  const label = active?.label || fallback || 'Working';
  const detail = active?.detail || 'Please keep this chat open while the response is generated.';
  const isQueued = active?.kind === 'queued' || active?.kind === 'busy';
  const elapsedLabel = elapsedSeconds >= 10 ? `${elapsedSeconds}s elapsed` : null;

  return (
    <div className={`min-w-0 max-w-xl border rounded px-3 py-2 ${isQueued ? 'bg-amber-50 border-amber-200' : 'bg-slate-50 border-slate-200'}`}>
      <div className="flex items-center gap-2 min-w-0">
        <span className={`material-symbols-outlined text-[18px] ${isQueued ? 'text-amber-600' : 'text-slate-500'}`}>{active?.icon || 'sync'}</span>
        <span className={`text-body-sm font-medium truncate ${isQueued ? 'text-amber-900' : 'text-slate-700'}`}>{label}</span>
        <ThinkingDots />
      </div>
      <div className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-[11px] text-slate-500">
        <span>{detail}</span>
        {elapsedLabel && <span className="font-semibold text-slate-600">{elapsedLabel}</span>}
      </div>
    </div>
  );
}

function MsgBubble({ msg, idx, isLast, isLoading, editingId, editText, setEditText,
  onCopy, onRegenerate, onEdit, onSubmitEdit, onCancelEdit, onSuggestion }) {
  const isUser    = msg.role === 'user';
  const isEditing = editingId === msg.id;
  const attachments = msg.attachments || [];

  return (
    <div className={`flex ${isUser ? 'flex-col items-end' : 'gap-4'} group`}>
      {!isUser && <AiBadge />}
      <div className={isUser ? 'max-w-[78%]' : 'flex-1'}>
        {isEditing ? (
          <div className="space-y-2">
            <textarea value={editText} onChange={e => setEditText(e.target.value)} autoFocus
              className="w-full bg-slate-50 border border-secondary/30 rounded px-3 py-2 text-body-sm resize-none focus:outline-none focus:ring-1 focus:ring-secondary" rows={3} />
            <div className="flex gap-2 justify-end">
              <button onClick={onCancelEdit} className="px-3 py-1 text-xs border border-slate-200 rounded hover:bg-slate-50">Cancel</button>
              <button onClick={() => onSubmitEdit(idx)} className="px-3 py-1 text-xs bg-primary text-white rounded hover:opacity-90">Send</button>
            </div>
          </div>
        ) : (
          <div className={isUser ? 'bg-white border border-slate-200 rounded shadow-card p-4' : 'space-y-3'}>
            {!isUser && <AnswerTrustBadge message={msg} />}

            {attachments.length > 0 && (
              <div className="space-y-2 mb-2" data-testid="message-attachments">
                {attachments.map(file => (
                  <FilePreviewCard key={file.id || file.document_id || file.name || file.file_name} file={file} />
                ))}
              </div>
            )}

            {isUser
              ? (msg.content ? <p className="text-body-sm text-on-surface leading-relaxed" data-testid="message-content">{msg.content}</p> : null)
              : <div className="text-body-sm text-on-surface" data-testid="message-content">{renderMarkdown(msg.content)}</div>
            }

            {!isUser && msg.sources && msg.sources.length > 0 && (
              <SourceEvidencePanel sources={msg.sources} compact />
            )}

            {/* Action bar — assistant */}
            {!isUser && msg.id !== 'welcome' && (
              <div className="flex items-center gap-4 pt-2 border-t border-slate-100 opacity-0 group-hover:opacity-100 transition-opacity">
                <button onClick={() => onCopy(msg.content)} className="flex items-center gap-1 text-slate-400 hover:text-slate-900 text-[12px] transition-colors">
                  <span className="material-symbols-outlined text-[15px]">content_copy</span> Copy
                </button>
                <button onClick={() => onRegenerate(idx)} disabled={isLoading}
                  className="flex items-center gap-1 text-slate-400 hover:text-slate-900 text-[12px] transition-colors disabled:opacity-40">
                  <span className="material-symbols-outlined text-[15px]">refresh</span> Regenerate
                </button>
                <ChatExportButton content={msg.content} />
              </div>
            )}

            {/* Edit button — user */}
            {isUser && msg.id !== 'welcome' && (
              <div className="flex justify-end mt-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <button onClick={() => onEdit(msg)} className="flex items-center gap-1 text-slate-400 hover:text-slate-900 text-[11px]">
                  <span className="material-symbols-outlined text-[13px]">edit</span> Edit
                </button>
              </div>
            )}

            {/* Timestamp */}
            {isUser && (
              <div className="text-[10px] text-slate-400 text-right font-label-caps uppercase mt-1">
                {formatMessageTime(msg.created_at)} · EN
              </div>
            )}
          </div>
        )}

        {/* Follow-up suggestions */}
        {!isUser && msg.suggestions && msg.suggestions.length > 0 && isLast && !isLoading && (
          <div className="flex flex-wrap gap-2 mt-3">
            {msg.suggestions.map((s, i) => (
              <button key={i} onClick={() => onSuggestion(s)}
                className="px-3 py-1.5 text-xs bg-white border border-slate-200 text-slate-700 hover:border-secondary hover:text-secondary rounded transition-colors text-left">
                {s}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
