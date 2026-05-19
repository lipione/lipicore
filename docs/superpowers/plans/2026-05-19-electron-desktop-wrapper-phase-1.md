# Electron Desktop Wrapper Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a macOS and Windows Electron wrapper that loads the hosted LipiCore server with desktop-native startup, app shell behavior, uploads/downloads, and hardened navigation.

**Architecture:** Add a separate `desktop/` Node package that does not change the FastAPI backend or Vite web deployment. Electron owns splash, main window, menu, tray, app lock, download handling, and navigation restrictions while loading `https://ai.silverlining.com.np` as the live app. The renderer stays sandboxed with no Node.js access.

**Tech Stack:** Electron, electron-builder, JavaScript CommonJS main process, HTML/CSS splash screen, ESLint, Node.js scripts.

---

## File Structure

- Create `desktop/package.json`: Electron package metadata, scripts, dependencies, and macOS/Windows build targets.
- Create `desktop/.eslintrc.cjs`: lint rules for Electron CommonJS source.
- Create `desktop/electron/config.js`: production URL, allowed origins, app metadata, idle lock timing.
- Create `desktop/electron/allowed-origins.js`: URL allowlist helpers used by navigation and test code.
- Create `desktop/electron/main.js`: Electron main process, splash lifecycle, main window, security hooks, menu, tray, downloads, and app lock.
- Create `desktop/electron/preload.js`: minimal isolated bridge for safe desktop metadata.
- Create `desktop/splash/splash.html`: boot screen markup.
- Create `desktop/splash/splash.css`: logo animation and desktop startup styling.
- Create `desktop/splash/splash.js`: splash text animation and status updates.
- Create `desktop/assets/logo.svg`: LipiCore desktop logo source used by splash and generated icons.
- Create `desktop/scripts/smoke-electron-config.js`: fast Node smoke checks for URL allowlist, package config, and required files.
- Create `desktop/scripts/generate-icons.js`: generate macOS `.icns` and Windows `.ico` assets from the SVG logo.
- Create `desktop/README.md`: run, build, signing, and release notes.
- Modify `.gitignore`: ignore Electron build outputs under `desktop/release/` and `desktop/dist/`.

## Task 1: Desktop Package Scaffold

**Files:**
- Create: `desktop/package.json`
- Create: `desktop/.eslintrc.cjs`
- Modify: `.gitignore`

- [ ] **Step 1: Create the Electron package file**

Create `desktop/package.json` with this exact content:

```json
{
  "name": "lipicore-desktop",
  "version": "0.1.0",
  "private": true,
  "description": "LipiCore Desktop secure server-connected wrapper",
  "main": "electron/main.js",
  "author": "LipiCore",
  "license": "UNLICENSED",
  "scripts": {
    "dev": "electron .",
    "lint": "eslint electron scripts",
    "icons": "node scripts/generate-icons.js",
    "smoke": "node scripts/smoke-electron-config.js",
    "check": "npm run lint && npm run smoke",
    "build:mac": "electron-builder --mac dmg",
    "build:win": "electron-builder --win nsis",
    "dist": "electron-builder"
  },
  "devDependencies": {
    "electron": "^42.1.0",
    "electron-builder": "^26.8.1",
    "eslint": "^8.57.1",
    "png2icons": "^2.0.1",
    "sharp": "^0.33.5"
  },
  "build": {
    "appId": "np.com.silverlining.lipicore.desktop",
    "productName": "LipiCore Desktop",
    "directories": {
      "output": "release"
    },
    "files": [
      "electron/**/*",
      "splash/**/*",
      "assets/**/*",
      "package.json"
    ],
    "mac": {
      "category": "public.app-category.business",
      "target": [
        "dmg"
      ],
      "icon": "assets/icon.icns",
      "hardenedRuntime": true,
      "gatekeeperAssess": false
    },
    "win": {
      "target": [
        "nsis"
      ],
      "icon": "assets/icon.ico"
    },
    "nsis": {
      "oneClick": false,
      "allowToChangeInstallationDirectory": true,
      "createDesktopShortcut": true,
      "createStartMenuShortcut": true
    }
  }
}
```

- [ ] **Step 2: Add Electron lint config**

Create `desktop/.eslintrc.cjs` with this exact content:

