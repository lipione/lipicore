const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("lipiCoreDesktop", {
  platform: process.platform,
  version: process.versions.electron,
  lock: () => ipcRenderer.invoke("desktop:lock")
});
