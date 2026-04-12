<template>
  <el-dialog
    :model-value="modelValue"
    width="900px"
    :close-on-click-modal="false"
    class="ihist-dialog"
    @open="onOpen"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <template #header>
      <div class="ihist-title-row">
        <div class="ihist-title-left">
          <div class="ihist-icon-badge">
            <el-icon size="18" color="var(--el-color-primary)"><Clock /></el-icon>
          </div>
          <span class="ihist-title">图片生成历史</span>
          <el-tag v-if="records.length > 0" type="info" size="small" effect="plain" class="ihist-count">
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
      class="ihist-retention-alert"
    >
      <template #default>
        历史数据仅保留最近 <strong>30 天</strong>，
        <strong>请及时将图片下载保存至本地</strong>。数据存储在本地数据库，换设备后无法访问。
      </template>
    </el-alert>

    <!-- 加载中 -->
    <div v-if="loading" class="ihist-loading">
      <el-icon size="32" class="ihist-spin"><Loading /></el-icon>
      <p>加载历史记录…</p>
    </div>

    <!-- 空状态 -->
    <div v-else-if="records.length === 0" class="ihist-empty">
      <el-icon size="64" color="var(--el-border-color)"><Picture /></el-icon>
      <p class="ihist-empty-title">暂无图片生成历史</p>
      <p class="ihist-empty-sub">完成图片生成后，记录会自动保存在这里</p>
    </div>

    <!-- 历史列表 -->
    <div v-else class="ihist-list">
      <div v-for="record in records" :key="record.id" class="ihist-item">

        <!-- 条目头部：状态 / 时间 / 模型 / 参数 / 删除 -->
        <div class="ihist-item-header">
          <div class="ihist-item-meta">
            <el-tag
              :type="statusTagType(record.status)"
              size="small"
              effect="light"
              class="status-tag"
            >
              <el-icon size="11">
                <CircleCheck v-if="record.status === 'done'" />
                <WarningFilled v-else-if="record.status === 'partial'" />
                <CircleClose v-else />
              </el-icon>
              {{ statusLabel(record.status) }}
            </el-tag>
            <span class="ihist-time">{{ formatDate(record.createdAt) }}</span>
            <span class="ihist-sep">·</span>
            <span class="ihist-model">{{ record.modelName }}</span>
            <el-tag v-if="record.aspectRatio" type="info" size="small" effect="plain" class="ihist-tag">
              {{ record.aspectRatio }}
            </el-tag>
            <el-tag v-if="record.imageSize" type="info" size="small" effect="plain" class="ihist-tag">
              {{ record.imageSize }}
            </el-tag>
            <el-tag v-if="record.search" type="warning" size="small" effect="plain" class="ihist-tag">
              联网
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
        <div class="ihist-prompt" :class="{ expanded: record._expanded }">
          {{ record.prompt }}
        </div>
        <button
          v-if="record.prompt.length > 100"
          class="ihist-expand-btn"
          @click="record._expanded = !record._expanded"
        >
          {{ record._expanded ? '收起' : '展开全文' }}
        </button>

        <!-- 参考图缩略图 -->
        <div v-if="record.baseImageThumbs?.length || record.refImageThumbs?.length" class="ihist-ref-images">
          <template v-if="record.baseImageThumbs?.length">
            <span class="ihist-images-label">底图：</span>
            <img
              v-for="(thumb, idx) in record.baseImageThumbs"
              :key="`base-${idx}`"
              :src="thumb"
              class="ihist-thumb"
              :title="`底图 ${idx + 1}`"
            />
          </template>
          <template v-if="record.refImageThumbs?.length">
            <span class="ihist-images-label" :class="{ 'ml-8': record.baseImageThumbs?.length }">参考图：</span>
            <img
              v-for="(thumb, idx) in record.refImageThumbs"
              :key="`ref-${idx}`"
              :src="thumb"
              class="ihist-thumb"
              :title="`参考图 ${idx + 1}`"
            />
          </template>
        </div>

        <!-- 统计信息行 -->
        <div class="ihist-stats">
          <span v-if="record.generationTimeMs" class="ihist-stat">
            <el-icon size="12"><Timer /></el-icon>
            耗时 {{ formatGenTime(record.generationTimeMs) }}
          </span>
          <span class="ihist-stat">
            <el-icon size="12"><Files /></el-icon>
            共 {{ record.results.length }} 张
          </span>
        </div>

        <!-- 生成图片网格 -->
        <div class="ihist-images-grid">
          <div
            v-for="result in record.results"
            :key="result.index"
            class="ihist-image-cell"
          >
            <template v-if="result.image_data || result.path">
              <el-image
                :src="imageSrc(result, record)"
                :preview-src-list="record.results.filter(r => r.image_data || r.path).map(r => imageSrc(r, record))"
                :initial-index="record.results.filter(r => r.image_data || r.path).findIndex(r => r.index === result.index)"
                fit="cover"
                class="ihist-image"
                lazy
              />
              <div class="ihist-image-footer">
                <span v-if="result.file_size" class="ihist-image-size">{{ result.file_size }}</span>
                <el-button
                  size="small"
                  type="primary"
                  text
                  class="ihist-dl-btn"
                  @click="downloadImage(result, record)"
                >
                  <el-icon><Download /></el-icon>
                  下载
                </el-button>
              </div>
              <div v-if="result.path" class="ihist-local-path" :title="result.path">
                <el-icon size="10"><FolderOpened /></el-icon>
                {{ result.path }}
              </div>
            </template>
            <div v-else class="ihist-image-error">
              <el-icon size="20" color="var(--el-color-danger)"><CircleClose /></el-icon>
              <span class="ihist-error-text">{{ result.error || '生成失败' }}</span>
            </div>
          </div>
        </div>

      </div>
    </div>

    <template #footer>
      <div class="ihist-footer">
        <div class="ihist-footer-left">
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
          <span class="ihist-footer-hint">
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
  Clock, Picture, Delete, Timer, Files,
  Download, CircleCheck, CircleClose, Loading, WarningFilled, FolderOpened,
} from '@element-plus/icons-vue'
import { loadImageHistory, deleteImageHistoryRecord, clearAllImageHistory } from '@/utils/imageHistory.js'

