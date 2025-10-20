<template>
  <div class="profile-page">
    <!-- 顶部导航 -->
    <div class="nav-header">
      <div class="nav-title">个人中心</div>
    </div>

    <!-- 用户信息卡片 -->
    <div class="user-card">
      <div class="user-avatar">
        <div class="avatar-img">👤</div>
        <div class="vip-badge" v-if="isVip">
          <span class="vip-text">{{ getVipLevelText() }}</span>
        </div>
      </div>
      
      <div class="user-info">
        <span class="username">{{ displayName }}</span>
        <span class="user-id">ID: {{ userInfo?.id }}</span>
        <span class="join-time">加入时间：{{ formatJoinTime() }}</span>
      </div>
    </div>

    <!-- 订阅状态 -->
    <div class="subscription-card">
      <div class="subscription-header">
        <span class="subscription-title">订阅状态</span>
        <button v-if="!isVip" class="upgrade-btn" @click="goToUpgrade">立即升级</button>
        <button v-else class="manage-btn" @click="manageSubscription">管理订阅</button>
      </div>
      
      <div class="subscription-info">
        <div class="info-row">
          <span class="info-label">当前套餐：</span>
          <span class="info-value">{{ getPlanTypeText() }}</span>
        </div>
        <div v-if="userInfo?.subscription_expires_at" class="info-row">
          <span class="info-label">到期时间：</span>
          <span class="info-value">{{ formatExpireTime() }}</span>
        </div>
        <div v-if="!isVip" class="info-row">
          <span class="info-label">剩余配额：</span>
          <span class="info-value quota-value">{{ remainingQuota }}/{{ quotaInfo?.monthly_quota || 0 }}</span>
        </div>
      </div>
    </div>

    <!-- 配额使用情况 -->
    <quota-display 
      :show-details="true" 
      @upgrade="onUpgradePrompt"
      @details="onQuotaDetails"
    />

    <!-- 统计信息 -->
    <div class="stats-section">
      <div class="stats-title">使用统计</div>
      <div class="stats-grid">
        <div class="stat-item">
          <span class="stat-number">{{ stats.totalTranslations }}</span>
          <span class="stat-label">总翻译次数</span>
        </div>
        <div class="stat-item">
          <span class="stat-number">{{ stats.thisMonth }}</span>
          <span class="stat-label">本月翻译</span>
        </div>
        <div class="stat-item">
          <span class="stat-number">{{ formatFileSize(stats.totalSize) }}</span>
          <span class="stat-label">处理文件大小</span>
        </div>
        <div class="stat-item">
          <span class="stat-number">{{ stats.avgDuration }}</span>
          <span class="stat-label">平均处理时长</span>
        </div>
      </div>
    </div>

    <!-- 功能菜单 -->
    <div class="menu-section">
      <div class="menu-item" @click="viewHistory">
        <div class="menu-icon">
          <div>📝</div>
        </div>
        <span class="menu-title">翻译历史</span>
        <span class="menu-arrow">›</span>
      </div>
      
      <div class="menu-item" @click="viewUsage">
        <div class="menu-icon">
          <div>📊</div>
        </div>
        <span class="menu-title">使用明细</span>
        <span class="menu-arrow">›</span>
      </div>
      
      <div class="menu-item" @click="contactSupport">
        <div class="menu-icon">
          <div>💬</div>
        </div>
        <span class="menu-title">联系客服</span>
        <span class="menu-arrow">›</span>
      </div>
      
      <div class="menu-item" @click="viewSettings">
        <div class="menu-icon">
          <div>⚙️</div>
        </div>
        <span class="menu-title">设置</span>
        <span class="menu-arrow">›</span>
      </div>
    </div>

    <!-- 版本信息 -->
    <div class="version-info">
      <span class="version-text">版本 {{ appVersion }}</span>
      <button class="check-update-btn" @click="checkUpdate">检查更新</button>
    </div>

    <!-- 退出登录 -->
    <div class="logout-section">
      <button class="logout-btn" @click="logout">退出登录</button>
    </div>

    <!-- 升级提示弹窗 -->
    <upgrade-prompt 
      v-if="showUpgradePrompt"
      :show="showUpgradePrompt"
      :type="upgradeType"
      :quota-info="quotaInfo"
      @close="closeUpgradePrompt"
      @confirm="confirmUpgrade"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { useTranslationStore } from '@/stores/translation'
