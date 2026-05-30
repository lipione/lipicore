# Product UX Trust Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make LipiCore feel like an enterprise document-intelligence workbench where staff can verify answers, inspect sources, and understand limitations without leaving the workflow.

**Architecture:** Improve existing React pages rather than creating a separate app shell. Add reusable trust components for answer status, source metadata, confidence badges, and not-found states; then use them in chat, evaluations, OCR, and document source views.

**Tech Stack:** React/Vite, existing Tailwind classes, Material Symbols, FastAPI source metadata.

---

## File Structure

- Create: `frontend/src/components/trust/AnswerTrustBadge.jsx`
- Create: `frontend/src/components/trust/SourceMetadataStrip.jsx`
- Create: `frontend/src/components/trust/NotFoundState.jsx`
- Modify: `frontend/src/pages/ChatAssistant.jsx`
- Modify: `frontend/src/pages/EvaluationCenter.jsx`
- Modify: `frontend/src/pages/OcrExtraction.jsx`
- Modify: `frontend/src/pages/Documents.jsx`

## Task 1: Add Answer Trust Badge Component

**Files:**
- Create: `frontend/src/components/trust/AnswerTrustBadge.jsx`

- [ ] **Step 1: Create component**

Create `frontend/src/components/trust/AnswerTrustBadge.jsx`:

```jsx
const BADGES = {
  official_source_backed: {
    icon: 'verified',
    label: 'Source-backed',
    className: 'border-emerald-200 bg-emerald-50 text-emerald-700',
  },
  uploaded_file_answer: {
    icon: 'attach_file',
    label: 'Uploaded file',
    className: 'border-blue-200 bg-blue-50 text-blue-700',
  },
  not_found: {
    icon: 'search_off',
    label: 'Not found in approved sources',
    className: 'border-amber-200 bg-amber-50 text-amber-800',
  },
  unsupported_source: {
    icon: 'report',
    label: 'Needs source review',
    className: 'border-red-200 bg-red-50 text-red-700',
  },
  general_answer: {
    icon: 'info',
    label: 'General answer',
    className: 'border-slate-200 bg-slate-50 text-slate-700',
  },
};

export default function AnswerTrustBadge({ answerType, trustLabel }) {
  const badge = BADGES[answerType] || BADGES.general_answer;
  const label = trustLabel && trustLabel !== 'source_supported'
    ? `${badge.label} · ${trustLabel.replaceAll('_', ' ')}`
    : badge.label;

  return (
    <span className={`inline-flex items-center gap-1 rounded border px-2 py-0.5 text-xs font-semibold ${badge.className}`}>
      <span className="material-symbols-outlined text-[14px]">{badge.icon}</span>
      {label}
    </span>
  );
}
```

- [ ] **Step 2: Run frontend build**

Run:

```bash
cd frontend && npm run build
```

Expected: build exits `0`.

## Task 2: Add Source Metadata Strip

**Files:**
- Create: `frontend/src/components/trust/SourceMetadataStrip.jsx`

- [ ] **Step 1: Create component**

Create `frontend/src/components/trust/SourceMetadataStrip.jsx`:

```jsx
function confidenceLabel(value) {
  if (value === null || value === undefined) return null;
  return `${Math.round(Number(value) * 100)}%`;
}

export default function SourceMetadataStrip({ source }) {
  const items = [
    source?.page_number ? `Page ${source.page_number}` : null,
    source?.section_label || source?.section_number || null,
    source?.chunk_index !== null && source?.chunk_index !== undefined ? `Chunk ${source.chunk_index}` : null,
    confidenceLabel(source?.ocr_confidence) ? `OCR ${confidenceLabel(source.ocr_confidence)}` : null,
    confidenceLabel(source?.table_confidence) ? `Table ${confidenceLabel(source.table_confidence)}` : null,
    source?.citation_verification ? `Citation ${source.citation_verification}` : null,
  ].filter(Boolean);

  if (!items.length) return null;

  return (
    <div className="flex flex-wrap gap-2 text-xs text-slate-600">
      {items.map((item) => (
        <span key={item} className="rounded border border-slate-200 bg-slate-50 px-2 py-0.5">
          {item}
        </span>
      ))}
    </div>
  );
}
```

- [ ] **Step 2: Run frontend build**

Run:

```bash
cd frontend && npm run build
```

Expected: build exits `0`.

## Task 3: Add Not Found State

**Files:**
- Create: `frontend/src/components/trust/NotFoundState.jsx`

- [ ] **Step 1: Create component**

Create `frontend/src/components/trust/NotFoundState.jsx`:

```jsx
export default function NotFoundState({ mode }) {
  return (
    <div className="rounded border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
      <div className="flex items-center gap-2 font-semibold">
        <span className="material-symbols-outlined text-[18px]">search_off</span>
        Not found in approved sources
      </div>
      <p className="mt-1 text-amber-800">
        LipiCore did not find enough approved evidence for this request. Check document approval status, select the right uploaded file, or escalate to the responsible supervisor.
      </p>
      {mode && <p className="mt-2 text-xs font-semibold uppercase tracking-wide">Mode: {mode}</p>}
    </div>
  );
}
```

- [ ] **Step 2: Run frontend build**

Run:

```bash
cd frontend && npm run build
```

Expected: build exits `0`.

## Task 4: Wire Trust Components Into Chat

**Files:**
- Modify: `frontend/src/pages/ChatAssistant.jsx`

- [ ] **Step 1: Locate message rendering**

Run:

```bash
rg -n "messages.map|sources_json|answer_metadata|source" frontend/src/pages/ChatAssistant.jsx
```

Expected: identify assistant message rendering.

- [ ] **Step 2: Import components**

Add:

```jsx
import AnswerTrustBadge from '../components/trust/AnswerTrustBadge';
import SourceMetadataStrip from '../components/trust/SourceMetadataStrip';
import NotFoundState from '../components/trust/NotFoundState';
```

- [ ] **Step 3: Render answer badge**

Near assistant answer content, render:

```jsx
{message.answer_metadata && (
  <AnswerTrustBadge
    answerType={message.answer_metadata.answer_type}
    trustLabel={message.answer_metadata.trust_label}
  />
)}
```

- [ ] **Step 4: Render not-found state**

When metadata answer type is `not_found`, render:

```jsx
{message.answer_metadata?.answer_type === 'not_found' && (
  <NotFoundState mode={message.answer_metadata.mode} />
)}
```

- [ ] **Step 5: Render source metadata strip**

Inside source list rendering:

```jsx
<SourceMetadataStrip source={source} />
```

- [ ] **Step 6: Run frontend build**

Run:

```bash
cd frontend && npm run build
```

Expected: build exits `0`.

## Task 5: Use Source Metadata Strip In Evaluation Center

**Files:**
- Modify: `frontend/src/pages/EvaluationCenter.jsx`

- [ ] **Step 1: Import component**

Add:

```jsx
import SourceMetadataStrip from '../components/trust/SourceMetadataStrip';
```

- [ ] **Step 2: Render metadata under each source**

Inside the source result map, after the document title:

```jsx
<SourceMetadataStrip source={source} />
```

- [ ] **Step 3: Run frontend build**

Run:

```bash
cd frontend && npm run build
```

Expected: build exits `0`.

## Final Verification

- [ ] Run frontend build:

```bash
cd frontend && npm run build
```

- [ ] Run frontend lint if configured:

```bash
cd frontend && npm run lint
```

- [ ] Run diff check:

```bash
git diff --check
```

