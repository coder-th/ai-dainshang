const { app, BrowserWindow, dialog, shell, ipcMain } = require("electron");
const { spawn } = require("child_process");
const path = require("path");
const http = require("http");
const fs = require("fs");
const https = require("https");

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

// ─── Auto-updater (GitHub Releases API) ───────────────────────────────────────

const GITHUB_OWNER = "coder-th";
const GITHUB_REPO  = "ai-dainshang";
const GITHUB_TAGS_API    = `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/tags`;
const GITHUB_RELEASE_API = (tag) => `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/releases/tags/${tag}`;

let _updaterWin = null;
let _downloadedInstallerPath = null;

const sendUpdaterStatus = (status, payload = {}) => {
  if (_updaterWin && !_updaterWin.isDestroyed()) {
    _updaterWin.webContents.send("updater-status", { status, ...payload });
  }
};

function compareVersions(a, b) {
  const pa = a.replace(/^v/, "").split(".").map(Number);
  const pb = b.replace(/^v/, "").split(".").map(Number);
  for (let i = 0; i < 3; i++) {
    if ((pa[i] || 0) > (pb[i] || 0)) return 1;
    if ((pa[i] || 0) < (pb[i] || 0)) return -1;
  }
  return 0;
}

// 支持重定向的 HTTPS GET，返回 { statusCode, headers, body }
function httpsGet(url) {
  return new Promise((resolve, reject) => {
    const req = https.get(url, { headers: { "User-Agent": `${GITHUB_REPO}/${app.getVersion()}` } }, (res) => {
      if (res.statusCode === 301 || res.statusCode === 302) {
        return httpsGet(res.headers.location).then(resolve).catch(reject);
      }
      let body = "";
      res.on("data", (c) => (body += c));
      res.on("end", () => resolve({ statusCode: res.statusCode, headers: res.headers, body }));
    });
    req.on("error", reject);
    req.setTimeout(10000, () => { req.destroy(); reject(new Error("Request timeout")); });
  });
}

// 带进度回调、支持重定向的文件下载
function downloadFile(url, destPath, onProgress) {
  return new Promise((resolve, reject) => {
    const doGet = (downloadUrl) => {
      const file = fs.createWriteStream(destPath);
      const req = https.get(downloadUrl, { headers: { "User-Agent": `${GITHUB_REPO}/${app.getVersion()}` } }, (res) => {
        if (res.statusCode === 301 || res.statusCode === 302) {
          file.close();
          fs.unlink(destPath, () => {});
          return doGet(res.headers.location);
        }
        const total = parseInt(res.headers["content-length"] || "0", 10);
        let received = 0;
        res.on("data", (chunk) => {
          received += chunk.length;
          if (total > 0) onProgress(Math.floor((received / total) * 100));
        });
        res.pipe(file);
        file.on("finish", () => file.close(() => resolve(destPath)));
        res.on("error", (err) => { file.close(); fs.unlink(destPath, () => {}); reject(err); });
      });
      req.on("error", (err) => { file.close(); fs.unlink(destPath, () => {}); reject(err); });
    };
    doGet(url);
  });
}

async function checkForUpdates() {
  sendUpdaterStatus("checking");

  // 第一步：查最新 tag
  const tagsRes = await httpsGet(GITHUB_TAGS_API);
  if (tagsRes.statusCode !== 200) throw new Error(`GitHub Tags API 返回 ${tagsRes.statusCode}`);
  const tags = JSON.parse(tagsRes.body);
  if (!tags.length) { sendUpdaterStatus("not-available"); return; }

  const latestTag     = tags[0].name;
  const latestVersion = latestTag.replace(/^v/, "");
  const currentVersion = app.getVersion();

  if (compareVersions(latestVersion, currentVersion) <= 0) {
    sendUpdaterStatus("not-available");
    return;
  }

  // 第二步：用 tag 名查对应 release，获取 asset 下载链接
  const releaseRes = await httpsGet(GITHUB_RELEASE_API(latestTag));
  if (releaseRes.statusCode !== 200) throw new Error(`GitHub Release API 返回 ${releaseRes.statusCode}`);
  const release = JSON.parse(releaseRes.body);

  const asset = release.assets.find((a) => /\.(exe|msi)$/i.test(a.name) && !/debug/i.test(a.name));
  if (!asset) {
    sendUpdaterStatus("error", { message: "Release 中未找到 Windows 安装包" });
    return;
  }

  sendUpdaterStatus("available", {
    version:      latestVersion,
    releaseNotes: release.body || "",
    downloadUrl:  asset.browser_download_url,
    assetName:    asset.name,
  });
}

async function downloadUpdate(downloadUrl, assetName) {
  _downloadedInstallerPath = null;
  const destPath = path.join(app.getPath("temp"), assetName);
  await downloadFile(downloadUrl, destPath, (percent) => {
    sendUpdaterStatus("downloading", { percent });
  });
  _downloadedInstallerPath = destPath;
  sendUpdaterStatus("downloaded");
}

// IPC handlers
ipcMain.removeHandler("check-for-updates");
ipcMain.handle("check-for-updates", async () => {
  if (!app.isPackaged) return;
  try { await checkForUpdates(); } catch (err) {
    console.error("[updater] check error:", err.message);
    sendUpdaterStatus("error", { message: err.message });
  }
});

ipcMain.removeHandler("download-update");
ipcMain.handle("download-update", async (_, { downloadUrl, assetName }) => {
  try { await downloadUpdate(downloadUrl, assetName); } catch (err) {
    console.error("[updater] download error:", err.message);
    sendUpdaterStatus("error", { message: err.message });
  }
});

ipcMain.removeHandler("install-update");
ipcMain.handle("install-update", () => {
  if (_downloadedInstallerPath && fs.existsSync(_downloadedInstallerPath)) {
    shell.openPath(_downloadedInstallerPath);
    setTimeout(() => { isQuitting = true; app.exit(0); }, 800);
  }
});

function setupAutoUpdater(win) {
  _updaterWin = win;
  if (!app.isPackaged) return;
  // 启动后 5 秒静默检查，之后每 6 小时检查一次
  setTimeout(() => checkForUpdates().catch(() => {}), 5000);
  setInterval(() => checkForUpdates().catch(() => {}), 6 * 60 * 60 * 1000);
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