import { authApi, quotaApi, subscriptionApi, apiUtils, systemApi } from '@/api'
import type { QuotaInfo, UserInfo } from '@/types'
import QuotaDisplay from '@/components/quota-display/index.vue'
import UpgradePrompt from '@/components/upgrade-prompt/index.vue'
import { uni } from '@/utils/uni-adapter'

// Stores
const userStore = useUserStore()
const translationStore = useTranslationStore()

// Reactive data
const userInfo = ref<UserInfo | null>(null)
const quotaInfo = ref<QuotaInfo | null>(null)
const stats = ref({
  totalTranslations: 0,
  thisMonth: 0,
  totalSize: 0,
  avgDuration: '0秒'
})
const appVersion = ref('1.0.0')
const showUpgradePrompt = ref(false)
const upgradeType = ref<string>('upgrade')

// Computed
const displayName = computed(() => {
  return userStore.displayName
})

const isVip = computed(() => {
  return userStore.isVip
})

const remainingQuota = computed(() => {
  return userStore.remainingQuota
})

// Lifecycle
onMounted(() => {
  loadUserInfo()
  loadQuotaInfo()
  loadStats()
  loadAppVersion()
})

// Methods
async function loadUserInfo() {
  try {
    const response = await authApi.getUserInfo()
    userInfo.value = response.data
    userStore.updateUserInfo(response.data)
  } catch (error) {
    console.error('Load user info error:', error)
  }
}

async function loadQuotaInfo() {
  try {
    const response = await quotaApi.getStatus()
    quotaInfo.value = response
    userStore.updateQuotaInfo(response)
  } catch (error) {
    console.error('Load quota info error:', error)
  }
}

async function loadStats() {
  try {
    // 获取翻译历史统计
    const historyResponse = await translationStore.getTranslationHistory({ limit: 1000 })
    const translations = historyResponse.data || []
    
    // 计算统计数据
    const now = new Date()
    const thisMonth = now.getMonth()
    const thisYear = now.getFullYear()
    
    let thisMonthCount = 0
    let totalSize = 0
    let totalDuration = 0
    let durationCount = 0
    
    translations.forEach((task) => {
      // 本月翻译数量
      const taskDate = new Date(task.created_at)
      if (taskDate.getMonth() === thisMonth && taskDate.getFullYear() === thisYear) {
        thisMonthCount++
      }
      
      // 文件大小累计
      totalSize += task.file_size
      
      // 处理时长统计
      if (task.processing_duration) {
        totalDuration += task.processing_duration
        durationCount++
      }
    })
    
    stats.value = {
      totalTranslations: translations.length,
      thisMonth: thisMonthCount,
      totalSize,
      avgDuration: durationCount > 0 
        ? apiUtils.formatDuration(Math.floor(totalDuration / durationCount))
        : '0秒'
    }
  } catch (error) {
    console.error('Load stats error:', error)
  }
}

async function loadAppVersion() {
  try {
    const response = await systemApi.getConfig()
    appVersion.value = response.data?.appVersion || '1.0.0'
  } catch (error) {
    console.error('Load app version error:', error)
  }
}

function getVipLevelText(): string {
  if (!userInfo.value) return ''
  
  const levelMap: Record<string, string> = {
    'basic_vip': '基础VIP',
    'premium_vip': '高级VIP',
    'pro_vip': '专业VIP'
  }
  
  return levelMap[userInfo.value.subscription_level] || 'VIP'
}

function getPlanTypeText(): string {
  if (!userInfo.value) return '免费版'
  
  const planMap: Record<string, string> = {
    'free': '免费版',
    'basic_vip': '基础VIP',
    'premium_vip': '高级VIP',
    'pro_vip': '专业VIP'
  }
  
  return planMap[userInfo.value.subscription_level] || '免费版'
}

function formatJoinTime(): string {
  if (!userInfo.value?.created_at) return ''
  
  try {
    const date = new Date(userInfo.value.created_at)
    return `${date.getFullYear()}年${date.getMonth() + 1}月${date.getDate()}日`
  } catch (error) {
    return ''
  }
}

