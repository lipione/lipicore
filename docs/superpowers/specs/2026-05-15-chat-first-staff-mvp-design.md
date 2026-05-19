# Chat-First Staff MVP Design

## Goal

Turn the existing chat page into the first usable bank-wide staff assistant: one GPT-style interface, explicit task modes, visible answer trust, source evidence, and better white-label onboarding.

## Scope

This slice does not rebuild RAG, document governance, or appliance operations. It adds the user-facing contract those systems will later enforce more strictly.

## Product Behavior

Staff users use one chat screen for all common work:

- Ask approved bank knowledge.
- Analyze uploaded session files.
- Summarize text or documents.
- Draft internal staff communications.
- Translate banking text between English and Nepali.
- Compare documents or policies.

Each assistant answer shows a trust state:

- `Official source-backed`: approved knowledge was used.
- `Uploaded-file answer`: session-uploaded files were used.
- `General answer`: model output is not official bank policy.
- `Not found`: the selected mode needs sources, but no supporting source was found.
- `Escalate`: reserved for future policy routing.

## Frontend Design

The chat page remains the default product surface. Add a compact mode selector above the input, prompt chips for fast onboarding, answer trust badges above assistant responses, and a source evidence panel on the right side for source-backed answers. On smaller screens, sources stay inline below the answer.

The UI should feel operational and bank-grade: dense, clear, low-friction, and not a marketing landing page.

## Backend Design

Extend `ChatRequest` with a validated `mode`. The streaming and non-streaming chat endpoints pass the mode into the prompt and return lightweight answer metadata in the final response event. No database schema change is required for this slice; persisted history can derive trust from saved sources.

The full unified AI gateway remains a later milestone.

## Testing

Backend tests cover mode validation, default mode behavior, answer trust derivation, and prompt instructions. Frontend verification covers build/lint and browser rendering after deployment.
