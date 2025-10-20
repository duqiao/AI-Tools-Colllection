<template>
  <div class="ai-tools-container">
    <!-- Status Bar -->
    <div class="status-bar">
      <div class="status-time">{{ currentTime }}</div>
      <div class="status-indicators">
        <div class="battery-indicator">
          <div class="battery-outer">
            <div class="battery-inner"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Header Icons -->
    <div class="header-icons">
      <button class="header-icon-btn" @click="showMenu">
        <div class="menu-dots">
          <div class="dot"></div>
          <div class="dot"></div>
          <div class="dot"></div>
        </div>
      </button>
      <button class="header-icon-btn" @click="showProfile">
        <div class="profile-circle">
          <div class="profile-inner"></div>
        </div>
      </button>
    </div>

    <!-- Title -->
    <div class="title-section">
      <h1 class="main-title">AI语音视频工具</h1>
    </div>

    <!-- Info Banner -->
    <div class="info-banner">
      <div class="banner-icon">🔊</div>
      <p class="banner-text">本工具，升级套餐解锁更多权限</p>
    </div>

    <!-- Main Content -->
    <div class="main-content">
      <!-- Feature Cards -->
      <div class="feature-cards">
        <div 
          v-for="feature in mainFeatures" 
          :key="feature.id"
          class="feature-card"
          @click="handleFeatureClick(feature)"
        >
          <div class="feature-icon-container" :class="feature.iconBg">
            <div class="feature-icon">{{ feature.icon }}</div>
          </div>
          <div class="feature-content">
            <div class="feature-header">
              <h3 class="feature-title">{{ feature.title }}</h3>
              <span v-if="feature.badge" class="feature-badge" :class="feature.badgeClass">
                {{ feature.badge }}
              </span>
            </div>
            <p class="feature-description">{{ feature.description }}</p>
          </div>
          <div class="feature-arrow">›</div>
        </div>
      </div>

      <!-- Bottom Feature Grid -->
      <div class="bottom-features">
        <div 
          v-for="feature in bottomFeatures" 
          :key="feature.id"
          class="bottom-feature-card"
          @click="handleFeatureClick(feature)"
        >
          <div class="bottom-feature-icon-container" :class="feature.iconBg">
            <div class="bottom-feature-icon">{{ feature.icon }}</div>
          </div>
          <h3 class="bottom-feature-title">{{ feature.title }}</h3>
          <div class="bottom-feature-desc">
            <span>{{ feature.description }}</span>
            <span class="bottom-feature-arrow">›</span>
          </div>
        </div>
      </div>

      <!-- CTA Button -->
      <div class="cta-section">
        <button class="cta-button" @click="showToolKit">
          <div class="cta-content">
            <div class="cta-icon">💼</div>
            <span class="cta-text">超全工具包！神器汇总！</span>
          </div>
          <div class="cta-go">
            <span>GO</span>
          </div>
        </button>
      </div>

      <!-- Footer -->
      <div class="footer">
        <p class="footer-text">©河南省云助手信息科技有限公司</p>
      </div>
    </div>

    <!-- Bottom Navigation -->
    <div class="bottom-navigation">
      <button 
        v-for="tab in bottomTabs" 
        :key="tab.id"
        class="nav-tab"
        :class="{ active: currentTab === tab.id }"
        @click="switchTab(tab.id)"
      >
        <div class="nav-icon" :class="{ active: currentTab === tab.id }">
          {{ tab.icon }}
        </div>
        <span class="nav-text" :class="{ active: currentTab === tab.id }">
          {{ tab.text }}
        </span>
      </button>
    </div>

    <!-- Android Navigation Bar -->
    <div class="android-nav">
      <button class="android-nav-btn" @click="showMenu">
        <div class="android-icon">☰</div>
      </button>
      <button class="android-nav-btn" @click="handleHome">
        <div class="android-icon">◻</div>
      </button>
      <button class="android-nav-btn" @click="goBack">
        <div class="android-icon">‹</div>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onActivated, onUnmounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { useTranslationStore } from '@/stores/translation'
import type { TranslationTask } from '@/types'
import { uni } from '@/utils/uni-adapter'

// Stores
const userStore = useUserStore()
const translationStore = useTranslationStore()

// Reactive data
const appVersion = ref('1.0.0')
const recentTranslations = ref<TranslationTask[]>([])
const currentTime = ref('')
const currentTab = ref('home')
let timeInterval: number | null = null

