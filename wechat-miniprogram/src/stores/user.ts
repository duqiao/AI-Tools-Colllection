import { defineStore } from 'pinia'
import type { UserInfo, QuotaInfo } from '@/types'

interface UserState {
  userInfo: UserInfo | null
  isLoggedIn: boolean
  token: string | null
  quotaInfo: QuotaInfo | null
  subscriptionLevel: string
  isVip: boolean
}

export const useUserStore = defineStore('user', {
  state: (): UserState => ({
    userInfo: null,
    isLoggedIn: false,
    token: null,
    quotaInfo: null,
    subscriptionLevel: 'free',
    isVip: false
  }),

  getters: {
    displayName: (state) => {
      return state.userInfo?.username || '用户'
    },
    
    remainingQuota: (state) => {
      return state.quotaInfo?.remaining || 0
    },
    
    quotaPercentage: (state) => {
      if (!state.quotaInfo) return 0
      const { remaining, monthly_quota } = state.quotaInfo
      return monthly_quota > 0 ? ((monthly_quota - remaining) / monthly_quota) * 100 : 0
    }
  },

  actions: {
    // 检查登录状态
    async checkLoginStatus() {
      try {
        const tokenStr = localStorage.getItem('token')
        const userInfoStr = localStorage.getItem('userInfo')
        const quotaInfoStr = localStorage.getItem('quota_info')

        if (tokenStr && userInfoStr) {
          this.token = tokenStr
          this.userInfo = JSON.parse(userInfoStr)
          this.isLoggedIn = true
          this.subscriptionLevel = this.userInfo.subscription_level || 'free'
          this.isVip = this.subscriptionLevel !== 'free'
          
          if (quotaInfoStr) {
            this.quotaInfo = JSON.parse(quotaInfoStr)
          }
        } else {
          this.logout()
        }
      } catch (error) {
        console.error('Check login status error:', error)
        this.logout()
      }
    },

    // 登录
    async login(loginData: { code: string; userInfo: any }) {
      try {
        // 模拟登录API调用
        const mockResponse = {
          success: true,
          data: {
            token: 'mock-token-' + Date.now(),
            user: {
              id: 1,
              openid: 'mock-openid',
              username: '测试用户',
              avatar_url: '/static/images/default-avatar.png',
              subscription_level: 'free',
              quota_used: 0,
              quota_limit: 10,
              is_active: true,
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString()
            },
            quota: {
              available: true,
              remaining: 10,
              plan_type: 'free',
              monthly_quota: 10,
              used_quota: 0,
              subscription_active: false,
              warning_level: 'normal',
              show_upgrade_prompt: false
            }
          }
        }
        
        if (mockResponse.success) {
          const { token, user, quota } = mockResponse.data
          
          // 保存登录信息
          this.token = token
          this.userInfo = user
          this.isLoggedIn = true
          this.subscriptionLevel = user.subscription_level || 'free'
          this.isVip = this.subscriptionLevel !== 'free'
          
          if (quota) {
            this.quotaInfo = quota
          }

          // 保存到本地存储
          localStorage.setItem('token', token)
          localStorage.setItem('userInfo', JSON.stringify(user))
          if (quota) {
            localStorage.setItem('quota_info', JSON.stringify(quota))
          }

          return { success: true, data: mockResponse.data }
        } else {
          throw new Error('登录失败')
        }
      } catch (error) {
        console.error('Login error:', error)
        throw error
      }
    },

    // 登出
    logout() {
      this.userInfo = null
      this.isLoggedIn = false
      this.token = null
      this.quotaInfo = null
      this.subscriptionLevel = 'free'
      this.isVip = false

      // 清除本地存储
      localStorage.removeItem('token')
      localStorage.removeItem('userInfo')
      localStorage.removeItem('quota_info')
    },

    // 更新配额信息
    updateQuotaInfo(quotaInfo: QuotaInfo) {
      this.quotaInfo = quotaInfo
      localStorage.setItem('quota_info', JSON.stringify(quotaInfo))
    },

    // 更新用户信息
    updateUserInfo(userInfo: Partial<UserInfo>) {
      if (this.userInfo) {
        this.userInfo = { ...this.userInfo, ...userInfo }
        localStorage.setItem('userInfo', JSON.stringify(this.userInfo))
      }
    },

    // 升级订阅
    async upgradeSubscription(planId: string) {
      try {
        const response = await uni.request({
          url: `${this.getBaseUrl()}/subscription/upgrade`,
          method: 'POST',
          data: { plan_id: planId },
          header: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.token}`
          }
        })

        if (response.statusCode === 200 && response.data.success) {
          const { subscription } = response.data.data
          
          // 更新订阅信息
          this.subscriptionLevel = subscription.plan_type
          this.isVip = subscription.plan_type !== 'free'
          
          if (this.userInfo) {
            this.userInfo.subscription_level = subscription.plan_type
          }

          return { success: true, data: response.data.data }
        } else {
          throw new Error(response.data.message || '升级失败')
        }
      } catch (error) {
        console.error('Upgrade subscription error:', error)
        throw error
      }
    },

    // 获取API基础URL
    getBaseUrl(): string {
      return localStorage.getItem('baseUrl') || 'http://localhost:8000/api/v1'
    },

    // 刷新配额信息
    async refreshQuotaInfo() {
      if (!this.isLoggedIn || !this.token) {
        return
      }

      try {
        const response = await uni.request({
          url: `${this.getBaseUrl()}/quota/status`,
          method: 'GET',
          header: {
            'Authorization': `Bearer ${this.token}`
          }
        })

        if (response.statusCode === 200 && response.data) {
          this.updateQuotaInfo(response.data)
          return response.data
        }
      } catch (error) {
        console.error('Refresh quota info error:', error)
      }
    }
  }
})