```javascript
module.exports = {
  root: true,
  env: {
    browser: false,
    node: true,
    es2022: true
  },
  extends: ["eslint:recommended"],
  parserOptions: {
    ecmaVersion: 2022
  },
  rules: {
    "no-console": "off",
    "no-unused-vars": ["error", { "argsIgnorePattern": "^_" }]
  }
};
```

- [ ] **Step 3: Ignore desktop build outputs**

Append these lines to `.gitignore`:

```gitignore

# Electron desktop outputs
desktop/node_modules/
desktop/release/
desktop/dist/
```

- [ ] **Step 4: Install desktop dependencies**

Run:

```bash
npm install --prefix desktop
```

Expected: `desktop/package-lock.json` is created and dependencies install without errors.

- [ ] **Step 5: Commit scaffold**

Run:

```bash
git add .gitignore desktop/package.json desktop/package-lock.json desktop/.eslintrc.cjs
git commit -m "Add LipiCore desktop package scaffold"
```

Expected: commit succeeds with only scaffold files staged.

## Task 2: URL Policy And Safe Preload

**Files:**
- Create: `desktop/electron/config.js`
- Create: `desktop/electron/allowed-origins.js`
- Create: `desktop/electron/preload.js`
- Create: `desktop/scripts/smoke-electron-config.js`

- [ ] **Step 1: Add desktop runtime config**

Create `desktop/electron/config.js` with this exact content:

```javascript
const DEFAULT_APP_URL = "https://ai.silverlining.com.np";
const APPROVED_ORIGINS = [
  "https://ai.silverlining.com.np",
  "https://staging.ai.silverlining.com.np"
];
const approvedOriginSet = new Set(APPROVED_ORIGINS);

function parseOrigins(rawValue) {
  if (!rawValue) {
    return [];
  }

  return rawValue
    .split(",")
    .map((origin) => origin.trim())
    .filter(Boolean);
}

function parseUrl(value, envName) {
  try {
    return new URL(value);
  } catch (_error) {
    throw new Error(`${envName} must be a valid URL`);
  }
}

function assertHttps(url, envName) {
  if (url.protocol !== "https:") {
    throw new Error(`${envName} must use https`);
  }
}

function assertApprovedOrigin(url, envName, message) {
  if (!approvedOriginSet.has(url.origin)) {
    throw new Error(`${envName} ${message}`);
  }
}

function resolveAppUrl(rawValue) {
  if (!rawValue) {
    return DEFAULT_APP_URL;
  }

  const url = parseUrl(rawValue, "LIPICORE_DESKTOP_URL");

  assertHttps(url, "LIPICORE_DESKTOP_URL");
  assertApprovedOrigin(url, "LIPICORE_DESKTOP_URL", "must use an approved origin");

  return url.href;
}

function resolveAllowedOrigins(rawValue) {
  return parseOrigins(rawValue).map((origin) => {
    const url = parseUrl(origin, "LIPICORE_DESKTOP_ALLOWED_ORIGINS");

    assertHttps(url, "LIPICORE_DESKTOP_ALLOWED_ORIGINS");
    assertApprovedOrigin(url, "LIPICORE_DESKTOP_ALLOWED_ORIGINS", "must use approved origins");

    return url.origin;
  });
}

const appUrl = resolveAppUrl(process.env.LIPICORE_DESKTOP_URL);
const configuredOrigins = resolveAllowedOrigins(process.env.LIPICORE_DESKTOP_ALLOWED_ORIGINS);

module.exports = {
  APP_URL: appUrl,
  ALLOWED_ORIGINS: Array.from(new Set([...APPROVED_ORIGINS, ...configuredOrigins])),
  APP_NAME: "LipiCore Desktop",
  IDLE_LOCK_MS: 15 * 60 * 1000
};
```

- [ ] **Step 2: Add URL allowlist helper**

Create `desktop/electron/allowed-origins.js` with this exact content:

```javascript
const { ALLOWED_ORIGINS } = require("./config");

const allowedOriginSet = new Set(ALLOWED_ORIGINS);

function toUrl(value) {
  try {
    return new URL(value);
  } catch (_error) {
    return null;
  }
}

function isAllowedUrl(value) {
  const url = toUrl(value);

  if (!url) {
    return false;
  }

  if (url.protocol !== "https:") {
    return false;
  }

  return allowedOriginSet.has(url.origin);
}

function shouldOpenExternally(value) {
  const url = toUrl(value);

  if (!url) {
    return false;
  }

  return ["http:", "https:", "mailto:", "tel:"].includes(url.protocol) && !isAllowedUrl(value);
}

module.exports = {
  isAllowedUrl,
  shouldOpenExternally
};
```

