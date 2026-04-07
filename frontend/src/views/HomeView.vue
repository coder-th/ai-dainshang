<template>
  <div class="home-page">
    <!-- Hero 区域 -->
    <div class="hero-section">
      <div class="hero-icon-wrap">
        <el-icon size="32" color="var(--el-color-primary)"><Brush /></el-icon>
        <span class="hero-dot"></span>
      </div>
      <h1 class="hero-title">AI创意工坊</h1>
      <p class="hero-subtitle">释放无限创意，让AI为您绘制想象中的世界</p>
      <el-button class="quick-setup-btn" size="small" round @click="showSettings = true">
        <el-icon><Setting /></el-icon>
        快速设置
      </el-button>
    </div>

    <!-- 主内容区：左右两栏 -->
    <div class="content-grid">
      <!-- 左栏：创作区 -->
      <div class="left-col">

        <!-- AI 模型选择 -->
        <el-card class="section-card" shadow="hover">
          <div class="card-header">
            <div class="card-header-left">
              <div class="icon-badge icon-badge--primary">
                <el-icon size="20"><MagicStick /></el-icon>
              </div>
              <div>
                <h2 class="section-title">AI创作模型</h2>
                <p class="section-subtitle">选择最适合的AI助手</p>
              </div>
            </div>
            <el-button type="primary" @click="showModelDialog = true">切换模型</el-button>
          </div>

          <div class="model-card" @click="showModelDialog = true">
            <div class="model-info">
              <div class="icon-badge icon-badge--primary">
                <el-icon size="22"><Lightning /></el-icon>
              </div>
              <div class="model-text">
                <div class="model-name">{{ currentModel.name }}</div>
                <div class="model-desc">{{ currentModel.desc }}</div>
              </div>
            </div>
            <el-icon size="20" color="var(--el-color-primary)"><ArrowDown /></el-icon>
          </div>
        </el-card>

        <!-- 创意描述 -->
        <el-card class="section-card" shadow="hover">
          <div class="card-header">
            <div class="card-header-left">
              <div class="icon-badge icon-badge--blue">
                <el-icon size="20" color="#409eff"><EditPen /></el-icon>
              </div>
              <div>
                <h2 class="section-title">创意描述</h2>
                <p class="section-subtitle">用文字描绘您的想象</p>
              </div>
            </div>
            <div class="btn-group">
              <el-button size="default" :disabled="!prompt" @click="optimizePrompt">
                <el-icon><MagicStick /></el-icon>
                智能优化
              </el-button>
              <el-button size="default" :disabled="!prompt" @click="translatePrompt">
                <el-icon><Promotion /></el-icon>
                翻译
              </el-button>
              <el-button size="default" :disabled="!prompt" @click="prompt = ''">
                <el-icon><Close /></el-icon>
              </el-button>
            </div>
          </div>

          <div class="textarea-wrap">
            <el-input
              v-model="prompt"
              type="textarea"
              :rows="6"
              placeholder="例如：一只戴着宇航员头盔的猫在月球上漫步，背景是地球，写实风格"
              resize="none"
              class="prompt-textarea"
            />
            <span class="char-count">{{ prompt.length }} 字符</span>
          </div>
        </el-card>

        <!-- 基准图片 -->
        <el-card class="section-card ref-images-card" shadow="never">
          <div class="ref-header">
            <div class="icon-badge icon-badge--blue">
              <el-icon size="16" color="#409eff"><Aim /></el-icon>
            </div>
            <div>
              <h3 class="ref-title">基准图片</h3>
              <p class="ref-count">{{ baseImages.length }}/10</p>
            </div>
          </div>
          <el-alert type="info" :closable="false" class="base-img-tip">
            <template #default>
              每张基准图对应一个独立的生成任务，上传 <strong>{{ baseImages.length || 'N' }}</strong> 张基准图将产生 <strong>{{ baseImages.length || 'N' }}</strong> 个任务并发执行。参考图片对所有基准图共享（1 基准 : N 参考）。
            </template>
          </el-alert>
          <div class="images-row">
            <div
              v-for="(img, idx) in baseImages"
              :key="img.uid"
              class="img-thumb"
              :class="{ 'is-drag-over': dragState.list === 'base' && dragState.overIdx === idx }"
              draggable="true"
              @dragstart="onDragStart('base', idx)"
              @dragover.prevent="onDragOver('base', idx)"
              @drop.prevent="onDrop('base', idx)"
              @dragend="onDragEnd"
              @click="openPreview(baseImages, idx)"
            >
              <img :src="img.url" :alt="img.name" />
              <button class="img-remove" @click.stop="removeImg('base', idx)">×</button>
            </div>
            <label v-if="baseImages.length < 10" class="img-add-btn">
              <input type="file" multiple accept="image/png,image/jpeg,image/jpg,image/webp" @change="e => onFileChange(e, 'base')" />
              <el-icon size="20"><Plus /></el-icon>
            </label>
          </div>
        </el-card>

        <!-- 参考图片 -->
        <el-card class="section-card ref-images-card" shadow="never" :class="{ 'is-disabled': baseImages.length === 0 }">
          <div class="ref-header">
            <div class="icon-badge icon-badge--green">
              <el-icon size="16" color="#67c23a"><Picture /></el-icon>
            </div>
            <div>
              <h3 class="ref-title">参考图片</h3>
              <p class="ref-count">{{ referenceImages.length }}/8</p>
            </div>
          </div>
          <el-alert
            v-if="baseImages.length === 0"
            type="warning"
            :closable="false"
            class="ref-disabled-tip"
          >
            请先上传基准图片后再添加参考图片
          </el-alert>
          <div v-else class="images-row">
            <div
              v-for="(img, idx) in referenceImages"
              :key="img.uid"
              class="img-thumb"
              :class="{ 'is-drag-over': dragState.list === 'ref' && dragState.overIdx === idx }"
              draggable="true"
              @dragstart="onDragStart('ref', idx)"
              @dragover.prevent="onDragOver('ref', idx)"
              @drop.prevent="onDrop('ref', idx)"
              @dragend="onDragEnd"
              @click="openPreview(referenceImages, idx)"
            >
              <img :src="img.url" :alt="img.name" />
              <span class="img-seq-badge">{{ idx + 2 }}</span>
              <button class="img-remove" @click.stop="removeImg('ref', idx)">×</button>
            </div>
            <label v-if="referenceImages.length < 8" class="img-add-btn">
              <input type="file" multiple accept="image/png,image/jpeg,image/jpg,image/webp" @change="e => onFileChange(e, 'ref')" />
              <el-icon size="20"><Plus /></el-icon>
            </label>
          </div>
        </el-card>
      </div>

      <!-- 右栏：参数 + 生成 -->
      <div class="right-col">
        <ParamsPanel
          :model-value="params"
          :model-id="currentModelId"
          @update:model-value="Object.assign(params, $event)"
        />

        <!-- 开始创作按钮 -->
        <el-button
          class="generate-btn"
          type="primary"
          size="large"
          :loading="isGenerating"
          :disabled="!prompt.trim() || isGenerating"
          @click="handleGenerate"
        >
          <el-icon v-if="!isGenerating" size="22"><StarFilled /></el-icon>
          {{ isGenerating ? '创作中…' : '开始创作' }}
        </el-button>
      </div>
    </div>

    <!-- 切换模型对话框 -->
    <ModelSelectDialog
      v-model="showModelDialog"
      :current-model-id="currentModelId"
      @select="onModelSelect"
    />

    <!-- 快速设置对话框 -->
    <QuickSettingsDialog v-model="showSettings" />

    <!-- 上传图片预览器 -->
    <el-image-viewer
      v-if="uploadPreview.visible"
      :url-list="uploadPreview.urls"
      :initial-index="uploadPreview.index"
      @close="uploadPreview.visible = false"
    />

    <!-- 生成结果预览器 -->
    <el-image-viewer
      v-if="genPreview.visible"
      :url-list="genPreview.urls"
      :initial-index="genPreview.index"
      @close="genPreview.visible = false"
    />

    <!-- 创作结果 -->
    <ResultsSection
      :tasks="generationTasks"
      :is-batch-saving="isBatchSaving"
      :done-count="doneTaskCount"
      :selected-count="selectedDoneCount"
      :all-selected="allSelected"
      @retry="retryTask"
      @download="downloadResult"
      @batch-save="batchSaveResults"
      @preview="openResultPreview"
      @toggle-all="val => { allSelected = val }"
      @toggle-select="task => { task.selected = !task.selected }"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Setting, MagicStick, Lightning, EditPen, Promotion, Close,
  Picture, StarFilled, ArrowDown, Brush, Plus, Aim,
} from '@element-plus/icons-vue'
import { getImageModelById } from '@/config/models.js'
import { useImageUpload } from '@/composables/useImageUpload.js'
import { useGeneration } from '@/composables/useGeneration.js'
import ParamsPanel from '@/components/ParamsPanel.vue'
import ModelSelectDialog from '@/components/ModelSelectDialog.vue'
import ResultsSection from '@/components/ResultsSection.vue'
import QuickSettingsDialog from '@/components/QuickSettingsDialog.vue'

