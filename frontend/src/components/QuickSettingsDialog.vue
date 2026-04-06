<template>
  <el-dialog
    :model-value="modelValue"
    width="480px"
    :show-close="true"
    class="settings-dialog"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <template #header>
      <div class="settings-dialog-header">
        <div class="icon-badge" style="width:40px;height:40px;border-radius:12px;background:rgba(251,119,1,0.1)">
          <el-icon size="22" color="var(--el-color-primary)"><Setting /></el-icon>
        </div>
        <div>
          <h2 class="settings-title">快速设置</h2>
          <p class="settings-subtitle">配置您的API密钥，开始AI创作之旅</p>
        </div>
      </div>
    </template>

    <div class="settings-body">
      <div class="api-key-item">
        <label class="api-key-label">API 密钥</label>
        <el-input
          v-model="localKey"
          :type="showKey ? 'text' : 'password'"
          placeholder="请输入您的 API Key"
          size="large"
          clearable
        >
          <template #prefix><el-icon><Key /></el-icon></template>
          <template #suffix>
            <el-icon style="cursor:pointer" @click="showKey = !showKey">
              <View v-if="!showKey" /><Hide v-else />
            </el-icon>
          </template>
        </el-input>
        <p class="api-key-tip">API 密钥将安全存储在本地，不会上传至任何服务器</p>
      </div>
    </div>

    <template #footer>
      <el-button @click="$emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" @click="save">
        <el-icon><Check /></el-icon>保存
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Setting, Key, View, Hide, Check } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: { type: Boolean, required: true },
})
const emit = defineEmits(['update:modelValue'])

const localKey = ref(localStorage.getItem('ai_api_key') || '')
const showKey = ref(false)

// 每次打开对话框时同步最新值
watch(() => props.modelValue, (val) => {
  if (val) localKey.value = localStorage.getItem('ai_api_key') || ''
})

function save() {
  if (!localKey.value.trim()) {
    ElMessage.warning('请输入 API 密钥')
    return
  }
  localStorage.setItem('ai_api_key', localKey.value.trim())
  ElMessage.success('API 密钥已保存')
  emit('update:modelValue', false)
}
</script>

<style scoped>
.settings-dialog-header { display: flex; align-items: center; gap: 14px; }
.settings-title { font-size: 17px; font-weight: 700; margin: 0 0 3px; }
.settings-subtitle { font-size: 13px; color: var(--el-text-color-secondary); margin: 0; }
.settings-body { padding: 4px 0; }
.api-key-item { display: flex; flex-direction: column; gap: 8px; }
.api-key-label { font-size: 14px; font-weight: 600; color: var(--el-text-color-primary); }
.api-key-tip {
  font-size: 12px; color: var(--el-text-color-secondary); margin: 0;
  display: flex; align-items: center; gap: 4px;
}
.api-key-tip::before { content: "🔒"; font-size: 12px; }
</style>
