<template>
  <div class="video-page">
    <!-- Page Header -->
    <div class="page-header">
      <div class="hero-section">
        <div class="hero-icon-wrap">
          <el-icon size="32" color="var(--el-color-primary)"><VideoCamera /></el-icon>
        </div>
        <div class="hero-text">
          <h1 class="hero-title">AI视频创作</h1>
          <p class="hero-subtitle">Google Veo 系列模型 · 支持音频生成 · 文生视频 / 图生视频</p>
        </div>
      </div>
      <div class="header-actions">
        <el-button size="large" @click="openHistoryDialog">
          <el-icon><List /></el-icon>
          历史记录
        </el-button>
        <el-button
          :type="anyVideoKeyConfigured ? 'default' : 'warning'"
          size="large"
          @click="openApiKeyDialog"
        >
          <el-icon><Key /></el-icon>
          {{ anyVideoKeyConfigured ? '已配置 API Key' : '配置 API Key' }}
        </el-button>
        <el-button type="primary" size="large" @click="addCard">
          <el-icon><Plus /></el-icon>
          增加视频创作卡片
        </el-button>
      </div>
    </div>

    <!-- API Key未配置时的提示横幅 -->
    <el-alert
      v-if="!anyVideoKeyConfigured"
      type="warning"
      show-icon
      :closable="false"
      class="key-alert"
    >
      <template #default>
        请先配置灵芽AI或云雾AI的视频 API Key，才能使用视频生成功能。
        <el-button type="warning" link @click="openApiKeyDialog">立即配置</el-button>
      </template>
    </el-alert>

    <!-- Empty State -->
    <div v-if="cards.length === 0" class="empty-state">
      <el-icon size="64" color="var(--el-border-color)"><VideoCamera /></el-icon>
      <p class="empty-title">暂无视频创作任务</p>
      <p class="empty-sub">点击上方按钮，开始创作您的第一个 AI 视频</p>
      <el-button type="primary" @click="addCard">
        <el-icon><Plus /></el-icon>
        增加视频创作卡片
      </el-button>
    </div>

    <!-- Video Cards -->
    <div class="cards-container">
      <el-card
        v-for="card in cards"
        :key="card.id"
        class="video-card"
        shadow="hover"
      >
        <!-- Card Header -->
        <template #header>
          <div class="card-header">
            <div class="card-header-left">
              <div class="icon-badge icon-badge--primary">
                <el-icon size="18"><VideoCamera /></el-icon>
              </div>
              <span class="card-title">AI视频创作</span>
              <el-select
                v-model="card.model"
                class="model-select"
                placeholder="选择视频模型"
                @change="onModelChange(card)"
              >
                <el-option-group
                  v-for="group in MODEL_GROUPS"
                  :key="group.label"
                  :label="group.label"
                >
                  <el-option
                    v-for="m in group.models"
                    :key="m.id"
                    :label="m.name"
                    :value="m.id"
                    :disabled="m.disabled"
                  >
                    <div class="model-option">
                      <span>{{ m.name }}</span>
                      <el-tag size="small" class="model-tag" :type="getTagType(m.tag)">{{ m.tag }}</el-tag>
                    </div>
                  </el-option>
                </el-option-group>
              </el-select>
            </div>
            <el-button type="danger" text circle @click="removeCard(card.id)">
              <el-icon><Close /></el-icon>
            </el-button>
          </div>
        </template>

        <!-- Model Desc -->
        <div class="model-desc-bar">
          <el-icon size="14" color="var(--el-text-color-placeholder)"><InfoFilled /></el-icon>
          <span class="model-desc-text">{{ currentModelOf(card).desc }}</span>
        </div>

        <!-- Card Body -->
        <div class="card-body">
          <!-- Left: Controls -->
          <div class="card-controls">

            <!-- Image Upload (conditional based on model) -->
            <div
              v-if="getVideoModelImageCapability(card.model).maxImages > 0"
              class="control-section"
            >
              <div class="control-label-row">
                <label class="control-label">{{ getVideoModelImageCapability(card.model).label }}</label>
                <el-tag size="small" type="info">
                  最多 {{ getVideoModelImageCapability(card.model).maxImages }} 张
                </el-tag>
              </div>
              <div class="image-upload-area">
                <div
                  v-for="(img, idx) in card.images"
                  :key="idx"
                  class="image-preview-item"
                >
                  <img :src="img" class="preview-img" />
                  <button class="remove-img-btn" @click="removeImage(card, idx)">
                    <el-icon size="12"><Close /></el-icon>
                  </button>
                </div>
                <div
                  v-if="card.images.length < getVideoModelImageCapability(card.model).maxImages"
                  class="image-upload-trigger"
                  @click="triggerImageUpload(card)"
                >
                  <el-icon size="22" color="var(--el-text-color-placeholder)"><Plus /></el-icon>
                  <span>上传图片</span>
                </div>
              </div>
              <input
                :ref="el => setFileInputRef(card.id, el)"
                type="file"
                accept="image/*"
                multiple
                style="display: none"
                :max="getVideoModelImageCapability(card.model).maxImages"
                @change="onImageSelected(card, $event)"
              />
            </div>

            <!-- Prompt -->
            <div class="control-section">
              <label class="control-label">创意提示词</label>
              <div class="textarea-wrap">
                <el-input
                  v-model="card.prompt"
                  type="textarea"
                  :rows="5"
                  placeholder="描述您想生成的视频内容，越详细越好，例如：夕阳下一匹白马在草原上奔跑，镜头缓慢推进，写实风格…"
                  resize="none"
                />
                <span class="char-count">{{ card.prompt.length }} 字符</span>
              </div>
            </div>

            <!-- Params -->
            <div class="control-section params-row">
              <!-- Ratio (veo3 only) -->
              <div v-if="supportsVideoAspectRatio(card.model)" class="param-item">
                <label class="param-label">视频比例</label>
                <el-select v-model="card.ratio" class="param-select">
                  <el-option
                    v-for="opt in VIDEO_RATIO_OPTIONS"
                    :key="opt.value"
                    :label="opt.label"
                    :value="opt.value"
                  />
                </el-select>
              </div>
              <!-- Duration -->
              <div class="param-item">
                <label class="param-label">视频时长</label>
                <el-select v-model="card.duration" class="param-select">
                  <el-option
                    v-for="opt in VIDEO_DURATION_OPTIONS"
                    :key="opt.value"
                    :label="opt.label"
                    :value="opt.value"
                  />
                </el-select>
              </div>
            </div>
          </div>

          <!-- Right: Result -->
          <div class="card-result">
            <!-- Video Player -->
            <div v-if="card.videoUrl" class="video-player-wrap">
              <!-- 元数据加载中占位 -->
              <div v-if="card.videoLoading" class="video-meta-loading">
                <el-icon size="32" class="spin-icon"><Loading /></el-icon>
                <p>视频加载中，请稍候…</p>
              </div>
              <video
                v-show="!card.videoLoading"
                :src="card.videoUrl"
                controls
                class="video-player"
                preload="metadata"
                @loadedmetadata="onVideoMetadataLoaded(card, $event)"
              />
              <div v-show="!card.videoLoading" class="video-actions">
                <el-button size="small" type="success" :loading="card.downloading" @click="downloadVideo(card)">
                  <el-icon><Download /></el-icon>
                  下载视频
                </el-button>
                <el-tag type="success" size="small">生成完成</el-tag>
              </div>
              <!-- 底部统计 -->
              <div v-if="!card.videoLoading && (card.generationTimeMs || card.videoFileSize)" class="video-stats-row">
                <span v-if="card.generationTimeMs" class="stat-item">
                  <el-icon size="12"><Timer /></el-icon>
                  {{ formatGenTime(card.generationTimeMs) }}
                </span>
                <span v-if="card.videoFileSize" class="stat-item">
                  <el-icon size="12"><Document /></el-icon>
                  {{ card.videoFileSize }}
                </span>
              </div>
              <!-- 增强后的 prompt -->
              <div v-if="card.enhancedPrompt" class="enhanced-prompt">
                <span class="enhanced-prompt-label">优化后的提示词：</span>
                <span class="enhanced-prompt-text">{{ card.enhancedPrompt }}</span>
              </div>
            </div>

            <!-- Submitting -->
            <div v-else-if="card.status === 'submitting'" class="result-loading">
              <el-icon size="44" class="spin-icon"><Loading /></el-icon>
              <p class="loading-text">提交任务中…</p>
            </div>

            <!-- Error -->
            <div v-else-if="card.status === 'error'" class="result-error">
              <el-icon size="44" color="var(--el-color-danger)"><Warning /></el-icon>
              <p class="error-text">{{ card.error }}</p>
              <el-button type="primary" text @click="card.status = 'idle'; card.error = null">
                重新填写
              </el-button>
            </div>

            <!-- Auto-polling: actively querying task status -->
            <div v-else-if="card.isAutoPolling" class="result-polling">
              <div class="poll-ring">
                <el-icon size="40" class="spin-icon"><Loading /></el-icon>
              </div>
              <!-- 模拟进度条 -->
              <div class="mock-progress-wrap">
                <el-progress
                  :percentage="card.mockProgress"
                  :stroke-width="7"
                  :show-text="false"
                  status=""
                />
                <span class="mock-progress-pct">{{ card.mockProgress }}%</span>
              </div>
              <p class="poll-status-text">{{ card.statusText || '查询视频状态中…' }}</p>
              <el-tag type="info" size="small" class="task-id-tag" effect="plain">
                ID: {{ card.taskId }}
              </el-tag>
              <p class="poll-hint">自动每 10 秒查询一次，完成后自动展示视频</p>
            </div>

            <!-- Task submitted but auto-polling ended (timeout / manual mode) -->
            <div v-else-if="card.taskId" class="result-pending">
              <el-icon size="44" color="var(--el-color-warning)"><Clock /></el-icon>
              <p class="pending-title">任务已提交</p>
              <p class="pending-sub">{{ card.statusText || '请点击下方"查询任务"获取最新状态' }}</p>
              <el-tag type="warning" size="small" class="task-id-tag" effect="plain">
                ID: {{ card.taskId }}
              </el-tag>
            </div>

            <!-- Placeholder -->
            <div v-else class="result-placeholder">
              <el-icon size="56" color="var(--el-border-color)"><VideoCamera /></el-icon>
              <p class="placeholder-title">等待生成</p>
              <p class="placeholder-sub">填写左侧参数后点击"生成视频"</p>
            </div>
          </div>
        </div>

        <!-- Card Footer -->
        <div class="card-footer">
          <div class="footer-info">
            <el-tag v-if="card.isAutoPolling" type="info" size="small" effect="plain">
              <el-icon class="spin-icon-sm"><Loading /></el-icon>
              轮询中
            </el-tag>
            <el-tag v-else-if="card.taskId && card.status !== 'done' && card.status !== 'error'" type="warning" size="small" effect="plain">
              <el-icon><Clock /></el-icon>
              待查询
            </el-tag>
            <el-tag v-if="card.status === 'done'" type="success" size="small">
              <el-icon><CircleCheck /></el-icon>
              已完成
            </el-tag>
          </div>
          <div class="footer-actions">
            <!-- 手动查询（仅在自动轮询停止后显示） -->
            <el-button
              v-if="card.taskId && !card.isAutoPolling && card.status !== 'done'"
              :loading="card.status === 'querying'"
              :disabled="card.status === 'submitting'"
              @click="queryTaskManual(card)"
            >
              <el-icon><Refresh /></el-icon>
              查询任务
            </el-button>
            <el-button
              type="primary"
              :loading="card.status === 'submitting'"
              :disabled="!card.prompt.trim() || card.status === 'submitting' || card.isAutoPolling"
              @click="generateVideo(card)"
            >
              <el-icon v-if="card.status !== 'submitting'"><VideoPlay /></el-icon>
              {{ card.status === 'submitting' ? '提交中…' : (card.taskId ? '重新生成' : '生成视频') }}
            </el-button>
          </div>
        </div>
      </el-card>
    </div>
  </div>

  <!-- API Key 配置弹窗 -->
  <QuickSettingsDialog v-model="showApiKeyDialog" :active-provider="apiKeyDialogProvider" />

  <!-- 视频历史记录弹窗 -->
  <VideoHistoryDialog v-model="showHistoryDialog" />
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  VideoCamera, VideoPlay, Plus, Close, Refresh, Download,
  Loading, Warning, Clock, CircleCheck, InfoFilled, Key, Timer, Document, List,
} from '@element-plus/icons-vue'
import {
  VIDEO_MODELS, VIDEO_RATIO_OPTIONS, VIDEO_DURATION_OPTIONS,
  getVideoModelImageCapability, supportsVideoAspectRatio,
  getVideoModelById, getVideoModelGroups,
} from '@/config/models.js'
import { videoApi } from '@/api/index.js'
import { getApiKey } from '@/config/providers.js'
import QuickSettingsDialog from '@/components/QuickSettingsDialog.vue'
import VideoHistoryDialog from '@/components/VideoHistoryDialog.vue'
import { appendHistory, createThumbnail } from '@/utils/videoHistory.js'