// ── 模型 ──────────────────────────────────────────
const currentModelId = ref('nano-banana-2')
const currentModel = computed(() => getImageModelById(currentModelId.value))

function onModelSelect(id) {
  currentModelId.value = id
}

// ── prompt（独立，避免 ParamsPanel 深度监听循环） ──
const prompt = ref('')

// ── 生成参数 ───────────────────────────────────────
const params = reactive({
  aspectRatio: '3:4',
  resolution: '1K',
  webAccess: 'true',
})

// ── 对话框状态 ─────────────────────────────────────
const showModelDialog = ref(false)
const showSettings = ref(false)

// ── 图片上传 ───────────────────────────────────────
const {
  baseImages,
  referenceImages,
  dragState,
  preview: uploadPreview,
  onFileChange,
  removeImg,
  onDragStart,
  onDragOver,
  onDrop,
  onDragEnd,
  openPreview,
} = useImageUpload()

// ── 生成任务 ───────────────────────────────────────
const {
  generationTasks,
  isGenerating,
  isBatchSaving,
  preview: genPreview,
  doneTaskCount,
  allSelected,
  selectedDoneCount,
  handleGenerate,
  retryTask,
  openResultPreview,
  downloadResult,
  batchSaveResults,
} = useGeneration({ baseImages, referenceImages, currentModelId, prompt, params, showSettings })

