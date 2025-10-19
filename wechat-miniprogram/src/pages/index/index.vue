<template>
  <div class="container">
    <div class="header-section">
      <div class="header-content">
        <div class="app-logo">
          <div class="logo-emoji">🎵</div>
        </div>
        <div class="app-title">媒体翻译助手</div>
        <div class="app-subtitle">专业的语音识别服务</div>
      </div>
    </div>

    <!-- User Section -->
    <div v-if="userStore.isLoggedIn" class="user-section">
      <div class="user-info">
        <div class="user-avatar">👤</div>
        <div class="user-details">
          <div class="user-name">{{ userStore.userInfo?.username || '用户' }}</div>
          <div class="user-plan">
            <span class="plan-text">{{ userStore.subscriptionLevel || '免费版' }}</span>
          </div>
        </div>
      </div>
      
      <!-- Quota Display Component -->
      <QuotaDisplay 
        @upgrade="onQuotaUpgrade"
        @details="onQuotaDetails"
      />
    </div>

    <!-- Login Section -->
    <div v-else class="login-section">
      <div class="login-prompt">
        <div class="login-icon">🔐</div>
        <div class="login-title">欢迎使用媒体翻译器</div>
        <div class="login-subtitle">请先登录以使用完整功能</div>
        <button class="login-btn" @click="handleLogin">
          微信登录
        </button>
      </div>
    </div>

    <!-- Quick Actions -->
    <div v-if="userStore.isLoggedIn" class="quick-actions">
      <div class="section-title">
        <span class="title-text">快速操作</span>
        <span class="title-more">查看全部</span>
      </div>
      
      <div class="action-buttons">
        <button class="btn-primary btn-large" @click="goToUpload">
          <div class="btn-icon">🎤</div>
          开始翻译
        </button>
      </div>

      <div class="secondary-actions">
        <button class="btn-secondary" @click="goToHistory">
          <div class="btn-icon">📝</div>
          翻译历史
        </button>
        <button class="btn-secondary" @click="goToVip">
          <div class="btn-icon">💎</div>
          升级VIP
        </button>
      </div>
    </div>

    <!-- Features Section -->
    <div class="features-section">
      <div class="section-title">
        <span class="title-text">功能特色</span>
      </div>
      
      <div class="features-grid">
        <div class="feature-item" @click="showFeatures">
          <div class="feature-icon">🎵</div>
          <div class="feature-title">多格式支持</div>
          <div class="feature-desc">支持音频、视频等多种格式</div>
        </div>
        
        <div class="feature-item" @click="showFeatures">
          <div class="feature-icon">🎯</div>
          <div class="feature-title">高质量识别</div>
          <div class="feature-desc">专业AI语音识别技术</div>
        </div>
        
        <div class="feature-item" @click="showFeatures">
          <div class="feature-icon">⚡</div>
          <div class="feature-title">快速处理</div>
          <div class="feature-desc">5-10秒完成识别</div>
        </div>
        
        <div class="feature-item" @click="showFeatures">
          <div class="feature-icon">✏️</div>
          <div class="feature-title">结果编辑</div>
          <div class="feature-desc">支持文本编辑和分享</div>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <div class="footer-section">
      <div class="footer-links">
        <span class="footer-link" @click="showHelp">使用帮助</span>
        <span class="footer-link" @click="showAbout">关于我们</span>
        <span class="footer-link" @click="checkUpdate">检查更新</span>
      </div>
      <div class="footer-info">
        <span class="version-text">v{{ appVersion }}</span>
        <span class="copyright-text">© 2024 媒体翻译器</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onActivated } from 'vue'
import { useUserStore } from '@/stores/user'
import { useTranslationStore } from '@/stores/translation'
import type { TranslationTask } from '@/types'
import { uni } from '@/utils/uni-adapter'
import QuotaDisplay from '@/components/quota-display/index.vue'

// Stores
const userStore = useUserStore()
const translationStore = useTranslationStore()

// Reactive data
const appVersion = ref('1.0.0')
const recentTranslations = ref<TranslationTask[]>([])

// Computed
const isLoggedIn = computed(() => userStore.isLoggedIn)

// Lifecycle
onMounted(() => {
  console.log('Index page mounted')
  initializePage()
})

onActivated(() => {
  console.log('Index page activated')
  refreshData()
})

// Methods
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

function handleLogin() {
  uni.showModal({
    title: '微信登录',
    content: '将使用微信账号登录',
    success: async (res) => {
      if (res.confirm) {
        try {
          await userStore.login({
            code: 'mock-code',
            userInfo: { nickName: '测试用户' }
          })
          uni.showToast({
            title: '登录成功',
            icon: 'success'
          })
        } catch (error) {
          uni.showToast({
            title: '登录失败',
            icon: 'none'
          })
        }
      }
    }
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

function showFeatures() {
  uni.showToast({
    title: '功能展示',
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

function checkUpdate() {
  uni.showToast({
    title: '已是最新版本',
    icon: 'success'
  })
}

function onQuotaUpgrade(quotaInfo: any) {
  console.log('Upgrade requested:', quotaInfo)
  goToVip()
}

function onQuotaDetails(quotaInfo: any) {
  console.log('Details requested:', quotaInfo)
}

// Share functions
function onShareAppMessage() {
  return {
    title: '媒体翻译器 - 语音识别转文字',
    desc: '专业的语音识别服务，支持多种音频视频格式',
    path: '/pages/index/index',
    imageUrl: '/static/images/share-app.png'
  }
}

function onShareTimeline() {
  return {
    title: '媒体翻译器 - 专业语音识别服务',
    desc: '支持多种格式，高精度识别',
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
/* Import existing styles from original index.wxss */
.container {
  min-height: 100vh;
  background: #f5f5f5;
  padding-bottom: 100rpx;
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