- [ ] **Step 3: Add safe preload bridge**

Create `desktop/electron/preload.js` with this exact content:

```javascript
const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("lipiCoreDesktop", {
  platform: process.platform,
  version: process.versions.electron,
  lock: () => ipcRenderer.invoke("desktop:lock")
});
```

- [ ] **Step 4: Add smoke checks**

Create `desktop/scripts/smoke-electron-config.js` with this exact content:

```javascript
const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

delete process.env.LIPICORE_DESKTOP_URL;
delete process.env.LIPICORE_DESKTOP_ALLOWED_ORIGINS;

const { APP_URL, ALLOWED_ORIGINS } = require("../electron/config");
const { isAllowedUrl, shouldOpenExternally } = require("../electron/allowed-origins");

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

const root = path.resolve(__dirname, "..");
const configPath = path.join(root, "electron/config.js");
const requiredFiles = [
  "electron/config.js",
  "electron/allowed-origins.js",
  "electron/preload.js",
  "package.json"
];

for (const filePath of requiredFiles) {
  assert(fs.existsSync(path.join(root, filePath)), `Missing ${filePath}`);
}

assert(APP_URL === "https://ai.silverlining.com.np", "Default app URL must be production");
assert(ALLOWED_ORIGINS.length === 2, "Only approved default origins should be allowed by default");
assert(ALLOWED_ORIGINS.includes("https://ai.silverlining.com.np"), "Production origin must be allowed");
assert(ALLOWED_ORIGINS.includes("https://staging.ai.silverlining.com.np"), "Staging origin must be allowed");
assert(isAllowedUrl("https://ai.silverlining.com.np/login"), "Production URL must be allowed");
assert(!isAllowedUrl("http://ai.silverlining.com.np/login"), "HTTP production URL must be blocked");
assert(!isAllowedUrl("https://example.com"), "Unknown HTTPS URL must be blocked");
assert(shouldOpenExternally("https://example.com/help"), "Unknown HTTPS URL should open externally");
assert(shouldOpenExternally("mailto:support@silverlining.com.np"), "Mailto links should open externally");

function assertConfigLoadFails(env, expectedMessage) {
  const child = spawnSync(process.execPath, ["-e", `require(${JSON.stringify(configPath)})`], {
    cwd: root,
    env: {
      ...process.env,
      LIPICORE_DESKTOP_URL: "",
      LIPICORE_DESKTOP_ALLOWED_ORIGINS: "",
      ...env
    },
    encoding: "utf8"
  });

  assert(child.status !== 0, `${Object.keys(env).join(", ")} should fail config load`);
  assert(
    child.stderr.includes(expectedMessage),
    `Expected config load error to include "${expectedMessage}", got: ${child.stderr}`
  );
}

function assertConfigLoadSucceeds(env, script) {
  const child = spawnSync(process.execPath, ["-e", script], {
    cwd: root,
    env: {
      ...process.env,
      LIPICORE_DESKTOP_URL: "",
      LIPICORE_DESKTOP_ALLOWED_ORIGINS: "",
      ...env
    },
    encoding: "utf8"
  });

  assert(child.status === 0, `Expected config load to succeed, got: ${child.stderr}`);
}

assertConfigLoadSucceeds(
  { LIPICORE_DESKTOP_URL: "https://staging.ai.silverlining.com.np/dashboard" },
  `
    const { APP_URL, ALLOWED_ORIGINS } = require(${JSON.stringify(configPath)});
    if (APP_URL !== "https://staging.ai.silverlining.com.np/dashboard") {
      throw new Error("Approved app URL with path was not preserved");
    }
    if (ALLOWED_ORIGINS.some((origin) => origin !== new URL(origin).origin)) {
      throw new Error("Allowed origins must be normalized origins");
    }
  `
);
assertConfigLoadFails(
  { LIPICORE_DESKTOP_URL: "http://ai.silverlining.com.np" },
  "LIPICORE_DESKTOP_URL must use https"
);
assertConfigLoadFails(
  { LIPICORE_DESKTOP_URL: "https://evil.test" },
  "LIPICORE_DESKTOP_URL must use an approved origin"
);
assertConfigLoadFails(
  { LIPICORE_DESKTOP_URL: "not-a-url" },
  "LIPICORE_DESKTOP_URL must be a valid URL"
);
assertConfigLoadFails(
  { LIPICORE_DESKTOP_ALLOWED_ORIGINS: "https://evil.test" },
  "LIPICORE_DESKTOP_ALLOWED_ORIGINS must use approved origins"
);
assertConfigLoadFails(
  { LIPICORE_DESKTOP_ALLOWED_ORIGINS: "http://ai.silverlining.com.np" },
  "LIPICORE_DESKTOP_ALLOWED_ORIGINS must use https"
);

console.log("Electron desktop config smoke checks passed");
```

