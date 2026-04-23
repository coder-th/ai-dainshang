const { app, BrowserWindow, dialog, shell, ipcMain } = require("electron");
const { spawn } = require("child_process");
const path = require("path");
const http = require("http");
const fs = require("fs");
const { autoUpdater } = require("electron-updater");

const PORT = 9527;
const BACKEND_URL = `http://127.0.0.1:${PORT}`;
const DEV_URL = "http://localhost:5173"; // Vite dev server

const isDev = !app.isPackaged;

// Auto-hide the menu bar (accessible via Alt key)
// Menu.setApplicationMenu(null); // Do not remove — keeps window management intact

// ─── IPC: window controls ─────────────────────────────────────────────────────
ipcMain.on("win-minimize", () => BrowserWindow.getFocusedWindow()?.minimize());
ipcMain.on("win-reload",  () => BrowserWindow.getFocusedWindow()?.webContents.reload());
ipcMain.on("win-maximize", () => {
  const win = BrowserWindow.getFocusedWindow();
  if (!win) return;
  win.isMaximized() ? win.unmaximize() : win.maximize();
});
ipcMain.on("win-close", () => {
  const win = BrowserWindow.getFocusedWindow();
  if (win) win.close(); // 触发 win.on("close") 统一处理确认逻辑
});
ipcMain.handle("win-is-maximized", () => BrowserWindow.getFocusedWindow()?.isMaximized() ?? false);

ipcMain.handle("get-version", () => app.getVersion());

ipcMain.handle("select-directory", async () => {
  const win = BrowserWindow.getFocusedWindow();
  const { canceled, filePaths } = await dialog.showOpenDialog(win, {
    properties: ["openDirectory", "createDirectory"],
  });
  return canceled ? null : filePaths[0];
});

// ─── Path helpers ─────────────────────────────────────────────────────────────

function getBackendExe() {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, "backend", "app.exe");
  }
  return path.join(__dirname, "..", "dist", "app.exe");
}

function getDataDir() {
  return app.getPath("userData");
}

// ─── Loading window ───────────────────────────────────────────────────────────

function createLoadingWindow() {
  const win = new BrowserWindow({
    width: 400,
    height: 260,
    frame: false,
    resizable: false,
    center: true,
    alwaysOnTop: true,
    webPreferences: { nodeIntegration: false },
  });
  win.loadFile(path.join(__dirname, "loading.html"));
  return win;
}

// ─── Main window ──────────────────────────────────────────────────────────────

function createMainWindow(loadingWin) {
  const win = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 960,
    minHeight: 600,
    show: false,
    frame: false,
    autoHideMenuBar: true,
    // icon: path.join(__dirname, "assets", "icon.ico"),
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      nodeIntegration: false,
      contextIsolation: true,
    },
  });

  // Dev: load from Vite (supports HMR); Prod: load from Django
  const targetURL = isDev ? DEV_URL : BACKEND_URL;
  win.loadURL(targetURL);

  win.once("ready-to-show", () => {
    if (loadingWin && !loadingWin.isDestroyed()) loadingWin.close();
    win.show();
  });

  // F12 toggle DevTools
  win.webContents.on("before-input-event", (_, input) => {
    if (input.type === "keyDown" && input.key === "F12") {
      win.webContents.isDevToolsOpened()
        ? win.webContents.closeDevTools()
        : win.webContents.openDevTools();
    }
  });

  win.on("maximize",   () => win.webContents.send("win-maximized", true));
  win.on("unmaximize", () => win.webContents.send("win-maximized", false));

  // Intercept OS-level close (Alt+F4, taskbar right-click close, etc.)
  win.on("close", (e) => {
    if (isQuitting) return; // app.exit 路径，直接放行
    e.preventDefault(); // block immediate close
    dialog.showMessageBox(win, {
      type: "question",
      title: "退出程序",
      message: "确定要退出程序吗？",
      buttons: ["退出", "取消"],
      defaultId: 1,
      cancelId: 1,
      noLink: true,
    }).then(({ response }) => {
      if (response === 0) {
        isQuitting = true;
        killDjango();
        app.exit(0);
      }
    });
  });

  win.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith(BACKEND_URL) || url.startsWith(DEV_URL)) return { action: "allow" };
    shell.openExternal(url);
    return { action: "deny" };
  });

  return win;
}

// ─── Django backend ───────────────────────────────────────────────────────────

function isDjangoRunning() {
  return new Promise((resolve) => {
    const req = http.get(`${BACKEND_URL}/api/`, () => resolve(true));
    req.on("error", () => resolve(false));
    req.setTimeout(800, () => { req.destroy(); resolve(false); });
  });
}