// ─── Model Groups for el-option-group ─────────────────────────────────────────
const MODEL_GROUPS = getVideoModelGroups()

// ─── API Key 配置弹窗 ──────────────────────────────────────────────────────────
const showApiKeyDialog = ref(false)
// 任意一个视频 provider 已配置即视为就绪
const anyVideoKeyConfigured = computed(() =>
  !!getApiKey('yunwu_video') || !!getApiKey('lingy_video')
)
// 弹窗默认打开的 Tab：优先跳到尚未配置的那个，都未配置时默认灵芽
const apiKeyDialogProvider = computed(() => {
  if (!getApiKey('lingy_video')) return 'lingy_video'
  if (!getApiKey('yunwu_video')) return 'yunwu_video'
  return 'lingy_video'
})

function openApiKeyDialog() {
  showApiKeyDialog.value = true
}

// ─── 历史记录弹窗 ──────────────────────────────────────────────────────────────
const showHistoryDialog = ref(false)

function openHistoryDialog() {
  showHistoryDialog.value = true
}

/**
 * 将已完成（done/error）的卡片状态写入历史记录。
 * 异步生成缩略图后通过 API 持久化到 SQLite，不阻塞主流程。
 */
async function saveToHistory(card) {
  try {
    const model      = getVideoModelById(card.model)
    const thumbnails = []
    for (const img of card.images.slice(0, 3)) {
      if (img) {
        const thumb = await createThumbnail(img, 80)
        if (thumb) thumbnails.push(thumb)
      }
    }
    await appendHistory({
      model:            card.model,
      modelName:        model.name,
      prompt:           card.prompt,
      thumbnails,
      imageCount:       card.images.length,
      ratio:            card.ratio,
      duration:         card.duration,
      taskId:           card.taskId   || null,
      status:           card.status,           // 'done' | 'error'
      videoUrl:         card.videoUrl || null,
      error:            card.error    || null,
      generationTimeMs: card.generationTimeMs || 0,
      enhancedPrompt:   card.enhancedPrompt   || '',
      videoFileSize:    card.videoFileSize     || '',
    })
  } catch (e) {
    console.warn('[VideoHistory] 保存历史失败:', e)
  }
}

