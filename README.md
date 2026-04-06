# AI电商 — AI 图像创作桌面应用

基于 **Electron + Vue 3 + Django** 的本地 AI 图像生成工具。通过灵芽 AI 等多模型接口，支持批量基准图上传、参考图融合、多任务并发生成，并提供视频生成模块（开发中）。

---

## 技术栈

| 层次 | 技术 |
|------|------|
| 桌面壳 | Electron 29 |
| 前端 | Vue 3 + Vite + Element Plus |
| 后端 | Django 4.2 + Django REST Framework |
| 静态服务 | WhiteNoise |
| 打包 | PyInstaller + electron-builder (NSIS) |
| 数据库 | SQLite |

---

## 功能特性

- **多模型支持**：Nano-banana 2 / Pro / 通用、Seedream、Qwen、GPT-image、RMBG 等（可扩展）
- **批量生成**：上传多张基准图，每张独立任务并发执行
- **参考图融合**：支持最多 8 张参考图与所有基准图共享（1:N 关系）
- **参数精调**：比例（13 种）、分辨率（1K/2K/4K）、联网检索，按模型能力动态过滤
- **结果管理**：生成耗时 / 文件大小展示，全选 / 逐张勾选批量保存
- **图片预览**：上传预览与生成结果预览独立，支持大图轮播
- **下载代理**：后端转发远程图片，规避跨域限制
- **API 日志**：出站请求与响应按日期写入 JSONL 日志文件
- **视频生成**：页面框架已就绪，接口待接入
- **DevTools**：F12 切换开发者工具

---

## 项目结构

```
ai-dianshang/
├── electron/               # Electron 主进程
│   ├── main.js             # 应用入口，管理窗口 & 后端进程
│   └── preload.js          # IPC 桥接
├── frontend/               # Vue 3 前端
│   ├── src/
│   │   ├── views/          # HomeView（绘画）、VideoView（视频）
│   │   ├── components/     # ParamsPanel、ResultsSection 等
│   │   ├── composables/    # useImageUpload、useGeneration
│   │   ├── config/         # models.js（模型能力配置表）
│   │   ├── api/            # axios 封装
│   │   └── layouts/        # MainLayout（侧边栏 + TabBar）
│   └── package.json
├── backend/                # Django 后端
│   ├── apps/core/
│   │   ├── providers.py    # Provider 抽象层（图像 / 视频）
│   │   ├── views.py        # GenerateView、ProxyImageView 等
│   │   └── urls.py
│   └── config/
│       └── settings.py
├── build.ps1               # 一键构建脚本
├── dev.ps1                 # 开发启动脚本
├── requirements.txt        # Python 依赖
└── package.json            # Electron & 构建配置
```

---

## 快速开始（开发模式）

### 前置依赖

- Node.js ≥ 18
- Python ≥ 3.10
- npm / pip

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

## 构建生产包

```powershell
# 一键构建（前端 → PyInstaller → electron-builder）
./build.ps1
```

输出产物位于 `dist-electron/`，包含 Windows NSIS 安装包。

---

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `APP_DATA_DIR` | 打包后可写数据目录（数据库、日志） | exe 所在目录 |

---

## API 接口

后端监听 `http://127.0.0.1:9527`，以下为核心端点：

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/generate/` | 图像生成 |
| `POST` | `/api/generate-video/` | 视频生成（开发中） |
| `GET` | `/api/proxy-image/?url=...` | 远程图片代理下载 |

---

## 新增 AI 模型

1. 在 `frontend/src/config/models.js` 的 `IMAGE_MODELS` 数组中追加模型配置（含 `supportedRatios`、`supportedSizes`、`supportsSearch` 等字段）
2. 如需对接新的 AI 服务商，在 `backend/apps/core/providers.py` 中继承 `BaseImageProvider` 并注册到 `_IMAGE_PROVIDERS`

---

## 许可证

Copyright © 2024
