<template>
  <div v-if="tasks.length > 0" class="results-section">
    <!-- 标题栏 -->
    <div class="results-header">
      <div class="card-header-left">
        <div class="icon-badge icon-badge--primary">
          <el-icon size="20" color="var(--el-color-primary)"><Picture /></el-icon>
        </div>
        <div>
          <h2 class="section-title">创作结果</h2>
          <p class="section-subtitle">{{ doneCount }} / {{ tasks.length }} 已完成</p>
        </div>
      </div>
      <el-button
        v-if="doneCount > 0"
        type="primary"
        plain
        :loading="isBatchSaving"
        :disabled="selectedCount === 0"
        @click="$emit('batch-save')"
      >
        <el-icon><FolderChecked /></el-icon>
        批量保存 ({{ selectedCount }})
      </el-button>
    </div>

    <!-- 提示语 -->
    <el-alert class="results-tip" type="warning" :closable="false" show-icon>
      <template #default>创作结果请您自己记得保存，本软件不会保存任何图片生成结果</template>
    </el-alert>

    <!-- 全选行 -->
    <div v-if="doneCount > 0" class="results-select-bar">
      <el-checkbox :model-value="allSelected" @change="$emit('toggle-all', $event)">全选</el-checkbox>
      <span class="results-select-tip">已选 {{ selectedCount }} / {{ doneCount }} 张</span>
    </div>

    <!-- 结果卡片列表 -->
    <div class="results-row">
      <div v-for="task in tasks" :key="task.id" class="result-card">
        <!-- 卡头 -->
        <div class="result-card-head" :class="{ 'is-selected': task.status === 'done' && task.selected }">
          <el-checkbox
            v-if="task.status === 'done'"
            :model-value="task.selected"
            class="result-card-checkbox"
            @change="$emit('toggle-select', task)"
            @click.stop
          />
          <span v-else class="result-card-num">#{{ task.index + 1 }}</span>
          <img
            v-if="task.baseImage"
            class="result-base-thumb"
            :src="task.baseImage.url"
            :alt="`基准${task.index + 1}`"
          />
          <div v-else class="result-base-thumb result-base-placeholder">
            <el-icon size="14" color="var(--el-text-color-placeholder)"><EditPen /></el-icon>
          </div>
          <span class="result-status-tag" :class="`is-${task.status}`">
            {{ STATUS_LABELS[task.status] }}
          </span>
        </div>

        <!-- 卡体 -->
        <div class="result-body">
          <!-- 加载中 -->
          <template v-if="task.status === 'pending' || task.status === 'loading'">
            <div class="result-skeleton"><div class="skeleton-shimmer" /></div>
            <div class="result-progress-wrap">
              <el-progress :percentage="task.progress" :stroke-width="5"
                :color="[{ color: 'var(--el-color-primary)', percentage: 100 }]" />
            </div>
          </template>

          <!-- 完成 -->
          <template v-else-if="task.status === 'done'">
            <div class="result-img-wrap" @click="$emit('preview', task)">
              <img :src="task.resultUrl" alt="生成结果" />
              <div class="result-img-mask">
                <el-icon size="26" color="#fff"><ZoomIn /></el-icon>
              </div>
            </div>
            <div class="result-meta">
              <span v-if="task.doneAt"><el-icon size="12"><Timer /></el-icon> {{ task.doneAt }}</span>
              <span v-if="task.fileSize"><el-icon size="12"><Document /></el-icon> {{ task.fileSize }}</span>
            </div>
            <div class="result-footer">
              <el-button size="small" @click="$emit('retry', task)">
                <el-icon><RefreshLeft /></el-icon>重试
              </el-button>
              <el-button size="small" type="primary" plain @click="$emit('download', task)">
                <el-icon><Download /></el-icon>下载
              </el-button>
            </div>
          </template>

          <!-- 失败 -->
          <template v-else-if="task.status === 'error'">
            <div class="result-error">
              <el-icon size="28" color="#f56c6c"><WarningFilled /></el-icon>
              <p>{{ task.error }}</p>
            </div>
            <div class="result-footer">
              <el-button size="small" @click="$emit('retry', task)">
                <el-icon><RefreshLeft /></el-icon>重试
              </el-button>
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {
  Picture, FolderChecked, ZoomIn, Timer, Document,
  RefreshLeft, Download, WarningFilled, EditPen,
} from '@element-plus/icons-vue'

const STATUS_LABELS = { pending: '等待中', loading: '生成中', done: '已完成', error: '失败' }

