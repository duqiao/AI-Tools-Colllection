<template>
  <div v-if="show" class="upgrade-prompt-overlay" @click="$emit('close')">
    <div class="upgrade-prompt-modal" @click.stop>
      <!-- 模态框头部 -->
      <div class="modal-header">
        <div class="prompt-icon">{{ getPromptIconEmoji() }}</div>
        <span class="prompt-title">{{ getPromptTitle() }}</span>
        <button class="close-btn" @click="$emit('close')">×</button>
      </div>

      <!-- 模态框内容 -->
      <div class="modal-content">
        <span class="prompt-message">{{ getPromptMessage() }}</span>
        
        <!-- 配额信息 -->
        <div v-if="quotaInfo" class="quota-info">
          <div class="quota-item">
            <span class="quota-label">当前配额：</span>
            <span class="quota-value">{{ quotaInfo.remaining }}/{{ quotaInfo.monthly_quota }}</span>
          </div>
          <div class="quota-item">
            <span class="quota-label">当前套餐：</span>
            <span class="quota-value">{{ getPlanTypeText(quotaInfo.plan_type) }}</span>
          </div>
        </div>

        <!-- 推荐套餐 -->
        <div class="recommended-plans">
          <div class="plans-title">推荐套餐</div>
          <div class="plans-list">
            <div 
              v-for="plan in recommendedPlans" 
              :key="plan.id"
              class="plan-item"
              :class="{ selected: selectedPlan?.id === plan.id }"
              @click="selectPlan(plan)"
            >
              <div class="plan-header">
                <span class="plan-name">{{ plan.name }}</span>
                <div v-if="plan.is_popular" class="popular-badge">推荐</div>
              </div>
              <div class="plan-price">
                <span class="price-amount">¥{{ plan.price }}</span>
                <span class="price-period">/月</span>
              </div>
              <div class="plan-quota">
                <span class="quota-text">{{ plan.quota_limit }} 次翻译</span>
              </div>
              <div class="plan-features">
                <div 
                  v-for="feature in plan.features" 
                  :key="feature"
                  class="feature-item"
                >
                  <span class="feature-icon">✓</span>
                  <span class="feature-text">{{ feature }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 升级特权 -->
        <div class="upgrade-benefits">
          <div class="benefits-title">升级特权</div>
          <div class="benefits-list">
            <div class="benefit-item">
              <span class="benefit-icon">🚀</span>
              <span class="benefit-text">更多翻译配额</span>
            </div>
            <div class="benefit-item">
              <span class="benefit-icon">⚡</span>
              <span class="benefit-text">优先处理队列</span>
            </div>
            <div class="benefit-item">
              <span class="benefit-icon">🎯</span>
              <span class="benefit-text">更高精度识别</span>
            </div>
            <div class="benefit-item">
              <span class="benefit-icon">💎</span>
              <span class="benefit-text">专属客服支持</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 模态框底部 -->
      <div class="modal-footer">
        <button class="cancel-btn" @click="$emit('close')">暂时不用</button>
        <button 
          class="confirm-btn" 
          :disabled="!selectedPlan"
          @click="confirmUpgrade"
        >
          {{ selectedPlan ? `立即升级 ¥${selectedPlan.price}/月` : '请选择套餐' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { subscriptionApi } from '@/api'
import type { QuotaInfo, SubscriptionPlan } from '@/types'
import { uni } from '@/utils/uni-adapter'

// Props
interface Props {
  show: boolean
  type?: 'exhausted' | 'warning' | 'upgrade'
  quotaInfo?: QuotaInfo | null
  title?: string
  message?: string
}

const props = withDefaults(defineProps<Props>(), {
  show: false,
  type: 'warning',
  quotaInfo: null,
  title: '',
  message: ''
})

// Emits
const emit = defineEmits<{
  close: []
  confirm: [plan: SubscriptionPlan]
}>()

// Reactive data
const recommendedPlans = ref<SubscriptionPlan[]>([])
const selectedPlan = ref<SubscriptionPlan | null>(null)

// Computed
const getPromptIcon = () => {
  const iconMap = {
    'exhausted': '/static/images/quota-exhausted.png',
    'warning': '/static/images/quota-warning.png',
    'upgrade': '/static/images/upgrade-icon.png'
  }
  return iconMap[props.type] || iconMap.warning
}

const getPromptIconEmoji = () => {
  const iconMap = {
    'exhausted': '⚠️',
    'warning': '⚠️',
    'upgrade': '💎'
  }
  return iconMap[props.type] || iconMap.warning
}

const getPromptTitle = () => {
  if (props.title) return props.title
  
  const titleMap = {
    'exhausted': '配额已用完',
    'warning': '配额不足提醒',
    'upgrade': '升级您的套餐'
  }
  return titleMap[props.type] || titleMap.warning
}

const getPromptMessage = () => {
  if (props.message) return props.message
  
  const messageMap = {
    'exhausted': '您的翻译配额已经用完，升级套餐后即可继续使用。',
    'warning': '您的配即将用完，建议及时升级套餐以免影响使用。',
    'upgrade': '升级到专业套餐，享受更多翻译配额和优质服务。'
  }
  return messageMap[props.type] || messageMap.warning
}

// Lifecycle
onMounted(() => {
  loadRecommendedPlans()
})

// Methods
async function loadRecommendedPlans() {
  try {
    const response = await subscriptionApi.getPlans()
    const plans = response.data || []
    
    // 过滤出推荐的套餐（排除免费版）
    recommendedPlans.value = plans
      .filter(plan => plan.code !== 'free' && plan.is_active)
      .sort((a, b) => a.price - b.price)
      .slice(0, 3) // 只显示前3个套餐
    
    // 自动选择最便宜的套餐
    if (recommendedPlans.value.length > 0) {
      selectedPlan.value = recommendedPlans.value[0]
    }
  } catch (error) {
    console.error('Load recommended plans error:', error)
    // 使用默认套餐
    recommendedPlans.value = [
      {
        id: 1,
        name: '基础VIP',
        code: 'basic_vip',
        price: 19.9,
        quota_limit: 500,
        description: '适合轻度使用',
        features: ['500次翻译/月', '标准精度', '普通处理'],
        is_active: true,
        created_at: '',
        updated_at: ''
      },
      {
        id: 2,
        name: '高级VIP',
        code: 'premium_vip',
        price: 39.9,
        quota_limit: 2000,
        description: '适合日常使用',
        features: ['2000次翻译/月', '高精度识别', '优先处理'],
        is_active: true,
        created_at: '',
        updated_at: ''
      }
    ]
    
    if (recommendedPlans.value.length > 0) {
      selectedPlan.value = recommendedPlans.value[0]
    }
  }
}

function selectPlan(plan: SubscriptionPlan) {
  selectedPlan.value = plan
}

function getPlanTypeText(planType: string): string {
  const planMap: Record<string, string> = {
    'free': '免费版',
    'basic_vip': '基础VIP',
    'premium_vip': '高级VIP',
    'pro_vip': '专业VIP'
  }
  return planMap[planType] || '免费版'
}

function confirmUpgrade() {
  if (selectedPlan.value) {
    emit('confirm', selectedPlan.value)
  }
}
</script>

<style>
/* components/upgrade-prompt/index.wxss */
.upgrade-prompt-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 40rpx;
}

.upgrade-prompt-modal {
  background: #fff;
  border-radius: 24rpx;
  width: 100%;
  max-width: 700rpx;
  max-height: 80vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 32rpx 32rpx 24rpx;
  border-bottom: 1rpx solid #f0f0f0;
  position: relative;
}

.prompt-icon {
  width: 60rpx;
  height: 60rpx;
  margin-right: 16rpx;
}

.prompt-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
  flex: 1;
}

.close-btn {
  background: none;
  border: none;
  color: #999;
  font-size: 40rpx;
  padding: 0;
  width: 40rpx;
  height: 40rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-content {
  flex: 1;
  padding: 32rpx;
  overflow-y: auto;
}

.prompt-message {
  font-size: 26rpx;
  color: #666;
  line-height: 1.5;
  margin-bottom: 24rpx;
}

.quota-info {
  background: #f8f9fa;
  border-radius: 12rpx;
  padding: 20rpx;
  margin-bottom: 32rpx;
}

.quota-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8rpx 0;
}

.quota-item:last-child {
  border-bottom: none;
}

.quota-label {
  font-size: 24rpx;
  color: #666;
}

.quota-value {
  font-size: 24rpx;
  color: #333;
  font-weight: 500;
}

.recommended-plans {
  margin-bottom: 32rpx;
}

.plans-title {
  font-size: 28rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 20rpx;
}

.plans-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.plan-item {
  border: 2rpx solid #e9ecef;
  border-radius: 16rpx;
  padding: 20rpx;
  transition: all 0.3s ease;
}

.plan-item.selected {
  border-color: #4CAF50;
  background: #f0fff4;
}

.plan-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12rpx;
}

