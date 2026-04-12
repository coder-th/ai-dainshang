<template>
  <el-dialog
    :model-value="modelValue"
    width="880px"
    :close-on-click-modal="false"
    class="vhist-dialog"
    @open="onOpen"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <template #header>
      <div class="vhist-title-row">
        <div class="vhist-title-left">
          <div class="vhist-icon-badge">
            <el-icon size="18" color="var(--el-color-primary)"><Clock /></el-icon>
          </div>
          <span class="vhist-title">视频生成历史</span>
          <el-tag v-if="records.length > 0" type="info" size="small" effect="plain" class="vhist-count">
            {{ records.length }} 条
          </el-tag>
        </div>
      </div>
    </template>

    <!-- 数据保留提示 -->
    <el-alert
      type="warning"
      :closable="false"
      show-icon
      class="vhist-retention-alert"
    >
      <template #default>
        历史数据仅保留最近 <strong>30 天</strong>，视频链接可能随时失效，
        <strong>请及时将视频下载保存至本地</strong>。数据存储在本地浏览器，换设备后无法访问。
      </template>
    </el-alert>

    <!-- 加载中 -->
    <div v-if="loading" class="vhist-loading">
      <el-icon size="32" class="vhist-spin"><Loading /></el-icon>
      <p>加载历史记录…</p>
    </div>

    <!-- 空状态 -->
    <div v-else-if="records.length === 0" class="vhist-empty">
      <el-icon size="64" color="var(--el-border-color)"><VideoCamera /></el-icon>
      <p class="vhist-empty-title">暂无视频生成历史</p>
      <p class="vhist-empty-sub">完成视频生成后，记录会自动保存在这里</p>
    </div>

    <!-- 历史列表 -->
    <div v-else class="vhist-list">
      <div v-for="record in records" :key="record.id" class="vhist-item">

        <!-- 条目头部：状态 / 时间 / 模型 / 参数 / 操作 -->
        <div class="vhist-item-header">
          <div class="vhist-item-meta">
            <el-tag
              :type="record.status === 'done' ? 'success' : 'danger'"
              size="small"
              effect="light"
              class="status-tag"
            >
              <el-icon size="11">
                <CircleCheck v-if="record.status === 'done'" />
                <CircleClose v-else />
              </el-icon>
              {{ record.status === 'done' ? '生成成功' : '生成失败' }}
            </el-tag>
            <span class="vhist-time">{{ formatDate(record.createdAt) }}</span>
            <span class="vhist-sep">·</span>
            <span class="vhist-model">{{ record.modelName }}</span>
            <el-tag
              v-if="record.ratio && supportsVideoAspectRatio(record.model)"
              type="info" size="small" effect="plain" class="vhist-tag"
            >
              {{ record.ratio }}
            </el-tag>
            <el-tag type="info" size="small" effect="plain" class="vhist-tag">
              {{ record.duration }} 秒
            </el-tag>
          </div>
          <el-button
            type="danger" text circle size="small"
            title="删除此条记录"
            @click="deleteRecord(record.id)"
          >
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>

        <!-- 提示词 -->
        <div class="vhist-prompt" :class="{ expanded: record._expanded }">
          {{ record.prompt }}
        </div>
        <button
          v-if="record.prompt.length > 100"
          class="vhist-expand-btn"
          @click="record._expanded = !record._expanded"
        >
          {{ record._expanded ? '收起' : '展开全文' }}
        </button>

        <!-- 参考图缩略图 -->
        <div v-if="record.thumbnails && record.thumbnails.length > 0" class="vhist-images">
          <span class="vhist-images-label">参考图：</span>
          <img
            v-for="(thumb, idx) in record.thumbnails"
            :key="idx"
            :src="thumb"
            class="vhist-thumb"
            :title="`参考图 ${idx + 1}`"
          />
          <span v-if="record.imageCount > record.thumbnails.length" class="vhist-more-count">
            共 {{ record.imageCount }} 张
          </span>
        </div>

        <!-- 统计信息行 -->
        <div class="vhist-stats">
          <span v-if="record.generationTimeMs" class="vhist-stat">
            <el-icon size="12"><Timer /></el-icon>
            耗时 {{ formatGenTime(record.generationTimeMs) }}
          </span>
          <span v-if="record.videoFileSize" class="vhist-stat">
            <el-icon size="12"><Document /></el-icon>
            {{ record.videoFileSize }}
          </span>
          <span
            v-if="record.taskId"
            class="vhist-stat vhist-taskid"
            title="点击复制任务ID"
            @click="copyTaskId(record.taskId)"
          >
            <el-icon size="12"><DocumentCopy /></el-icon>
            任务 ID: {{ record.taskId }}
          </span>
        </div>

        <!-- 视频播放器（生成成功时） -->
        <template v-if="record.status === 'done' && (record.videoPath || record.videoUrl)">
          <div class="vhist-video-wrap">
            <video
              :src="videoSrc(record)"
              controls
              class="vhist-video"
              preload="none"
            />
          </div>
          <div class="vhist-video-actions">
            <el-button
              size="small"
              type="success"
              :loading="record._downloading"
              @click="downloadVideo(record)"
            >
              <el-icon><Download /></el-icon>
              下载视频
            </el-button>
            <span v-if="record.videoPath" class="vhist-local-path" :title="record.videoPath">
              <el-icon size="11"><FolderOpened /></el-icon>
              本地：{{ record.videoPath }}
            </span>
            <span v-else class="vhist-link-hint">视频链接可能有时效限制，建议尽早下载</span>
          </div>
        </template>

        <!-- 错误信息（失败时） -->
        <div v-else-if="record.status !== 'done' && record.error" class="vhist-error">
          <el-icon size="13" color="var(--el-color-danger)"><Warning /></el-icon>
          {{ record.error }}
        </div>

        <!-- AI 优化提示词 -->
        <div v-if="record.enhancedPrompt" class="vhist-enhanced">
          <span class="vhist-enhanced-label">AI 优化提示词：</span>
          <span class="vhist-enhanced-text">{{ record.enhancedPrompt }}</span>
        </div>

      </div>
    </div>

    <template #footer>
      <div class="vhist-footer">
        <div class="vhist-footer-left">
          <el-popconfirm
            v-if="records.length > 0"
            title="确认清空所有历史记录？此操作不可恢复。"
            confirm-button-text="清空"
            cancel-button-text="取消"
            confirm-button-type="danger"
            width="240"
            @confirm="clearAll"
          >
            <template #reference>
              <el-button type="danger" plain size="small">
                <el-icon><Delete /></el-icon>
                清空历史
              </el-button>
            </template>
          </el-popconfirm>
          <span class="vhist-footer-hint">
            {{ records.length > 0 ? `共 ${records.length} 条，仅保留最近 30 天` : '暂无记录' }}
          </span>
        </div>
        <el-button type="primary" @click="$emit('update:modelValue', false)">关闭</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Clock, VideoCamera, Delete, Timer, Document, DocumentCopy,
  Warning, Download, CircleCheck, CircleClose, Loading, FolderOpened,
} from '@element-plus/icons-vue'
import { supportsVideoAspectRatio } from '@/config/models.js'
import { loadHistory, deleteHistoryRecord, clearAllHistory } from '@/utils/videoHistory.js'