function startDjango() {
  const exe = getBackendExe();
  if (!fs.existsSync(exe)) {
    dialog.showErrorBox(
      "Backend not found",
      `Expected:\n${exe}\n\nFor development: start Django manually.\nFor production: run build.ps1.`
    );
    app.quit();
    return false;
  }

  const dataDir = getDataDir();
  fs.mkdirSync(dataDir, { recursive: true });

  const proc = spawn(exe, [], {
    env: { ...process.env, APP_DATA_DIR: dataDir },
    stdio: "ignore",
    detached: false,
  });
  proc.on("error", (err) => dialog.showErrorBox("Backend error", err.message));
  return proc;
}

function waitFor(url, onReady, retries = 80) {
  const req = http.get(url, () => onReady());
  req.on("error", () => {
    if (retries > 0) setTimeout(() => waitFor(url, onReady, retries - 1), 500);
    else { dialog.showErrorBox("Timeout", `${url} did not respond within 40s.`); app.quit(); }
  });
  req.setTimeout(1000, () => req.destroy());
}

// ─── Auto-updater ─────────────────────────────────────────────────────────────

let _updaterWin = null; // 延迟绑定窗口引用

const sendUpdaterStatus = (status, payload = {}) => {
  if (_updaterWin && !_updaterWin.isDestroyed()) {
    _updaterWin.webContents.send("updater-status", { status, ...payload });
  }
};

// 事件监听在模块加载时就注册，不依赖 setupAutoUpdater 是否已执行
autoUpdater.autoDownload = false;
autoUpdater.autoInstallOnAppQuit = true;

autoUpdater.on("checking-for-update",   () => sendUpdaterStatus("checking"));
autoUpdater.on("update-not-available",  () => sendUpdaterStatus("not-available"));
autoUpdater.on("update-downloaded",     () => sendUpdaterStatus("downloaded"));
autoUpdater.on("update-available", (info) => {
  sendUpdaterStatus("available", { version: info.version });
  autoUpdater.downloadUpdate();
});
autoUpdater.on("download-progress", ({ percent }) =>
  sendUpdaterStatus("downloading", { percent: Math.floor(percent) })
);
autoUpdater.on("error", (err) => {
  console.error("[updater] error:", err.message);
  const isNoRelease = /Unable to find latest version|releases feed/i.test(err.message);
  sendUpdaterStatus(isNoRelease ? "not-available" : "error", { message: err.message });
});

// IPC handlers — 模块加载时注册，任何时候都可响应
ipcMain.removeHandler("check-for-updates"); // 防止热重载时重复注册
ipcMain.handle("check-for-updates", async () => {
  if (!app.isPackaged) return;
  try { await autoUpdater.checkForUpdates(); } catch (e) { /* 已由 error 事件处理 */ }
});

ipcMain.removeHandler("install-update");
ipcMain.handle("install-update", () => {
  if (app.isPackaged) autoUpdater.quitAndInstall();
});

function setupAutoUpdater(win) {
  _updaterWin = win; // 绑定窗口，此后 sendUpdaterStatus 才能推送消息到渲染层
  if (!app.isPackaged) return;
  // 启动后 5 秒静默检查，之后每 6 小时检查一次
  setTimeout(() => autoUpdater.checkForUpdates(), 5000);
  setInterval(() => autoUpdater.checkForUpdates(), 6 * 60 * 60 * 1000);
}



let djangoProcess = null;
let isQuitting = false; // 防止 close 事件与 app.exit 形成重入循环

const gotLock = app.requestSingleInstanceLock();
if (!gotLock) {
  app.quit();
} else {
  app.on("second-instance", (_, __, ___, additionalData) => {
    // handled below via mainWindow ref
  });

  let mainWindow = null;

  app.whenReady().then(async () => {
    const loadingWin = createLoadingWindow();

    const alreadyRunning = await isDjangoRunning();
    if (!alreadyRunning) {
      djangoProcess = startDjango();
      if (!djangoProcess) return;
    }

    if (isDev) {
      // Wait for both Django API and Vite dev server
      waitFor(`${BACKEND_URL}/api/`, () => {
        waitFor(DEV_URL, () => {
          mainWindow = createMainWindow(loadingWin);
          setupAutoUpdater(mainWindow);
        });
      });
    } else {
      waitFor(`${BACKEND_URL}/api/`, () => {
        mainWindow = createMainWindow(loadingWin);
        setupAutoUpdater(mainWindow);
      });
    }
  });

  app.on("window-all-closed", () => { if (isQuitting) { killDjango(); app.quit(); } });
  // before-quit is kept as safety net for edge cases
  app.on("before-quit", killDjango);
}

function killDjango() {
  if (djangoProcess) { djangoProcess.kill(); djangoProcess = null; }
}