// Feature data from Figma design
const mainFeatures = ref([
  {
    id: 1,
    icon: '🎤',
    iconBg: 'bg-green-500',
    title: '实时语音转文字',
    description: '实时录音同步生成文字',
    badge: '高级功能',
    badgeClass: 'badge-default'
  },
  {
    id: 2,
    icon: '🎧',
    iconBg: 'bg-blue-500',
    title: '音频转文字',
    description: '请将音频文件发送至微信文件传输助手',
    badge: null
  },
  {
    id: 3,
    icon: '🎬',
    iconBg: 'bg-purple-500',
    title: '视频转文字',
    description: '上传视频转换文字',
    badge: null
  },
  {
    id: 4,
    icon: '📹',
    iconBg: 'bg-blue-400',
    title: '视频写文案提取',
    description: '转发视频号视频提取文字',
    badge: '新',
    badgeClass: 'badge-destructive'
  }
])

const bottomFeatures = ref([
  {
    id: 5,
    icon: '🔗',
    iconBg: 'bg-orange-500',
    title: '链接转文字',
    description: '从链接提'
  },
  {
    id: 6,
    icon: '🖼️',
    iconBg: 'bg-cyan-400',
    title: '图片转文字',
    description: '上传图片'
  }
])

const bottomTabs = ref([
  {
    id: 'home',
    icon: '🏠',
    text: '语音转文字'
  },
  {
    id: 'history',
    icon: '📄',
    text: '识别记录'
  },
  {
    id: 'profile',
    icon: '👤',
    text: '我的'
  }
])

// Computed
const isLoggedIn = computed(() => userStore.isLoggedIn)

// Lifecycle
onMounted(() => {
  console.log('Index page mounted')
  initializePage()
  updateCurrentTime()
  timeInterval = setInterval(updateCurrentTime, 1000)
})

onUnmounted(() => {
  if (timeInterval) {
    clearInterval(timeInterval)
  }
})

onActivated(() => {
  console.log('Index page activated')
  refreshData()
})

// Methods
function updateCurrentTime() {
  const now = new Date()
  currentTime.value = now.toLocaleTimeString('zh-CN', { 
    hour: '2-digit', 
    minute: '2-digit',
    hour12: false 
  })
}

async function initializePage() {
  await userStore.checkLoginStatus()
  await loadRecentTranslations()
}

async function refreshData() {
  await userStore.checkLoginStatus()
  await loadRecentTranslations()
}

async function loadRecentTranslations() {
  try {
    // Mock recent translations for now
    recentTranslations.value = []
  } catch (error) {
    console.error('Load recent translations error:', error)
  }
}

function handleFeatureClick(feature: any) {
  console.log('Feature clicked:', feature.title)
  
  // Handle different features based on their type
  switch (feature.id) {
    case 1: // 实时语音转文字
      uni.showToast({
        title: '开启实时录音',
        icon: 'none'
      })
      break
    case 2: // 音频转文字
      goToUpload()
      break
    case 3: // 视频转文字
      goToUpload()
      break
    case 4: // 视频写文案提取
      uni.showToast({
        title: '视频文案提取',
        icon: 'none'
      })
      break
    case 5: // 链接转文字
      uni.showToast({
        title: '链接解析功能',
        icon: 'none'
      })
      break
    case 6: // 图片转文字
      uni.showToast({
        title: '图片文字识别',
        icon: 'none'
      })
      break
  }
}

function showMenu() {
  uni.showActionSheet({
    itemList: ['设置', '帮助中心', '关于我们', '意见反馈'],
    success: (res) => {
      switch (res.tapIndex) {
        case 0:
          showSettings()
          break
        case 1:
          showHelp()
          break
        case 2:
          showAbout()
          break
        case 3:
          showFeedback()
          break
      }
    }
  })
}

function showProfile() {
  uni.navigateTo({
    url: '/pages/profile/index'
  })
}

function showToolKit() {
  uni.showModal({
    title: '工具包',
    content: '完整的AI工具集合，包含语音转文字、视频转文字、图片识别等多种功能',
    showCancel: false,
    confirmText: '了解详情'
  })
}

function switchTab(tabId: string) {
  currentTab.value = tabId
  console.log('Switched to tab:', tabId)
  
  switch (tabId) {
    case 'home':
      // Already on home page
      break
    case 'history':
      uni.navigateTo({
        url: '/pages/history/index'
      })
      break
    case 'profile':
      uni.navigateTo({
        url: '/pages/profile/index'
      })
      break
  }
}

function handleHome() {
  // Already on home page, just refresh
  refreshData()
}

function goBack() {
  uni.navigateBack({
    delta: 1
  })
}