const props = defineProps({
  tasks: { type: Array, required: true },
  isBatchSaving: { type: Boolean, default: false },
  doneCount: { type: Number, default: 0 },
  selectedCount: { type: Number, default: 0 },
  allSelected: { type: Boolean, default: false },
})

defineEmits(['retry', 'download', 'batch-save', 'preview', 'toggle-all', 'toggle-select'])
</script>

<style scoped>
.results-section {
  margin-top: 24px;
  padding: 20px;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 16px;
}

.results-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.card-header-left { display: flex; align-items: center; gap: 12px; }

.section-title { font-size: 16px; font-weight: 600; margin: 0 0 2px; }
.section-subtitle { font-size: 12px; color: var(--el-text-color-secondary); margin: 0; }

.icon-badge {
  width: 36px; height: 36px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.icon-badge--primary { background: rgba(251, 119, 1, 0.1); }

.results-tip { margin-bottom: 12px; border-radius: 8px; font-size: 12px; }

.results-select-bar {
  display: flex; align-items: center; gap: 12px;
  margin-bottom: 12px;
  padding: 6px 10px;
  background: var(--el-fill-color-lighter);
  border-radius: 8px;
}
.results-select-tip { font-size: 12px; color: var(--el-text-color-secondary); }

.results-row {
  display: flex;
  gap: 14px;
  overflow-x: auto;
  padding-bottom: 6px;
  scrollbar-width: thin;
  scrollbar-color: var(--el-border-color) transparent;
}

.result-card {
  flex-shrink: 0;
  width: 200px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 12px;
  overflow: hidden;
  background: var(--el-fill-color-lighter);
  display: flex;
  flex-direction: column;
}

.result-card-head {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 10px;
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color-lighter);
  transition: background 0.15s;
}
.result-card-head.is-selected { background: rgba(251, 119, 1, 0.06); }

.result-card-num { font-size: 12px; font-weight: 700; color: var(--el-color-primary); flex-shrink: 0; }
.result-card-checkbox { flex-shrink: 0; }

.result-base-thumb {
  width: 28px; height: 28px;
  object-fit: cover; border-radius: 4px;
  border: 1px solid var(--el-border-color-lighter); flex-shrink: 0;
}

.result-base-placeholder {
  display: flex; align-items: center; justify-content: center;
  background: var(--el-fill-color-light);
}

.result-status-tag {
  margin-left: auto; font-size: 11px;
  padding: 1px 6px; border-radius: 10px; font-weight: 500;
}
.result-status-tag.is-pending  { background: #f0f0f0; color: #888; }
.result-status-tag.is-loading  { background: #e6f4ff; color: #1677ff; }
.result-status-tag.is-done     { background: #f6ffed; color: #52c41a; }
.result-status-tag.is-error    { background: #fff2f0; color: #f5222d; }

.result-body { flex: 1; display: flex; flex-direction: column; }

.result-skeleton { flex: 1; min-height: 150px; padding: 8px 8px 4px; }
.skeleton-shimmer {
  width: 100%; height: 100%; min-height: 130px; border-radius: 8px;
  background: linear-gradient(90deg, var(--el-fill-color) 25%, var(--el-fill-color-dark, #e8e8e8) 50%, var(--el-fill-color) 75%);
  background-size: 400% 100%;
  animation: shimmer 1.6s ease-in-out infinite;
}
@keyframes shimmer {
  0%   { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.result-progress-wrap { padding: 6px 10px 10px; }

.result-img-wrap {
  flex: 1; position: relative; cursor: pointer; min-height: 150px; overflow: hidden;
}
.result-img-wrap img { width: 100%; height: 100%; object-fit: cover; display: block; }
.result-img-mask {
  position: absolute; inset: 0;
  background: rgba(0,0,0,0.38);
  display: flex; align-items: center; justify-content: center;
  opacity: 0; transition: opacity 0.2s;
}
.result-img-wrap:hover .result-img-mask { opacity: 1; }

.result-meta {
  display: flex; align-items: center; gap: 8px;
  padding: 4px 10px; font-size: 11px; color: var(--el-text-color-secondary);
}
.result-meta span { display: flex; align-items: center; gap: 3px; }

.result-error {
  flex: 1; display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  gap: 8px; padding: 16px 12px; min-height: 150px;
}
.result-error p {
  font-size: 12px; color: var(--el-text-color-secondary);
  text-align: center; margin: 0; line-height: 1.5;
}

.result-footer {
  padding: 8px 10px;
  border-top: 1px solid var(--el-border-color-lighter);
  display: flex; justify-content: flex-end; gap: 6px;
}
</style>