.plan-name {
  font-size: 28rpx;
  font-weight: 600;
  color: #333;
}

.popular-badge {
  background: linear-gradient(45deg, #FFD700, #FFA500);
  color: white;
  font-size: 20rpx;
  padding: 4rpx 12rpx;
  border-radius: 12rpx;
  font-weight: 500;
}

.plan-price {
  display: flex;
  align-items: baseline;
  margin-bottom: 8rpx;
}

.price-amount {
  font-size: 32rpx;
  font-weight: 700;
  color: #ff4757;
}

.price-period {
  font-size: 20rpx;
  color: #999;
  margin-left: 4rpx;
}

.plan-quota {
  margin-bottom: 16rpx;
}

.quota-text {
  font-size: 24rpx;
  color: #4CAF50;
  font-weight: 500;
}

.plan-features {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.feature-item {
  display: flex;
  align-items: center;
}

.feature-icon {
  color: #4CAF50;
  font-size: 20rpx;
  margin-right: 8rpx;
  width: 20rpx;
}

.feature-text {
  font-size: 22rpx;
  color: #666;
}

.upgrade-benefits {
  margin-bottom: 32rpx;
}

.benefits-title {
  font-size: 28rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 20rpx;
}

.benefits-list {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16rpx;
}

.benefit-item {
  display: flex;
  align-items: center;
  background: #f8f9fa;
  border-radius: 12rpx;
  padding: 16rpx;
}

.benefit-icon {
  font-size: 24rpx;
  margin-right: 12rpx;
}

.benefit-text {
  font-size: 22rpx;
  color: #333;
  font-weight: 500;
}

.modal-footer {
  display: flex;
  gap: 20rpx;
  padding: 24rpx 32rpx 32rpx;
  border-top: 1rpx solid #f0f0f0;
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

.confirm-btn {
  flex: 2;
  background: linear-gradient(45deg, #4CAF50, #45a049);
  color: white;
  border: none;
  border-radius: 12rpx;
  font-size: 28rpx;
  font-weight: 500;
  padding: 24rpx;
  transition: all 0.3s ease;
}

.confirm-btn:disabled {
  background: #ccc;
  color: #999;
}

.confirm-btn:active:not(:disabled) {
  opacity: 0.8;
  transform: scale(0.98);
}

/* 响应式设计 */
@media (max-width: 400rpx) {
  .upgrade-prompt-modal {
    margin: 20rpx;
  }
  
  .modal-header {
    padding: 24rpx;
  }
  
  .modal-content {
    padding: 24rpx;
  }
  
  .benefits-list {
    grid-template-columns: 1fr;
  }
  
  .modal-footer {
    flex-direction: column;
    padding: 24rpx;
  }
  
  .cancel-btn,
  .confirm-btn {
    width: 100%;
  }
}

/* 动画效果 */
.upgrade-prompt-overlay {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.upgrade-prompt-modal {
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from {
    transform: translateY(100rpx);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}
</style>