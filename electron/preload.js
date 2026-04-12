const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("electronAPI", {
  // Window controls
  minimize:         ()    => ipcRenderer.send("win-minimize"),
  maximize:         ()    => ipcRenderer.send("win-maximize"),
  close:            ()    => ipcRenderer.send("win-close"),
  isMaximized:      ()    => ipcRenderer.invoke("win-is-maximized"),
  onMaximizeChange: (cb)  => ipcRenderer.on("win-maximized", (_e, val) => cb(val)),
  // File system
  selectDirectory:  ()    => ipcRenderer.invoke("select-directory"),
  // Page
  reload:           ()    => ipcRenderer.send("win-reload"),
  // Updater
  checkForUpdates:  ()    => ipcRenderer.invoke("check-for-updates"),
  installUpdate:    ()    => ipcRenderer.invoke("install-update"),
  onUpdateStatus:   (cb)  => ipcRenderer.on("updater-status", (_e, payload) => cb(payload)),
});