// ── 工具方法 ───────────────────────────────────────
function optimizePrompt() {
  ElMessage.info('智能优化功能开发中…')
}

function translatePrompt() {
  ElMessage.info('翻译功能开发中…')
}
</script>

<style scoped>
.home-page {
  max-width: 1200px;
  margin: 0 auto;
}

/* ── Hero ──────────────────────────────────────────── */
.hero-section {
  text-align: center;
  padding: 32px 0 24px;
  position: relative;
}

.hero-icon-wrap {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 64px;
  height: 64px;
  background: rgba(251, 119, 1, 0.1);
  border-radius: 20px;
  margin-bottom: 16px;
}

.hero-dot {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 10px;
  height: 10px;
  background: var(--el-color-primary);
  border-radius: 50%;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.3); opacity: 0.6; }
}

.hero-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  margin: 0 0 8px;
}

.hero-subtitle {
  font-size: 14px;
  color: var(--el-text-color-secondary);
  margin: 0 0 16px;
}

.quick-setup-btn {
  border-color: var(--el-color-primary);
  color: var(--el-color-primary);
}

/* ── Layout Grid ───────────────────────────────────── */
.content-grid {
  display: grid;
  grid-template-columns: 1fr 340px;
  gap: 20px;
  align-items: start;
}

.left-col, .right-col {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* ── Cards ─────────────────────────────────────────── */
.section-card { border-radius: 16px; }

.card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 16px;
}