function goToUpload() {
  uni.navigateTo({
    url: '/pages/upload/index'
  })
}

function goToHistory() {
  uni.navigateTo({
    url: '/pages/history/index'
  })
}

function goToVip() {
  uni.navigateTo({
    url: '/pages/profile/index'
  })
}

function showSettings() {
  uni.showToast({
    title: '设置功能',
    icon: 'none'
  })
}

function showHelp() {
  uni.showToast({
    title: '使用帮助',
    icon: 'none'
  })
}

function showAbout() {
  uni.showToast({
    title: '关于我们',
    icon: 'none'
  })
}

function showFeedback() {
  uni.showToast({
    title: '意见反馈',
    icon: 'none'
  })
}

function checkUpdate() {
  uni.showToast({
    title: '已是最新版本',
    icon: 'success'
  })
}

// Share functions
function onShareAppMessage() {
  return {
    title: 'AI语音视频工具 - 专业语音识别服务',
    desc: '支持语音转文字、视频转文字、图片识别等多种功能',
    path: '/pages/index/index',
    imageUrl: '/static/images/share-app.png'
  }
}

function onShareTimeline() {
  return {
    title: 'AI语音视频工具',
    desc: '专业的AI语音视频处理工具',
    imageUrl: '/static/images/share-app.png'
  }
}

// Export share functions for Vue 3 app
defineExpose({
  onShareAppMessage,
  onShareTimeline
})
</script>

