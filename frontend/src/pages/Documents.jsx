import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/axios';
import useDropZone from '../hooks/useDropZone';

export default function Documents() {
  const navigate = useNavigate();
  const [docs, setDocs] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [uploadQueue, setUploadQueue] = useState([]);
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [analysisJobs, setAnalysisJobs] = useState([]);
  const [analysisModalDoc, setAnalysisModalDoc] = useState(null);
  const [analysisPrompt, setAnalysisPrompt] = useState('');
  const [analysisSubmitting, setAnalysisSubmitting] = useState(false);
  const [analysisError, setAnalysisError] = useState('');
  const [analysisResultJob, setAnalysisResultJob] = useState(null);
  const fileInputRef = useRef(null);
  const mainRef = useRef(null);
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  const canApprove = ['super_admin', 'bank_admin', 'compliance_user', 'compliance_officer', 'document_reviewer'].includes(user.role);
  const canReviewBankDocs = canApprove;

  // Fetch documents
  const fetchDocs = useCallback(async () => {
    try {
      setLoading(true);
      const r = await api.get('/documents?limit=200');
      setDocs(r.data);
    } catch (_) {}
    setLoading(false);
  }, []);

  const fetchAnalysisJobs = useCallback(async () => {
    try {
      const r = await api.get('/long-document-analysis?limit=100');
      setAnalysisJobs(r.data || []);
    } catch (_) {}
  }, []);

  useEffect(() => {
    fetchDocs();
    fetchAnalysisJobs();
  }, [fetchDocs, fetchAnalysisJobs]);

  const activeAnalysisCount = useMemo(
    () => analysisJobs.filter(job => !['completed', 'failed'].includes(job.status)).length,
    [analysisJobs]
  );

  useEffect(() => {
    if (activeAnalysisCount === 0) return;
    const poll = setInterval(fetchAnalysisJobs, 3000);
    return () => clearInterval(poll);
  }, [activeAnalysisCount, fetchAnalysisJobs]);

  // Handle file drops and selections (parallel with concurrency limit)
  const handleFiles = useCallback(async (files) => {
    const fileArray = Array.from(files);
    const tmpIds = fileArray.map((f, i) => ({ file: f, tmpId: `tmp-${Date.now()}-${i}` }));

    // Add all files to queue at once
    setUploadQueue(prev => [
      ...prev,
      ...tmpIds.map(({ file, tmpId }) => ({
        id: tmpId,
        name: file.name,
        status: 'uploading',
        progress: 0,
      }))
    ]);

    // Upload with concurrency limit of 3
    const CONCURRENCY = 3;
    for (let i = 0; i < tmpIds.length; i += CONCURRENCY) {
      const batch = tmpIds.slice(i, i + CONCURRENCY);
      await Promise.all(
        batch.map(async ({ file, tmpId }) => {
          try {
            const fd = new FormData();
            fd.append('file', file);
            const r = await api.post('/documents/upload', fd);
            setUploadQueue(prev =>
              prev.map(u => u.id === tmpId ? { ...r.data, status: 'uploaded', progress: 0 } : u)
            );
          } catch (err) {
            setUploadQueue(prev =>
              prev.map(u => u.id === tmpId ? { ...u, status: 'failed' } : u)
            );
          }
        })
      );
    }
  }, []);

  const { isDragging, dropHandlers } = useDropZone(handleFiles);

  // Stable uploadingIds for polling (prevents interval recreation)
  const uploadingIds = useMemo(
    () => uploadQueue
      .filter(u => !String(u.id).startsWith('tmp') && !['ready', 'approved', 'failed'].includes(u.status))
      .map(u => u.id),
    [uploadQueue]
  );

  // Poll document progress with stable dependency
  useEffect(() => {
    if (uploadingIds.length === 0) return;

    const poll = setInterval(async () => {
      try {
        const r = await api.get('/documents?limit=200');
        const updatedDocs = r.data.filter(d => uploadingIds.includes(d.id));
        if (updatedDocs.length > 0) {
          setUploadQueue(prev =>
            prev.map(item =>
              uploadingIds.includes(item.id)
                ? { ...item, ...updatedDocs.find(d => d.id === item.id) }
                : item
            )
          );
        }
      } catch (_) {}
    }, 2000);

    return () => clearInterval(poll);
  }, [uploadingIds]);

  // Approve document
  const handleApprove = async (docId) => {
    try {
      await api.patch(`/documents/${docId}/approve`);
      fetchDocs();
    } catch (_) {}
  };

  // Delete document
  const handleDelete = async (docId) => {
    if (!confirm('Delete this document? Cannot be undone.')) return;
    try {
      await api.delete(`/documents/${docId}`);
      fetchDocs();
    } catch (_) {}
  };

  // Bulk approve
  const handleBulkApprove = async () => {
    if (selectedIds.size === 0) return;
    if (!confirm(`Approve ${selectedIds.size} document(s)?`)) return;
    try {
      await Promise.all(Array.from(selectedIds).map(id => api.patch(`/documents/${id}/approve`)));
      setSelectedIds(new Set());
      fetchDocs();
    } catch (_) {}
  };

  // Bulk delete
  const handleBulkDelete = async () => {
    if (selectedIds.size === 0) return;
    if (!confirm(`Delete ${selectedIds.size} document(s)? Cannot be undone.`)) return;
    try {
      await Promise.all(Array.from(selectedIds).map(id => api.delete(`/documents/${id}`)));
      setSelectedIds(new Set());
      fetchDocs();
    } catch (_) {}
  };

  const defaultAnalysisPrompt = (doc) => {
    const ext = (doc?.file_type || '').toLowerCase();
    if (['xlsx', 'xls'].includes(ext)) {
      return 'Summarize the workbook, identify important sheets, totals, exceptions, missing values, formulas, and staff action points. Cite sheet names and cell ranges where possible.';
    }
    return 'Summarize the document, extract key rules, dates, exceptions, tables, risks, and staff action points. Cite page or section labels where possible.';
  };

  const canQueueLongAnalysis = (doc) => {
    if (!doc || ['disabled', 'archived', 'superseded', 'failed'].includes(doc.status)) return false;
    if (['disabled', 'archived', 'superseded'].includes(doc.version_state)) return false;
    if (canReviewBankDocs) return true;
    if (doc.document_scope === 'session_upload') {
      return ['ready', 'indexed', 'approved'].includes(doc.status) && doc.uploaded_by === user.id;
    }
    return doc.document_scope === 'global_knowledge' && doc.status === 'approved' && doc.version_state === 'approved';
  };

  const openAnalysisModal = (doc) => {
    setAnalysisModalDoc(doc);
    setAnalysisPrompt(defaultAnalysisPrompt(doc));
    setAnalysisError('');
  };

  const closeAnalysisModal = () => {
    setAnalysisModalDoc(null);
    setAnalysisPrompt('');
    setAnalysisError('');
  };

  const submitLongAnalysis = async () => {
    const prompt = analysisPrompt.trim();
    if (!analysisModalDoc || prompt.length < 3) {
      setAnalysisError('Enter a prompt before queueing.');
      return;
    }
    try {
      setAnalysisSubmitting(true);
      setAnalysisError('');
      await api.post('/long-document-analysis', {
        document_id: analysisModalDoc.id,
        prompt,
        analysis_type: ['xlsx', 'xls'].includes((analysisModalDoc.file_type || '').toLowerCase())
          ? 'spreadsheet_analysis'
          : 'long_document_analysis',
      });
      closeAnalysisModal();
      fetchAnalysisJobs();
    } catch (err) {
      setAnalysisError(err?.response?.data?.detail || 'Failed to queue analysis.');
    } finally {
      setAnalysisSubmitting(false);
    }
  };

  // Toggle selection
  const toggleSelect = (docId) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      if (next.has(docId)) next.delete(docId);
      else next.add(docId);
      return next;
    });
  };

  // Select all visible
  const toggleSelectAll = () => {
    if (selectedIds.size === filtered.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(filtered.map(d => d.id)));
    }
  };

  const filtered = docs.filter(d =>
    (d.file_name || '').toLowerCase().includes(search.toLowerCase()) && !String(d.id).startsWith('tmp')
  );

  const getIcon = (ext) => {
    const icons = {
      pdf: 'description',
      docx: 'article',
      doc: 'article',
      xlsx: 'table_chart',
      xls: 'table_chart',
      pptx: 'slideshow',
      ppt: 'slideshow',
      txt: 'text_snippet',
      jpg: 'image',
      jpeg: 'image',
      png: 'image',
    };
    return icons[ext?.toLowerCase()] || 'insert_drive_file';
  };

  const statusColor = (status) => {
    const colors = {
      uploaded: 'text-slate-500',
      queued: 'text-blue-600',
      processing: 'text-blue-600',
      extracting_text: 'text-blue-600',
      chunking: 'text-blue-600',
      embedding: 'text-blue-600',
      indexing: 'text-blue-600',
      indexed: 'text-green-600',
      ready: 'text-green-600',
      approved: 'text-green-700 font-bold',
      failed: 'text-red-600',
      disabled: 'text-slate-500',
    };
    return colors[status] || 'text-slate-500';
  };

  const statusMeta = (doc) => {
    const status = doc.status || 'uploaded';
    const map = {
      uploaded: { label: 'Uploaded', detail: 'Waiting for ingestion queue', icon: 'cloud_done', pct: 10 },
      queued: { label: 'Queued', detail: 'Waiting for worker capacity', icon: 'pending_actions', pct: 15 },
      processing: { label: 'Processing', detail: 'Preparing document', icon: 'sync', pct: doc.processing_progress || 25 },
      extracting_text: { label: 'Extracting text/OCR', detail: 'Reading pages, OCR, and tables', icon: 'document_scanner', pct: doc.processing_progress || 35 },
      chunking: { label: 'Chunking', detail: 'Splitting into searchable passages', icon: 'segment', pct: doc.processing_progress || 55 },
      embedding: { label: 'Embedding', detail: 'Creating vector search index', icon: 'hub', pct: doc.processing_progress || 70 },
      indexing: { label: 'Indexing', detail: 'Writing chunks to knowledge base', icon: 'database', pct: doc.processing_progress || 85 },
      indexed: { label: 'Ready for chat', detail: 'Indexed and retrievable', icon: 'forum', pct: 100 },
      ready: { label: 'Ready for review', detail: 'Processed, not yet approved', icon: 'fact_check', pct: 100 },
      approved: { label: 'Approved knowledge', detail: 'Available as official source', icon: 'verified', pct: 100 },
      failed: { label: 'Failed', detail: doc.processing_message || 'Ingestion failed', icon: 'error', pct: doc.processing_progress || 0 },
      disabled: { label: 'Disabled', detail: 'Hidden from retrieval', icon: 'visibility_off', pct: 0 },
    };
    return map[status] || { label: status, detail: doc.processing_message || 'Status pending', icon: 'description', pct: doc.processing_progress || 0 };
  };

  const latestAnalysisByDoc = useMemo(() => {
    const byDoc = new Map();
    analysisJobs.forEach(job => {
      if (!byDoc.has(job.document_id)) byDoc.set(job.document_id, job);
    });
    return byDoc;
  }, [analysisJobs]);

  const analysisJobMeta = (job) => {
    const map = {
      queued: { label: 'Queued', icon: 'pending_actions', className: 'bg-blue-50 text-blue-700 border-blue-200' },
      processing: { label: 'Processing', icon: 'sync', className: 'bg-blue-50 text-blue-700 border-blue-200' },
      packing_context: { label: 'Packing context', icon: 'inventory_2', className: 'bg-blue-50 text-blue-700 border-blue-200' },
      generating: { label: 'Generating', icon: 'auto_awesome', className: 'bg-violet-50 text-violet-700 border-violet-200' },
      completed: { label: 'Analysis ready', icon: 'task_alt', className: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
      failed: { label: 'Analysis failed', icon: 'error', className: 'bg-rose-50 text-rose-700 border-rose-200' },
    };
    return map[job?.status] || { label: job?.status || 'Analysis', icon: 'manage_search', className: 'bg-slate-50 text-slate-600 border-slate-200' };
  };

  const versionBadgeClass = (state) => {
    const map = {
      approved: 'bg-emerald-50 text-emerald-700 border-emerald-200',
      draft: 'bg-amber-50 text-amber-700 border-amber-200',
      superseded: 'bg-slate-100 text-slate-600 border-slate-200',
      archived: 'bg-slate-100 text-slate-600 border-slate-200',
      disabled: 'bg-rose-50 text-rose-700 border-rose-200',
    };
    return map[state] || 'bg-slate-50 text-slate-600 border-slate-200';
  };

  const isPastDate = (value) => {
    if (!value) return false;
    const parsed = new Date(value);
    return Number.isFinite(parsed.getTime()) && parsed < new Date();
  };

  const isFutureDate = (value) => {
    if (!value) return false;
    const parsed = new Date(value);
    return Number.isFinite(parsed.getTime()) && parsed > new Date();
  };

  const freshnessWarnings = (doc) => {
    const warnings = [];
    if (doc.version_state === 'superseded') warnings.push({ key: 'superseded', label: 'Superseded', icon: 'history', className: 'bg-slate-100 text-slate-700 border-slate-200' });
    if (isFutureDate(doc.effective_from)) warnings.push({ key: 'not-effective', label: 'Not effective yet', icon: 'event_upcoming', className: 'bg-sky-50 text-sky-800 border-sky-200' });
    if (isPastDate(doc.effective_to)) warnings.push({ key: 'expired', label: 'Expired', icon: 'event_busy', className: 'bg-rose-50 text-rose-800 border-rose-200' });
    if (isPastDate(doc.review_due_at)) warnings.push({ key: 'review-due', label: 'Review due', icon: 'pending_actions', className: 'bg-amber-50 text-amber-800 border-amber-200' });
    return warnings;
  };

  const analysisResultDoc = useMemo(
    () => docs.find(doc => doc.id === analysisResultJob?.document_id),
    [docs, analysisResultJob]
  );

  return (
    <div ref={mainRef} {...dropHandlers} className="flex h-full overflow-hidden bg-slate-50">
      {/* Drag overlay */}
      {isDragging && (
        <div className="fixed inset-0 bg-primary/10 border-2 border-dashed border-primary flex items-center justify-center z-40 pointer-events-none">
          <div className="flex flex-col items-center gap-2">
            <span className="material-symbols-outlined text-primary text-6xl">cloud_upload</span>
            <p className="text-primary font-semibold">Drop files to upload</p>
          </div>
        </div>
      )}

      {/* Main content */}
      <section className="flex-1 flex flex-col overflow-hidden">
        <div className="p-8 border-b border-slate-200 bg-white flex-shrink-0">
          <h1 className="text-2xl font-bold text-slate-900 mb-4">Documents</h1>

          {/* Upload zone */}
          <div className="p-6 border-2 border-dashed border-slate-300 rounded-lg bg-slate-50 hover:border-primary transition-colors">
            <div className="flex items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <span className="material-symbols-outlined text-primary text-3xl">cloud_upload</span>
                <div>
                  <p className="font-semibold text-slate-900">Drag files here</p>
                  <p className="text-sm text-slate-500">PDF, DOCX, images, spreadsheets...</p>
                </div>
              </div>
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".pdf,.docx,.doc,.txt,.xlsx,.xls,.pptx,.ppt,.jpg,.jpeg,.png"
                onChange={(e) => handleFiles(e.target.files || [])}
                className="hidden"
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                className="px-4 py-2 bg-primary text-white font-semibold rounded-lg hover:bg-primary/90 transition-colors whitespace-nowrap"
              >
                Choose Files
              </button>
            </div>
          </div>

          {/* Search */}
          <div className="mt-6 flex items-center gap-3">
            <div className="relative flex-1 max-w-xs">
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search documents..."
                className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/20 text-sm"
              />
              <span className="material-symbols-outlined absolute left-3 top-2.5 text-slate-400 text-[18px]">search</span>
            </div>
            {filtered.length > 0 && (
              <label className="flex items-center gap-2 text-sm text-slate-600 hover:text-slate-900 cursor-pointer">
                <input
                  type="checkbox"
                  checked={selectedIds.size === filtered.length && filtered.length > 0}
                  onChange={toggleSelectAll}
                  className="w-4 h-4 rounded border-slate-300 text-primary"
                />
                Select all
              </label>
            )}
          </div>
        </div>

        {/* Documents list */}
        <div className="flex-1 overflow-y-auto p-8">
          {loading ? (
            <div className="flex items-center justify-center h-32">
              <div className="text-center">
                <div className="w-8 h-8 border-2 border-slate-200 border-t-primary rounded-full animate-spin mx-auto mb-2" />
                <p className="text-sm text-slate-500">Loading documents...</p>
              </div>
            </div>
          ) : filtered.length === 0 ? (
            <div className="text-center py-16 text-slate-400">
              <span className="material-symbols-outlined text-5xl block mb-3">folder_open</span>
              <p className="text-sm">No documents yet. Drag files above to get started.</p>
            </div>
          ) : (
            <div className="space-y-2">
              {/* Bulk action bar */}
              {selectedIds.size > 0 && (
                <div className="sticky top-0 bg-primary/5 border-b border-primary/20 rounded-lg p-4 mb-4 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={selectedIds.size === filtered.length && filtered.length > 0}
                      onChange={toggleSelectAll}
                      className="w-5 h-5 rounded border-slate-300 text-primary"
                    />
                    <span className="font-semibold text-primary">{selectedIds.size} selected</span>
                  </div>
                  <div className="flex items-center gap-2">
                    {canApprove && (
                      <button
                        onClick={handleBulkApprove}
                        className="px-3 py-1.5 bg-green-50 text-green-700 font-semibold text-xs rounded hover:bg-green-100 transition-colors flex items-center gap-1"
                      >
                        <span className="material-symbols-outlined text-[14px]">check_circle</span>
                        Approve All
                      </button>
                    )}
                    <button
                      onClick={handleBulkDelete}
                      className="px-3 py-1.5 bg-red-50 text-red-700 font-semibold text-xs rounded hover:bg-red-100 transition-colors flex items-center gap-1"
                    >
                      <span className="material-symbols-outlined text-[14px]">delete</span>
                      Delete All
                    </button>
                  </div>
                </div>
              )}

              {filtered.map(doc => {
                const meta = statusMeta(doc);
                const isProcessing = ['uploaded', 'queued', 'processing', 'extracting_text', 'chunking', 'embedding', 'indexing'].includes(doc.status);
                const isReadyForChat = ['indexed', 'approved'].includes(doc.status);
                const warnings = freshnessWarnings(doc);
                const latestAnalysis = latestAnalysisByDoc.get(doc.id);
                const analysisMeta = analysisJobMeta(latestAnalysis);
                const analysisActive = latestAnalysis && !['completed', 'failed'].includes(latestAnalysis.status);
                return (
                <div
                  key={doc.id}
                  className={`grid grid-cols-[auto_auto_1fr_auto] items-center gap-4 p-4 bg-white border rounded-lg transition-all ${
                    selectedIds.has(doc.id)
                      ? 'border-primary bg-primary/5 shadow-sm'
                      : 'border-slate-200 hover:shadow-sm'
                  }`}
                  onClick={() => toggleSelect(doc.id)}
                >
                  {/* Checkbox */}
                  <input
                    type="checkbox"
                    checked={selectedIds.has(doc.id)}
                    onChange={() => toggleSelect(doc.id)}
                    onClick={(e) => e.stopPropagation()}
                    className="w-5 h-5 rounded border-slate-300 text-primary flex-shrink-0"
                  />

                  {/* File icon */}
                  <div className="w-10 h-10 rounded bg-slate-100 flex items-center justify-center flex-shrink-0">
                    <span className="material-symbols-outlined text-slate-600">{getIcon(doc.file_type)}</span>
                  </div>

                  {/* File info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="font-semibold text-slate-900 truncate text-sm">{doc.file_name}</p>
                      {isReadyForChat && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded text-[10px] font-bold uppercase">
                          <span className="material-symbols-outlined text-[12px]">forum</span>
                          Chat ready
                        </span>
                      )}
                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 border rounded text-[10px] font-bold uppercase ${versionBadgeClass(doc.version_state)}`}>
                        {doc.version_state || 'draft'}
                      </span>
                      {warnings.map(warning => (
                        <span key={warning.key} className={`inline-flex items-center gap-1 px-2 py-0.5 border rounded text-[10px] font-bold uppercase ${warning.className}`}>
                          <span className="material-symbols-outlined text-[12px]">{warning.icon}</span>
                          {warning.label}
                        </span>
                      ))}
                      {latestAnalysis && (
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 border rounded text-[10px] font-bold uppercase ${analysisMeta.className}`}>
                          <span className="material-symbols-outlined text-[12px]">{analysisMeta.icon}</span>
                          {analysisMeta.label}
                        </span>
                      )}
                    </div>
                    <div className="flex flex-wrap items-center gap-2 mt-1 text-xs">
                      <span className={`inline-flex items-center gap-1 font-semibold ${statusColor(doc.status)}`}>
                        <span className="material-symbols-outlined text-[14px]">{meta.icon}</span>
                        {meta.label}
                      </span>
                      <span className="text-slate-500">{doc.processing_message || meta.detail}</span>
                      {doc.document_type && doc.document_type !== 'other' && (
                        <span className="px-2 py-0.5 bg-primary/10 text-primary rounded font-semibold">
                          {doc.document_type}
                          {doc.department ? ` · ${doc.department}` : ''}
                        </span>
                      )}
                      <span className="px-2 py-0.5 bg-slate-100 text-slate-500 rounded font-semibold">
                        {doc.document_scope === 'session_upload' ? 'Chat upload' : 'Knowledge library'}
                      </span>
                      {(doc.regulator || doc.jurisdiction) && (
                        <span className="px-2 py-0.5 bg-slate-100 text-slate-500 rounded font-semibold">
                          {[doc.regulator, doc.jurisdiction].filter(Boolean).join(' · ')}
                        </span>
                      )}
                      <span className="text-slate-400">
                        {new Date(doc.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    {doc.summary && (
                      <p className="text-xs text-slate-500 mt-2 line-clamp-2">{doc.summary}</p>
                    )}
                    {latestAnalysis?.status === 'completed' && latestAnalysis.result_text && (
                      <button
                        type="button"
                        onClick={(e) => { e.stopPropagation(); setAnalysisResultJob(latestAnalysis); }}
                        className="mt-2 block w-full text-left border-l-2 border-emerald-300 pl-3 py-1 hover:bg-emerald-50 transition-colors"
                      >
                        <span className="block text-[10px] font-bold uppercase text-emerald-700">Long analysis ready</span>
                        <span className="block text-xs text-slate-600 line-clamp-2">{latestAnalysis.result_text}</span>
                      </button>
                    )}
                    {latestAnalysis?.status === 'failed' && latestAnalysis.error_message && (
                      <p className="text-xs text-rose-600 mt-2 line-clamp-2">{latestAnalysis.error_message}</p>
                    )}
                  </div>

                  {/* Progress bar (if processing) */}
                  {isProcessing && (
                    <div className="w-36 flex-shrink-0">
                      <div className="flex justify-between text-[10px] text-slate-500 mb-1">
                        <span>{meta.label}</span>
                        <span>{Math.max(0, Math.min(meta.pct || 0, 100))}%</span>
                      </div>
                      <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-primary transition-all duration-300"
                          style={{ width: `${Math.max(0, Math.min(meta.pct || 0, 100))}%` }}
                      />
                      </div>
                    </div>
                  )}

                  {/* Actions */}
                  {selectedIds.size === 0 && (
                    <div className="flex items-center gap-2 flex-shrink-0">
                      {latestAnalysis?.status === 'completed' && (
                        <button
                          onClick={(e) => { e.stopPropagation(); setAnalysisResultJob(latestAnalysis); }}
                          className="px-3 py-1 bg-emerald-50 text-emerald-700 font-semibold text-xs rounded hover:bg-emerald-100 transition-colors flex items-center gap-1"
                        >
                          <span className="material-symbols-outlined text-[14px]">visibility</span>
                          View
                        </button>
                      )}
                      {canQueueLongAnalysis(doc) && (
                        <button
                          onClick={(e) => { e.stopPropagation(); openAnalysisModal(doc); }}
                          disabled={analysisActive}
                          className={`px-3 py-1 font-semibold text-xs rounded transition-colors flex items-center gap-1 ${
                            analysisActive
                              ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
                              : 'bg-blue-50 text-blue-700 hover:bg-blue-100'
                          }`}
                        >
                          <span className="material-symbols-outlined text-[14px]">{analysisActive ? 'hourglass_top' : 'manage_search'}</span>
                          {analysisActive ? 'Queued' : 'Queue analysis'}
                        </button>
                      )}
                      {doc.status === 'ready' && canApprove && !doc.approved_by && (
                        <button
                          onClick={(e) => { e.stopPropagation(); handleApprove(doc.id); }}
                          className="px-3 py-1 bg-green-50 text-green-700 font-semibold text-xs rounded hover:bg-green-100 transition-colors flex items-center gap-1"
                        >
                          <span className="material-symbols-outlined text-[14px]">check_circle</span>
                          Approve
                        </button>
                      )}
                      {doc.approved_by && (
                        <span className="text-[10px] text-slate-500 font-semibold">
                          ✓ Approved
                        </span>
                      )}
                      <button
                        onClick={(e) => { e.stopPropagation(); handleDelete(doc.id); }}
                        className="p-1 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                        title="Delete"
                      >
                        <span className="material-symbols-outlined text-[18px]">delete</span>
                      </button>
                    </div>
                  )}
                </div>
              );
              })}
            </div>
          )}
        </div>
      </section>

      {analysisModalDoc && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/30 px-4">
          <div className="w-full max-w-2xl bg-white border border-slate-200 rounded-lg shadow-xl">
            <div className="flex items-start justify-between gap-4 p-5 border-b border-slate-200">
              <div className="min-w-0">
                <p className="text-sm font-bold text-slate-900 truncate">Queue long analysis</p>
                <p className="text-xs text-slate-500 truncate">{analysisModalDoc.file_name}</p>
              </div>
              <button
                type="button"
                onClick={closeAnalysisModal}
                disabled={analysisSubmitting}
                className="p-1 rounded text-slate-400 hover:text-slate-700 hover:bg-slate-100 disabled:opacity-50"
                title="Close"
              >
                <span className="material-symbols-outlined text-[20px]">close</span>
              </button>
            </div>
            <div className="p-5 space-y-4">
              <textarea
                value={analysisPrompt}
                onChange={(e) => setAnalysisPrompt(e.target.value)}
                rows={7}
                className="w-full resize-none rounded-lg border border-slate-200 p-3 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-primary/20"
                placeholder="Enter analysis prompt"
              />
              {analysisError && (
                <p className="text-xs font-semibold text-rose-600">{analysisError}</p>
              )}
            </div>
            <div className="flex items-center justify-end gap-2 p-5 border-t border-slate-200">
              <button
                type="button"
                onClick={closeAnalysisModal}
                disabled={analysisSubmitting}
                className="px-4 py-2 text-sm font-semibold text-slate-600 rounded-lg hover:bg-slate-100 disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={submitLongAnalysis}
                disabled={analysisSubmitting}
                className="px-4 py-2 text-sm font-semibold text-white bg-primary rounded-lg hover:bg-primary/90 disabled:opacity-50 inline-flex items-center gap-2"
              >
                {analysisSubmitting && <span className="w-3 h-3 border-2 border-white/40 border-t-white rounded-full animate-spin" />}
                Queue analysis
              </button>
            </div>
          </div>
        </div>
      )}

      {analysisResultJob && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/30 px-4">
          <div className="w-full max-w-3xl max-h-[82vh] bg-white border border-slate-200 rounded-lg shadow-xl flex flex-col">
            <div className="flex items-start justify-between gap-4 p-5 border-b border-slate-200 flex-shrink-0">
              <div className="min-w-0">
                <p className="text-sm font-bold text-slate-900 truncate">Long analysis result</p>
                <p className="text-xs text-slate-500 truncate">{analysisResultDoc?.file_name || `Document ${analysisResultJob.document_id}`}</p>
              </div>
              <button
                type="button"
                onClick={() => setAnalysisResultJob(null)}
                className="p-1 rounded text-slate-400 hover:text-slate-700 hover:bg-slate-100"
                title="Close"
              >
                <span className="material-symbols-outlined text-[20px]">close</span>
              </button>
            </div>
            <div className="p-5 overflow-y-auto">
              <pre className="whitespace-pre-wrap break-words text-sm leading-6 text-slate-800 font-sans">
                {analysisResultJob.result_text || analysisResultJob.error_message || ''}
              </pre>
            </div>
          </div>
        </div>
      )}

      {/* Upload queue toast */}
      {uploadQueue.filter(u => ['uploading', 'uploaded'].includes(u.status)).length > 0 && (
        <div className="fixed bottom-6 right-6 bg-white border border-slate-200 rounded-lg shadow-lg p-4 w-80 z-30">
          <p className="text-xs font-bold text-slate-500 uppercase mb-3">Uploading</p>
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {uploadQueue.filter(u => ['uploading', 'uploaded'].includes(u.status)).map(item => (
              <div key={item.id} className="flex items-center gap-2">
                <div className="w-6 h-6 rounded bg-slate-100 flex items-center justify-center flex-shrink-0 text-xs">
                  <span className="material-symbols-outlined text-[12px] text-slate-600">insert_drive_file</span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-semibold text-slate-900 truncate">{item.name}</p>
                  {item.status === 'uploading' && (
                    <div className="mt-0.5 h-1 bg-slate-200 rounded-full overflow-hidden">
                      <div className="h-full bg-primary transition-all duration-300" style={{ width: '100%' }} />
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
