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
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { settingsApi } from '@/api/index.js'

const SETTINGS_KEY = 'export_path'

const form = reactive({ exportPath: '' })
const saving = ref(false)

onMounted(async () => {
  try {
    const { data } = await settingsApi.get(SETTINGS_KEY)
    form.exportPath = data.value || ''
  } catch {
    form.exportPath = ''
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
</style>
