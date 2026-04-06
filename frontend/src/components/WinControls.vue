<template>
  <div class="win-controls">
    <button class="btn" @click="minimize" title="最小化">
      <svg width="10" height="1" viewBox="0 0 10 1">
        <rect width="10" height="1.5" fill="currentColor" />
      </svg>
    </button>
    <button class="btn" @click="maximize" :title="isMax ? '还原' : '最大化'">
      <svg v-if="!isMax" width="10" height="10" viewBox="0 0 10 10">
        <rect x=".5" y=".5" width="9" height="9" fill="none" stroke="currentColor" stroke-width="1.2" />
      </svg>
      <svg v-else width="10" height="10" viewBox="0 0 10 10">
        <rect x="2" y="0" width="8" height="8" fill="none" stroke="currentColor" stroke-width="1.2" />
        <rect x="0" y="2" width="8" height="8" fill="none" stroke="currentColor" stroke-width="1.2" />
      </svg>
    </button>
    <button class="btn btn-close" @click="close" title="关闭">
      <svg width="10" height="10" viewBox="0 0 10 10">
        <line x1="0" y1="0" x2="10" y2="10" stroke="currentColor" stroke-width="1.4" />
        <line x1="10" y1="0" x2="0"  y2="10" stroke="currentColor" stroke-width="1.4" />
      </svg>
    </button>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";

const isMax = ref(false);
const api = window.electronAPI;

onMounted(async () => {
  if (!api) return;
  isMax.value = await api.isMaximized();
  api.onMaximizeChange((val) => (isMax.value = val));
});

function minimize() { api?.minimize(); }
function maximize() { api?.maximize(); }
function close()    { api?.close(); }
</script>

<style scoped>
.win-controls {
  display: flex;
  height: 100%;
  -webkit-app-region: no-drag;
}

.btn {
  width: 46px;
  height: 100%;
  border: none;
  background: transparent;
  color: #595959;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s, color 0.15s;
}

.btn:hover {
  background: #f0f0f0;
  color: #262626;
}

.btn-close:hover {
  background: #e81123;
  color: #ffffff;
}
</style>