- [ ] **Step 5: Run smoke check**

Run:

```bash
npm run --prefix desktop smoke
```

Expected: output contains `Electron desktop config smoke checks passed`.

- [ ] **Step 6: Run lint**

Run:

```bash
npm run --prefix desktop lint
```

Expected: lint exits 0.

- [ ] **Step 7: Commit URL policy and preload**

Run:

```bash
git add desktop/electron/config.js desktop/electron/allowed-origins.js desktop/electron/preload.js desktop/scripts/smoke-electron-config.js
git commit -m "Add desktop URL policy and preload bridge"
```

Expected: commit succeeds with only Task 2 files staged.

## Task 3: Splash Screen And Branding

**Files:**
- Create: `desktop/assets/logo.svg`
- Create: `desktop/splash/splash.html`
- Create: `desktop/splash/splash.css`
- Create: `desktop/splash/splash.js`

- [ ] **Step 1: Add LipiCore logo asset**

Create `desktop/assets/logo.svg` with this exact content:

```xml
<svg width="256" height="256" viewBox="0 0 256 256" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect width="256" height="256" rx="56" fill="#0B1220"/>
  <path d="M64 178V70h28v84h55v24H64Z" fill="#F8FAFC"/>
  <path d="M157 178V70h28v108h-28Z" fill="#38BDF8"/>
  <path d="M106 93h30c18 0 31 11 31 27 0 17-13 28-31 28h-30V93Zm27 34c6 0 10-3 10-8 0-4-4-7-10-7h-4v15h4Z" fill="#22C55E"/>
  <circle cx="187" cy="74" r="10" fill="#22C55E"/>
</svg>
```

- [ ] **Step 2: Add splash markup**

Create `desktop/splash/splash.html` with this exact content:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta
      http-equiv="Content-Security-Policy"
      content="default-src 'self'; img-src 'self'; style-src 'self'; script-src 'self';"
    />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>LipiCore Desktop</title>
    <link rel="stylesheet" href="./splash.css" />
  </head>
  <body>
    <main class="splash">
      <div class="brand-mark" aria-hidden="true">
        <img src="../assets/logo.svg" alt="" />
        <span class="pulse"></span>
      </div>
      <section class="copy" aria-label="LipiCore startup status">
        <h1>LipiCore</h1>
        <p id="status">Starting secure desktop session</p>
      </section>
    </main>
    <script src="./splash.js"></script>
  </body>
</html>
```

- [ ] **Step 3: Add splash styles**

Create `desktop/splash/splash.css` with this exact content:

```css
:root {
  color-scheme: dark;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background: #0b1220;
  color: #f8fafc;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  overflow: hidden;
  background:
    radial-gradient(circle at 20% 20%, rgba(56, 189, 248, 0.22), transparent 30%),
    linear-gradient(135deg, #0b1220 0%, #121826 48%, #07111f 100%);
}

.splash {
  width: 100vw;
  height: 100vh;
  display: grid;
  place-items: center;
  gap: 20px;
  align-content: center;
  padding: 40px;
}

.brand-mark {
  position: relative;
  width: 112px;
  height: 112px;
  display: grid;
  place-items: center;
}

.brand-mark img {
  width: 96px;
  height: 96px;
  border-radius: 24px;
  box-shadow: 0 24px 80px rgba(15, 23, 42, 0.55);
  animation: lift 1.6s ease-in-out infinite;
}

.pulse {
  position: absolute;
  inset: 0;
  border: 1px solid rgba(56, 189, 248, 0.42);
  border-radius: 32px;
  animation: pulse 1.6s ease-in-out infinite;
}

.copy {
  text-align: center;
}

h1 {
  margin: 0;
  font-size: 34px;
  font-weight: 700;
  letter-spacing: 0;
}

p {
  margin: 10px 0 0;
  min-height: 22px;
  color: #cbd5e1;
  font-size: 14px;
}

@keyframes lift {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-6px);
  }
}