// ─── Card State ────────────────────────────────────────────────────────────────
let _nextId = 1

function createCard() {
  return {
    id: _nextId++,
    model: VIDEO_MODELS[0]?.id || 'veo3.1-fast',
    prompt: '',
    images: [],
    ratio: '9:16',          // 默认竖屏，适合大多数场景，用户可选（仅 veo3 系列支持）
    duration: 8,
    status: 'idle',         // idle | submitting | querying | done | error
    taskId: null,
    videoUrl: null,
    error: null,
    statusText: '',         // 当前步骤描述（轮询中展示）
    isAutoPolling: false,   // 自动轮询是否进行中
    enhancedPrompt: '',     // API 返回的优化后提示词
    videoLoading: false,    // video 元素元数据是否已加载
    downloading: false,     // 下载中状态
    mockProgress: 0,        // 模拟进度 0-100
    startTime: 0,           // 提交时间戳（ms）
    generationTimeMs: 0,    // 总生成耗时（ms）
    videoFileSize: '',      // 格式化后的文件大小
  }
}

const cards = ref([])

function addCard() {
  cards.value.push(createCard())
}

function removeCard(id) {
  const card = cards.value.find(c => c.id === id)
  if (card) _stopAutoPolling(card)
  const idx = cards.value.findIndex(c => c.id === id)
  if (idx !== -1) cards.value.splice(idx, 1)
}

