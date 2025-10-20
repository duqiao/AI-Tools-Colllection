<template>
  <div class="result-page">
    <!-- 顶部导航 -->
    <div class="nav-header">
      <div class="nav-back" @click="goBack">
        <span class="back-icon">←</span>
      </div>
      <div class="nav-title">翻译结果</div>
      <div class="nav-action">
        <button class="share-btn" @click="shareResult">分享</button>
      </div>
    </div>

    <!-- 任务状态 -->
    <div v-if="loading" class="loading-section">
      <div class="loading-animation">
        <div class="loading-spinner"></div>
      </div>
      <span class="loading-text">{{ loadingText }}</span>
      <div v-if="currentTask" class="progress-info">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: progressPercentage + '%' }"></div>
        </div>
        <span class="progress-text">{{ progressPercentage }}%</span>
      </div>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="error-section">
      <div class="error-icon">⚠️</div>
      <span class="error-title">翻译失败</span>
      <span class="error-message">{{ error }}</span>
      <button class="retry-btn" @click="retryTranslation">重新翻译</button>
    </div>

    <!-- 翻译结果 -->
    <div v-else-if="currentTask && isCompleted" class="result-section">
      <!-- 文件信息 -->
      <div class="file-info-card">
        <div class="file-header">
          <div class="file-type-icon">{{ getFileIconEmoji(currentTask.file_type) }}</div>
          <div class="file-details">
            <span class="file-name">{{ currentTask.original_filename }}</span>
            <span class="file-meta">{{ getFileTypeText(currentTask.file_type) }} • {{ formatFileSize(currentTask.file_size) }}</span>
            <span v-if="currentTask.duration_seconds" class="file-duration">时长：{{ formatDuration(currentTask.duration_seconds) }}</span>
          </div>
        </div>
      </div>

      <!-- 翻译结果卡片 -->
      <div class="result-card">
        <div class="result-header">
          <span class="result-title">翻译结果</span>
          <div class="result-actions">
            <button class="copy-btn" @click="copyResult">复制</button>
            <button class="download-btn" @click="downloadResult">下载</button>
          </div>
        </div>
        
        <div class="result-content">
          <!-- 文本结果 -->
          <div v-if="currentTask.transcribed_text" class="text-result">
            <span class="result-text">{{ currentTask.transcribed_text }}</span>
          </div>
          
          <!-- 置信度 -->
          <div v-if="currentTask.confidence_score" class="confidence-info">
            <span class="confidence-label">置信度：</span>
            <span class="confidence-value">{{ (currentTask.confidence_score * 100).toFixed(1) }}%</span>
          </div>
          
          <!-- 字数统计 -->
          <div v-if="currentTask.word_count" class="word-count">
            <span class="word-label">字数：</span>
            <span class="word-value">{{ currentTask.word_count }} 字</span>
          </div>
        </div>
      </div>

      <!-- 处理信息 -->
      <div class="processing-info">
        <div class="info-item">
          <span class="info-label">处理时间：</span>
          <span class="info-value">{{ formatProcessingTime() }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">服务提供商：</span>
          <span class="info-value">{{ getProviderText(currentTask.service_provider) }}</span>
        </div>
        <div v-if="currentTask.service_cost" class="info-item">
          <span class="info-label">服务费用：</span>
          <span class="info-value">¥{{ currentTask.service_cost.toFixed(2) }}</span>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="action-buttons">
        <button class="new-translation-btn" @click="newTranslation">新建翻译</button>
        <button class="history-btn" @click="viewHistory">历史记录</button>
      </div>
    </div>

    <!-- 分享弹窗 -->
    <div v-if="showShareModal" class="share-modal" @click="closeShareModal">
      <div class="share-content" @click.stop>
        <div class="share-title">分享翻译结果</div>
        <div class="share-options">
          <button class="share-option" @click="shareToWechat">
            <div class="share-icon">💬</div>
            <span class="share-text">微信好友</span>
          </button>
          <button class="share-option" @click="shareToMoments">
            <div class="share-icon">👥</div>
            <span class="share-text">朋友圈</span>
          </button>
          <button class="share-option" @click="copyShareLink">
            <div class="share-icon">🔗</div>
            <span class="share-text">复制链接</span>
          </button>
        </div>
        <button class="close-share-btn" @click="closeShareModal">取消</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useTranslationStore } from '@/stores/translation'
import { useUserStore } from '@/stores/user'
import { translationApi, apiUtils } from '@/api'
import { useTranslationStatus } from '@/services/translation-service'
import type { TranslationTask } from '@/types'
import { uni } from '@/utils/uni-adapter'

// Props
const props = defineProps<{
  task_id?: string
}>()

