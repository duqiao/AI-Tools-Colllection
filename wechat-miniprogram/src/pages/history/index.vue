<template>
  <div class="history-page">
    <!-- 顶部导航 -->
    <div class="nav-header">
      <div class="nav-back" @click="goBack">
        <span class="back-icon">←</span>
      </div>
      <div class="nav-title">翻译历史</div>
      <div class="nav-action">
        <button class="filter-btn" @click="showFilter">筛选</button>
      </div>
    </div>

    <!-- 搜索栏 -->
    <div class="search-section">
      <div class="search-bar">
        <input 
          class="search-input" 
          placeholder="搜索文件名..." 
          v-model="searchKeyword"
          @input="onSearchInput"
        />
        <button class="search-btn" @click="performSearch">搜索</button>
      </div>
    </div>

    <!-- 统计信息 -->
    <div class="stats-bar">
      <div class="stat-item">
        <span class="stat-number">{{ pagination.total }}</span>
        <span class="stat-label">总记录</span>
      </div>
      <div class="stat-item">
        <span class="stat-number">{{ completedCount }}</span>
        <span class="stat-label">已完成</span>
      </div>
      <div class="stat-item">
        <span class="stat-number">{{ failedCount }}</span>
        <span class="stat-label">失败</span>
      </div>
    </div>

    <!-- 历史记录列表 -->
    <div class="history-list">
      <!-- 加载状态 -->
      <div v-if="loading" class="loading-state">
        <div class="loading-spinner"></div>
        <span class="loading-text">加载中...</span>
      </div>

      <!-- 空状态 -->
      <div v-else-if="historyList.length === 0" class="empty-state">
        <div class="empty-icon">📝</div>
        <span class="empty-text">暂无翻译记录</span>
        <button class="start-translation-btn" @click="startTranslation">开始翻译</button>
      </div>

      <!-- 列表项 -->
      <div v-else class="history-items">
        <div 
          v-for="item in historyList" 
          :key="item.id" 
          class="history-item"
          @click="viewDetail(item)"
        >
          <!-- 文件信息 -->
          <div class="item-header">
            <div class="file-info">
              <div class="file-icon">{{ getFileIconEmoji(item.file_type) }}</div>
              <div class="file-details">
                <span class="file-name">{{ item.original_filename }}</span>
                <span class="file-meta">{{ getFileTypeText(item.file_type) }} • {{ formatFileSize(item.file_size) }}</span>
                <span v-if="item.duration_seconds" class="file-duration">{{ formatDuration(item.duration_seconds) }}</span>
              </div>
            </div>
            <div class="status-badge" :class="item.processing_status">
              <span class="status-text">{{ getStatusText(item.processing_status) }}</span>
            </div>
          </div>

          <!-- 结果预览 -->
          <div v-if="item.transcribed_text" class="result-preview">
            <span class="preview-text">{{ item.transcribed_text.substring(0, 100) }}{{ item.transcribed_text.length > 100 ? '...' : '' }}</span>
          </div>

          <!-- 错误信息 -->
          <div v-if="item.processing_status === 'failed' && item.processing_error" class="error-info">
            <span class="error-text">{{ item.processing_error }}</span>
          </div>

          <!-- 操作按钮 -->
          <div class="item-actions">
            <button 
              v-if="item.processing_status === 'completed'" 
              class="action-btn view-btn" 
              @click.stop="viewResult(item)"
            >
              查看结果
            </button>
            <button 
              v-if="item.processing_status === 'failed'" 
              class="action-btn retry-btn" 
              @click.stop="retryTranslation(item)"
            >
              重新翻译
            </button>
            <button 
              v-if="item.processing_status === 'processing'" 
              class="action-btn cancel-btn" 
              @click.stop="cancelTranslation(item)"
            >
              取消翻译
            </button>
            <button 
              class="action-btn delete-btn" 
              @click.stop="deleteTranslation(item)"
            >
              删除
            </button>
          </div>

          <!-- 时间信息 -->
          <div class="item-footer">
            <span class="create-time">{{ formatCreateTime(item.created_at) }}</span>
            <div v-if="item.processing_completed_at" class="processing-time">
              <span class="time-label">处理用时：</span>
              <span class="time-value">{{ getProcessingTime(item) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 加载更多 -->
      <div v-if="hasMore && !loading" class="load-more">
        <button class="load-more-btn" @click="loadMore">加载更多</button>
      </div>
    </div>

    <!-- 筛选弹窗 -->
    <div v-if="showFilterModal" class="filter-modal" @click="closeFilter">
      <div class="filter-content" @click.stop>
        <div class="filter-header">
          <span class="filter-title">筛选条件</span>
          <button class="close-filter-btn" @click="closeFilter">×</button>
        </div>
        
        <div class="filter-section">
          <div class="filter-label">状态筛选</div>
          <div class="filter-options">
            <button 
              v-for="status in statusOptions" 
              :key="status.value"
              class="filter-option" 
              :class="{ active: filterStatus === status.value }"
              @click="selectStatus(status.value)"
            >
              {{ status.label }}
            </button>
          </div>
        </div>

        <div class="filter-section">
          <div class="filter-label">时间筛选</div>
          <div class="filter-options">
            <button 
              v-for="time in timeOptions" 
              :key="time.value"
              class="filter-option" 
              :class="{ active: filterTime === time.value }"
              @click="selectTime(time.value)"
            >
              {{ time.label }}
            </button>
          </div>
        </div>

        <div class="filter-actions">
          <button class="reset-btn" @click="resetFilter">重置</button>
          <button class="confirm-btn" @click="applyFilter">确定</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useTranslationStore } from '@/stores/translation'
import { translationApi, apiUtils } from '@/api'
import type { TranslationTask } from '@/types'
import { uni } from '@/utils/uni-adapter'

// Stores
const translationStore = useTranslationStore()

// Reactive data
const loading = ref(false)
const historyList = ref<TranslationTask[]>([])
const searchKeyword = ref('')
const filterStatus = ref('')
const filterTime = ref('')
const showFilterModal = ref(false)
const pagination = ref({
  total: 0,
  limit: 20,
  offset: 0,
  has_more: false
})

// 筛选选项
const statusOptions = [
  { label: '全部', value: '' },
  { label: '已完成', value: 'completed' },
  { label: '处理中', value: 'processing' },
  { label: '等待中', value: 'pending' },
  { label: '失败', value: 'failed' }
]

const timeOptions = [
  { label: '全部时间', value: '' },
  { label: '今天', value: 'today' },
  { label: '本周', value: 'week' },
  { label: '本月', value: 'month' },
  { label: '最近三月', value: 'quarter' }
]

// Computed
const hasMore = computed(() => {
  return pagination.value.has_more
})

const completedCount = computed(() => {
  return historyList.value.filter(item => item.processing_status === 'completed').length
})

const failedCount = computed(() => {
  return historyList.value.filter(item => item.processing_status === 'failed').length
})

// Lifecycle
onMounted(() => {
  loadHistory()
})

// 模拟下拉刷新 - 可以通过用户手动触发或定时刷新
function handlePullDownRefresh() {
  refreshHistory()
}

// Methods
async function loadHistory(reset = true) {
  try {
    loading.value = true
    
    if (reset) {
      pagination.value.offset = 0
      historyList.value = []
    }

    const params = {
      limit: pagination.value.limit,
      offset: pagination.value.offset,
      status: filterStatus.value || undefined,
      search: searchKeyword.value || undefined,
      time_range: filterTime.value || undefined
    }

    const response = await translationApi.getHistory(params)
    
    if (reset) {
      historyList.value = response.data || []
    } else {
      historyList.value.push(...(response.data || []))
    }
    
    pagination.value = {
      total: response.total || 0,
      limit: response.limit || 20,
      offset: response.offset || 0,
      has_more: response.has_more || false
    }
    
  } catch (error) {
    console.error('Load history error:', error)
    uni.showToast({
      title: '加载失败',
      icon: 'none'
    })
  } finally {
    loading.value = false
    if (!reset) {
      uni.stopPullDownRefresh()
    }
  }
}

async function refreshHistory() {
  await loadHistory(true)
  uni.stopPullDownRefresh()
  uni.showToast({
    title: '刷新成功',
    icon: 'success'
  })
}

async function loadMore() {
  if (!hasMore.value || loading.value) return
  
  pagination.value.offset += pagination.value.limit
  await loadHistory(false)
}

function onSearchInput() {
  // 防抖搜索
  clearTimeout(searchDebounceTimer)
  searchDebounceTimer = setTimeout(() => {
    performSearch()
  }, 500)
}

let searchDebounceTimer: number = 0

function performSearch() {
  loadHistory(true)
}

function showFilter() {
  showFilterModal.value = true
}

function closeFilter() {
  showFilterModal.value = false
}

function selectStatus(status: string) {
  filterStatus.value = status
}

function selectTime(time: string) {
  filterTime.value = time
}

function resetFilter() {
  filterStatus.value = ''
  filterTime.value = ''
  searchKeyword.value = ''
}

function applyFilter() {
  closeFilter()
  loadHistory(true)
}

function goBack() {
  uni.navigateBack({
    delta: 1
  })
}

function startTranslation() {
  uni.navigateTo({
    url: '/pages/upload/index'
  })
}

function viewDetail(item: TranslationTask) {
  uni.navigateTo({
    url: `/pages/result/index?task_id=${item.task_id}`
  })
}

function viewResult(item: TranslationTask) {
  uni.navigateTo({
    url: `/pages/result/index?task_id=${item.task_id}`
  })
}

async function retryTranslation(item: TranslationTask) {
  try {
    uni.showLoading({
      title: '重新翻译中...'
    })
    
    await translationApi.startTranslation({
      task_id: item.task_id,
      language: 'zh-CN',
      provider: 'alibaba'
    })
    
    uni.hideLoading()
    uni.showToast({
      title: '重新翻译已开始',
      icon: 'success'
    })
    
    // 刷新列表
    loadHistory(false)
    
  } catch (error) {
    uni.hideLoading()
    uni.showToast({
      title: error.message || '重新翻译失败',
      icon: 'none'
    })
  }
}

async function cancelTranslation(item: TranslationTask) {
  try {
    uni.showModal({
      title: '取消翻译',
      content: '确定要取消这个翻译任务吗？',
      success: async (res) => {
        if (res.confirm) {
          await translationApi.cancelTranslation(item.task_id)
          uni.showToast({
            title: '已取消翻译',
            icon: 'success'
          })
          
          // 刷新列表
          loadHistory(false)
        }
      }
    })
  } catch (error) {
    uni.showToast({
      title: '取消失败',
      icon: 'none'
    })
  }
}

async function deleteTranslation(item: TranslationTask) {
  try {
    uni.showModal({
      title: '删除记录',
      content: '确定要删除这条翻译记录吗？此操作不可恢复。',
      success: async (res) => {
        if (res.confirm) {
          // 这里需要调用删除API
          // await translationApi.deleteTranslation(item.id)
          
          uni.showToast({
            title: '删除成功',
            icon: 'success'
          })
          
          // 从列表中移除
          const index = historyList.value.findIndex(h => h.id === item.id)
          if (index > -1) {
            historyList.value.splice(index, 1)
          }
        }
      }
    })
  } catch (error) {
    uni.showToast({
      title: '删除失败',
      icon: 'none'
    })
  }
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

function getStatusText(status: string): string {
  return apiUtils.getStatusText(status)
}

function formatFileSize(size: number): string {
  return apiUtils.formatFileSize(size)
}

function formatDuration(duration: number): string {
  return apiUtils.formatDuration(duration)
}

function formatCreateTime(time: string): string {
  try {
    const date = new Date(time)
    const now = new Date()
    const diffTime = now.getTime() - date.getTime()
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24))
    
    if (diffDays === 0) {
      return '今天 ' + date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    } else if (diffDays === 1) {
      return '昨天 ' + date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    } else if (diffDays < 7) {
      return `${diffDays}天前`
    } else {
      return date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
    }
  } catch (error) {
    return time
  }
}

