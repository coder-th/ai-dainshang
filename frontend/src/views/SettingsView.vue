<template>
  <div class="settings-page">
    <el-card>
      <template #header>
        <span>导出路径设置</span>
      </template>
      <el-form :model="form" label-width="100px">
        <el-form-item label="导出路径">
          <div class="path-row">
            <el-input
              v-model="form.exportPath"
              placeholder="请选择文件导出目录"
              readonly
            />
            <el-button @click="selectDir">浏览</el-button>
          </div>
          <div class="path-hint">
            视频和图片将保存至该目录下的 videos/ 和 images/ 子文件夹。
            留空则使用程序默认目录。
          </div>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="saving" @click="save">保存设置</el-button>
          <el-button :loading="saving" @click="reset">恢复默认</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="isElectron" style="margin-top: 16px;">
      <template #header>
        <span>检查更新</span>
      </template>
      <el-form label-width="100px">
        <el-form-item label="当前版本">
          <span class="version-text">{{ appVersion }}</span>
        </el-form-item>
        <el-form-item label="更新状态">
          <div class="update-status">
            <el-tag :type="statusTag.type" size="small">{{ statusTag.text }}</el-tag>
            <el-progress
              v-if="updateStatus.status === 'downloading'"
              :percentage="updateStatus.percent"
              :stroke-width="6"
              style="width: 200px; margin-left: 12px;"
            />
          </div>
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            :loading="updateStatus.status === 'checking' || updateStatus.status === 'downloading'"
            :disabled="updateStatus.status === 'downloaded'"
            @click="checkUpdate"
          >
            检查更新
          </el-button>
          <el-button
            v-if="updateStatus.status === 'downloaded'"
            type="success"
            @click="installUpdate"
          >
            立即安装并重启
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { settingsApi } from '@/api/index.js'

const SETTINGS_KEY = 'export_path'

const form = reactive({ exportPath: '' })
const saving = ref(false)

// ─── 路径设置 ──────────────────────────────────────────────────────────────────

onMounted(async () => {
  try {
    const { data } = await settingsApi.get(SETTINGS_KEY)
    form.exportPath = data.value || ''
  } catch {
    form.exportPath = ''
  }

  if (isElectron) {
    window.electronAPI.onUpdateStatus((payload) => {
      updateStatus.status = payload.status
      if (payload.version) updateStatus.version = payload.version
      if (payload.percent !== undefined) updateStatus.percent = payload.percent
      if (payload.message) updateStatus.message = payload.message
    })
  }
})

async function selectDir() {
  const api = window.electronAPI
  if (!api?.selectDirectory) {
    ElMessage.warning('目录选择仅在桌面端可用')
    return
  }
  const dir = await api.selectDirectory()
  if (dir) form.exportPath = dir
}

async function save() {
  saving.value = true
  try {
    await settingsApi.set(SETTINGS_KEY, form.exportPath)
    ElMessage.success('设置已保存')
  } catch {
    ElMessage.error('保存失败，请重试')
  } finally {
    saving.value = false
  }
}

async function reset() {
  saving.value = true
  try {
    await settingsApi.del(SETTINGS_KEY)
    form.exportPath = ''
    ElMessage.info('已恢复默认')
  } catch {
    ElMessage.error('重置失败，请重试')
  } finally {
    saving.value = false
  }
}

// ─── 检查更新 ──────────────────────────────────────────────────────────────────

const isElectron = !!window.electronAPI?.checkForUpdates

const appVersion = computed(() => window.__APP_VERSION__ || '未知')

const updateStatus = reactive({
  status: 'idle',   // idle | checking | available | not-available | downloading | downloaded | error
  version: '',
  percent: 0,
  message: '',
})

const STATUS_MAP = {
  'idle':          { type: 'info',    text: '未检查' },
  'checking':      { type: 'warning', text: '检查中...' },
  'available':     { type: 'warning', text: `发现新版本 ${updateStatus.version}` },
  'not-available': { type: 'success', text: '已是最新版本' },
  'downloading':   { type: 'warning', text: `下载中 ${updateStatus.percent}%` },
  'downloaded':    { type: 'success', text: '下载完成，可立即安装' },
  'error':         { type: 'danger',  text: '检查失败' },
}

const statusTag = computed(() => {
  const s = updateStatus.status
  if (s === 'available' && updateStatus.version)
    return { type: 'warning', text: `发现新版本 v${updateStatus.version}` }
  if (s === 'downloading')
    return { type: 'warning', text: `下载中 ${updateStatus.percent}%` }
  if (s === 'error' && updateStatus.message)
    return { type: 'danger', text: `检查失败：${updateStatus.message}` }
  return STATUS_MAP[s] ?? STATUS_MAP['idle']
})

async function checkUpdate() {
  if (!window.electronAPI?.checkForUpdates) {
    ElMessage.warning('检查更新仅在桌面端可用')
    return
  }
  updateStatus.status = 'checking'
  await window.electronAPI.checkForUpdates()
}

async function installUpdate() {
  await window.electronAPI.installUpdate()
}
</script>

<style scoped>
.settings-page {
  max-width: 640px;
}

.path-row {
  display: flex;
  gap: 8px;
  width: 100%;
}

.path-hint {
  font-size: 12px;
  color: #8c8c8c;
  margin-top: 4px;
  line-height: 1.6;
}

.version-text {
  font-size: 13px;
  color: #606266;
}

.update-status {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
