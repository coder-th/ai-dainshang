<template>
  <div class="titlebar" :class="{ maximized }">
    <!-- 拖拽区域 -->
    <div class="titlebar-drag">
      <span class="titlebar-title">{{ title }}</span>
    </div>
    <!-- 窗口控制按钮 -->
    <div class="titlebar-controls">
      <button class="btn-minimize" @click="minimize" title="最小化">
        <svg width="10" height="1" viewBox="0 0 10 1"><rect width="10" height="1" fill="currentColor"/></svg>
      </button>
      <button class="btn-maximize" @click="maximize" :title="maximized ? '还原' : '最大化'">
        <svg v-if="!maximized" width="10" height="10" viewBox="0 0 10 10">
          <rect x="0" y="0" width="10" height="10" fill="none" stroke="currentColor" stroke-width="1"/>
        </svg>
        <svg v-else width="10" height="10" viewBox="0 0 10 10">
          <rect x="2" y="0" width="8" height="8" fill="none" stroke="currentColor" stroke-width="1"/>
          <rect x="0" y="2" width="8" height="8" fill="none" stroke="currentColor" stroke-width="1"/>
        </svg>
      </button>
      <button class="btn-close" @click="close" title="关闭">
        <svg width="10" height="10" viewBox="0 0 10 10">
          <line x1="0" y1="0" x2="10" y2="10" stroke="currentColor" stroke-width="1.2"/>
          <line x1="10" y1="0" x2="0" y2="10" stroke="currentColor" stroke-width="1.2"/>
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from "vue";

const props = defineProps({
  title: { type: String, default: "AI 电商" },
});

const maximized = ref(false);
const api = window.electronAPI;

onMounted(async () => {
  if (!api) return;
  maximized.value = await api.isMaximized();
  api.onMaximizeChange((val) => (maximized.value = val));
});

function minimize() { api?.minimize(); }
function maximize() { api?.maximize(); }
function close()    { api?.close(); }
</script>

<style scoped>
.titlebar {
  display: flex;
  align-items: center;
  height: 38px;
  background: #001529;
  user-select: none;
  flex-shrink: 0;
}

.titlebar-drag {
  flex: 1;
  height: 100%;
  display: flex;
  align-items: center;
  padding-left: 12px;
  /* Make this region draggable */
  -webkit-app-region: drag;
}

.titlebar-title {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.65);
}

.titlebar-controls {
  display: flex;
  height: 100%;
  -webkit-app-region: no-drag;
}

.titlebar-controls button {
  width: 46px;
  height: 100%;
  border: none;
  background: transparent;
  color: rgba(255, 255, 255, 0.65);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s;
}

.btn-minimize:hover,
.btn-maximize:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.btn-close:hover {
  background: #e81123;
  color: #fff;
}
</style>