function getProcessingTime(item: TranslationTask): string {
  if (!item.processing_started_at || !item.processing_completed_at) {
    return '未知'
  }
  
  try {
    const start = new Date(item.processing_started_at).getTime()
    const end = new Date(item.processing_completed_at).getTime()
    const duration = end - start
    
    return apiUtils.formatDuration(Math.floor(duration / 1000))
  } catch (error) {
    return '未知'
  }
}
</script>

<style>
/* History Page - Figma Design Styles */
.history-page {
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

.filter-btn {
  background: none;
  border: none;
  color: #4CAF50;
  font-size: 24rpx;
  padding: 0;
}

.search-section {
  background: #fff;
  padding: 20rpx 24rpx;
  border-bottom: 1rpx solid #f0f0f0;
}

.search-bar {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.search-input {
  flex: 1;
  background: #f8f9fa;
  border: 1rpx solid #dee2e6;
  border-radius: 24rpx;
  padding: 16rpx 24rpx;
  font-size: 26rpx;
}

.search-btn {
  background: #4CAF50;
  color: white;
  border: none;
  border-radius: 24rpx;
  font-size: 24rpx;
  padding: 16rpx 24rpx;
}

.stats-bar {
  background: #fff;
  padding: 20rpx 24rpx;
  display: flex;
  justify-content: space-around;
  border-bottom: 1rpx solid #f0f0f0;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-number {
  font-size: 32rpx;
  font-weight: 600;
  color: #4CAF50;
  margin-bottom: 4rpx;
}

.stat-label {
  font-size: 22rpx;
  color: #666;
}

.history-list {
  padding: 24rpx;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 80rpx 0;
}

.loading-spinner {
  width: 60rpx;
  height: 60rpx;
  border: 4rpx solid #f0f0f0;
  border-top: 4rpx solid #4CAF50;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 20rpx;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-text {
  font-size: 26rpx;
  color: #666;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 120rpx 40rpx;
}

.empty-icon {
  width: 120rpx;
  height: 120rpx;
  margin-bottom: 32rpx;
  opacity: 0.5;
}

.empty-text {
  font-size: 28rpx;
  color: #999;
  margin-bottom: 40rpx;
}

.start-translation-btn {
  background: linear-gradient(45deg, #4CAF50, #45a049);
  color: white;
  border: none;
  border-radius: 12rpx;
  font-size: 28rpx;
  padding: 24rpx 48rpx;
}

.history-items {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.history-item {
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.05);
  transition: all 0.2s ease;
}

.history-item:active {
  transform: scale(0.98);
  box-shadow: 0 1rpx 4rpx rgba(0, 0, 0, 0.1);
}

.item-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16rpx;
}

.file-info {
  flex: 1;
  display: flex;
  align-items: flex-start;
}

.file-icon {
  width: 48rpx;
  height: 48rpx;
  margin-right: 16rpx;
  margin-top: 4rpx;
}

.file-details {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.file-name {
  font-size: 28rpx;
  font-weight: 500;
  color: #333;
  margin-bottom: 8rpx;
  line-height: 1.3;
}

.file-meta,
.file-duration {
  font-size: 22rpx;
  color: #666;
  margin-bottom: 4rpx;
}

.status-badge {
  padding: 6rpx 12rpx;
  border-radius: 12rpx;
  min-width: 80rpx;
  text-align: center;
}

.status-badge.pending {
  background: #fff3cd;
}

.status-badge.pending .status-text {
  color: #856404;
  font-size: 20rpx;
}

.status-badge.processing {
  background: #cce5ff;
}

.status-badge.processing .status-text {
  color: #004085;
  font-size: 20rpx;
}

.status-badge.completed {
  background: #d4edda;
}

.status-badge.completed .status-text {
  color: #155724;
  font-size: 20rpx;
}

.status-badge.failed {
  background: #f8d7da;
}

.status-badge.failed .status-text {
  color: #721c24;
  font-size: 20rpx;
}

.result-preview {
  background: #f8f9fa;
  border-radius: 12rpx;
  padding: 16rpx;
  margin-bottom: 16rpx;
}

.preview-text {
  font-size: 24rpx;
  color: #333;
  line-height: 1.4;
}

.error-info {
  background: #fff5f5;
  border: 1rpx solid #fed7d7;
  border-radius: 12rpx;
  padding: 16rpx;
  margin-bottom: 16rpx;
}

.error-text {
  font-size: 22rpx;
  color: #ff4757;
  line-height: 1.3;
}

.item-actions {
  display: flex;
  gap: 12rpx;
  margin-bottom: 16rpx;
  flex-wrap: wrap;
}

.action-btn {
  background: #f8f9fa;
  color: #333;
  border: 1rpx solid #dee2e6;
  border-radius: 8rpx;
  font-size: 22rpx;
  padding: 8rpx 16rpx;
  min-width: 80rpx;
}

.view-btn {
  background: #4CAF50;
  color: white;
  border: none;
}

.retry-btn {
  background: #ffa502;
  color: white;
  border: none;
}

.cancel-btn {
  background: #6c757d;
  color: white;
  border: none;
}

.delete-btn {
  background: #ff4757;
  color: white;
  border: none;
}

.item-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 20rpx;
  color: #999;
}

.processing-time {
  display: flex;
  align-items: center;
}

.time-label {
  color: #999;
}

.time-value {
  color: #4CAF50;
  font-weight: 500;
}

.load-more {
  display: flex;
  justify-content: center;
  margin-top: 40rpx;
}

.load-more-btn {
  background: #f8f9fa;
  color: #666;
  border: 1rpx solid #dee2e6;
  border-radius: 24rpx;
  font-size: 26rpx;
  padding: 16rpx 32rpx;
}

/* 筛选弹窗 */
.filter-modal {
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

.filter-content {
  background: #fff;
  border-radius: 24rpx 24rpx 0 0;
  padding: 40rpx 24rpx;
  width: 100%;
  max-width: 750rpx;
  max-height: 80vh;
  overflow-y: auto;
}

.filter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32rpx;
}

.filter-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
}

.close-filter-btn {
  background: none;
  border: none;
  color: #999;
  font-size: 40rpx;
  padding: 0;
  width: 40rpx;
  height: 40rpx;
}

.filter-section {
  margin-bottom: 32rpx;
}

.filter-label {
  font-size: 28rpx;
  font-weight: 500;
  color: #333;
  margin-bottom: 16rpx;
}

.filter-options {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
}

.filter-option {
  background: #f8f9fa;
  color: #333;
  border: 1rpx solid #dee2e6;
  border-radius: 24rpx;
  font-size: 24rpx;
  padding: 12rpx 24rpx;
  min-width: 80rpx;
}

.filter-option.active {
  background: #4CAF50;
  color: white;
  border-color: #4CAF50;
}

.filter-actions {
  display: flex;
  gap: 20rpx;
  margin-top: 40rpx;
}

.reset-btn {
  flex: 1;
  background: #f8f9fa;
  color: #666;
  border: 1rpx solid #dee2e6;
  border-radius: 12rpx;
  font-size: 28rpx;
  padding: 24rpx;
}

.confirm-btn {
  flex: 2;
  background: linear-gradient(45deg, #4CAF50, #45a049);
  color: white;
  border: none;
  border-radius: 12rpx;
  font-size: 28rpx;
  padding: 24rpx;
}

/* 响应式设计 */
@media (max-width: 400rpx) {
  .item-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12rpx;
  }
  
  .item-actions {
    justify-content: flex-start;
  }
  
  .stats-bar {
    flex-direction: column;
    gap: 16rpx;
  }
  
  .stat-item {
    flex-direction: row;
    width: 100%;
    justify-content: space-between;
  }
}
</style>