// ─── 轮询常量 & 计时器 ────────────────────────────────────────────────────────
const POLL_INTERVAL_MS = 20000   // 每 10 秒查询一次
const MAX_POLL_ATTEMPTS = 30     // 最多 30 次 ≈ 10 分钟

// 计时器 & 计数器（不放进 reactive，避免 Vue 包装 setInterval 句柄）
const _pollingTimers   = new Map()   // cardId → intervalId
const _pollingAttempts = new Map()   // cardId → number

function _startAutoPolling(card) {
  _stopAutoPolling(card)
  _pollingAttempts.set(card.id, 0)
  card.isAutoPolling = true
  _pollOnce(card)                                          // 立即查询一次
  _pollingTimers.set(card.id, setInterval(() => _pollOnce(card), POLL_INTERVAL_MS))
}

function _stopAutoPolling(card) {
  const timer = _pollingTimers.get(card.id)
  if (timer) { clearInterval(timer); _pollingTimers.delete(card.id) }
  _pollingAttempts.delete(card.id)
  card.isAutoPolling = false
}

async function _pollOnce(card) {
  const attempts = (_pollingAttempts.get(card.id) ?? 0) + 1
  _pollingAttempts.set(card.id, attempts)

  // 更新模拟进度（0 → 95，到达终态时跳到 100）
  card.mockProgress = Math.min(95, Math.round((attempts / MAX_POLL_ATTEMPTS) * 100))

  if (attempts > MAX_POLL_ATTEMPTS) {
    _stopAutoPolling(card)
    card.statusText = '自动查询超时，请手动点击"查询任务"获取最新状态'
    return
  }

  const apiKey = getApiKey(getVideoModelById(card.model).provider)   // Fix 1
  if (!apiKey) { _stopAutoPolling(card); return }

  try {
    const { data } = await videoApi.queryTask({
      task_id: card.taskId,
      api_key: apiKey,
      model: card.model,
    })

    if (data.status_text) card.statusText = data.status_text

    if (data.status === 'done') {
      _stopAutoPolling(card)
      card.generationTimeMs = Date.now() - card.startTime  // Fix 6
      card.mockProgress     = 100
      card.videoUrl         = data.video_url
      card.videoLoading     = true                          // Fix 3
      card.enhancedPrompt   = data.enhanced_prompt || ''
      card.status           = 'done'
      ElMessage.success('视频生成完成！')
      saveToHistory(card)
    } else if (data.status === 'error') {
      _stopAutoPolling(card)
      card.error  = data.error || '任务失败'
      card.status = 'error'
      ElMessage.error(card.error)
      saveToHistory(card)
    }
    // status === 'pending' → 继续轮询
  } catch {
    // 网络抖动不中断轮询，静默重试
  }
}