@keyframes pulse {
  0% {
    opacity: 0.65;
    transform: scale(0.86);
  }
  100% {
    opacity: 0;
    transform: scale(1.18);
  }
}
```

- [ ] **Step 4: Add splash status script**

Create `desktop/splash/splash.js` with this exact content:

```javascript
const statuses = [
  "Starting secure desktop session",
  "Connecting to LipiCore",
  "Preparing workspace"
];

let index = 0;
const statusElement = document.getElementById("status");

window.setInterval(() => {
  index = (index + 1) % statuses.length;
  statusElement.textContent = statuses[index];
}, 1200);
```

- [ ] **Step 5: Run desktop lint**

Run:

```bash
npm run --prefix desktop lint
```

Expected: lint exits 0.

- [ ] **Step 6: Commit splash and branding**

Run:

```bash
git add desktop/assets/logo.svg desktop/splash/splash.html desktop/splash/splash.css desktop/splash/splash.js
git commit -m "Add LipiCore desktop splash screen"
```

Expected: commit succeeds with only splash and asset files staged.

## Task 4: Main Electron App Shell

**Files:**
- Create: `desktop/electron/main.js`
- Modify: `desktop/scripts/smoke-electron-config.js`

- [ ] **Step 1: Add main Electron process**

Create `desktop/electron/main.js` with this exact content:

```javascript
const fs = require("node:fs");
const path = require("node:path");
const {
  app,
  BrowserWindow,
  Menu,
  Tray,
  ipcMain,
  nativeImage,
  session,
  shell
} = require("electron");
const { APP_NAME, APP_URL, IDLE_LOCK_MS } = require("./config");
const { isAllowedUrl, shouldOpenExternally } = require("./allowed-origins");

let splashWindow;
let mainWindow;
let tray;
let idleTimer;
let isQuitting = false;

function assetPath(...parts) {
  return path.join(__dirname, "..", ...parts);
}

function runtimeIconPath() {
  const platformIcon = process.platform === "win32"
    ? assetPath("assets", "icon.ico")
    : assetPath("assets", "icon.icns");

  if (fs.existsSync(platformIcon)) {
    return platformIcon;
  }

  return assetPath("assets", "logo.svg");
}

function preferencesPath() {
  return path.join(app.getPath("userData"), "desktop-preferences.json");
}

function readPreferences() {
  try {
    return JSON.parse(fs.readFileSync(preferencesPath(), "utf8"));
  } catch (_error) {
    return {};
  }
}

function writePreferences(nextPreferences) {
  const current = readPreferences();
  const merged = { ...current, ...nextPreferences };
  fs.writeFileSync(preferencesPath(), JSON.stringify(merged, null, 2));
}

function getWindowBounds() {
  const preferences = readPreferences();
  return preferences.windowBounds || {
    width: 1280,
    height: 820
  };
}

function setWindowBounds(bounds) {
  writePreferences({ windowBounds: bounds });
}