const props = defineProps({
  modelValue: { type: Boolean, required: true },
})
const emit = defineEmits(['update:modelValue'])

const records = ref([])
const loading = ref(false)

// 打开时从服务端加载
async function onOpen() {
  loading.value = true
  try {
    const raw = await loadImageHistory()
    records.value = raw.map(r => ({ ...r, _expanded: false }))
  } finally {
    loading.value = false
  }
}

// ─── 本地/远程图片源 ─────────────────────────────────────────────────────────

/** 有本地文件时走 /api/media/image/?id=N&index=I，否则用 base64 */
function imageSrc(result, record) {
  if (result.path) {
    return `/api/media/image/?id=${record.id}&index=${result.index ?? 0}`
  }
  return result.image_data || ''
}

function pathBasename(p) {
  return p ? p.replace(/\\/g, '/').split('/').pop() : ''
}

// ─── 状态标签 ─────────────────────────────────────────────────────────────────

function statusTagType(status) {
  if (status === 'done')    return 'success'
  if (status === 'partial') return 'warning'
  return 'danger'
}

function statusLabel(status) {
  if (status === 'done')    return '生成成功'
  if (status === 'partial') return '部分成功'
  return '生成失败'
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
  await deleteImageHistoryRecord(id)
  records.value = records.value.filter(r => r.id !== id)
  ElMessage.success('已删除该条记录')
}

async function clearAll() {
  await clearAllImageHistory()
  records.value = []
  ElMessage.success('历史记录已全部清空')
}

function downloadImage(result, record) {
  const src = imageSrc(result, record)
  const index = result.index ?? 0
  let ext = 'jpg'
  if (src.startsWith('data:image/png') || src.endsWith('.png')) ext = 'png'
  else if (src.endsWith('.webp')) ext = 'webp'
  const filename = `img_${record.model}_${index + 1}.${ext}`
  const a = document.createElement('a')
  a.href = src
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
}
</script>

<style scoped>
/* ── 标题行 ──────────────────────────────────────────────────────────────────── */
.ihist-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.ihist-title-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.ihist-icon-badge {
  width: 34px;
  height: 34px;
  background: rgba(251, 119, 1, 0.1);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.ihist-title {
  font-size: 16px;
  font-weight: 700;
}

.ihist-count {
  font-family: monospace;
}

/* ── 数据保留提示 ─────────────────────────────────────────────────────────────── */
.ihist-retention-alert {
  margin-bottom: 16px;
  border-radius: 8px;
}

/* ── 空状态 ──────────────────────────────────────────────────────────────────── */
.ihist-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 64px 24px;
  text-align: center;
}

