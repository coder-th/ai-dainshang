# AI电商 — AI 创意工坊

基于 **Electron + Vue 3 + Django** 的 AI 电商内容创作桌面应用，支持 AI 图片生成与 AI 视频生成，适配多家 AI 服务供应商，具备自动更新能力。

---

## 技术栈

| 层次 | 技术 |
|------|------|
| 桌面壳 | Electron 29 + electron-builder (NSIS) |
| 前端 | Vue 3 + Vite + Element Plus + Pinia |
| 后端 | Django 4.2 + Django REST Framework |
| 静态服务 | WhiteNoise |
| 打包 | PyInstaller（Django → 单文件 exe） |
| 数据库 | SQLite |
| 自动更新 | electron-updater（GitHub Releases） |

---

## 功能特性

### AI 图片生成
- **多模型支持**：灵芽AI、云雾AI，多模型可随时切换
- **批量生成**：上传多张基准图，每张独立任务并发执行
- **参考图融合**：支持最多 8 张参考图与所有基准图共享（1:N 关系）
- **参数精调**：比例（13 种）、分辨率（1K/2K/4K）、联网检索，按模型能力动态过滤
- **结果管理**：生成耗时 / 文件大小展示，全选 / 逐张勾选批量保存
- **历史记录**：本地持久化，可随时查看和重新下载

### AI 视频生成
- 基于 Google Veo 系列模型
- 支持文生视频 / 图生视频 / 音频生成
- 多任务卡片并行管理，独立跟踪每个视频任务进度
- 历史记录本地保存

### 应用能力
- **多供应商 API Key**：灵芽AI / 云雾AI，图片与视频分别管理，Key 存储于本地 localStorage
- **自动更新**：启动后 5 秒静默检查，每 6 小时检查一次；设置页支持手动触发，实时显示下载进度
- **自定义导出路径**：图片 / 视频保存至用户指定目录
- **下载代理**：后端转发远程图片，规避跨域限制
- **API 日志**：出站请求按日期写入 JSONL 日志文件
- **DevTools**：F12 切换开发者工具

---

## 项目结构

```
ai-dianshang/
├── electron/               # Electron 主进程
│   ├── main.js             # 应用入口（窗口管理、后端启动、自动更新 IPC）
│   ├── preload.js          # 渲染层 IPC 桥接（窗口控制、目录选择、更新控制）
│   └── assets/             # 图标等静态资源
├── frontend/               # Vue 3 前端
│   └── src/
│       ├── views/          # HomeView（图片）、VideoView（视频）、SettingsView（设置）
│       ├── components/     # ImageHistoryDialog、VideoHistoryDialog 等
│       ├── composables/    # useGeneration 等
│       ├── config/         # models.js（模型配置）、providers.js（供应商配置）
│       ├── api/            # axios 封装
│       └── electron.d.ts   # electronAPI 类型声明
├── backend/                # Django 后端
│   ├── apps/core/
│   │   ├── providers.py    # Provider 抽象层（图像 / 视频）
│   │   ├── models.py       # 数据模型
│   │   ├── views.py        # GenerateView、ProxyImageView 等
│   │   └── urls.py
│   └── config/
│       └── settings.py     # 支持开发 / PyInstaller 双模式
├── build.ps1               # 完整构建脚本（支持 -Publish 参数）
├── publish.ps1             # 版本检测 + 发布到 GitHub Releases
├── build.spec              # PyInstaller 配置
├── requirements.txt        # Python 依赖
└── package.json            # Electron 依赖 & electron-builder 配置
```

---

## 快速开始（开发模式）

### 前置依赖

- Node.js ≥ 18
- Python ≥ 3.10

### 1. 安装依赖

```bash
# Python 依赖
pip install -r requirements.txt

# 前端依赖
cd frontend && npm install && cd ..

# Electron 依赖
npm install
```

### 2. 启动后端

```bash
python main.py runserver 127.0.0.1:9527
```

### 3. 启动前端（Vite 开发服务器）

```bash
cd frontend && npm run dev
```

### 4. 启动 Electron

```bash
npm run dev
```

> Electron 会等待后端 (`http://127.0.0.1:9527/api/`) 和 Vite (`http://localhost:5173`) 均就绪后再显示主窗口。

---

## 构建 & 发布

### 本地构建（仅生成安装包）

```powershell
.\build.ps1
```

构建流程：
1. 编译 Vue 前端 → `frontend/dist/`
2. 安装 Python 依赖
3. PyInstaller 打包 Django → `dist/app.exe`
4. electron-builder 打包为 NSIS 安装程序 → `dist/AI-Dianshang Setup x.x.x.exe`
5. 自动清理中间产物（`win-unpacked/`、`app.exe`）

### 发布到 GitHub Releases

```powershell
.\publish.ps1
```

发布流程：
1. 读取 `package.json` 中的 `version`
2. 检查远程是否已存在同名 tag（`v{version}`），已存在则跳过
3. 从 `.env.local` 读取 `github_token`，注入 `GH_TOKEN`
4. 调用 `build.ps1 -Publish` 完整重建，并以 `--publish always` 上传 Release
5. 自动创建 git tag 并推送到远程

**发版只需两步**：修改 `package.json` 中的 `version` → 运行 `.\publish.ps1`

### 环境变量配置

在项目根目录创建 `.env.local`（不要提交到 git）：

```
github_token=your_github_pat_token
```

GitHub Token 需要 `repo` 权限（用于创建 Release 和上传产物）。

---

## API Key 配置

Key 存储在用户本地 `localStorage`，不经过服务器，不会上传。

| 供应商 | 用途 | 配置入口 |
|--------|------|----------|
| 灵芽AI | 图片生成 | 首页「快速设置」|
| 云雾AI | 图片生成 | 首页「快速设置」|
| 灵芽AI（视频） | 视频生成 | 视频页「配置 API Key」|
| 云雾AI（视频） | 视频生成 | 视频页「配置 API Key」|

---

## 自动更新

- 启动后 **5 秒**自动静默检查
- 之后每 **6 小时**检查一次
- **设置页**可手动点击「检查更新」，实时展示检查 / 下载进度
- 下载完成后可「立即安装并重启」，或退出时自动安装

更新服务基于 GitHub Releases，配置见 `package.json`：

```json
"publish": {
  "provider": "github",
  "owner": "coder-th",
  "repo": "ai-dainshang"
}
```

---

## API 接口

后端监听 `http://127.0.0.1:9527`，核心端点：

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/generate/` | 图像生成 |
| `POST` | `/api/generate-video/` | 视频生成 |
| `GET` | `/api/proxy-image/?url=...` | 远程图片代理下载 |
| `GET/POST` | `/api/settings/` | 用户设置读写 |

---

## 扩展指引

### 新增图片模型

在 `frontend/src/config/models.js` 的 `IMAGE_MODELS` 数组追加配置（含 `supportedRatios`、`supportedSizes` 等字段），无需修改其他文件。

### 新增供应商

1. 在 `frontend/src/config/providers.js` 的 `PROVIDERS` 数组追加配置
2. 在 `backend/apps/core/providers.py` 中继承 `BaseImageProvider` 并注册到 `_IMAGE_PROVIDERS`

---

## 许可证

Copyright © 2026
