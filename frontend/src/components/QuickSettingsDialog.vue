<template>
  <el-dialog
    :model-value="modelValue"
    width="500px"
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
          <p class="settings-subtitle">为每个AI供应商单独配置API密钥</p>
        </div>
      </div>
    </template>

    <div class="settings-body">
      <el-tabs v-model="activeTab" class="provider-tabs">
        <el-tab-pane
          v-for="provider in PROVIDERS"
          :key="provider.id"
          :label="provider.name"
          :name="provider.id"
        >
          <div class="api-key-item">
            <div class="provider-status">
              <el-tag
                v-if="keys[provider.id]"
                type="success"
                size="small"
                effect="light"
              >
                已配置
              </el-tag>
              <el-tag
                v-else
                type="warning"
                size="small"
                effect="light"
              >
                未配置
              </el-tag>
            </div>
            <el-input
              v-model="keys[provider.id]"
              :type="showKey[provider.id] ? 'text' : 'password'"
              :placeholder="provider.placeholder"
              size="large"
              clearable
            >
              <template #prefix><el-icon><Key /></el-icon></template>
              <template #suffix>
                <el-icon style="cursor:pointer" @click="showKey[provider.id] = !showKey[provider.id]">
                  <View v-if="!showKey[provider.id]" /><Hide v-else />
                </el-icon>
              </template>
            </el-input>
            <p class="api-key-tip">API 密钥将安全存储在本地，不会上传至任何服务器</p>
          </div>
        </el-tab-pane>
      </el-tabs>
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
import { ref, reactive, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Setting, Key, View, Hide, Check } from '@element-plus/icons-vue'
import { PROVIDERS, getProviderById, saveApiKey, getApiKey } from '@/config/providers.js'

const props = defineProps({
  modelValue: { type: Boolean, required: true },
  // 打开时自动定位到的供应商 Tab，默认第一个
  activeProvider: { type: String, default: PROVIDERS[0].id },
})
const emit = defineEmits(['update:modelValue'])

const activeTab = ref(props.activeProvider)

// 每个供应商各自的 key 和显示状态
const keys = reactive(Object.fromEntries(PROVIDERS.map(p => [p.id, ''])))
const showKey = reactive(Object.fromEntries(PROVIDERS.map(p => [p.id, false])))

// 打开对话框时同步最新值并定位到指定 Tab
watch(() => props.modelValue, (val) => {
  if (val) {
    activeTab.value = props.activeProvider
    PROVIDERS.forEach(p => {
      keys[p.id] = getApiKey(p.id)
      showKey[p.id] = false
    })
  }
})

// activeProvider 变化时同步 tab（如父组件在对话框已打开时切换）
watch(() => props.activeProvider, (val) => {
  activeTab.value = val
})

function save() {
  const provider = getProviderById(activeTab.value)
  const key = keys[activeTab.value]?.trim()
  if (!key) {
    ElMessage.warning(`请输入 ${provider.name} 的 API 密钥`)
    return
  }
  saveApiKey(activeTab.value, key)
  ElMessage.success(`${provider.name} 的 API 密钥已保存`)
  emit('update:modelValue', false)
}
</script>

<style scoped>
.settings-dialog-header { display: flex; align-items: center; gap: 14px; }
.settings-title { font-size: 17px; font-weight: 700; margin: 0 0 3px; }
.settings-subtitle { font-size: 13px; color: var(--el-text-color-secondary); margin: 0; }

.settings-body { padding: 4px 0 0; }

.provider-tabs :deep(.el-tabs__nav-wrap::after) { height: 1px; }
.provider-tabs :deep(.el-tabs__item) { font-weight: 600; }

.api-key-item { display: flex; flex-direction: column; gap: 8px; padding-top: 16px; }

.provider-status { display: flex; align-items: center; }

.api-key-tip {
  font-size: 12px; color: var(--el-text-color-secondary); margin: 0;
  display: flex; align-items: center; gap: 4px;
}
.api-key-tip::before { content: "🔒"; font-size: 12px; }
</style>