// 页面卸载时清理所有计时器
onUnmounted(() => {
  for (const timer of _pollingTimers.values()) clearInterval(timer)
  _pollingTimers.clear()
})
function currentModelOf(card) {
  return getVideoModelById(card.model)
}

function onModelChange(card) {
  const cap = getVideoModelImageCapability(card.model)
  // 裁剪超出数量的图片
  if (card.images.length > cap.maxImages) {
    card.images = card.images.slice(0, cap.maxImages)
  }
}

function getTagType(tag) {
  const map = { '推荐': 'success', '高质量': 'warning', '4K': 'primary', '4K高质量': 'danger' }
  return map[tag] || 'info'
}

// ─── Image Upload ──────────────────────────────────────────────────────────────
const fileInputRefs = ref({})

function setFileInputRef(cardId, el) {
  if (el) {
    fileInputRefs.value[cardId] = el
  } else {
    delete fileInputRefs.value[cardId]
  }
}

function triggerImageUpload(card) {
  const input = fileInputRefs.value[card.id]
  if (input) {
    input.value = ''
    input.click()
  }
}

async function onImageSelected(card, event) {
  const files = Array.from(event.target.files || [])
  if (!files.length) return

  const cap = getVideoModelImageCapability(card.model)
  const remaining = cap.maxImages - card.images.length
  const toProcess = files.slice(0, remaining)

  for (const file of toProcess) {
    const base64 = await fileToBase64(file)
    card.images.push(base64)
  }
}

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result)
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

