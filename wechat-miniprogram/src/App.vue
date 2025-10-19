<template>
  <div id="app">
    <div class="mobile-container">
      <!-- 顶部导航栏 -->
      <div class="app-header">
        <div class="header-title">媒体翻译助手</div>
        <div class="header-actions">
          <button class="header-btn" @click="showProfile">
            <div class="profile-icon">👤</div>
          </button>
        </div>
      </div>

      <!-- 主要内容区域 -->
      <div class="app-content">
        <!-- 首页 -->
        <div v-if="currentPage === 'home'" class="page-content">
          <IndexPage />
        </div>

        <!-- 上传页面 -->
        <div v-else-if="currentPage === 'upload'" class="page-content">
          <UploadPage />
        </div>

        <!-- 历史页面 -->
        <div v-else-if="currentPage === 'history'" class="page-content">
          <HistoryPage />
        </div>

        <!-- 个人中心页面 -->
        <div v-else-if="currentPage === 'profile'" class="page-content">
          <ProfilePage />
        </div>

        <!-- 结果页面 -->
        <div v-else-if="currentPage === 'result'" class="page-content">
          <ResultPage :task-id="currentTaskId" />
        </div>
      </div>

      <!-- 底部导航栏 -->
      <div class="app-tabbar">
        <div 
          v-for="tab in tabs" 
          :key="tab.key"
          class="tab-item"
          :class="{ active: currentPage === tab.key }"
          @click="switchPage(tab.key)"
        >
          <div class="tab-icon">{{ currentPage === tab.key ? tab.activeIcon : tab.icon }}</div>
          <span class="tab-text">{{ tab.text }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import IndexPage from './pages/index/index.vue'
import UploadPage from './pages/upload/index.vue'
import HistoryPage from './pages/history/index.vue'
import ProfilePage from './pages/profile/index.vue'
import ResultPage from './pages/result/index.vue'

// 页面状态
const currentPage = ref('home')
const currentTaskId = ref<string>('')

// 底部导航配置
const tabs = [
  {
    key: 'home',
    text: '首页',
    icon: '🏠',
    activeIcon: '🏠'
  },
  {
    key: 'upload',
    text: '翻译',
    icon: '🎤',
    activeIcon: '🎤'
  },
  {
    key: 'history',
    text: '历史',
    icon: '📝',
    activeIcon: '📝'
  },
  {
    key: 'profile',
    text: '我的',
    icon: '👤',
    activeIcon: '👤'
  }
]

// 页面切换
function switchPage(page: string) {
  currentPage.value = page
}

// 显示个人中心
function showProfile() {
  currentPage.value = 'profile'
}

// 处理页面跳转
onMounted(() => {
  // 监听页面跳转事件
  window.navigateTo = (options: { url: string }) => {
    const url = options.url
    if (url.includes('/pages/result/index')) {
      const match = url.match(/task_id=([^&]+)/)
      if (match) {
        currentTaskId.value = match[1]
        currentPage.value = 'result'
      }
    } else if (url.includes('/pages/upload/index')) {
      currentPage.value = 'upload'
    } else if (url.includes('/pages/history/index')) {
      currentPage.value = 'history'
    } else if (url.includes('/pages/profile/index')) {
      currentPage.value = 'profile'
    }
  }

  // 监听页面返回事件
  window.navigateBack = () => {
    // 简单的返回逻辑
    if (currentPage.value === 'result') {
      currentPage.value = 'upload'
    }
  }

  // 监听重定向事件
  window.redirectTo = (options: { url: string }) => {
    window.navigateTo(options)
  }
})

// 声明全局类型
declare global {
  interface Window {
    navigateTo: (options: { url: string }) => void
    navigateBack: () => void
    redirectTo: (options: { url: string }) => void
  }
}
</script>

<style>
/* 全局样式 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
  background: #f5f5f5;
  color: #333;
}

#app {
  width: 100%;
  min-height: 100vh;
}

.mobile-container {
  max-width: 430px;
  margin: 0 auto;
  background: #fff;
  min-height: 100vh;
  position: relative;
  box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
}

/* 顶部导航栏 */
.app-header {
  background: linear-gradient(135deg, #4CAF50, #45a049);
  color: white;
  padding: 20rpx 32rpx;
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 88rpx;
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-title {
  font-size: 32rpx;
  font-weight: 600;
  flex: 1;
  text-align: center;
}

.header-actions {
  width: 60rpx;
  display: flex;
  justify-content: flex-end;
}

.header-btn {
  background: none;
  border: none;
  padding: 0;
  width: 40rpx;
  height: 40rpx;
}

.profile-icon {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20rpx;
  color: white;
}

/* 主要内容区域 */
.app-content {
  min-height: calc(100vh - 176rpx);
  background: #f5f5f5;
}

.page-content {
  width: 100%;
  height: 100%;
}

/* 底部导航栏 */
.app-tabbar {
  position: fixed;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 100%;
  max-width: 430px;
  background: white;
  border-top: 1rpx solid #e9ecef;
  display: flex;
  justify-content: space-around;
  padding: 16rpx 0;
  z-index: 100;
}

.tab-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8rpx 16rpx;
  cursor: pointer;
  transition: all 0.2s ease;
}

.tab-item.active {
  color: #4CAF50;
}

.tab-icon {
  width: 48rpx;
  height: 48rpx;
  margin-bottom: 8rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20rpx;
}

.tab-text {
  font-size: 20rpx;
  color: #7A7E83;
}

.tab-item.active .tab-text {
  color: #4CAF50;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .mobile-container {
    max-width: 100%;
    box-shadow: none;
  }
  
  .app-tabbar {
    max-width: 100%;
  }
}

/* 工具类 */
.text-center {
  text-align: center;
}

.flex {
  display: flex;
}

.flex-center {
  display: flex;
  align-items: center;
  justify-content: center;
}

.flex-column {
  display: flex;
  flex-direction: column;
}

.hidden {
  display: none !important;
}

/* 动画效果 */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

.slide-enter-active, .slide-leave-active {
  transition: transform 0.3s ease;
}

.slide-enter-from {
  transform: translateX(100%);
}

.slide-leave-to {
  transform: translateX(-100%);
}
</style>