import type { 
  ApiResponse, 
  PaginationResponse, 
  TranslationTask, 
  CreateTranslationParams,
  StartTranslationParams,
  TranslationHistoryParams,
  UserInfo,
  QuotaInfo,
  SubscriptionPlan,
  PaymentOrder
} from '@/types'

// 获取API基础URL
function getBaseUrl(): string {
  return localStorage.getItem('baseUrl') || 'http://localhost:8000/api/v1'
}

// 获取认证token
function getAuthToken(): string {
  const token = localStorage.getItem('token')
  if (!token) {
    throw new Error('用户未登录')
  }
  return token
}

// 统一请求处理
async function request<T = any>(
  url: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  try {
    const fullUrl = url.startsWith('http') ? url : `${getBaseUrl()}${url}`
    
    const response = await fetch(fullUrl, {
      method: options.method || 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      body: options.body,
      ...options
    })

    if (response.status === 200) {
      return await response.json() as ApiResponse<T>
    } else if (response.status === 401) {
      // Token过期，清除登录状态
      localStorage.removeItem('token')
      localStorage.removeItem('userInfo')
      throw new Error('登录已过期，请重新登录')
    } else {
      const errorData = await response.json().catch(() => null)
      throw new Error(errorData?.message || '请求失败')
    }
  } catch (error) {
    console.error('API request error:', error)
    throw error
  }
}

// 文件上传处理
async function uploadFile(
  url: string,
  filePath: string,
  formData: Record<string, any>,
  options: Record<string, any> = {}
): Promise<ApiResponse> {
  try {
    const token = getAuthToken()
    
    const response = await uni.uploadFile({
      url,
      filePath,
      name: options.name || 'file',
      formData,
      header: {
        'Authorization': `Bearer ${token}`,
        ...options.header
      },
      ...options
    })

    if (response.statusCode === 200) {
      return JSON.parse(response.data) as ApiResponse
    } else if (response.statusCode === 401) {
      uni.removeStorageSync('token')
      uni.removeStorageSync('userInfo')
      throw new Error('登录已过期，请重新登录')
    } else {
      throw new Error('上传失败')
    }
  } catch (error) {
    console.error('File upload error:', error)
    throw error
  }
}

// 用户认证API
export const authApi = {
  // 微信登录
  async wechatLogin(loginData: { code: string; userInfo: any }) {
    return request('/auth/wechat-login', {
      method: 'POST',
      data: loginData
    })
  },

  // 获取用户信息
  async getUserInfo() {
    return request<UserInfo>('/auth/user', {
      header: {
        'Authorization': `Bearer ${getAuthToken()}`
      }
    })
  },

  // 刷新token
  async refreshToken() {
    return request<{ token: string }>('/auth/refresh', {
      method: 'POST',
      header: {
        'Authorization': `Bearer ${getAuthToken()}`
      }
    })
  },

  // 退出登录
  async logout() {
    return request('/auth/logout', {
      method: 'POST',
      header: {
        'Authorization': `Bearer ${getAuthToken()}`
      }
    })
  }
}

// 翻译API
export const translationApi = {
  // 创建翻译任务
  async createTask(data: CreateTranslationParams) {
    return request<TranslationTask>('/translation/create', {
      method: 'POST',
      data
    })
  },

  // 上传文件
  async uploadFile(filePath: string, fileData: CreateTranslationParams) {
    return uploadFile('/translation/upload', filePath, {
      file_type: fileData.file_type,
      original_filename: fileData.original_filename,
      file_size: fileData.file_size
    })
  },

  // 开始翻译
  async startTranslation(data: StartTranslationParams) {
    return request('/translation/start', {
      method: 'POST',
      data
    })
  },

  // 获取翻译状态
  async getStatus(taskId: string) {
    return request<TranslationTask>(`/translation/${taskId}/status`)
  },

  // 获取翻译历史
  async getHistory(params: TranslationHistoryParams) {
    return request<PaginationResponse<TranslationTask>>('/translation/history', {
      data: params
    })
  },

  // 获取翻译详情
  async getDetail(taskId: string) {
    return request<TranslationTask>(`/translation/${taskId}`)
  },

  // 取消翻译
  async cancelTranslation(taskId: string) {
    return request(`/translation/${taskId}/cancel`, {
      method: 'POST'
    })
  }
}

