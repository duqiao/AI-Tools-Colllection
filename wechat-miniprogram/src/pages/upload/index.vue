<template>
  <div class="upload-page">
    <!-- 顶部导航 -->
    <div class="nav-header">
      <div class="nav-title">上传文件</div>
    </div>

    <!-- 配额显示 -->
    <quota-display 
      :show-details="false" 
      @upgrade="onUpgradePrompt"
      @details="onQuotaDetails"
    />

    <!-- 文件上传区域 -->
    <div class="upload-section">
      <!-- 上传区域 -->
      <div class="upload-area" @click="chooseFile">
        <div v-if="!uploadFile" class="upload-placeholder">
          <div class="upload-icon">📁</div>
          <span class="upload-text">点击选择文件</span>
          <span class="upload-hint">支持音频、视频文件</span>
        </div>
        
        <div v-else class="upload-preview">
          <div class="file-icon">{{ getFileIconEmoji(uploadFile.type) }}</div>
          <div class="file-info">
            <span class="file-name">{{ uploadFile.name }}</span>
            <span class="file-size">{{ formatFileSize(uploadFile.size) }}</span>
            <span v-if="uploadFile.duration" class="file-duration">{{ formatDuration(uploadFile.duration) }}</span>
          </div>
          <button class="remove-btn" @click.stop="removeFile">×</button>
        </div>
      </div>

      <!-- 上传进度 -->
      <div v-if="uploading" class="upload-progress">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: uploadProgress + '%' }"></div>
        </div>
        <span class="progress-text">{{ uploadProgress }}%</span>
      </div>

      <!-- 文件信息 -->
      <div v-if="uploadFile && !uploading" class="file-details">
        <div class="detail-item">
          <span class="detail-label">文件类型：</span>
          <span class="detail-value">{{ getFileTypeText(uploadFile.type) }}</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">文件大小：</span>
          <span class="detail-value">{{ formatFileSize(uploadFile.size) }}</span>
        </div>
        <div v-if="uploadFile.duration" class="detail-item">
          <span class="detail-label">时长：</span>
          <span class="detail-value">{{ formatDuration(uploadFile.duration) }}</span>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="action-buttons">
        <button 
          v-if="!uploadFile" 
          class="choose-btn" 
          @click="chooseFile"
        >
          选择文件
        </button>
        
        <button 
          v-if="uploadFile && !uploading" 
          class="upload-btn" 
          :disabled="!canUpload"
          @click="startUpload"
        >
          开始上传
        </button>
        
        <button 
          v-if="uploading" 
          class="cancel-btn" 
          @click="cancelUpload"
        >
          取消上传
        </button>
      </div>
    </div>

    <!-- 错误提示 -->
    <div v-if="error" class="error-message">
      <div class="error-icon">⚠️</div>
      <span class="error-text">{{ error }}</span>
      <button class="error-close" @click="clearError">×</button>
    </div>

    <!-- 上传说明 -->
    <div class="upload-tips">
      <div class="tips-title">上传说明</div>
      <div class="tips-list">
        <div class="tip-item">• 支持音频格式：MP3、WAV、AAC、M4A</div>
        <div class="tip-item">• 支持视频格式：MP4、AVI、MOV、MKV</div>
        <div class="tip-item">• 文件大小限制：{{ maxFileSizeText }}</div>
        <div class="tip-item">• 上传后自动开始翻译处理</div>
      </div>
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
import { quotaApi, translationApi, apiUtils } from '@/api'
import type { MediaFileInfo, QuotaInfo } from '@/types'
import QuotaDisplay from '@/components/quota-display/index.vue'
import UpgradePrompt from '@/components/upgrade-prompt/index.vue'
import { uni } from '@/utils/uni-adapter'

// Stores
const userStore = useUserStore()
const translationStore = useTranslationStore()

// Reactive data
const uploadFile = ref<MediaFileInfo | null>(null)
const uploading = ref(false)
const uploadProgress = ref(0)
const error = ref<string | null>(null)
const maxFileSize = ref(100 * 1024 * 1024) // 100MB
const showUpgradePrompt = ref(false)
const upgradeType = ref<string>('warning')
const quotaInfo = ref<QuotaInfo | null>(null)