// Stores
const translationStore = useTranslationStore()
const userStore = useUserStore()

// Translation status service
const { 
  currentTask: serviceTask,
  isPolling,
  pollingProgress,
  pollingMessage,
  pollingError,
  startPolling,
  stopPolling
} = useTranslationStatus()

// Reactive data
const loading = ref(true)
const error = ref<string | null>(null)
const currentTask = ref<TranslationTask | null>(null)
const taskId = ref<string>(props.task_id || '')
const showShareModal = ref(false)

// Computed
const isCompleted = computed(() => {
  return currentTask.value?.processing_status === 'completed' || serviceTask.value?.status === 'completed'
})

const progressPercentage = computed(() => {
  return currentTask.value?.progress_percentage || pollingProgress.value || 0
})

const loadingText = computed(() => {
  // 使用轮询服务的消息，如果没有则使用默认逻辑
  if (pollingMessage.value) {
    return pollingMessage.value
  }
  
  if (!currentTask.value) return '加载中...'
  
  switch (currentTask.value.processing_status) {
    case 'pending':
      return '等待处理...'
    case 'processing':
      return '正在翻译...'
    case 'completed':
      return '翻译完成'
    case 'failed':
      return '翻译失败'
    default:
      return '处理中...'
  }
})

// Lifecycle
onMounted(() => {
  if (taskId.value) {
    loadTaskResult()
    startAdvancedPolling()
  } else {
    // 从页面参数获取task_id
    const pages = getCurrentPages()
    const currentPage = pages[pages.length - 1]
    const options = currentPage.options || {}
    
    if (options.task_id) {
      taskId.value = options.task_id
      loadTaskResult()
      startAdvancedPolling()
    } else {
      error.value = '未找到翻译任务'
      loading.value = false
    }
  }
})

onUnmounted(() => {
  stopPolling()
})

// Methods
async function loadTaskResult() {
  try {
    if (!taskId.value) return

    const response = await translationApi.getDetail(taskId.value)
    currentTask.value = response.data
    
    if (response.processing_status === 'completed') {
      loading.value = false
    } else if (response.processing_status === 'failed') {
      error.value = response.processing_error || '翻译失败'
      loading.value = false
    }
  } catch (error) {
    console.error('Load task result error:', error)
    error.value = error.message || '加载结果失败'
    loading.value = false
  }
}

function startAdvancedPolling() {
  if (!taskId.value) return
  
  startPolling({
    taskId: taskId.value,
    interval: 2000, // 2秒轮询一次
    timeout: 10 * 60 * 1000, // 10分钟超时
    onProgress: (progress, message) => {
      console.log(`Translation progress: ${progress}% - ${message}`)
    },
    onSuccess: (result) => {
      console.log('Translation completed:', result)
      currentTask.value = result
      loading.value = false
    },
    onError: (error) => {
      console.error('Translation failed:', error)
      error.value = error.message
      loading.value = false
    },
    onTimeout: () => {
      console.log('Translation timeout')
      error.value = '翻译超时，请重试'
      loading.value = false
    }
  }).catch((error) => {
    console.error('Polling error:', error)
    error.value = error.message || '轮询状态失败'
    loading.value = false
  })
}

function goBack() {
  uni.navigateBack({
    delta: 1
  })
}

function retryTranslation() {
  if (!taskId.value) return
  
  uni.showModal({
    title: '重新翻译',
    content: '确定要重新翻译这个文件吗？',
    success: (res) => {
      if (res.confirm) {
        // 重置任务状态并重新开始
        currentTask.value = null
        error.value = null
        loading.value = true
        
        // 重新开始翻译
        translationApi.startTranslation({
          task_id: taskId.value,
          language: 'zh-CN',
          provider: 'alibaba'
        }).then(() => {
          startAdvancedPolling()
        }).catch((error) => {
          error.value = error.message || '重新翻译失败'
          loading.value = false
        })
      }
    }
  })
}

function copyResult() {
  if (!currentTask.value?.transcribed_text) return
  
  uni.setClipboardData({
    data: currentTask.value.transcribed_text,
    success: () => {
      uni.showToast({
        title: '已复制到剪贴板',
        icon: 'success'
      })
    }
  })
}

function downloadResult() {
  if (!currentTask.value) return
  
  // 生成文件内容
  const content = `翻译结果\n\n文件名：${currentTask.value.original_filename}\n翻译内容：\n${currentTask.value.transcribed_text}\n\n置信度：${(currentTask.value.confidence_score * 100).toFixed(1)}%\n字数：${currentTask.value.word_count} 字`
  
  // 保存到本地文件
  const fileName = `翻译结果_${currentTask.value.original_filename}_${Date.now()}.txt`
  
  uni.saveFile({
    tempFilePath: '', // 这里需要实际的文件路径
    success: (res) => {
      uni.showToast({
        title: '下载成功',
        icon: 'success'
      })
    },
    fail: () => {
      // 备用方案：复制到剪贴板
      copyResult()
    }
  })
}