function formatExpireTime(): string {
  if (!userInfo.value?.subscription_expires_at) return ''
  
  try {
    const date = new Date(userInfo.value.subscription_expires_at)
    return `${date.getFullYear()}年${date.getMonth() + 1}月${date.getDate()}日`
  } catch (error) {
    return ''
  }
}

function formatFileSize(size: number): string {
  return apiUtils.formatFileSize(size)
}

function goToUpgrade() {
  uni.navigateTo({
    url: '/pages/upgrade/index'
  })
}

function manageSubscription() {
  uni.navigateTo({
    url: '/pages/subscription/index'
  })
}

function viewHistory() {
  uni.navigateTo({
    url: '/pages/history/index'
  })
}

function viewUsage() {
  uni.navigateTo({
    url: '/pages/usage/index'
  })
}

function contactSupport() {
  uni.showActionSheet({
    itemList: ['在线客服', '意见反馈', '关于我们'],
    success: (res) => {
      switch (res.tapIndex) {
        case 0:
          // 打开在线客服
          uni.navigateTo({
            url: '/pages/support/index'
          })
          break
        case 1:
          // 打开意见反馈
          uni.navigateTo({
            url: '/pages/feedback/index'
          })
          break
        case 2:
          // 打开关于我们
          uni.navigateTo({
            url: '/pages/about/index'
          })
          break
      }
    }
  })
}

function viewSettings() {
  uni.navigateTo({
    url: '/pages/settings/index'
  })
}

async function checkUpdate() {
  try {
    uni.showLoading({
      title: '检查更新中...'
    })
    
    const response = await systemApi.checkUpdate()
    
    uni.hideLoading()
    
    if (response.data?.hasUpdate) {
      uni.showModal({
        title: '发现新版本',
        content: `最新版本：${response.data.latestVersion}\n更新内容：${response.data.updateContent}`,
        confirmText: '立即更新',
        success: (res) => {
          if (res.confirm) {
            // 执行更新逻辑
            performUpdate(response.data.downloadUrl)
          }
        }
      })
    } else {
      uni.showToast({
        title: '已是最新版本',
        icon: 'success'
      })
    }
  } catch (error) {
    uni.hideLoading()
    uni.showToast({
      title: '检查更新失败',
      icon: 'none'
    })
  }
}

function performUpdate(downloadUrl: string) {
  // 这里可以实现应用更新逻辑
  uni.showLoading({
    title: '下载更新中...'
  })
  
  // 模拟下载过程
  setTimeout(() => {
    uni.hideLoading()
    uni.showToast({
      title: '更新完成',
      icon: 'success'
    })
  }, 3000)
}

function logout() {
  uni.showModal({
    title: '退出登录',
    content: '确定要退出登录吗？',
    success: (res) => {
      if (res.confirm) {
        userStore.logout()
        uni.reLaunch({
          url: '/pages/index/index'
        })
      }
    }
  })
}

function onUpgradePrompt(quota: QuotaInfo) {
  quotaInfo.value = quota
  upgradeType.value = 'upgrade'
  showUpgradePrompt.value = true
}

function onQuotaDetails(quota: QuotaInfo) {
  // 可以显示更详细的配额信息
}

function closeUpgradePrompt() {
  showUpgradePrompt.value = false
}

function confirmUpgrade(planData: any) {
  closeUpgradePrompt()
  goToUpgrade()
}
</script>