// Computed
const canUpload = computed(() => {
  return uploadFile.value && 
         !uploading.value && 
         uploadFile.value.size <= maxFileSize.value &&
         userStore.remainingQuota > 0
})

const maxFileSizeText = computed(() => {
  return apiUtils.formatFileSize(maxFileSize.value)
})

// Lifecycle
onMounted(() => {
  // 检查登录状态
  if (!userStore.isLoggedIn) {
    uni.redirectTo({
      url: '/pages/index/index'
    })
    return
  }
  
  // 加载配额信息
  loadQuotaInfo()
})

// Methods
async function loadQuotaInfo() {
  try {
    const response = await quotaApi.getStatus()
    quotaInfo.value = response
    userStore.updateQuotaInfo(response)
  } catch (error) {
    console.error('Load quota info error:', error)
  }
}

function chooseFile() {
  uni.chooseMedia({
    count: 1,
    mediaType: ['video', 'image'],
    sourceType: ['album', 'camera'],
    maxDuration: 60 * 60, // 1小时
    camera: 'back',
    success: (res) => {
      const file = res.tempFiles[0]
      processChosenFile(file)
    },
    fail: (error) => {
      console.error('Choose file error:', error)
      showError('选择文件失败')
    }
  })
}

function processChosenFile(file: any) {
  // 检查文件大小
  if (file.size > maxFileSize.value) {
    showError(`文件大小超过限制（${maxFileSizeText.value}）`)
    return
  }

  // 确定文件类型
  let fileType = 'video'
  if (file.fileType === 'image') {
    fileType = 'audio' // 假设图片为音频封面
  }

  uploadFile.value = {
    type: fileType,
    name: file.tempFilePath.split('/').pop() || `file_${Date.now()}`,
    size: file.size,
    duration: file.duration,
    path: file.tempFilePath
  }

  clearError()
}

function removeFile() {
  uploadFile.value = null
  uploadProgress.value = 0
  clearError()
}

async function startUpload() {
  if (!uploadFile.value || !canUpload.value) return

  try {
    uploading.value = true
    uploadProgress.value = 0
    clearError()

    // 检查配额
    await quotaApi.checkAvailability(1)

    // 创建翻译任务
    const taskData = {
      file_type: uploadFile.value.type,
      original_filename: uploadFile.value.name,
      file_size: uploadFile.value.size,
      file_url: uploadFile.value.path,
      duration_seconds: uploadFile.value.duration
    }

    const taskResponse = await translationApi.createTask(taskData)
    const taskId = taskResponse.data.task_id

    // 上传文件
    const uploadResponse = await translationApi.uploadFile(
      uploadFile.value.path,
      taskData
    )

    // 开始翻译
    await translationApi.startTranslation({
      task_id: taskId,
      language: 'zh-CN',
      provider: 'alibaba'
    })

    // 跳转到结果页面
    uni.redirectTo({
      url: `/pages/result/index?task_id=${taskId}`
    })

  } catch (error) {
    console.error('Upload error:', error)
    if (error.message?.includes('配额')) {
      showUpgrade('warning')
    } else {
      showError(error.message || '上传失败')
    }
  } finally {
    uploading.value = false
  }
}

function cancelUpload() {
  uploading.value = false
  uploadProgress.value = 0
  // 可以在这里添加取消上传的逻辑
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

function showError(message: string) {
  error.value = message
}

function clearError() {
  error.value = null
}

function onUpgradePrompt(quota: QuotaInfo) {
  quotaInfo.value = quota
  showUpgrade('exhausted')
}

function onQuotaDetails(quota: QuotaInfo) {
  // 可以显示详细信息
}

function showUpgrade(type: string) {
  upgradeType.value = type
  showUpgradePrompt.value = true
}

function closeUpgradePrompt() {
  showUpgradePrompt.value = false
}

function confirmUpgrade(planData: any) {
  closeUpgradePrompt()
  // 跳转到升级页面或处理升级逻辑
  uni.navigateTo({
    url: '/pages/upgrade/index'
  })
}
</script>

<style>
/* pages/upload/index.wxss */
.upload-page {
  min-height: 100vh;
  background: #f5f5f5;
  padding-bottom: 40rpx;
}

.nav-header {
  background: #fff;
  padding: 20rpx 32rpx;
  border-bottom: 1rpx solid #f0f0f0;
}

.nav-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
  text-align: center;
}