function newTranslation() {
  uni.redirectTo({
    url: '/pages/upload/index'
  })
}

function viewHistory() {
  uni.navigateTo({
    url: '/pages/history/index'
  })
}

function shareResult() {
  showShareModal.value = true
}

function closeShareModal() {
  showShareModal.value = false
}

function shareToWechat() {
  // 实现微信好友分享
  uni.share({
    provider: 'weixin',
    scene: 'WXSceneSession',
    type: 0,
    href: `pages/result/index?task_id=${taskId.value}`,
    title: '翻译结果分享',
    summary: currentTask.value?.transcribed_text?.substring(0, 100) || '查看翻译结果',
    imageUrl: '/static/images/share-icon.png',
    success: () => {
      uni.showToast({
        title: '分享成功',
        icon: 'success'
      })
      closeShareModal()
    }
  })
}

function shareToMoments() {
  // 实现朋友圈分享
  uni.share({
    provider: 'weixin',
    scene: 'WXSenceTimeline',
    type: 0,
    href: `pages/result/index?task_id=${taskId.value}`,
    title: '语音翻译助手',
    summary: '使用语音翻译助手，轻松转换语音为文字',
    imageUrl: '/static/images/share-icon.png',
    success: () => {
      uni.showToast({
        title: '分享成功',
        icon: 'success'
      })
      closeShareModal()
    }
  })
}

function copyShareLink() {
  const shareUrl = `pages/result/index?task_id=${taskId.value}`
  uni.setClipboardData({
    data: shareUrl,
    success: () => {
      uni.showToast({
        title: '链接已复制',
        icon: 'success'
      })
      closeShareModal()
    }
  })
}

function getFileIcon(fileType: string): string {
  return apiUtils.getFileTypeIcon(fileType)
}

function getFileIconEmoji(fileType: string): string {
  const iconMap: Record<string, string> = {
    'audio': '🎵',
    'video': '🎬',
    'image': '🖼️'
  }
  return iconMap[fileType] || '📄'
}

function getFileTypeText(fileType: string): string {
  return apiUtils.getFileTypeText(fileType)
}

function formatFileSize(size: number): string {
  return apiUtils.formatFileSize(size)
}

function formatDuration(duration: number): string {
  return apiUtils.formatDuration(duration)
}

function formatProcessingTime(): string {
  if (!currentTask.value?.processing_started_at || !currentTask.value?.processing_completed_at) {
    return '未知'
  }
  
  const start = new Date(currentTask.value.processing_started_at).getTime()
  const end = new Date(currentTask.value.processing_completed_at).getTime()
  const duration = end - start
  
  return apiUtils.formatDuration(Math.floor(duration / 1000))
}

function getProviderText(provider?: string): string {
  const providerMap: Record<string, string> = {
    'alibaba': '阿里云',
    'tencent': '腾讯云',
    'baidu': '百度',
    'xunfei': '讯飞'
  }
  
  return providerMap[provider || ''] || '未知'
}
</script>

<style>
/* Result Page - Figma Design Styles */
.result-page {
  min-height: 100vh;
  background: linear-gradient(to bottom right, #e0e7ff 0%, #dbeafe 50%, #cffafe 100%);
  padding: 24rpx;
}

.nav-header {
  background: #fff;
  padding: 20rpx 32rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1rpx solid #f0f0f0;
}

.nav-back {
  width: 60rpx;
  height: 60rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.back-icon {
  font-size: 32rpx;
  color: #333;
  font-weight: 600;
}

.nav-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
  flex: 1;
  text-align: center;
}

.nav-action {
  width: 60rpx;
}

.share-btn {
  background: none;
  border: none;
  color: #4CAF50;
  font-size: 24rpx;
  padding: 0;
}

.loading-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 120rpx 40rpx;
}

.loading-animation {
  margin-bottom: 40rpx;
}

.loading-spinner {
  width: 60rpx;
  height: 60rpx;
  border: 4rpx solid #f0f0f0;
  border-top: 4rpx solid #4CAF50;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-text {
  font-size: 28rpx;
  color: #666;
  margin-bottom: 40rpx;
}

.progress-info {
  width: 200rpx;
  text-align: center;
}

.progress-bar {
  background: #f0f0f0;
  border-radius: 6rpx;
  height: 8rpx;
  overflow: hidden;
  margin-bottom: 16rpx;
}

