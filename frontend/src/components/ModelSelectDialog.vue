<template>
  <el-dialog
    :model-value="modelValue"
    title="选择AI模型"
    width="660px"
    class="model-dialog"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <div class="model-list">
      <template v-for="provider in PROVIDERS" :key="provider.id">
        <!-- 供应商分组标题 -->
        <div class="provider-group-header">
          <span class="provider-group-name">{{ provider.name }}</span>
          <span class="provider-group-count">{{ getModelsByProvider(provider.id).filter(m => !m.disabled).length }} 个可用模型</span>
        </div>

        <!-- 该供应商的模型列表 -->
        <div
          v-for="model in getModelsByProvider(provider.id)"
          :key="model.id"
          class="model-option"
          :class="{ 'is-active': currentModelId === model.id, 'is-disabled': model.disabled }"
          @click="!model.disabled && select(model.id)"
        >
          <div class="model-option-info">
            <div class="model-option-name">
              {{ model.name }}
              <el-tag v-if="currentModelId === model.id" size="small" type="warning" style="margin-left:8px;vertical-align:middle">当前选择</el-tag>
              <el-tag v-if="model.disabled" size="small" type="info" style="margin-left:8px;vertical-align:middle">暂未开放</el-tag>
            </div>
            <div class="model-option-desc">{{ model.desc }}</div>
          </div>
          <el-icon v-if="currentModelId === model.id" color="var(--el-color-primary)"><Select /></el-icon>
        </div>
      </template>
    </div>
    <template #footer>
      <el-button @click="$emit('update:modelValue', false)">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { Select } from '@element-plus/icons-vue'
import { getModelsByProvider } from '@/config/models.js'
import { PROVIDERS } from '@/config/providers.js'

defineProps({
  modelValue: { type: Boolean, required: true },
  currentModelId: { type: String, required: true },
})
const emit = defineEmits(['update:modelValue', 'select'])

function select(id) {
  emit('select', id)
  emit('update:modelValue', false)
}
</script>

<style scoped>
.model-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

/* 供应商分组标题 */
.provider-group-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 4px 6px;
  margin-top: 4px;
}

.provider-group-header:first-child {
  margin-top: 0;
  padding-top: 4px;
}

.provider-group-name {
  font-size: 13px;
  font-weight: 700;
  color: var(--el-color-primary);
  letter-spacing: 0.3px;
}

.provider-group-count {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}

/* 模型选项 */
.model-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  border: 2px solid var(--el-border-color-lighter);
  border-radius: 10px;
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
}

.model-option:not(.is-disabled):hover {
  border-color: var(--el-color-primary-light-3);
  background: var(--el-fill-color-lighter);
}

.model-option.is-active {
  border-color: var(--el-color-primary);
  background: rgba(251, 119, 1, 0.05);
}

.model-option.is-disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.model-option-name { font-size: 14px; font-weight: 600; margin-bottom: 4px; }

.model-option-desc {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
