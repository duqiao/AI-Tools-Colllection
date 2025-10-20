// User and Authentication Types
export interface User {
  id: number;
  openid: string;
  unionid?: string;
  username?: string;
  avatar_url?: string;
  phone?: string;
  email?: string;
  subscription_level: 'free' | 'basic_vip' | 'premium_vip';
  subscription_expires_at?: string;
  quota_used: number;
  quota_limit: number;
  quota_reset_date?: string;
  is_active: boolean;
  last_login_at?: string;
  created_at: string;
  updated_at: string;
}

export interface AuthResponse {
  user: User;
  token: string;
  expires_in: number;
}

export interface WeChatUserInfo {
  openid: string;
  unionid?: string;
  nickname?: string;
  headimgurl?: string;
  sex?: number;
  province?: string;
  city?: string;
  country?: string;
}

// Translation Types
export interface TranslationTask {
  id: string;
  user_id: number;
  original_filename: string;
  original_file_url: string;
  file_size: number;
  file_type: 'audio' | 'video' | 'wechat_video' | 'link';
  mime_type?: string;
  duration_seconds?: number;
  processing_status: 'pending' | 'processing' | 'completed' | 'failed';
  processing_error?: string;
  processing_started_at?: string;
  processing_completed_at?: string;
  transcribed_text?: string;
  confidence_score?: number;
  word_count?: number;
  service_provider?: string;
  service_request_id?: string;
  service_cost?: number;
  is_quota_used: boolean;
  quota_deducted_at?: string;
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface TranslationRequest {
  file_type: string;
  original_filename: string;
  file_size: number;
  file_url: string;
}

export interface TranslationResponse {
  task_id: string;
  status: string;
  transcribed_text?: string;
  confidence_score?: number;
  word_count?: number;
}

export interface UploadResponse {
  task_id: string;
  file_url: string;
  file_size: number;
  file_type: string;
}

// Subscription Types
export interface SubscriptionPlan {
  id: number;
  name: string;
  code: 'basic_vip' | 'premium_vip';
  price: number;
  quota_limit: number;
  description?: string;
  features?: Record<string, any>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface PaymentOrder {
  id: number;
  order_no: string;
  user_id: number;
  plan_id: number;
  amount: number;
  currency: string;
  payment_method: string;
  payment_status: 'pending' | 'paid' | 'failed' | 'refunded';
  prepay_id?: string;
  transaction_id?: string;
  paid_at?: string;
  refunded_at?: string;
  created_at: string;
  updated_at: string;
}

export interface QuotaStatus {
  used: number;
  limit: number;
  remaining: number;
  reset_date: string;
  days_until_reset: number;
}

// API Response Types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
  code?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

// UI Types
export interface FeatureInfo {
  id: number;
  icon: string;
  iconBg: string;
  title: string;
  description: string;
  badge?: string;
  badgeVariant?: 'default' | 'secondary' | 'success' | 'warning' | 'error';
  onPress: () => void;
}

export interface FileInfo {
  uri: string;
  name: string;
  size: number;
  type: string;
  mimeType?: string;
}

export interface ToastConfig {
  visible: boolean;
  message: string;
  type: 'success' | 'error' | 'info';
  duration?: number;
}

// Navigation Types
export type RootStackParamList = {
  MainTabs: undefined;
  Result: { taskId: string };
  Upload: undefined;
};

export type TabParamList = {
  Home: undefined;
  Upload: undefined;
  History: undefined;
  Profile: undefined;
};

// Error Types
export interface AppError {
  code: string;
  message: string;
  details?: Record<string, any>;
}

// System Types
export interface SystemSettings {
  id: number;
  key: string;
  value: string;
  description?: string;
  data_type: 'string' | 'number' | 'boolean' | 'json';
  is_public: boolean;
  created_at: string;
  updated_at: string;
}

export interface UsageStatistics {
  id: number;
  user_id: number;
  date: string;
  translations_completed: number;
  total_duration_seconds: number;
  total_file_size: number;
  quota_consumed: number;
  service_cost_total: number;
  created_at: string;
  updated_at: string;
}