<template>
  <div class="video-page">
    <!-- Hero -->
    <div class="hero-section">
      <div class="hero-icon-wrap">
        <el-icon size="32" color="var(--el-color-primary)"><VideoCamera /></el-icon>
      </div>
      <h1 class="hero-title">AI视频创作</h1>
      <p class="hero-subtitle">文字描述，一键生成专业级AI视频</p>
    </div>

    <div class="content-grid">
      <!-- 左栏：输入区 -->
      <div class="left-col">

        <!-- 模型选择 -->
        <el-card class="section-card" shadow="hover">
          <div class="card-header">
            <div class="card-header-left">
              <div class="icon-badge icon-badge--primary">
                <el-icon size="20"><MagicStick /></el-icon>
              </div>
              <div>
                <h2 class="section-title">AI视频模型</h2>
                <p class="section-subtitle">选择视频生成引擎</p>
              </div>
            </div>
          </div>

          <div class="model-info-card">
            <div class="icon-badge icon-badge--primary">
              <el-icon size="22"><VideoCamera /></el-icon>
            </div>
            <div class="model-text">
              <div class="model-name">{{ currentModel.name }}</div>
              <div class="model-desc">{{ currentModel.desc }}</div>
            </div>
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
                <h2 class="section-title">视频描述</h2>
                <p class="section-subtitle">用文字描述您想生成的视频内容</p>
              </div>
            </div>
          </div>
          <div class="textarea-wrap">
            <el-input
              v-model="prompt"
              type="textarea"
              :rows="6"
              placeholder="例如：夕阳下，一匹白马在草原上奔跑，镜头缓慢推进，写实风格"
              resize="none"
            />
            <span class="char-count">{{ prompt.length }} 字符</span>
          </div>
        </el-card>

        <!-- 参数设置 -->
        <el-card class="section-card" shadow="hover">
          <div class="card-header">
            <div class="card-header-left">
              <div class="icon-badge icon-badge--purple">
                <el-icon size="20" color="#9b59b6"><Operation /></el-icon>
              </div>
              <div>
                <h2 class="section-title">视频参数</h2>
                <p class="section-subtitle">配置视频输出规格</p>
              </div>
            </div>
          </div>

          <div class="params-list">
            <div class="param-item">
              <label class="param-label">视频比例</label>
              <el-select v-model="params.ratio" class="param-select">
                <el-option
                  v-for="opt in VIDEO_RATIO_OPTIONS"
                  :key="opt.value"
                  :label="opt.label"
                  :value="opt.value"
                />
              </el-select>
            </div>
            <div class="param-item">
              <label class="param-label">视频时长</label>
              <el-select v-model="params.duration" class="param-select">
                <el-option
                  v-for="opt in VIDEO_DURATION_OPTIONS"
                  :key="opt.value"
                  :label="opt.label"
                  :value="opt.value"
                />
              </el-select>
            </div>
          </div>
        </el-card>
      </div>

      <!-- 右栏：生成 + 结果 -->
      <div class="right-col">
        <el-button
          class="generate-btn"
          type="primary"
          size="large"
          :loading="isGenerating"
          :disabled="!prompt.trim() || isGenerating"
          @click="handleGenerate"
        >
          <el-icon v-if="!isGenerating" size="22"><VideoPlay /></el-icon>
          {{ isGenerating ? '生成中…' : '开始生成' }}
        </el-button>

        <!-- 占位区 -->
        <div class="result-placeholder">
          <div class="placeholder-inner">
            <el-icon size="56" color="var(--el-border-color)"><VideoCamera /></el-icon>
            <p class="placeholder-title">视频功能开发中</p>
            <p class="placeholder-sub">AI视频生成功能即将上线，敬请期待</p>
            <el-tag type="warning" size="large">即将开放</el-tag>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { VideoCamera, MagicStick, EditPen, Operation, VideoPlay } from '@element-plus/icons-vue'
import { VIDEO_MODELS, VIDEO_RATIO_OPTIONS, VIDEO_DURATION_OPTIONS } from '@/config/models.js'

