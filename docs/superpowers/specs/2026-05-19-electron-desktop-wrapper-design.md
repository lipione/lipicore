# LipiCore Electron Desktop Wrapper Design

## Goal

Build a Phase 1 LipiCore Desktop app for macOS and Windows as a secure Electron wrapper around the existing hosted LipiCore web application.

The desktop app connects only to the LipiCore server. It does not run a local backend, database, vector database, object store, RAG pipeline, or model service on staff machines.

## Decisions

- Phase 1 platform support: macOS and Windows.
- Runtime mode: server-connected desktop client only.
- UI source: live hosted LipiCore web app, loaded from the fixed production URL.
- Default production URL: `https://ai.silverlining.com.np`.
- Internal staging/testing URL support is allowed through hidden developer/admin configuration, not visible to normal staff.
- Wrapper level: secure desktop wrapper with native desktop behavior.
- Downloads: all server-approved downloads are permitted.
- Clipboard and copy-paste: normal OS behavior; no wrapper-level blocking.

## Non-Goals

- Do not package FastAPI, PostgreSQL, Qdrant, MinIO, Redis, RAG, or LLM services inside Electron.
- Do not duplicate or fork the LipiCore React UI for Phase 1.
- Do not create offline RAG or offline document processing.
- Do not promise screenshot blocking, clipboard blocking, or OS-level data loss prevention in Phase 1.
- Do not move permission enforcement from the backend into Electron.

## Architecture

The desktop app is a thin Electron shell with two windows:

- A splash window shown at boot.
- A main browser window that loads the hosted LipiCore URL.

The splash window displays LipiCore branding, a logo animation, and connection/loading state. After the main window is ready, the splash fades out and the main app is shown.

The main window loads only allowed LipiCore domains. Unknown navigations are blocked or opened in the system browser. The web app remains the source of truth for authentication, authorization, chat, documents, RAG, and all business logic.

The Electron main process owns native desktop capabilities:

- Window lifecycle.
- Splash screen lifecycle.
- Tray/dock integration.
- App menu.
- Native notifications bridge where needed.
- Download handling.
- External-link routing.
- Idle/app lock shell behavior.
- Auto-update configuration.

The renderer has no Node.js access. A preload script is permitted only for a minimal, reviewed API surface.

## Desktop UX

The wrapper should feel like a real desktop app instead of a browser shortcut.

Required Phase 1 behavior:

- Boot splash with LipiCore logo animation.
- Main desktop window with remembered size and position.
- macOS dock behavior and Windows taskbar behavior.
- App icon for installer, taskbar/dock, and window.
- Native app menu with actions such as Reload, Lock LipiCore, Quit, and About.
- Tray support for Windows and menu bar/dock-friendly behavior for macOS.
- Native notifications for server/web notifications where browser notification permission is granted.
- External links open in the default system browser.
- In-app navigation stays within approved LipiCore domains.
- App lock hides visible content after an idle timeout or when the user selects Lock LipiCore.

The desktop layer should not redesign the full LipiCore product UI in Phase 1. It adds polished startup, native shell behavior, and desktop-safe controls around the existing web app.

## Files, Uploads, And Downloads

Uploads use the normal operating system file picker exposed through the web app.

Downloads are permitted when the LipiCore server allows them. The Electron wrapper should not add extra restrictions on downloads beyond backend authorization and server policy.

Download behavior:

- Use the native save flow where Electron download handling is needed.
- Preserve the filename supplied by the server when safe.
- Avoid silent background saves.
- Surface failed downloads clearly.
- Keep download auditing on the backend where the corresponding API supports it.

The wrapper must not create new bypass paths to files. It should only download files requested through authenticated LipiCore web/API flows.

## Security

Electron hardening is required:

- `contextIsolation: true`.
- `sandbox: true`.
- `nodeIntegration: false`.
- No remote module.
- No arbitrary preload APIs.
- Restrictive navigation allowlist.
- Deny or externalize unknown popups and new windows.
- Prefer HTTPS-only production loading.
- Use a strict Content Security Policy where wrapper-owned pages exist, especially the splash screen.

Session and storage behavior:

- Web session data remains in Electron's browser session storage.
- Any desktop-only secrets must use OS keychain/keychain-compatible storage.
- No auth token should be manually copied into plain local files.

Operational security:

- Backend remains the source of truth for permissions and file access.
- Clipboard and copy-paste remain enabled.
- All server-approved downloads remain enabled.
- macOS builds should be code signed and notarized before production rollout.
- Windows builds should use signed installers before production rollout.
- Auto-updates must come from a trusted internal or controlled release channel.

## Suggested Package Layout

```text
desktop/
  package.json
  electron/
    main.js
    preload.js
    allowed-origins.js
    app-lock.js
    downloads.js
  splash/
    splash.html
    splash.css
    splash.js
  assets/
    icon.icns
    icon.ico
    logo.png
  README.md
```

The desktop package should be separate from `frontend/` so the web deployment remains unchanged.

## Build And Release

Use `electron-builder` for packaging:

- macOS DMG target.
- Windows NSIS installer target.
- Separate app identifiers for production and staging if staging builds are needed.
- Signed release artifacts for production distribution.

Expected scripts:

- `npm run dev`: run the wrapper against the production URL or approved dev URL.
- `npm run lint`: lint Electron source.
- `npm run build:mac`: package macOS app.
- `npm run build:win`: package Windows app.
- `npm run dist`: package all configured targets for the current build host.

## Testing

Phase 1 verification should cover:

- App launches and splash appears before the main window.
- Main window loads `https://ai.silverlining.com.np`.
- Unknown domains do not load inside the main app window.
- External links open in the system browser.
- Login flow works through the hosted web app.
- Uploads work through the normal web UI.
- Downloads work for server-approved files.
- Native notification permission and display work where supported.
- App lock hides visible content and can be unlocked.
- macOS build config exists.
- Windows build config exists.
- Electron source passes lint.

## Acceptance Criteria

- A staff user can install and open LipiCore Desktop on macOS or Windows.
- The splash screen shows a LipiCore logo animation during startup.
- The app loads the fixed production LipiCore server by default.
- The app does not start or bundle local backend infrastructure.
- The app blocks or externalizes navigation outside approved LipiCore domains.
- Uploads and downloads work when the LipiCore server permits them.
- Copy-paste works normally.
- The app provides native desktop behavior such as app menu, window persistence, and notifications.
- The implementation does not change the backend security model or RAG/document processing behavior.