function removeImage(card, idx) {
  card.images.splice(idx, 1)
}

// ─── Video Generation ──────────────────────────────────────────────────────────
async function generateVideo(card) {
  if (!card.prompt.trim()) {
    ElMessage.warning('请填写创意提示词')
    return
  }

  const provider = getVideoModelById(card.model).provider  // Fix 1
  const apiKey = getApiKey(provider)
  if (!apiKey) {
    ElMessage.error('请先在设置中配置 API Key')
    return
  }

  _stopAutoPolling(card)

  card.status         = 'submitting'
  card.error          = null
  card.taskId         = null
  card.videoUrl       = null
  card.statusText     = ''
  card.enhancedPrompt = ''
  card.mockProgress   = 0        // Fix 5
  card.startTime      = Date.now()  // Fix 6
  card.generationTimeMs = 0
  card.videoFileSize  = ''

  try {
    const payload = {
      api_key: apiKey,
      model:   card.model,
      prompt:  card.prompt,
      duration: card.duration,
      images:  card.images,
    }
    if (supportsVideoAspectRatio(card.model)) {
      payload.aspect_ratio = card.ratio
    }

    const { data } = await videoApi.generate(payload)

    if (data.task_id) {
      card.taskId     = data.task_id
      card.status     = 'idle'
      card.statusText = '任务已提交，正在为您查询视频创作状态…'
      ElMessage.success(`视频任务提交完成，ID：${data.task_id}，正在持续追踪进度`)
      _startAutoPolling(card)
    } else if (data.video_url) {
      card.generationTimeMs = Date.now() - card.startTime
      card.videoUrl     = data.video_url
      card.videoLoading = true   // Fix 3
      card.mockProgress = 100
      card.status       = 'done'
      ElMessage.success('视频生成完成！')
      saveToHistory(card)
    } else if (data.error) {
      card.error  = data.error
      card.status = 'error'
      ElMessage.error(data.error)
      saveToHistory(card)
    } else {
      card.error  = '未知响应格式'
      card.status = 'error'
      saveToHistory(card)
    }
  } catch (err) {
    const msg = err.response?.data?.error || err.message || '网络错误，请重试'
    card.error  = msg
    card.status = 'error'
    ElMessage.error(msg)
    saveToHistory(card)
  }
}

// ─── 手动查询（自动轮询超时后备用） ───────────────────────────────────────────
async function queryTaskManual(card) {
  if (!card.taskId) return

  const provider = getVideoModelById(card.model).provider  // Fix 1
  const apiKey = getApiKey(provider)
  if (!apiKey) {
    ElMessage.error('请先配置 API Key')
    return
  }

  card.status = 'querying'

  try {
    const { data } = await videoApi.queryTask({
      task_id: card.taskId,
      api_key: apiKey,
      model:   card.model,
    })

    if (data.status_text) card.statusText = data.status_text

    if (data.status === 'done') {
      card.generationTimeMs = Date.now() - card.startTime   // Fix 6
      card.mockProgress     = 100
      card.videoUrl         = data.video_url
      card.videoLoading     = true                          // Fix 3
      card.enhancedPrompt   = data.enhanced_prompt || ''
      card.status           = 'done'
      ElMessage.success('视频生成完成！')
      saveToHistory(card)
    } else if (data.status === 'error') {
      card.error  = data.error || '任务失败'
      card.status = 'error'
      ElMessage.error(card.error)
      saveToHistory(card)
    } else {
      card.status = 'idle'
      ElMessage.info(`当前状态：${data.status_text || '生成中'}，已重新开启自动查询`)
      _startAutoPolling(card)
    }
  } catch (err) {
    const msg = err.response?.data?.error || err.message || '查询失败'
    card.status = 'idle'
    ElMessage.error(msg)
  }
}

// ─── 视频元数据加载回调（Fix 3 + Fix 6 文件大小）─────────────────────────────
async function onVideoMetadataLoaded(card) {
  card.videoLoading = false
  if (card.videoFileSize) return   // 已有大小（下载时获取）
  try {
    const resp = await fetch(card.videoUrl, { method: 'HEAD', mode: 'cors' })
    const size = parseInt(resp.headers.get('content-length') || '0')
    if (size > 0) card.videoFileSize = formatBytes(size)
  } catch { /* CORS 限制时静默失败 */ }
}