<style>
/* Figma Design Styles - AI Voice Video Tools */
.ai-tools-container {
  min-height: 100vh;
  background: linear-gradient(to bottom right, #e0e7ff 0%, #dbeafe 50%, #cffafe 100%);
  display: flex;
  flex-direction: column;
  position: relative;
}

/* Status Bar */
.status-bar {
  padding: 12rpx 24rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #374151;
  font-size: 24rpx;
}

.status-time {
  font-weight: 500;
}

.status-indicators {
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.battery-indicator {
  width: 32rpx;
  height: 24rpx;
  border: 2rpx solid #374151;
  border-radius: 4rpx;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.battery-inner {
  width: 16rpx;
  height: 12rpx;
  background: #374151;
  border-radius: 2rpx;
}

/* Header Icons */
.header-icons {
  padding: 0 24rpx;
  display: flex;
  justify-content: flex-end;
  gap: 32rpx;
  margin-bottom: 32rpx;
}

.header-icon-btn {
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  backdrop-filter: blur(10rpx);
}

.menu-dots {
  display: flex;
  gap: 4rpx;
}

.dot {
  width: 8rpx;
  height: 8rpx;
  border-radius: 50%;
  background: #374151;
}

.profile-circle {
  width: 40rpx;
  height: 40rpx;
  border: 4rpx solid #374151;
  border-radius: 50%;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.profile-inner {
  width: 16rpx;
  height: 16rpx;
  border: 4rpx solid #374151;
  border-radius: 50%;
}

/* Title */
.title-section {
  text-align: center;
  margin-bottom: 48rpx;
}

.main-title {
  color: #3b82f6;
  font-size: 48rpx;
  font-weight: 700;
  margin: 0;
  line-height: 1.2;
}

/* Info Banner */
.info-banner {
  padding: 0 24rpx;
  margin-bottom: 32rpx;
}

.info-banner {
  background: #fef3c7;
  border-radius: 9999rpx;
  padding: 24rpx 32rpx;
  display: flex;
  align-items: center;
  gap: 24rpx;
}

.banner-icon {
  width: 40rpx;
  height: 40rpx;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32rpx;
}

.banner-text {
  color: #374151;
  font-size: 28rpx;
  margin: 0;
  flex: 1;
}

/* Main Content */
.main-content {
  flex: 1;
  padding: 0 24rpx 256rpx;
  display: flex;
  flex-direction: column;
  gap: 32rpx;
}

/* Feature Cards */
.feature-cards {
  display: flex;
  flex-direction: column;
  gap: 32rpx;
}

.feature-card {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10rpx);
  border-radius: 48rpx;
  padding: 32rpx;
  display: flex;
  align-items: center;
  gap: 32rpx;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  cursor: pointer;
  border: none;
}

.feature-card:hover {
  box-shadow: 0 8rpx 24rpx rgba(0, 0, 0, 0.1);
  transform: translateY(-2rpx);
}

.feature-icon-container {
  width: 112rpx;
  height: 112rpx;
  border-radius: 32rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.feature-icon {
  font-size: 56rpx;
  color: white;
}

.feature-content {
  flex: 1;
  min-width: 0;
}

.feature-header {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-bottom: 8rpx;
}

.feature-title {
  color: #111827;
  font-size: 32rpx;
  font-weight: 600;
  margin: 0;
}

.feature-badge {
  font-size: 20rpx;
  padding: 4rpx 16rpx;
  border-radius: 16rpx;
  font-weight: 500;
}

.badge-default {
  background: #f3f4f6;
  color: #374151;
}

.badge-destructive {
  background: #fee2e2;
  color: #dc2626;
}

.feature-description {
  color: #6b7280;
  font-size: 28rpx;
  margin: 0;
  line-height: 1.5;
}

.feature-arrow {
  color: #9ca3af;
  font-size: 40rpx;
  flex-shrink: 0;
}

/* Bottom Features Grid */
.bottom-features {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 32rpx;
}

.bottom-feature-card {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10rpx);
  border-radius: 48rpx;
  padding: 32rpx;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  cursor: pointer;
  border: none;
  text-align: left;
}

.bottom-feature-card:hover {
  box-shadow: 0 8rpx 24rpx rgba(0, 0, 0, 0.1);
  transform: translateY(-2rpx);
}

.bottom-feature-icon-container {
  width: 96rpx;
  height: 96rpx;
  border-radius: 32rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 24rpx;
}

.bottom-feature-icon {
  font-size: 48rpx;
  color: white;
}

.bottom-feature-title {
  color: #111827;
  font-size: 28rpx;
  font-weight: 600;
  margin: 0 0 8rpx 0;
}

.bottom-feature-desc {
  display: flex;
  align-items: center;
  gap: 8rpx;
  color: #6b7280;
  font-size: 24rpx;
}

.bottom-feature-arrow {
  color: #9ca3af;
  font-size: 32rpx;
}

/* CTA Section */
.cta-section {
  padding-top: 32rpx;
}

.cta-button {
  width: 100%;
  background: linear-gradient(to right, #4ade80 0%, #06b6d4 100%);
  border-radius: 9999rpx;
  padding: 32rpx 48rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  cursor: pointer;
  border: none;
}

.cta-button:hover {
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.01);
  transform: translateY(-2rpx);
}

.cta-content {
  display: flex;
  align-items: center;
  gap: 24rpx;
}

.cta-icon {
  font-size: 48rpx;
  color: white;
}

.cta-text {
  color: white;
  font-size: 32rpx;
  font-weight: 600;
}

.cta-go {
  background: #67e8f9;
  border-radius: 9999rpx;
  width: 96rpx;
  height: 96rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 28rpx;
  font-weight: 700;
}

/* Footer */
.footer {
  text-align: center;
  padding-top: 32rpx;
}

.footer-text {
  color: #6b7280;
  font-size: 20rpx;
  margin: 0;
}

/* Bottom Navigation */
.bottom-navigation {
  position: fixed;
  bottom: 96rpx;
  left: 0;
  right: 0;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10rpx);
  border-top: 1rpx solid #e5e7eb;
}

.bottom-navigation {
  display: flex;
  align-items: center;
  justify-content: space-around;
  padding: 24rpx 0;
}

.nav-tab {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8rpx;
  background: none;
  border: none;
  padding: 8rpx 16rpx;
  cursor: pointer;
  transition: all 0.2s ease;
}

.nav-icon {
  font-size: 48rpx;
  color: #9ca3af;
}

.nav-icon.active {
  color: #3b82f6;
}

.nav-text {
  font-size: 20rpx;
  color: #9ca3af;
}

.nav-text.active {
  color: #3b82f6;
}

/* Android Navigation Bar */
.android-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10rpx);
  height: 96rpx;
  display: flex;
  align-items: center;
  justify-content: space-around;
}

.android-nav-btn {
  background: none;
  border: none;
  padding: 16rpx;
  cursor: pointer;
}

.android-icon {
  font-size: 48rpx;
  color: #4b5563;
}

/* Color classes for icon backgrounds - Exact Tailwind Colors from Figma */
.bg-green-500 {
  background: #22c55e;
}

.bg-blue-500 {
  background: #3b82f6;
}

.bg-purple-500 {
  background: #a855f7;
}

.bg-blue-400 {
  background: #60a5fa;
}

.bg-orange-500 {
  background: #f97316;
}

.bg-cyan-400 {
  background: #22d3ee;
}

/* Responsive Design */
@media (max-width: 750rpx) {
  .bottom-features {
    grid-template-columns: 1fr;
    gap: 24rpx;
  }
  
  .feature-card {
    padding: 24rpx;
    gap: 24rpx;
  }
  
  .feature-icon-container {
    width: 96rpx;
    height: 96rpx;
  }
  
  .main-title {
    font-size: 40rpx;
  }
}