const props = defineProps({
  modelValue: { type: Boolean, required: true },
})
const emit = defineEmits(['update:modelValue'])

const records = ref([])
const loading = ref(false)

// 打开时从服务端加载，附加 UI 专属字段（不持久化）
async function onOpen() {
  loading.value = true
  try {
    const raw = await loadHistory()
    records.value = raw.map(r => ({ ...r, _expanded: false, _downloading: false }))
  } finally {
    loading.value = false
  }
}

// ─── 本地/远程视频源 ─────────────────────────────────────────────────────────

/** 有本地文件时走 /api/media/video/?id=N，否则用远程 URL */
function videoSrc(record) {
  if (record.videoPath) {
    return `/api/media/video/?id=${record.id}`
  }
  return record.videoUrl || ''
}

// ─── 日期 / 时间格式化 ─────────────────────────────────────────────────────────

function formatDate(iso) {
  const d   = new Date(iso)
  const pad = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function formatGenTime(ms) {
  const s = Math.round(ms / 1000)
  if (s < 60) return `${s} 秒`
  const m = Math.floor(s / 60), r = s % 60
  return r > 0 ? `${m} 分 ${r} 秒` : `${m} 分`
}

// ─── 操作 ──────────────────────────────────────────────────────────────────────

async function deleteRecord(id) {
  await deleteHistoryRecord(id)
  records.value = records.value.filter(r => r.id !== id)
  ElMessage.success('已删除该条记录')
}

async function clearAll() {
  await clearAllHistory()
  records.value = []
  ElMessage.success('历史记录已全部清空')
}

function copyTaskId(taskId) {
  navigator.clipboard?.writeText(taskId)
    .then(()  => ElMessage.success('任务 ID 已复制'))
    .catch(()  => ElMessage.warning('复制失败，请手动选中复制'))
}

async function downloadVideo(record) {
  if (record._downloading) return
  const filename = `veo_${record.model}_${record.taskId || Date.now()}.mp4`
  record._downloading = true
  // 优先下载本地已缓存文件
  const src = videoSrc(record)
  try {
    const resp = await fetch(src)
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    const blob   = await resp.blob()
    const blobUrl = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = blobUrl
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    setTimeout(() => URL.revokeObjectURL(blobUrl), 60000)
  } catch {
    // CORS fallback：直接触发链接
    const a = document.createElement('a')
    a.href = src
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
  } finally {
    record._downloading = false
  }
}
</script>

<style scoped>
/* ── 标题行 ──────────────────────────────────────────────────────────────────── */
.vhist-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.vhist-title-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.vhist-icon-badge {
  width: 34px;
  height: 34px;
  background: rgba(251, 119, 1, 0.1);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.vhist-title {
  font-size: 16px;
  font-weight: 700;
}

.vhist-count {
  font-family: monospace;
}

/* ── 数据保留提示 ─────────────────────────────────────────────────────────────── */
.vhist-retention-alert {
  margin-bottom: 16px;
  border-radius: 8px;
}

/* ── 空状态 ──────────────────────────────────────────────────────────────────── */
.vhist-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 64px 24px;
  text-align: center;
}

.vhist-empty-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
  margin: 0;
}