.card-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.section-title { font-size: 16px; font-weight: 600; margin: 0 0 2px; }
.section-subtitle { font-size: 12px; color: var(--el-text-color-secondary); margin: 0; }

.icon-badge {
  width: 36px; height: 36px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.icon-badge--primary { background: rgba(251, 119, 1, 0.1); }
.icon-badge--blue    { background: rgba(64, 158, 255, 0.1); }
.icon-badge--green   { background: rgba(103, 194, 58, 0.1); }

/* ── Model Card ────────────────────────────────────── */
.model-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border: 1.5px solid var(--el-border-color-lighter);
  border-radius: 12px;
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
}
.model-card:hover {
  border-color: var(--el-color-primary-light-3);
  background: var(--el-fill-color-lighter);
}
.model-info { display: flex; align-items: center; gap: 12px; }
.model-text { display: flex; flex-direction: column; gap: 3px; }
.model-name { font-size: 14px; font-weight: 600; }
.model-desc {
  font-size: 12px; color: var(--el-text-color-secondary);
  display: -webkit-box; -webkit-line-clamp: 2; line-clamp: 2;
  -webkit-box-orient: vertical; overflow: hidden; line-height: 1.5;
  max-width: 360px;
}

/* ── Prompt ────────────────────────────────────────── */
.btn-group { display: flex; gap: 6px; flex-shrink: 0; }

.textarea-wrap { position: relative; }
.char-count {
  position: absolute; bottom: 8px; right: 10px;
  font-size: 11px; color: var(--el-text-color-placeholder);
  pointer-events: none;
}

/* ── Image Upload ──────────────────────────────────── */
.ref-images-card { border-radius: 16px; }

.ref-header {
  display: flex; align-items: center; gap: 10px; margin-bottom: 10px;
}
.ref-title { font-size: 14px; font-weight: 600; margin: 0 0 2px; }
.ref-count { font-size: 12px; color: var(--el-text-color-secondary); margin: 0; }

.ref-disabled-tip {
  border-radius: 8px;
  font-size: 12px;
}

.base-img-tip {
  margin-bottom: 10px;
  border-radius: 8px;
  font-size: 12px;
}

.images-row {
  display: flex; flex-wrap: wrap; gap: 8px;
}

.img-thumb {
  position: relative;
  width: 72px; height: 72px;
  border-radius: 8px; overflow: hidden;
  border: 1.5px solid var(--el-border-color-lighter);
  cursor: pointer;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.img-thumb:hover { border-color: var(--el-color-primary); box-shadow: 0 0 0 2px rgba(251,119,1,0.15); }
.img-thumb.is-drag-over { border-color: var(--el-color-primary); box-shadow: 0 0 0 3px rgba(251,119,1,0.25); }
.img-thumb img { width: 100%; height: 100%; object-fit: cover; display: block; }

.img-remove {
  position: absolute; top: 2px; right: 2px;
  width: 18px; height: 18px;
  background: rgba(0,0,0,0.55); color: #fff;
  border: none; border-radius: 50%; cursor: pointer;
  font-size: 13px; line-height: 1; display: flex; align-items: center; justify-content: center;
  padding: 0; opacity: 0; transition: opacity 0.15s;
}
.img-thumb:hover .img-remove { opacity: 1; }

.img-seq-badge {
  position: absolute; bottom: 2px; left: 2px;
  background: var(--el-color-primary);
  color: #fff; font-size: 10px; font-weight: 700;
  padding: 0 4px; border-radius: 4px; line-height: 16px;
}

.img-add-btn {
  width: 72px; height: 72px;
  border-radius: 8px;
  border: 1.5px dashed var(--el-border-color);
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; color: var(--el-text-color-placeholder);
  transition: border-color 0.15s, color 0.15s;
}
.img-add-btn:hover { border-color: var(--el-color-primary); color: var(--el-color-primary); }
.img-add-btn input[type="file"] { display: none; }

/* ── Generate Button ───────────────────────────────── */
.generate-btn {
  width: 100%;
  height: 52px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 14px;
  letter-spacing: 0.5px;
}
</style>
