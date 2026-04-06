<template>
  <div class="tab-bar">
    <div
      v-for="tab in tabsStore.tabs"
      :key="tab.path"
      class="tab-item"
      :class="{ active: tab.path === tabsStore.activePath }"
      @click="switchTab(tab.path)"
    >
      <span class="tab-title">{{ tab.title }}</span>
      <el-icon
        v-if="tab.closable"
        class="tab-close"
        @click.stop="closeTab(tab.path)"
      >
        <Close />
      </el-icon>
    </div>
  </div>
</template>

<script setup>
import { watch } from "vue";
import { useRouter, useRoute } from "vue-router";
import { useTabsStore } from "@/stores/tabs";

const router = useRouter();
const route = useRoute();
const tabsStore = useTabsStore();

// Sync route changes → open tab
watch(
  () => route.path,
  () => {
    if (route.name) tabsStore.openTab(route);
  },
  { immediate: true }
);

function switchTab(path) {
  tabsStore.activePath = path;
  router.push(path);
}

function closeTab(path) {
  const redirectTo = tabsStore.closeTab(path);
  if (redirectTo) router.push(redirectTo);
}
</script>

<style scoped>
.tab-bar {
  display: flex;
  align-items: center;
  height: 36px;
  background: #f5f5f5;
  border-bottom: 1px solid #e8e8e8;
  padding: 0 4px;
  overflow-x: auto;
  overflow-y: hidden;
  flex-shrink: 0;
}

/* Hide scrollbar but allow scroll */
.tab-bar::-webkit-scrollbar { height: 0; }

.tab-item {
  display: flex;
  align-items: center;
  gap: 6px;
  height: 28px;
  padding: 0 12px;
  margin-right: 2px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  color: #595959;
  background: #ffffff;
  border: 1px solid #e8e8e8;
  white-space: nowrap;
  transition: all 0.15s;
  flex-shrink: 0;
}

.tab-item:hover {
  color: #fb7701;
  border-color: #fb7701;
}

.tab-item.active {
  color: #fb7701;
  border-color: #fb7701;
  background: #fff4e8;
  font-weight: 500;
}

.tab-close {
  font-size: 12px;
  color: #bfbfbf;
  border-radius: 50%;
  padding: 1px;
  transition: all 0.15s;
}

.tab-close:hover {
  color: #ffffff;
  background: #fb7701;
}
</style>
