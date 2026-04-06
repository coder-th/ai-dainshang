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
          <div class="path-hint">文件将保存至该目录，留空则使用程序默认目录</div>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="save">保存设置</el-button>
          <el-button @click="reset">恢复默认</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, onMounted } from "vue";
import { ElMessage } from "element-plus";

const STORAGE_KEY = "settings_exportPath";

const form = reactive({ exportPath: "" });

onMounted(() => {
  form.exportPath = localStorage.getItem(STORAGE_KEY) || "";
});

async function selectDir() {
  const api = window.electronAPI;
  if (!api?.selectDirectory) {
    ElMessage.warning("目录选择仅在桌面端可用");
    return;
  }
  const dir = await api.selectDirectory();
  if (dir) form.exportPath = dir;
}

function save() {
  localStorage.setItem(STORAGE_KEY, form.exportPath);
  ElMessage.success("设置已保存");
}

function reset() {
  form.exportPath = "";
  localStorage.removeItem(STORAGE_KEY);
  ElMessage.info("已恢复默认");
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
}
</style>