.upload-section {
  margin: 24rpx;
}

.upload-area {
  background: #fff;
  border-radius: 16rpx;
  border: 2rpx dashed #ddd;
  padding: 60rpx 40rpx;
  text-align: center;
  margin-bottom: 24rpx;
  transition: all 0.3s ease;
}

.upload-area:active {
  background: #f8f9fa;
  border-color: #4CAF50;
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.upload-icon {
  width: 80rpx;
  height: 80rpx;
  margin-bottom: 20rpx;
  opacity: 0.6;
}

.upload-text {
  font-size: 28rpx;
  color: #333;
  margin-bottom: 12rpx;
  font-weight: 500;
}

.upload-hint {
  font-size: 24rpx;
  color: #999;
}

.upload-preview {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.file-icon {
  width: 60rpx;
  height: 60rpx;
  margin-right: 20rpx;
}

.file-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.file-name {
  font-size: 26rpx;
  color: #333;
  margin-bottom: 8rpx;
  font-weight: 500;
}

.file-size,
.file-duration {
  font-size: 22rpx;
  color: #666;
  margin-bottom: 4rpx;
}

.remove-btn {
  background: #ff4757;
  color: white;
  border: none;
  border-radius: 50%;
  width: 40rpx;
  height: 40rpx;
  line-height: 40rpx;
  font-size: 20rpx;
  padding: 0;
}

.upload-progress {
  background: #fff;
  border-radius: 12rpx;
  padding: 24rpx;
  margin-bottom: 24rpx;
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
  text-align: center;
  display: block;
}

.file-details {
  background: #fff;
  border-radius: 12rpx;
  padding: 24rpx;
  margin-bottom: 24rpx;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12rpx 0;
  border-bottom: 1rpx solid #f0f0f0;
}

.detail-item:last-child {
  border-bottom: none;
}

.detail-label {
  font-size: 26rpx;
  color: #666;
}

.detail-value {
  font-size: 26rpx;
  color: #333;
  font-weight: 500;
}

.action-buttons {
  display: flex;
  gap: 20rpx;
  margin-bottom: 24rpx;
}

.choose-btn,
.upload-btn {
  flex: 1;
  background: linear-gradient(45deg, #4CAF50, #45a049);
  color: white;
  border: none;
  border-radius: 12rpx;
  font-size: 28rpx;
  font-weight: 500;
  padding: 24rpx;
}

.choose-btn:active,
.upload-btn:active {
  opacity: 0.8;
  transform: scale(0.98);
}

.upload-btn:disabled {
  background: #ccc;
  color: #999;
}

.cancel-btn {
  flex: 1;
  background: #f8f9fa;
  color: #666;
  border: 1rpx solid #dee2e6;
  border-radius: 12rpx;
  font-size: 28rpx;
  padding: 24rpx;
}

.error-message {
  background: #fff5f5;
  border: 1rpx solid #fed7d7;
  border-radius: 12rpx;
  padding: 20rpx;
  margin: 0 24rpx 24rpx;
  display: flex;
  align-items: center;
}

.error-icon {
  color: #ff4757;
  margin-right: 12rpx;
  font-size: 28rpx;
}

.error-text {
  flex: 1;
  color: #ff4757;
  font-size: 24rpx;
}

.error-close {
  background: none;
  border: none;
  color: #ff4757;
  font-size: 28rpx;
  padding: 0;
  width: 32rpx;
  height: 32rpx;
}

.upload-tips {
  background: #fff;
  border-radius: 12rpx;
  padding: 24rpx;
  margin: 0 24rpx;
}

.tips-title {
  font-size: 28rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 16rpx;
}

.tips-list {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.tip-item {
  font-size: 24rpx;
  color: #666;
  line-height: 1.4;
}

/* 响应式设计 */
@media (max-width: 400rpx) {
  .upload-area {
    padding: 40rpx 24rpx;
  }
  
  .action-buttons {
    flex-direction: column;
  }
  
  .upload-preview {
    flex-direction: column;
    align-items: center;
    gap: 20rpx;
  }
  
  .file-info {
    align-items: center;
    width: 100%;
  }
}
</style>