.ihist-empty-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
  margin: 0;
}

.ihist-empty-sub {
  font-size: 13px;
  color: var(--el-text-color-placeholder);
  margin: 0;
}

/* ── 历史列表 ─────────────────────────────────────────────────────────────────── */
.ihist-list {
  max-height: calc(70vh - 200px);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-right: 4px;
}

.ihist-list::-webkit-scrollbar { width: 5px; }
.ihist-list::-webkit-scrollbar-track { background: transparent; }
.ihist-list::-webkit-scrollbar-thumb {
  background: var(--el-border-color);
  border-radius: 3px;
}

/* ── 单条记录 ─────────────────────────────────────────────────────────────────── */
.ihist-item {
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 10px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  transition: border-color 0.2s;
  background: var(--el-bg-color);
}

.ihist-item:hover {
  border-color: var(--el-border-color);
}

/* ── 条目头部 ─────────────────────────────────────────────────────────────────── */
.ihist-item-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.ihist-item-meta {
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

.ihist-time {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
}

.ihist-sep {
  color: var(--el-border-color);
}

.ihist-model {
  font-size: 13px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 200px;
}

.ihist-tag {
  flex-shrink: 0;
}

/* ── 提示词 ──────────────────────────────────────────────────────────────────── */
.ihist-prompt {
  font-size: 13px;
  color: var(--el-text-color-regular);
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  word-break: break-all;
}

.ihist-prompt.expanded {
  display: block;
  overflow: visible;
  -webkit-line-clamp: unset;
}

.ihist-expand-btn {
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
  font-size: 12px;
  color: var(--el-color-primary);
  line-height: 1.2;
  margin-top: -4px;
}

.ihist-expand-btn:hover {
  text-decoration: underline;
}

/* ── 参考图缩略图 ──────────────────────────────────────────────────────────────── */
.ihist-ref-images {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.ihist-images-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
}

.ihist-images-label.ml-8 {
  margin-left: 8px;
}

.ihist-thumb {
  width: 52px;
  height: 52px;
  object-fit: cover;
  border-radius: 6px;
  border: 1px solid var(--el-border-color-lighter);
  flex-shrink: 0;
}

/* ── 统计行 ──────────────────────────────────────────────────────────────────── */
.ihist-stats {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
}

.ihist-stat {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  white-space: nowrap;
}

/* ── 图片网格 ─────────────────────────────────────────────────────────────────── */
.ihist-images-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 10px;
}

.ihist-image-cell {
  display: flex;
  flex-direction: column;
  gap: 6px;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid var(--el-border-color-lighter);
}

.ihist-image {
  width: 100%;
  height: 160px;
  display: block;
  cursor: zoom-in;
}

.ihist-image-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 8px;
  background: var(--el-bg-color-page);
}

.ihist-image-size {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
}

.ihist-dl-btn {
  padding: 0;
  font-size: 12px;
}

.ihist-local-path {
  display: flex;
  align-items: flex-start;
  gap: 3px;
  padding: 3px 8px 5px;
  font-size: 10px;
  color: var(--el-color-success);
  font-family: monospace;
  word-break: break-all;
  white-space: normal;
  line-height: 1.5;
  background: var(--el-bg-color-page);
}

.ihist-image-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  height: 160px;
  background: var(--el-color-danger-light-9);
  padding: 12px;
}

.ihist-error-text {
  font-size: 11px;
  color: var(--el-color-danger);
  text-align: center;
  word-break: break-word;
}

/* ── 底部 ──────────────────────────────────────────────────────────────────────── */
.ihist-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.ihist-footer-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.ihist-footer-hint {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}

/* ── 全局弹窗 ─────────────────────────────────────────────────────────────────── */
:deep(.ihist-dialog .el-dialog__body) {
  padding: 16px 24px;
  max-height: 80vh;
  overflow: hidden;
}

/* ── 加载状态 ─────────────────────────────────────────────────────────────────── */
.ihist-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 48px 24px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

@keyframes ihist-spin {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}

.ihist-spin {
  animation: ihist-spin 1s linear infinite;
}
</style>