function createSplashWindow() {
  splashWindow = new BrowserWindow({
    width: 460,
    height: 360,
    frame: false,
    resizable: false,
    show: false,
    transparent: false,
    backgroundColor: "#0b1220",
    webPreferences: {
      sandbox: true,
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  splashWindow.loadFile(assetPath("splash", "splash.html"));
  splashWindow.once("ready-to-show", () => splashWindow.show());
}

function createMainWindow() {
  const bounds = getWindowBounds();

  mainWindow = new BrowserWindow({
    ...bounds,
    minWidth: 1040,
    minHeight: 680,
    show: false,
    title: APP_NAME,
    backgroundColor: "#0f172a",
    icon: runtimeIconPath(),
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      sandbox: true,
      contextIsolation: true,
      nodeIntegration: false,
      webSecurity: true,
      allowRunningInsecureContent: false
    }
  });

  mainWindow.loadURL(APP_URL);
  wireWindowSecurity(mainWindow);
  wireWindowLifecycle(mainWindow);

  mainWindow.once("ready-to-show", () => {
    if (splashWindow && !splashWindow.isDestroyed()) {
      splashWindow.close();
    }
    mainWindow.show();
    resetIdleTimer();
  });
}

function wireWindowSecurity(windowRef) {
  windowRef.webContents.setWindowOpenHandler(({ url }) => {
    if (shouldOpenExternally(url)) {
      shell.openExternal(url);
    }

    return { action: "deny" };
  });

  windowRef.webContents.on("will-navigate", (event, url) => {
    if (isAllowedUrl(url)) {
      return;
    }

    event.preventDefault();

    if (shouldOpenExternally(url)) {
      shell.openExternal(url);
    }
  });

  windowRef.webContents.on("will-redirect", (event, url) => {
    if (!isAllowedUrl(url)) {
      event.preventDefault();
    }
  });
}

function wireWindowLifecycle(windowRef) {
  windowRef.on("close", (event) => {
    if (process.platform === "darwin" && !isQuitting) {
      event.preventDefault();
      windowRef.hide();
      return;
    }

    setWindowBounds(windowRef.getBounds());
  });

  windowRef.on("resize", () => setWindowBounds(windowRef.getBounds()));
  windowRef.on("move", () => setWindowBounds(windowRef.getBounds()));
}

function createMenu() {
  const template = [
    {
      label: APP_NAME,
      submenu: [
        { role: "about" },
        { type: "separator" },
        { label: "Lock LipiCore", click: () => lockApp() },
        { type: "separator" },
        { role: "quit" }
      ]
    },
    {
      label: "View",
      submenu: [
        { label: "Reload", accelerator: "CmdOrCtrl+R", click: () => mainWindow?.reload() },
        { role: "togglefullscreen" }
      ]
    },
    {
      label: "Window",
      submenu: [
        { role: "minimize" },
        { role: "close" }
      ]
    }
  ];

  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

function createTray() {
  const image = nativeImage.createFromPath(runtimeIconPath());

  if (image.isEmpty()) {
    return;
  }

  const trayImage = image.resize({ width: 18, height: 18 });

  if (trayImage.isEmpty()) {
    return;
  }

  tray = new Tray(trayImage);
  tray.setToolTip(APP_NAME);
  tray.setContextMenu(Menu.buildFromTemplate([
    { label: "Open LipiCore", click: () => showMainWindow() },
    { label: "Lock LipiCore", click: () => lockApp() },
    { type: "separator" },
    { label: "Quit", click: () => quitApp() }
  ]));
  tray.on("click", () => showMainWindow());
}

function showMainWindow() {
  if (!mainWindow) {
    return;
  }

  mainWindow.show();
  mainWindow.focus();
}

async function lockApp() {
  if (!mainWindow || mainWindow.isDestroyed()) {
    return;
  }

  clearIdleTimer();
  mainWindow.hide();

  await mainWindow.webContents.session.clearStorageData({
    storages: ["cookies", "localstorage", "indexdb", "cachestorage"]
  });

  await mainWindow.loadURL(APP_URL);
  mainWindow.show();
  mainWindow.focus();
  resetIdleTimer();
}

function resetIdleTimer() {
  clearIdleTimer();
  idleTimer = setTimeout(() => {
    lockApp();
  }, IDLE_LOCK_MS);
}

function clearIdleTimer() {
  if (idleTimer) {
    clearTimeout(idleTimer);
    idleTimer = null;
  }
}

function quitApp() {
  isQuitting = true;
  app.quit();
}

function wireDownloads() {
  session.defaultSession.on("will-download", (_event, item) => {
    const defaultPath = path.join(app.getPath("downloads"), item.getFilename());

    item.setSaveDialogOptions({
      title: "Save LipiCore download",
      defaultPath
    });
  });
}

function isMainWindowPermissionRequest(webContents, permission, requestingUrl, isMainFrame) {
  if (permission !== "notifications") {
    return false;
  }

  if (!mainWindow || mainWindow.isDestroyed() || webContents !== mainWindow.webContents) {
    return false;
  }

  if (isMainFrame === false) {
    return false;
  }

  return Boolean(requestingUrl && isAllowedUrl(requestingUrl));
}

function isAllowedPermissionCheck(permission, requestingOrigin, details = {}) {
  if (permission !== "notifications") {
    return false;
  }

  if (details.isMainFrame === false) {
    return false;
  }

  return [requestingOrigin, details.requestingUrl, details.embeddingOrigin].some((requestUrl) => (
    Boolean(requestUrl && isAllowedUrl(requestUrl))
  ));
}

function wirePermissions() {
  session.defaultSession.setPermissionRequestHandler((webContents, permission, callback, details = {}) => {
    const requestingUrl = details.requestingUrl || webContents.getURL();

    callback(
      isMainWindowPermissionRequest(webContents, permission, requestingUrl, details.isMainFrame)
    );
  });

  session.defaultSession.setPermissionCheckHandler((_webContents, permission, requestingOrigin, details = {}) => {
    return isAllowedPermissionCheck(permission, requestingOrigin, details);
  });
}

app.on("before-quit", () => {
  isQuitting = true;
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("activate", () => {
  if (mainWindow) {
    showMainWindow();
    return;
  }

  createMainWindow();
});

ipcMain.handle("desktop:lock", () => lockApp());

app.whenReady().then(() => {
  app.setName(APP_NAME);
  createMenu();
  createTray();
  wireDownloads();
  wirePermissions();
  createSplashWindow();
  createMainWindow();
});
```

- [ ] **Step 2: Extend smoke checks for main app file**

Replace the `requiredFiles` array in `desktop/scripts/smoke-electron-config.js` with:

```javascript
const requiredFiles = [
  "electron/config.js",
  "electron/allowed-origins.js",
  "electron/main.js",
  "electron/preload.js",
  "splash/splash.html",
  "splash/splash.css",
  "splash/splash.js",
  "assets/logo.svg",
  "package.json"
];
```

- [ ] **Step 3: Run desktop checks**

Run:

```bash
npm run --prefix desktop check
```

Expected: lint exits 0 and smoke output contains `Electron desktop config smoke checks passed`.

- [ ] **Step 4: Run Electron manually**

Run:

```bash
npm run --prefix desktop dev
```

Expected: splash appears first, then the main LipiCore window loads `https://ai.silverlining.com.np`.

- [ ] **Step 5: Commit app shell**

Run:

```bash
git add desktop/electron/main.js desktop/scripts/smoke-electron-config.js
git commit -m "Add secure Electron app shell"
```

Expected: commit succeeds with only Task 4 files staged.

## Task 5: Desktop Documentation And Release Notes

**Files:**
- Create: `desktop/README.md`

- [ ] **Step 1: Add desktop README**

Create `desktop/README.md` with this exact content:

```markdown
# LipiCore Desktop

LipiCore Desktop is a macOS and Windows Electron wrapper for the hosted LipiCore server.

## Runtime Model

- The app loads `https://ai.silverlining.com.np` by default.
- The app does not run FastAPI, PostgreSQL, Qdrant, MinIO, Redis, RAG, or LLM services locally.
- Backend authorization remains the source of truth for documents, chat, uploads, and downloads.
- All downloads allowed by the server are allowed by the desktop wrapper.
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

Use an internal staging URL:

```bash
LIPICORE_DESKTOP_URL=https://staging.ai.silverlining.com.np npm run dev
```

Use extra allowed origins for internal testing:

```bash
LIPICORE_DESKTOP_ALLOWED_ORIGINS=https://staging.ai.silverlining.com.np npm run dev
```

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

## Security Defaults

- Renderer sandbox is enabled.
- Node integration is disabled.
- Context isolation is enabled.
- Unknown app-window navigations are blocked or opened in the system browser.
- Only approved LipiCore HTTPS origins can load inside the main app window.
- The app lock action clears local web session storage and reloads the LipiCore app.
```

- [ ] **Step 2: Run desktop checks**

Run:

```bash
npm run --prefix desktop check
```

Expected: lint exits 0 and smoke output contains `Electron desktop config smoke checks passed`.

- [ ] **Step 3: Commit documentation**

Run:

```bash
git add desktop/README.md
git commit -m "Document LipiCore desktop wrapper"
```

Expected: commit succeeds with only `desktop/README.md` staged.

## Task 6: Packaging Verification

**Files:**
- Create: `desktop/scripts/generate-icons.js`
- Create: `desktop/assets/icon.icns`
- Create: `desktop/assets/icon.ico`
- Modify: `desktop/scripts/smoke-electron-config.js`

- [ ] **Step 1: Add deterministic icon generator**

Create `desktop/scripts/generate-icons.js` with this exact content:

```javascript
const fs = require("node:fs");
const path = require("node:path");
const png2icons = require("png2icons");
const sharp = require("sharp");

const root = path.resolve(__dirname, "..");
const assetDir = path.join(root, "assets");
const svgPath = path.join(assetDir, "logo.svg");
const pngPath = path.join(assetDir, "icon-1024.png");
const icnsPath = path.join(assetDir, "icon.icns");
const icoPath = path.join(assetDir, "icon.ico");

async function main() {
  await sharp(svgPath)
    .resize(1024, 1024)
    .png()
    .toFile(pngPath);

  const pngBuffer = fs.readFileSync(pngPath);
  const icnsBuffer = png2icons.createICNS(pngBuffer, png2icons.BILINEAR, 0);
  const icoBuffer = png2icons.createICO(pngBuffer, png2icons.BILINEAR, 0);

  if (!icnsBuffer || !icoBuffer) {
    throw new Error("Icon generation failed");
  }

  fs.writeFileSync(icnsPath, icnsBuffer);
  fs.writeFileSync(icoPath, icoBuffer);
  fs.rmSync(pngPath, { force: true });

  console.log("Generated desktop/assets/icon.icns and desktop/assets/icon.ico");
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
```

- [ ] **Step 2: Generate production icon files from the SVG source**

Run:

```bash
npm run --prefix desktop icons
```

Expected: output contains `Generated desktop/assets/icon.icns and desktop/assets/icon.ico`.

- [ ] **Step 3: Extend smoke checks for icon files**

Replace the `requiredFiles` array in `desktop/scripts/smoke-electron-config.js` with:

```javascript
const requiredFiles = [
  "electron/config.js",
  "electron/allowed-origins.js",
  "electron/main.js",
  "electron/preload.js",
  "splash/splash.html",
  "splash/splash.css",
  "splash/splash.js",
  "assets/logo.svg",
  "assets/icon.icns",
  "assets/icon.ico",
  "package.json"
];
```

- [ ] **Step 4: Run desktop checks**

Run:

```bash
npm run --prefix desktop check
```

Expected: lint exits 0 and smoke output contains `Electron desktop config smoke checks passed`.

- [ ] **Step 5: Run package config validation**

Run:

```bash
npm run --prefix desktop dist -- --dir
```

Expected: electron-builder creates an unpacked app under `desktop/release/` without missing-file errors.

- [ ] **Step 6: Commit icon generation and files**

Run:

```bash
git add desktop/scripts/generate-icons.js desktop/assets/icon.icns desktop/assets/icon.ico desktop/scripts/smoke-electron-config.js
git commit -m "Add desktop installer icons"
```

Expected: commit succeeds with only icon generator, icon files, and smoke check updates staged.

## Task 7: Final Verification

**Files:**
- All files created in `desktop/`
- `.gitignore`

- [ ] **Step 1: Run complete desktop checks**

Run:

```bash
npm run --prefix desktop check
```

Expected: lint exits 0 and smoke output contains `Electron desktop config smoke checks passed`.

- [ ] **Step 2: Launch desktop app**

Run:

```bash
npm run --prefix desktop dev
```

Expected:

- Splash window appears with LipiCore branding.
- Main window loads `https://ai.silverlining.com.np`.
- App menu contains Reload, Lock LipiCore, and Quit.
- Unknown domains do not load inside the main window.
- External links open in the default system browser.
- Upload controls in the web app open the OS file picker.
- Server-approved downloads open a native save dialog.

- [ ] **Step 3: Verify app lock**

In the running app, select `LipiCore Desktop > Lock LipiCore`.

Expected:

- Main window hides briefly.
- Local web session storage is cleared.
- Main window reloads the LipiCore URL.
- Visible content is no longer left on screen after locking.

- [ ] **Step 4: Verify packaging directory build**

Run:

```bash
npm run --prefix desktop dist -- --dir
```

Expected: electron-builder creates an unpacked app under `desktop/release/` without missing-file errors.

- [ ] **Step 5: Check git state**

Run:

```bash
git status --short
```

Expected: no tracked files are modified. Ignored build outputs under `desktop/release/` may exist locally.

- [ ] **Step 6: Commit final adjustments**

If final verification required changes, commit them:

```bash
git add desktop .gitignore
git commit -m "Finalize LipiCore desktop wrapper"
```

Expected: commit succeeds or there are no final changes to commit.