// ─── 下载视频到本地（Fix 4）─────────────────────────────────────────────────
async function downloadVideo(card) {
  if (!card.videoUrl || card.downloading) return
  const filename = `veo_${card.model}_${Date.now()}.mp4`
  card.downloading = true
  try {
    const resp = await fetch(card.videoUrl)
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    const blob = await resp.blob()
    // 顺便更新文件大小
    if (!card.videoFileSize && blob.size > 0) card.videoFileSize = formatBytes(blob.size)
    const blobUrl = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = blobUrl
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    setTimeout(() => URL.revokeObjectURL(blobUrl), 60000)
  } catch {
    // CORS fallback：直接触发链接下载
    const a = document.createElement('a')
    a.href = card.videoUrl
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
  } finally {
    card.downloading = false
  }
}

// ─── 格式化辅助函数（Fix 6）──────────────────────────────────────────────────
function formatGenTime(ms) {
  const s = Math.round(ms / 1000)
  if (s < 60) return `${s} 秒`
  const m = Math.floor(s / 60), r = s % 60
  return r > 0 ? `${m} 分 ${r} 秒` : `${m} 分`
}

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}
</script>

<style scoped>
.video-page {
  max-width: 1200px;
  margin: 0 auto;
  padding-bottom: 40px;
}

/* ── Page Header ──────────────────────────────────────────────────────────── */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 28px 0 20px;
  gap: 16px;
  flex-wrap: wrap;
}

.hero-section {
  display: flex;
  align-items: center;
  gap: 16px;
}

.hero-icon-wrap {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  background: rgba(251, 119, 1, 0.1);
  border-radius: 16px;
  flex-shrink: 0;
}

.hero-text { display: flex; flex-direction: column; gap: 4px; }
.hero-title { font-size: 24px; font-weight: 700; color: var(--el-text-color-primary); margin: 0; }
.hero-subtitle { font-size: 13px; color: var(--el-text-color-secondary); margin: 0; }

.add-card-btn { flex-shrink: 0; }

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.key-alert {
  margin-bottom: 16px;
  border-radius: 10px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 80px 24px;
  text-align: center;
}
.empty-title { font-size: 16px; font-weight: 600; color: var(--el-text-color-secondary); margin: 0; }
.empty-sub { font-size: 13px; color: var(--el-text-color-placeholder); margin: 0; }

/* ── Cards Container ──────────────────────────────────────────────────────── */
.cards-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.video-card { border-radius: 16px; }

/* ── Card Header ──────────────────────────────────────────────────────────── */
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.card-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
}

.icon-badge {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.icon-badge--primary { background: rgba(251, 119, 1, 0.1); }

.card-title {
  font-size: 15px;
  font-weight: 600;
  white-space: nowrap;
  flex-shrink: 0;
}

.model-select {
  width: 220px;
  flex-shrink: 0;
}

.model-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  width: 100%;
}
.model-tag { flex-shrink: 0; }

/* ── Model Desc Bar ───────────────────────────────────────────────────────── */
.model-desc-bar {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  padding: 8px 12px;
  background: var(--el-bg-color-page);
  border-radius: 8px;
  margin-bottom: 16px;
}
.model-desc-text {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  line-height: 1.5;
}

/* ── Card Body ────────────────────────────────────────────────────────────── */
.card-body {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  align-items: start;
}

/* ── Controls ─────────────────────────────────────────────────────────────── */
.card-controls {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.control-section { display: flex; flex-direction: column; gap: 8px; }

.control-label-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.control-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--el-text-color-regular);
}

/* ── Image Upload ─────────────────────────────────────────────────────────── */
.image-upload-area {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.image-preview-item {
  position: relative;
  width: 80px;
  height: 80px;
  border-radius: 8px;
  overflow: visible;
  flex-shrink: 0;
}

.preview-img {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: 8px;
  border: 1.5px solid var(--el-border-color-lighter);
  display: block;
}

.remove-img-btn {
  position: absolute;
  top: -6px;
  right: -6px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--el-color-danger);
  color: #fff;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  z-index: 1;
}