<style>
/* Profile Page - Figma Design Styles */
.profile-page {
  min-height: 100vh;
  background: linear-gradient(to bottom right, #e0e7ff 0%, #dbeafe 50%, #cffafe 100%);
  padding: 24rpx;
  padding-bottom: 40rpx;
}

.nav-header {
  background: linear-gradient(to right, #4ade80 0%, #06b6d4 100%);
  padding: 20rpx 32rpx 40rpx;
}

.nav-title {
  font-size: 32rpx;
  font-weight: 600;
  color: white;
  text-align: center;
}

.user-card {
  background: white;
  margin: -20rpx 24rpx 24rpx;
  border-radius: 16rpx;
  padding: 32rpx;
  display: flex;
  align-items: center;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.1);
}

.user-avatar {
  position: relative;
  margin-right: 24rpx;
}

.avatar-img {
  width: 100rpx;
  height: 100rpx;
  border-radius: 50%;
}

.vip-badge {
  position: absolute;
  bottom: -4rpx;
  right: -4rpx;
  background: linear-gradient(45deg, #FFD700, #FFA500);
  border-radius: 16rpx;
  padding: 4rpx 8rpx;
  min-width: 48rpx;
  text-align: center;
}

.vip-text {
  font-size: 16rpx;
  color: white;
  font-weight: 600;
}

.user-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.username {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 8rpx;
}

.user-id,
.join-time {
  font-size: 24rpx;
  color: #666;
  margin-bottom: 4rpx;
}

.subscription-card {
  background: white;
  margin: 0 24rpx 24rpx;
  border-radius: 16rpx;
  padding: 24rpx;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.05);
}

.subscription-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20rpx;
}

.subscription-title {
  font-size: 28rpx;
  font-weight: 600;
  color: #333;
}

.upgrade-btn,
.manage-btn {
  background: linear-gradient(45deg, #4CAF50, #45a049);
  color: white;
  border: none;
  border-radius: 8rpx;
  font-size: 22rpx;
  padding: 8rpx 16rpx;
}

.manage-btn {
  background: #f8f9fa;
  color: #333;
  border: 1rpx solid #dee2e6;
}

.subscription-info {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-label {
  font-size: 26rpx;
  color: #666;
}

.info-value {
  font-size: 26rpx;
  color: #333;
  font-weight: 500;
}

.quota-value {
  color: #4CAF50;
  font-weight: 600;
}

.stats-section {
  background: white;
  margin: 0 24rpx 24rpx;
  border-radius: 16rpx;
  padding: 24rpx;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.05);
}

.stats-title {
  font-size: 28rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 20rpx;
}

.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20rpx;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20rpx;
  background: #f8f9fa;
  border-radius: 12rpx;
}

.stat-number {
  font-size: 36rpx;
  font-weight: 700;
  color: #4CAF50;
  margin-bottom: 8rpx;
}

.stat-label {
  font-size: 22rpx;
  color: #666;
  text-align: center;
}

.menu-section {
  background: white;
  margin: 0 24rpx 24rpx;
  border-radius: 16rpx;
  overflow: hidden;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.05);
}

.menu-item {
  display: flex;
  align-items: center;
  padding: 24rpx;
  border-bottom: 1rpx solid #f0f0f0;
  transition: background-color 0.2s ease;
}

.menu-item:last-child {
  border-bottom: none;
}

.menu-item:active {
  background: #f8f9fa;
}

.menu-icon {
  width: 40rpx;
  height: 40rpx;
  margin-right: 20rpx;
}

.menu-icon image {
  width: 100%;
  height: 100%;
}

.menu-title {
  flex: 1;
  font-size: 28rpx;
  color: #333;
}

.menu-arrow {
  font-size: 32rpx;
  color: #ccc;
}

.version-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 0 24rpx 24rpx;
  padding: 20rpx;
}

.version-text {
  font-size: 24rpx;
  color: #999;
}

.check-update-btn {
  background: none;
  border: 1rpx solid #ddd;
  border-radius: 8rpx;
  font-size: 22rpx;
  color: #666;
  padding: 8rpx 16rpx;
}

.logout-section {
  margin: 0 24rpx;
}

.logout-btn {
  width: 100%;
  background: #ff4757;
  color: white;
  border: none;
  border-radius: 12rpx;
  font-size: 28rpx;
  font-weight: 500;
  padding: 24rpx;
}

.logout-btn:active {
  opacity: 0.8;
  transform: scale(0.98);
}

/* 响应式设计 */
@media (max-width: 400rpx) {
  .user-card {
    flex-direction: column;
    text-align: center;
    margin: -20rpx 16rpx 24rpx;
    padding: 24rpx;
  }
  
  .user-avatar {
    margin-right: 0;
    margin-bottom: 16rpx;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
    gap: 16rpx;
  }
  
  .stat-item {
    padding: 16rpx;
  }
  
  .menu-item {
    padding: 20rpx;
  }
  
  .logout-section {
    margin: 0 16rpx;
  }
}
</style>