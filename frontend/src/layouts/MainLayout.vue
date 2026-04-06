<template>
  <el-container class="layout-container">
    <!-- 侧边栏 -->
    <el-aside width="220px" class="aside">
      <div class="logo">
        <el-icon size="24"><Shop /></el-icon>
        <span>管理系统</span>
      </div>
      <el-menu
        :default-active="$route.path"
        router
        background-color="#ffffff"
        text-color="#333333"
        active-text-color="#fb7701"
      >
        <el-menu-item index="/">
          <el-icon><House /></el-icon>
          <span>AI绘画</span>
        </el-menu-item>
        <el-menu-item index="/video">
          <el-icon><VideoCamera /></el-icon>
          <span>AI视频</span>
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <span>设置</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container style="flex-direction: column; overflow: hidden;">
      <!-- 顶栏 -->
      <el-header class="header">
        <span class="page-title">{{ $route.meta.title || "管理系统" }}</span>
        <div class="header-right">
          <el-tooltip content="刷新页面" placement="bottom" :show-after="300">
            <button class="refresh-btn" :class="{ spinning: isRefreshing }" @click="refreshPage" aria-label="刷新">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/>
                <path d="M21 3v5h-5"/>
                <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/>
                <path d="M8 16H3v5"/>
              </svg>
            </button>
          </el-tooltip>
          <el-tag type="success" size="small" style="-webkit-app-region: no-drag">本地运行</el-tag>
          <WinControls />
        </div>
      </el-header>

      <!-- 多标签栏 -->
      <TabBar />

      <!-- 主内容 -->
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import WinControls from "@/components/WinControls.vue";
import TabBar from "@/components/TabBar.vue";
import { VideoCamera } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const isRefreshing = ref(false)

function refreshPage() {
  if (isRefreshing.value) return
  isRefreshing.value = true

  // Electron 环境：直接调用 webContents reload
  if (window.electronAPI?.reload) {
    window.electronAPI.reload()
    setTimeout(() => { isRefreshing.value = false }, 800)
    return
  }

  // Web 环境：用路由跳转空白页再返回实现组件重载
  const currentPath = route.fullPath
  router.replace('/blank').then(() => {
    router.replace(currentPath).then(() => {
      setTimeout(() => { isRefreshing.value = false }, 400)
    })
  })
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
  overflow: hidden;
}

.aside {
  background-color: #ffffff;
  overflow: hidden;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
  z-index: 1;
  display: flex;
  flex-direction: column;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  height: 64px;
  padding: 0 20px;
  color: #fb7701;
  font-size: 16px;
  font-weight: 600;
  border-bottom: 1px solid #f0f0f0;
  flex-shrink: 0;
  -webkit-app-region: drag;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #ffffff;
  border-bottom: 1px solid #f0f0f0;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  padding: 0;
  flex-shrink: 0;
  -webkit-app-region: drag;
}

.page-title {
  font-size: 16px;
  font-weight: 500;
  color: #262626;
  padding-left: 20px;
  -webkit-app-region: drag;
}

.header-right {
  display: flex;
  align-items: center;
  height: 100%;
  gap: 8px;
  padding-right: 4px;
  -webkit-app-region: no-drag;
}

.main {
  background: #f5f5f5;
  padding: 24px;
  overflow-y: auto;
  flex: 1;
}

/* Active item */
:deep(.el-menu-item.is-active) {
  background-color: #fff4e8 !important;
  border-left: 3px solid #fb7701;
}

:deep(.el-menu-item:hover) {
  background-color: #fff4e8 !important;
}

.refresh-btn {
  -webkit-app-region: no-drag;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  border: none;
  background: transparent;
  color: #666;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  transition: background 0.15s, color 0.15s;
}

.refresh-btn:hover {
  background: #f0f0f0;
  color: #fb7701;
}

.refresh-btn svg {
  width: 15px;
  height: 15px;
  transition: transform 0.6s ease;
}

.refresh-btn.spinning svg {
  animation: spin-once 0.6s ease;
}

@keyframes spin-once {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}
</style>