const currentModelId = ref(VIDEO_MODELS[0]?.id || '')
const currentModel = computed(() => VIDEO_MODELS.find(m => m.id === currentModelId.value) || VIDEO_MODELS[0])

const prompt = ref('')
const isGenerating = ref(false)
const params = reactive({
  ratio: '16:9',
  duration: 5,
})

async function handleGenerate() {
  if (!prompt.value.trim()) {
    ElMessage.warning('请填写视频描述')
    return
  }
  isGenerating.value = true
  try {
    ElMessage.info('视频生成功能开发中，敬请期待')
  } finally {
    isGenerating.value = false
  }
}
</script>

<style scoped>
.video-page {
  max-width: 1200px;
  margin: 0 auto;
}

/* ── Hero ────────────────────────────────────────────── */
.hero-section {
  text-align: center;
  padding: 32px 0 24px;
}

.hero-icon-wrap {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 64px; height: 64px;
  background: rgba(251, 119, 1, 0.1);
  border-radius: 20px;
  margin-bottom: 16px;
}

.hero-title {
  font-size: 28px; font-weight: 700;
  color: var(--el-text-color-primary); margin: 0 0 8px;
}
.hero-subtitle {
  font-size: 14px; color: var(--el-text-color-secondary); margin: 0;
}

/* ── Layout ──────────────────────────────────────────── */
.content-grid {
  display: grid;
  grid-template-columns: 1fr 340px;
  gap: 20px;
  align-items: start;
}

.left-col, .right-col {
  display: flex; flex-direction: column; gap: 16px;
}

/* ── Cards ───────────────────────────────────────────── */
.section-card { border-radius: 16px; }

.card-header {
  display: flex; align-items: flex-start;
  justify-content: space-between; margin-bottom: 16px;
}

.card-header-left { display: flex; align-items: center; gap: 12px; }
.section-title { font-size: 16px; font-weight: 600; margin: 0 0 2px; }
.section-subtitle { font-size: 12px; color: var(--el-text-color-secondary); margin: 0; }

.icon-badge {
  width: 36px; height: 36px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.icon-badge--primary { background: rgba(251, 119, 1, 0.1); }
.icon-badge--blue    { background: rgba(64, 158, 255, 0.1); }
.icon-badge--purple  { background: rgba(155, 89, 182, 0.1); }

/* ── Model Info ──────────────────────────────────────── */
.model-info-card {
  display: flex; align-items: center; gap: 12px;
  padding: 14px 16px;
  border: 1.5px solid var(--el-border-color-lighter);
  border-radius: 12px;
}
.model-text { display: flex; flex-direction: column; gap: 3px; }
.model-name { font-size: 14px; font-weight: 600; }
.model-desc {
  font-size: 12px; color: var(--el-text-color-secondary); line-height: 1.5;
}

/* ── Prompt ──────────────────────────────────────────── */
.textarea-wrap { position: relative; }
.char-count {
  position: absolute; bottom: 8px; right: 10px;
  font-size: 11px; color: var(--el-text-color-placeholder); pointer-events: none;
}

/* ── Params ──────────────────────────────────────────── */
.params-list { display: flex; flex-direction: column; gap: 14px; }
.param-item { display: flex; flex-direction: column; gap: 6px; }
.param-label { font-size: 13px; font-weight: 500; color: var(--el-text-color-regular); }
.param-select { width: 100%; }

/* ── Generate Button ─────────────────────────────────── */
.generate-btn {
  width: 100%; height: 52px;
  font-size: 16px; font-weight: 600;
  border-radius: 14px; letter-spacing: 0.5px;
}

/* ── Placeholder ─────────────────────────────────────── */
.result-placeholder {
  border: 2px dashed var(--el-border-color-lighter);
  border-radius: 16px;
  background: var(--el-bg-color);
  padding: 60px 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.placeholder-inner {
  display: flex; flex-direction: column;
  align-items: center; gap: 12px; text-align: center;
}
.placeholder-title { font-size: 16px; font-weight: 600; color: var(--el-text-color-secondary); margin: 0; }
.placeholder-sub { font-size: 13px; color: var(--el-text-color-placeholder); margin: 0; }
</style>