.progress-fill {
  background: linear-gradient(90deg, #4CAF50, #45a049);
  height: 100%;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 24rpx;
  color: #4CAF50;
}

.error-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 120rpx 40rpx;
}

.error-icon {
  font-size: 80rpx;
  color: #ff4757;
  margin-bottom: 24rpx;
}

.error-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 16rpx;
}

.error-message {
  font-size: 26rpx;
  color: #666;
  text-align: center;
  margin-bottom: 40rpx;
  line-height: 1.4;
}

.retry-btn {
  background: linear-gradient(45deg, #4CAF50, #45a049);
  color: white;
  border: none;
  border-radius: 12rpx;
  font-size: 28rpx;
  padding: 24rpx 48rpx;
}

.result-section {
  padding: 24rpx;
}

.file-info-card {
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
  margin-bottom: 24rpx;
}

.file-header {
  display: flex;
  align-items: center;
}

.file-type-icon {
  width: 60rpx;
  height: 60rpx;
  margin-right: 20rpx;
}

.file-details {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.file-name {
  font-size: 28rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 8rpx;
}

.file-meta,
.file-duration {
  font-size: 24rpx;
  color: #666;
  margin-bottom: 4rpx;
}

.result-card {
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
  margin-bottom: 24rpx;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20rpx;
}

.result-title {
  font-size: 28rpx;
  font-weight: 600;
  color: #333;
}

.result-actions {
  display: flex;
  gap: 12rpx;
}

.copy-btn,
.download-btn {
  background: #f8f9fa;
  color: #333;
  border: 1rpx solid #dee2e6;
  border-radius: 8rpx;
  font-size: 22rpx;
  padding: 8rpx 16rpx;
}

.text-result {
  background: #f8f9fa;
  border-radius: 12rpx;
  padding: 20rpx;
  margin-bottom: 20rpx;
}

.result-text {
  font-size: 26rpx;
  line-height: 1.6;
  color: #333;
  white-space: pre-wrap;
}

.confidence-info,
.word-count {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12rpx 0;
  border-bottom: 1rpx solid #f0f0f0;
}

.confidence-info:last-child,
.word-count:last-child {
  border-bottom: none;
}

.confidence-label,
.word-label {
  font-size: 24rpx;
  color: #666;
}

.confidence-value,
.word-value {
  font-size: 24rpx;
  color: #4CAF50;
  font-weight: 500;
}

.processing-info {
  background: #fff;
  border-radius: 12rpx;
  padding: 20rpx;
  margin-bottom: 24rpx;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12rpx 0;
  border-bottom: 1rpx solid #f0f0f0;
}

.info-item:last-child {
  border-bottom: none;
}

.info-label {
  font-size: 24rpx;
  color: #666;
}

.info-value {
  font-size: 24rpx;
  color: #333;
  font-weight: 500;
}

.action-buttons {
  display: flex;
  gap: 20rpx;
}

.new-translation-btn {
  flex: 2;
  background: linear-gradient(to right, #4ade80 0%, #06b6d4 100%);
  color: white;
  border: none;
  border-radius: 12rpx;
  font-size: 28rpx;
  font-weight: 500;
  padding: 24rpx;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
}

.history-btn {
  flex: 1;
  background: #f8f9fa;
  color: #333;
  border: 1rpx solid #dee2e6;
  border-radius: 12rpx;
  font-size: 28rpx;
  padding: 24rpx;
}

/* 分享弹窗 */
.share-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  z-index: 1000;
}

.share-content {
  background: #fff;
  border-radius: 24rpx 24rpx 0 0;
  padding: 40rpx 24rpx;
  width: 100%;
  max-width: 750rpx;
}

.share-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
  text-align: center;
  margin-bottom: 40rpx;
}

.share-options {
  display: flex;
  justify-content: space-around;
  margin-bottom: 40rpx;
}

.share-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: none;
  border: none;
  padding: 0;
}

.share-icon {
  width: 80rpx;
  height: 80rpx;
  margin-bottom: 12rpx;
}

.share-text {
  font-size: 24rpx;
  color: #333;
}

.close-share-btn {
  width: 100%;
  background: #f8f9fa;
  color: #666;
  border: 1rpx solid #dee2e6;
  border-radius: 12rpx;
  font-size: 28rpx;
  padding: 24rpx;
}

/* 响应式设计 */
@media (max-width: 400rpx) {
  .file-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16rpx;
  }
  
  .result-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16rpx;
  }
  
  .result-actions {
    width: 100%;
    justify-content: flex-end;
  }
  
  .action-buttons {
    flex-direction: column;
  }
  
  .share-options {
    flex-wrap: wrap;
    gap: 20rpx;
  }
}
</style>