.image-upload-trigger {
  width: 80px;
  height: 80px;
  border: 1.5px dashed var(--el-border-color);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  cursor: pointer;
  font-size: 11px;
  color: var(--el-text-color-placeholder);
  transition: border-color 0.2s, background 0.2s;
  flex-shrink: 0;
}
.image-upload-trigger:hover {
  border-color: var(--el-color-primary);
  background: rgba(251, 119, 1, 0.04);
}

/* ── Textarea ─────────────────────────────────────────────────────────────── */
.textarea-wrap { position: relative; }
.char-count {
  position: absolute;
  bottom: 8px;
  right: 10px;
  font-size: 11px;
  color: var(--el-text-color-placeholder);
  pointer-events: none;
}

/* ── Params ───────────────────────────────────────────────────────────────── */
.params-row { flex-direction: row; gap: 12px; }
.param-item { display: flex; flex-direction: column; gap: 6px; flex: 1; min-width: 0; }
.param-label { font-size: 13px; font-weight: 500; color: var(--el-text-color-regular); }
.param-select { width: 100%; }

/* ── Result Area ──────────────────────────────────────────────────────────── */
.card-result {
  min-height: 280px;
  border: 1.5px solid var(--el-border-color-lighter);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background: var(--el-bg-color);
  position: relative;
}

.video-player-wrap {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 12px;
}

.video-player {
  width: 100%;
  border-radius: 8px;
  max-height: 320px;
  background: #000;
}

.video-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 2px;
}

/* Loading */
.result-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 32px 24px;
}
.spin-icon { animation: spin 1s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
.loading-text { font-size: 14px; color: var(--el-text-color-secondary); margin: 0; }

/* Error */
.result-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 32px 24px;
  text-align: center;
}
.error-text { font-size: 13px; color: var(--el-color-danger); margin: 0; line-height: 1.5; }

/* Pending */
.result-pending {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 32px 24px;
  text-align: center;
}
.pending-title { font-size: 15px; font-weight: 600; color: var(--el-text-color-primary); margin: 0; }
.pending-sub { font-size: 12px; color: var(--el-text-color-secondary); margin: 0; line-height: 1.5; }
.task-id-tag { font-family: monospace; font-size: 11px; }

/* Placeholder */
.result-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 32px 24px;
  text-align: center;
}
.placeholder-title { font-size: 15px; font-weight: 600; color: var(--el-text-color-secondary); margin: 0; }
.placeholder-sub { font-size: 12px; color: var(--el-text-color-placeholder); margin: 0; }

/* ── Card Footer ──────────────────────────────────────────────────────────── */
.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 16px;
  border-top: 1px solid var(--el-border-color-lighter);
  margin-top: 16px;
}

.footer-info { display: flex; align-items: center; gap: 8px; }
.footer-actions { display: flex; align-items: center; gap: 8px; }
/* ── Video metadata loading skeleton ─────────────────────────────────────── */
.video-meta-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 48px 24px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

/* ── Mock progress ────────────────────────────────────────────────────────── */
.mock-progress-wrap {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
}

.mock-progress-pct {
  font-size: 12px;
  font-weight: 600;
  color: var(--el-color-primary);
  white-space: nowrap;
  min-width: 34px;
  text-align: right;
}

/* ── Video stats ──────────────────────────────────────────────────────────── */
.video-stats-row {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 6px 4px 0;
}

.stat-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

/* ── Auto-polling ─────────────────────────────────────────────────────────── */
.result-polling {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 32px 24px;
  text-align: center;
}

.poll-ring {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  border: 3px solid var(--el-color-primary-light-5);
  border-top-color: var(--el-color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  animation: spin 1.2s linear infinite;
}

.poll-status-text {
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin: 0;
}

.poll-hint {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
  margin: 0;
}

.spin-icon-sm {
  animation: spin 1s linear infinite;
  display: inline-flex;
}

/* ── Enhanced Prompt ──────────────────────────────────────────────────────── */
.enhanced-prompt {
  padding: 8px 12px;
  background: var(--el-bg-color-page);
  border-radius: 8px;
  font-size: 12px;
  line-height: 1.6;
}
.enhanced-prompt-label {
  font-weight: 600;
  color: var(--el-text-color-secondary);
  margin-right: 4px;
}
.enhanced-prompt-text { color: var(--el-text-color-regular); }
</style>
