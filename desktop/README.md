# LipiCore Desktop

LipiCore Desktop is a macOS and Windows Electron wrapper for the hosted LipiCore server.

## Runtime Model

- The app loads `https://ai.silverlining.com.np` by default.
- The approved in-app origins are production, `https://ai.silverlining.com.np`, and staging, `https://staging.ai.silverlining.com.np`.
- `LIPICORE_DESKTOP_URL` and `LIPICORE_DESKTOP_ALLOWED_ORIGINS` must use HTTPS and must resolve to an approved LipiCore origin; they cannot add arbitrary origins.
- The app does not run FastAPI, PostgreSQL, Qdrant, MinIO, Redis, RAG, LLM services, or other backend services locally.
- Backend authorization remains the source of truth for documents, chat, uploads, and downloads.
- All downloads allowed by the server are allowed by the desktop wrapper and use Electron save dialog options.
- Copy and paste use normal operating system behavior.

## Development

Install dependencies:

```bash
npm install
```

Run the desktop app:

```bash
npm run dev
```

Run checks:

```bash
npm run check
```

Use the approved staging URL:

```bash
LIPICORE_DESKTOP_URL=https://staging.ai.silverlining.com.np npm run dev
```

Explicitly list an extra allowed origin for internal testing:

```bash
LIPICORE_DESKTOP_ALLOWED_ORIGINS=https://staging.ai.silverlining.com.np npm run dev
```

The extra allowed origin must still be one of the approved production or staging origins.

## Packaging

Build macOS DMG:

```bash
npm run build:mac
```

Build Windows installer:

```bash
npm run build:win
```

Production macOS builds must be code signed and notarized. Production Windows builds must use a signed installer.

The desktop package currently depends on Electron `^42.1.0`, with `42.1.0` resolved in `package-lock.json`.

## Security Defaults

- Renderer sandbox is enabled.
- Node integration is disabled.
- Context isolation is enabled.
- Unknown app-window navigations are blocked or opened in the system browser.
- Only approved LipiCore HTTPS origins can load inside the main app window.
- Notification permission is restricted to the main LipiCore window and an approved LipiCore origin.
- The app lock action hides the main window, clears local web session storage, reloads the LipiCore app, and shows the window again.
