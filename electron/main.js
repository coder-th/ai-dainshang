const { app, BrowserWindow, dialog, shell, Menu, ipcMain } = require("electron");
const { spawn } = require("child_process");
const path = require("path");
const http = require("http");
const fs = require("fs");

const PORT = 9527;
const BACKEND_URL = `http://127.0.0.1:${PORT}`;
const DEV_URL = "http://localhost:5173"; // Vite dev server

const isDev = !app.isPackaged;

// Remove the default application menu bar
Menu.setApplicationMenu(null);

// ─── IPC: window controls ─────────────────────────────────────────────────────
ipcMain.on("win-minimize", () => BrowserWindow.getFocusedWindow()?.minimize());
ipcMain.on("win-reload",  () => BrowserWindow.getFocusedWindow()?.webContents.reload());
ipcMain.on("win-maximize", () => {
  const win = BrowserWindow.getFocusedWindow();
  if (!win) return;
  win.isMaximized() ? win.unmaximize() : win.maximize();
});
ipcMain.on("win-close", async () => {
  const win = BrowserWindow.getFocusedWindow();
  if (!win) return;

  const { response } = await dialog.showMessageBox(win, {
    type: "question",
    title: "退出程序",
    message: "确定要退出程序吗？",
    buttons: ["退出", "取消"],
    defaultId: 1,
    cancelId: 1,
    noLink: true,
  });

  if (response === 0) {
    // User confirmed: kill backend and quit
    killDjango();
    app.exit(0);
  }
});
ipcMain.handle("win-is-maximized", () => BrowserWindow.getFocusedWindow()?.isMaximized() ?? false);

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
  return path.join(__dirname, "..", "dist", "app", "app.exe");
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

// ─── App lifecycle ────────────────────────────────────────────────────────────

let djangoProcess = null;

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
        });
      });
    } else {
      waitFor(`${BACKEND_URL}/api/`, () => {
        mainWindow = createMainWindow(loadingWin);
      });
    }
  });

  app.on("window-all-closed", () => { killDjango(); app.quit(); });
  // before-quit is kept as safety net for edge cases
  app.on("before-quit", killDjango);
}

function killDjango() {
  if (djangoProcess) { djangoProcess.kill(); djangoProcess = null; }
}