// 配额API
export const quotaApi = {
  // 获取配额状态
  async getStatus() {
    return request<QuotaInfo>('/quota/status', {
      header: {
        'Authorization': `Bearer ${getAuthToken()}`
      }
    })
  },

  // 检查配额可用性
  async checkAvailability(requiredQuota: number = 1) {
    return request<QuotaInfo>('/quota/check', {
      method: 'POST',
      data: { required_quota: requiredQuota },
      header: {
        'Authorization': `Bearer ${getAuthToken()}`
      }
    })
  },

  // 使用配额
  async useQuota(data: {
    amount?: number
    usage_type?: string
    description?: string
    translation_id?: number
  }) {
    return request('/quota/use', {
      method: 'POST',
      data,
      header: {
        'Authorization': `Bearer ${getAuthToken()}`
      }
    })
  },

  // 重置配额
  async resetQuota() {
    return request('/quota/reset', {
      method: 'POST',
      header: {
        'Authorization': `Bearer ${getAuthToken()}`
      }
    })
  },

  // 获取配额历史
  async getHistory(params: {
    limit?: number
    usage_type?: string
  }) {
    return request('/quota/history', {
      data: params,
      header: {
        'Authorization': `Bearer ${getAuthToken()}`
      }
    })
  },

  // 获取配额分析
  async getAnalytics(days: number = 30) {
    return request('/quota/analytics', {
      data: { days },
      header: {
        'Authorization': `Bearer ${getAuthToken()}`
      }
    })
  }
}

// 订阅API
export const subscriptionApi = {
  // 获取订阅计划
  async getPlans() {
    return request<SubscriptionPlan[]>('/subscription/plans')
  },

  // 获取用户订阅信息
  async getUserSubscription() {
    return request('/subscription/user', {
      header: {
        'Authorization': `Bearer ${getAuthToken()}`
      }
    })
  },

  // 创建订单
  async createOrder(planId: number) {
    return request<PaymentOrder>('/subscription/create-order', {
      method: 'POST',
      data: { plan_id: planId },
      header: {
        'Authorization': `Bearer ${getAuthToken()}`
      }
    })
  },

  // 发起微信支付
  async initiateWechatPayment(orderId: string) {
    return request('/payment/wechat-pay', {
      method: 'POST',
      data: { order_id: orderId },
      header: {
        'Authorization': `Bearer ${getAuthToken()}`
      }
    })
  },

  // 检查支付状态
  async checkPaymentStatus(orderNo: string) {
    return request(`/payment/status/${orderNo}`)
  },

  // 升级订阅
  async upgrade(planId: string) {
    return request('/subscription/upgrade', {
      method: 'POST',
      data: { plan_id: planId },
      header: {
        'Authorization': `Bearer ${getAuthToken()}`
      }
    })
  }
}

// 系统API
export const systemApi = {
  // 获取系统配置
  async getConfig() {
    return request('/system/config')
  },

  // 检查更新
  async checkUpdate() {
    return request('/system/update-check')
  },

  // 上传错误日志
  async uploadErrorLog(errorData: any) {
    return request('/system/error-log', {
      method: 'POST',
      data: errorData,
      header: {
        'Authorization': `Bearer ${getAuthToken()}`
      }
    })
  }
}

// 工具函数
export const apiUtils = {
  // 格式化文件大小
  formatFileSize(bytes: number): string {
    if (!bytes) return '0B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + sizes[i]
  },

  // 格式化持续时间
  formatDuration(seconds: number): string {
    if (!seconds) return '0秒'
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60
    
    if (hours > 0) {
      return `${hours}小时${minutes}分钟`
    } else if (minutes > 0) {
      return `${minutes}分钟${secs}秒`
    } else {
      return `${secs}秒`
    }
  },

  // 获取文件类型图标
  getFileTypeIcon(fileType: string): string {
    const iconMap: Record<string, string> = {
      'audio': '/static/images/audio-icon.png',
      'video': '/static/images/video-icon.png',
      'wechat_video': '/static/images/wechat-video-icon.png'
    }
    return iconMap[fileType] || '/static/images/default-file-icon.png'
  },

  // 获取文件类型文本
  getFileTypeText(fileType: string): string {
    const textMap: Record<string, string> = {
      'audio': '音频',
      'video': '视频',
      'wechat_video': '微信视频'
    }
    return textMap[fileType] || '文件'
  },

  // 获取状态文本
  getStatusText(status: string): string {
    const statusMap: Record<string, string> = {
      'pending': '等待中',
      'processing': '处理中',
      'completed': '已完成',
      'failed': '失败'
    }
    return statusMap[status] || '未知'
  }
}

export default {
  authApi,
  translationApi,
  quotaApi,
  subscriptionApi,
  systemApi,
  apiUtils
}