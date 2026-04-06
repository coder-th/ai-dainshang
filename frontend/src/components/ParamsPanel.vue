<template>
  <el-card class="section-card" shadow="hover">
    <div class="card-header">
      <div class="card-header-left">
        <div class="icon-badge icon-badge--purple">
          <el-icon size="20" color="#9b59b6"><Operation /></el-icon>
        </div>
        <div>
          <h2 class="section-title">高级参数</h2>
          <p class="section-subtitle">精细调控制作效果</p>
        </div>
      </div>
      <el-button size="small" text @click="resetParams">
        <el-icon><RefreshLeft /></el-icon>
        重置
      </el-button>
    </div>

    <div class="params-list">
      <!-- 图片比例 -->
      <div class="param-item">
        <label class="param-label">图片比例</label>
        <el-select v-model="innerParams.aspectRatio" class="param-select">
          <el-option
            v-for="opt in availableRatios"
            :key="opt.value"
            :label="opt.label"
            :value="opt.value"
          />
        </el-select>
      </div>

      <!-- 分辨率 -->
      <div class="param-item">
        <label class="param-label">分辨率</label>
        <el-select v-model="innerParams.resolution" class="param-select">
          <el-option
            v-for="opt in availableSizes"
            :key="opt.value"
            :label="opt.label"
            :value="opt.value"
          />
        </el-select>
      </div>

      <!-- 联网（模型不支持时禁用） -->
      <div class="param-item">
        <label class="param-label">
          联网
          <el-tooltip v-if="!currentModel.supportsSearch" content="当前模型不支持联网检索" placement="top">
            <el-icon size="12" color="var(--el-text-color-placeholder)" style="margin-left:4px;cursor:help"><QuestionFilled /></el-icon>
          </el-tooltip>
        </label>
        <el-select
          v-model="innerParams.webAccess"
          class="param-select"
          :disabled="!currentModel.supportsSearch"
        >
          <el-option label="否" value="false" />
          <el-option label="是" value="true" />
        </el-select>
      </div>

      <div class="params-tip">
        <el-text size="small" type="info">参数将自动保存</el-text>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { reactive, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Operation, RefreshLeft, QuestionFilled } from '@element-plus/icons-vue'
import { getImageModelById, getAvailableRatios, getAvailableSizes } from '@/config/models.js'

const props = defineProps({
  modelId: { type: String, required: true },
  modelValue: { type: Object, required: true },
})
const emit = defineEmits(['update:modelValue'])

const innerParams = reactive({ ...props.modelValue })

// 双向同步
watch(innerParams, (val) => emit('update:modelValue', { ...val }))
watch(() => props.modelValue, (val) => Object.assign(innerParams, val), { deep: true })

const currentModel = computed(() => getImageModelById(props.modelId))
const availableRatios = computed(() => getAvailableRatios(props.modelId))
const availableSizes = computed(() => getAvailableSizes(props.modelId))

// 切换模型时自动重置为该模型的默认参数
watch(() => props.modelId, () => {
  const model = currentModel.value
  innerParams.aspectRatio = model.defaultRatio
  innerParams.resolution = model.defaultSize
  if (!model.supportsSearch) innerParams.webAccess = 'false'
})

function resetParams() {
  const model = currentModel.value
  innerParams.aspectRatio = model.defaultRatio
  innerParams.resolution = model.defaultSize
  innerParams.webAccess = model.supportsSearch ? 'true' : 'false'
  ElMessage.success('参数已重置')
}
</script>

<style scoped>
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
.icon-badge--purple { background: rgba(155, 89, 182, 0.1); }

.params-list { display: flex; flex-direction: column; gap: 14px; }

.param-item { display: flex; flex-direction: column; gap: 6px; }

.param-label {
  font-size: 13px; font-weight: 500;
  color: var(--el-text-color-regular);
  display: flex; align-items: center;
}

.param-select { width: 100%; }

.params-tip {
  text-align: center;
  padding-top: 8px;
  border-top: 1px solid var(--el-border-color-lighter);
}
</style>
