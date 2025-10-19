<template>
  <div class="quota-display" :class="customClass">
    <!-- Loading state -->
    <div v-if="loading" class="quota-loading">
      <div class="loading-spinner">⏳</div>
      <span class="loading-text">加载中...</span>
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="quota-error">
      <div class="error-icon">⚠️</div>
      <span class="error-text">{{ error }}</span>
      <button class="retry-btn" @click="refreshQuota">重试</button>
    </div>

    <!-- Quota info -->
    <div v-else class="quota-info">
      <div class="quota-header">
        <div class="quota-title">翻译配额</div>
        <div class="quota-stats">
          <span class="quota-number">{{ quotaInfo?.remaining || 0 }}</span>
          <span class="quota-separator">/</span>
          <span class="quota-total">{{ quotaInfo?.monthly_quota || 0 }}</span>
        </div>
      </div>
      
      <div class="quota-details">
        <div class="detail-row">
          <span class="detail-label">状态：</span>
          <span class="detail-value" :class="statusClass">{{ statusText }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">类型：</span>
          <span class="detail-value">{{ quotaInfo?.plan_type || '免费' }}</span>
        </div>
      </div>
      
      <div v-if="quotaInfo?.show_upgrade_prompt" class="upgrade-section">
        <button class="upgrade-btn" @click="$emit('upgrade')">
          立即升级
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { QuotaInfo } from '@/types'
import { uni } from '@/utils/uni-adapter'

// Props
interface Props {
  customClass?: string
}

const props = withDefaults(defineProps<Props>(), {
  customClass: ''
})

// Emits
const emit = defineEmits<{
  upgrade: []
  details: []
}>()

// Reactive data
const quotaInfo = ref<QuotaInfo | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)

// Computed
const statusText = computed(() => {
  if (!quotaInfo.value) return '未知'
  
  const statusMap: Record<string, string> = {
    'exhausted': '已用完',
    'critical': '仅剩少量',
    'warning': '即将用完',
    'normal': '充足'
  }
  
  return statusMap[quotaInfo.value.warning_level || 'normal'] || '正常'
})

const statusClass = computed(() => {
  if (!quotaInfo.value) return ''
  return `status-${quotaInfo.value.warning_level || 'normal'}`
})

// Lifecycle
onMounted(() => {
  loadQuotaStatus()
})

// Methods
async function loadQuotaStatus() {
  try {
    loading.value = true
    error.value = null
    
    // Mock quota data for now
    setTimeout(() => {
      quotaInfo.value = {
        available: true,
        remaining: 5,
        plan_type: 'free',
        monthly_quota: 10,
        used_quota: 5,
        subscription_active: false,
        warning_level: 'warning',
        message: '配额即将用完，建议升级套餐',
        show_upgrade_prompt: true
      }
      loading.value = false
    }, 1000)
    
  } catch (err) {
    console.error('Load quota status error:', err)
    error.value = '获取配额信息失败'
    loading.value = false
  }
}

function refreshQuota() {
  loadQuotaStatus()
}
</script>

<style>
.quota-display {
  background: #fff;
  border-radius: 12rpx;
  padding: 24rpx;
  margin: 16rpx 0;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.1);
}

.quota-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40rpx 0;
}

.loading-spinner {
  font-size: 40rpx;
  margin-bottom: 16rpx;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-text {
  color: #999;
  font-size: 24rpx;
}

.quota-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40rpx 0;
}

.error-icon {
  font-size: 40rpx;
  color: #ff4757;
  margin-bottom: 16rpx;
}

.error-text {
  color: #ff4757;
  font-size: 24rpx;
  margin-bottom: 16rpx;
}

.retry-btn {
  background: #4CAF50;
  color: white;
  border: none;
  border-radius: 8rpx;
  font-size: 24rpx;
  padding: 8rpx 16rpx;
}

.quota-info {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.quota-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.quota-title {
  font-size: 28rpx;
  font-weight: 600;
  color: #333;
}

.quota-stats {
  display: flex;
  align-items: baseline;
  gap: 8rpx;
}

.quota-number {
  font-size: 36rpx;
  font-weight: 700;
  color: #4CAF50;
}

.quota-separator {
  color: #666;
  font-size: 24rpx;
}

.quota-total {
  font-size: 24rpx;
  color: #666;
}

.quota-details {
  background: #f8f9fa;
  border-radius: 8rpx;
  padding: 16rpx;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8rpx 0;
}

.detail-label {
  font-size: 24rpx;
  color: #666;
}

.detail-value {
  font-size: 24rpx;
  color: #333;
  font-weight: 500;
}

.status-exhausted {
  color: #ff4757;
}

.status-critical {
  color: #ff4757;
}

.status-warning {
  color: #ffa502;
}

.status-normal {
  color: #4CAF50;
}

.upgrade-section {
  margin-top: 16rpx;
}

.upgrade-btn {
  width: 100%;
  background: linear-gradient(45deg, #4CAF50, #45a049);
  color: white;
  border: none;
  border-radius: 8rpx;
  font-size: 24rpx;
  padding: 12rpx;
  font-weight: 500;
}

/* Button states */
.retry-btn:active,
.upgrade-btn:active {
  opacity: 0.8;
  transform: scale(0.98);
}
</style>