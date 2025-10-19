// 用户相关类型
export interface UserInfo {
  id: number
  openid: string
  unionid?: string
  username: string
  avatar_url?: string
  phone?: string
  email?: string
  subscription_level: string
  subscription_expires_at?: string
  quota_used: number
  quota_limit: number
  quota_reset_date?: string
  is_active: boolean
  last_login_at?: string
  created_at: string
  updated_at: string
}

export interface QuotaInfo {
  available: boolean
  remaining: number
  plan_type: string
  monthly_quota: number
  used_quota: number
  subscription_active: boolean
  warning_level?: string
  message?: string
  next_reset?: string
  show_upgrade_prompt: boolean
}

// 翻译任务相关类型
export interface TranslationTask {
  id: number
  task_id: string
  user_id: number
  original_filename: string
  original_file_url: string
  file_size: number
  file_type: string
  mime_type: string
  duration_seconds?: number
  processing_status: 'pending' | 'processing' | 'completed' | 'failed'
  processing_error?: string
  processing_started_at?: string
  processing_completed_at?: string
  transcribed_text?: string
  confidence_score?: number
  word_count?: number
  service_provider?: string
  service_request_id?: string
  service_cost?: number
  is_quota_used: boolean
  quota_deducted_at?: string
  metadata?: string
  created_at: string
  updated_at: string
  progress_percentage?: number
  processing_duration?: number
}

// API请求参数类型
export interface TranslationHistoryParams {
  limit?: number
  offset?: number
  status?: string
}

export interface CreateTranslationParams {
  file_type: string
  original_filename: string
  file_size: number
  file_url: string
  duration_seconds?: number
}

export interface StartTranslationParams {
  task_id: string
  language?: string
  provider?: string
}

// 文件上传相关类型
export interface FileUploadData {
  tempFilePath: string
  name: string
  size: number
  type: string
}

export interface MediaFileInfo {
  type: 'audio' | 'video' | 'wechat_video' | 'link'
  name: string
  size: number
  duration?: number
  path: string
}

// API响应类型
export interface ApiResponse<T = any> {
  success: boolean
  message?: string
  data?: T
  error?: string
}

export interface PaginationResponse<T> {
  data: T[]
  total: number
  limit: number
  offset: number
  has_more: boolean
}

// 订阅相关类型
export interface SubscriptionPlan {
  id: number
  name: string
  code: string
  price: number
  quota_limit: number
  description: string
  features: string[]
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface PaymentOrder {
  id: number
  order_no: string
  user_id: number
  plan_id: number
  amount: number
  currency: string
  payment_method: string
  payment_status: string
  prepay_id?: string
  transaction_id?: string
  paid_at?: string
  refunded_at?: string
  created_at: string
  updated_at: string
}

// 应用配置类型
export interface AppConfig {
  apiBaseUrl: string
  appVersion: string
  environment: 'development' | 'production'
  features: {
    enableShare: boolean
    enableHistory: boolean
    enableVip: boolean
    maxFileSize: number
    supportedFormats: string[]
  }
}

// 错误类型
export interface AppError {
  code: string
  message: string
  details?: any
}

// 事件类型
export interface TranslationEvent {
  type: 'upload_start' | 'upload_progress' | 'upload_complete' | 'translation_start' | 'translation_progress' | 'translation_complete' | 'translation_error'
  data: any
}

// 通知类型
export interface NotificationData {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message: string
  duration?: number
  showCancel?: boolean
}

// 分享信息类型
export interface ShareInfo {
  title: string
  desc?: string
  path: string
  imageUrl?: string
}

// WeChat小程序特定类型
export interface WechatLoginResponse {
  code: string
  state?: string
}

export interface WechatUserInfo {
  openid: string
  nickname: string
  avatarUrl: string
  gender: number
  city: string
  province: string
  country: string
  language: string
}

// 组件Props类型
export interface QuotaDisplayProps {
  showDetails?: boolean
  customClass?: string
}

export interface UpgradePromptProps {
  show: boolean
  type?: 'exhausted' | 'warning' | 'upgrade'
  quotaInfo?: QuotaInfo
  title?: string
  message?: string
}

// 平台适配器类型
export interface PlatformAdapter {
  login: () => Promise<any>
  pay: (orderData: any) => Promise<any>
  share: (shareInfo: ShareInfo) => boolean
  chooseMedia: (options: any) => Promise<any>
  getSystemInfo: () => Promise<any>
}