/* Button active states */
.header-icon-btn:active,
.feature-card:active,
.bottom-feature-card:active,
.cta-button:active,
.nav-tab:active,
.android-nav-btn:active {
  opacity: 0.8;
  transform: scale(0.98);
}

.header-section {
  background: linear-gradient(135deg, #4CAF50, #45a049);
  color: white;
  padding: 40rpx 32rpx 60rpx;
}

.header-content {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.app-logo {
  margin-bottom: 24rpx;
}

.logo-emoji {
  width: 80rpx;
  height: 80rpx;
  font-size: 60rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.app-title {
  font-size: 36rpx;
  font-weight: 700;
  margin-bottom: 8rpx;
  text-align: center;
}

.app-subtitle {
  font-size: 26rpx;
  opacity: 0.8;
  text-align: center;
}

.user-section {
  margin: -20rpx 24rpx 32rpx;
}

.user-info {
  background: white;
  border-radius: 16rpx;
  padding: 32rpx;
  display: flex;
  align-items: center;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.1);
}

.user-avatar {
  width: 80rpx;
  height: 80rpx;
  border-radius: 50%;
  background: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32rpx;
  margin-right: 24rpx;
}

.user-details {
  flex: 1;
}

.user-name {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 8rpx;
}

.plan-text {
  font-size: 24rpx;
  color: #4CAF50;
  font-weight: 500;
}

.login-section {
  margin: 24rpx;
}

.login-prompt {
  background: white;
  border-radius: 16rpx;
  padding: 60rpx 40rpx;
  text-align: center;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.05);
}

.login-icon {
  font-size: 80rpx;
  margin-bottom: 24rpx;
}

.login-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 12rpx;
}

.login-subtitle {
  font-size: 26rpx;
  color: #666;
  margin-bottom: 32rpx;
}

.login-btn {
  background: linear-gradient(45deg, #4CAF50, #45a049);
  color: white;
  border: none;
  border-radius: 12rpx;
  font-size: 28rpx;
  padding: 24rpx 48rpx;
}

.quick-actions {
  margin: 0 24rpx 32rpx;
}

.section-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24rpx;
}

.title-text {
  font-size: 28rpx;
  font-weight: 600;
  color: #333;
}

.title-more {
  font-size: 24rpx;
  color: #4CAF50;
}

.action-buttons {
  margin-bottom: 24rpx;
}

.btn-primary {
  width: 100%;
  background: linear-gradient(45deg, #4CAF50, #45a049);
  color: white;
  border: none;
  border-radius: 16rpx;
  font-size: 28rpx;
  font-weight: 500;
  padding: 32rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-large {
  padding: 40rpx;
}

.btn-icon {
  font-size: 32rpx;
  margin-right: 12rpx;
}

.secondary-actions {
  display: flex;
  gap: 16rpx;
}

.btn-secondary {
  flex: 1;
  background: white;
  color: #333;
  border: 1rpx solid #e9ecef;
  border-radius: 12rpx;
  font-size: 24rpx;
  padding: 24rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.features-section {
  margin: 0 24rpx 32rpx;
}

.features-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16rpx;
}

.feature-item {
  background: white;
  border-radius: 12rpx;
  padding: 24rpx;
  text-align: center;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.05);
}

.feature-icon {
  font-size: 48rpx;
  margin-bottom: 16rpx;
}

.feature-title {
  font-size: 26rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 8rpx;
}

.feature-desc {
  font-size: 22rpx;
  color: #666;
  line-height: 1.4;
}

.footer-section {
  margin: 0 24rpx;
  padding: 24rpx 0;
}

.footer-links {
  display: flex;
  justify-content: center;
  gap: 32rpx;
  margin-bottom: 16rpx;
}

.footer-link {
  font-size: 24rpx;
  color: #666;
}

.footer-info {
  text-align: center;
}

.version-text,
.copyright-text {
  font-size: 20rpx;
  color: #999;
  display: block;
  margin-bottom: 4rpx;
}

/* Button active states */
.login-btn:active,
.btn-primary:active,
.btn-secondary:active {
  opacity: 0.8;
  transform: scale(0.98);
}

/* Responsive design */
@media (max-width: 750rpx) {
  .features-grid {
    grid-template-columns: 1fr;
  }
  
  .secondary-actions {
    flex-direction: column;
  }
  
  .footer-links {
    flex-direction: column;
    gap: 16rpx;
  }
}
</style>