.vhist-empty-sub {
  font-size: 13px;
  color: var(--el-text-color-placeholder);
  margin: 0;
}

/* ── 历史列表 ─────────────────────────────────────────────────────────────────── */
.vhist-list {
  max-height: calc(70vh - 200px);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-right: 4px;
}

/* 滚动条美化 */
.vhist-list::-webkit-scrollbar { width: 5px; }
.vhist-list::-webkit-scrollbar-track { background: transparent; }
.vhist-list::-webkit-scrollbar-thumb {
  background: var(--el-border-color);
  border-radius: 3px;
}

/* ── 单条记录 ─────────────────────────────────────────────────────────────────── */
.vhist-item {
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 10px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  transition: border-color 0.2s;
  background: var(--el-bg-color);
}

.vhist-item:hover {
  border-color: var(--el-border-color);
}

/* ── 条目头部 ─────────────────────────────────────────────────────────────────── */
.vhist-item-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.vhist-item-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  min-width: 0;
}

.status-tag {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  flex-shrink: 0;
}

.vhist-time {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
}

.vhist-sep {
  color: var(--el-border-color);
}

.vhist-model {
  font-size: 13px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 200px;
}

.vhist-tag {
  flex-shrink: 0;
}

/* ── 提示词 ──────────────────────────────────────────────────────────────────── */
.vhist-prompt {
  font-size: 13px;
  color: var(--el-text-color-regular);
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  word-break: break-all;
}

.vhist-prompt.expanded {
  display: block;
  overflow: visible;
  -webkit-line-clamp: unset;
}

.vhist-expand-btn {
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
  font-size: 12px;
  color: var(--el-color-primary);
  line-height: 1.2;
  margin-top: -4px;
}

.vhist-expand-btn:hover {
  text-decoration: underline;
}

/* ── 参考图 ──────────────────────────────────────────────────────────────────── */
.vhist-images {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.vhist-images-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
}

.vhist-thumb {
  width: 52px;
  height: 52px;
  object-fit: cover;
  border-radius: 6px;
  border: 1px solid var(--el-border-color-lighter);
  flex-shrink: 0;
}

.vhist-more-count {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
}

/* ── 统计行 ──────────────────────────────────────────────────────────────────── */
.vhist-stats {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
}

.vhist-stat {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
}

.vhist-taskid {
  cursor: pointer;
  font-family: monospace;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 320px;
  white-space: nowrap;
  transition: color 0.2s;
}

.vhist-taskid:hover {
  color: var(--el-color-primary);
}

/* ── 视频播放器 ───────────────────────────────────────────────────────────────── */
.vhist-video-wrap {
  width: 100%;
  background: #000;
  border-radius: 8px;
  overflow: hidden;
}

.vhist-video {
  width: 100%;
  max-height: 260px;
  display: block;
  border-radius: 8px;
}

.vhist-video-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.vhist-link-hint {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
}

.vhist-local-path {
  display: inline-flex;
  align-items: flex-start;
  gap: 4px;
  font-size: 11px;
  color: var(--el-color-success);
  font-family: monospace;
  word-break: break-all;
  white-space: normal;
  line-height: 1.5;
}

/* ── 错误信息 ─────────────────────────────────────────────────────────────────── */
.vhist-error {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--el-color-danger);
  padding: 8px 12px;
  background: var(--el-color-danger-light-9);
  border-radius: 6px;
  line-height: 1.5;
  word-break: break-word;
}

/* ── AI 优化提示词 ─────────────────────────────────────────────────────────────── */
.vhist-enhanced {
  padding: 8px 12px;
  background: var(--el-bg-color-page);
  border-radius: 6px;
  font-size: 12px;
  line-height: 1.6;
  color: var(--el-text-color-regular);
}

.vhist-enhanced-label {
  font-weight: 600;
  color: var(--el-text-color-secondary);
  margin-right: 4px;
}

/* ── 底部 ──────────────────────────────────────────────────────────────────────── */
.vhist-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.vhist-footer-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.vhist-footer-hint {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}

/* ── 全局弹窗宽度自适应 ───────────────────────────────────────────────────────── */
:deep(.vhist-dialog .el-dialog__body) {
  padding: 16px 24px;
  max-height: 80vh;
  overflow: hidden;
}

/* ── 加载状态 ─────────────────────────────────────────────────────────────────── */
.vhist-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 48px 24px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

@keyframes vhist-spin {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}

.vhist-spin {
  animation: vhist-spin 1s linear infinite;
}
</style>
