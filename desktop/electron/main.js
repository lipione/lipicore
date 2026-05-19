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

  wireWindowSecurity(mainWindow);
  wireWindowLifecycle(mainWindow);
  mainWindow.loadURL(APP_URL);

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
