import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { ApiResponse, User, TranslationTask, SubscriptionPlan, PaymentOrder, QuotaStatus, WeChatUserInfo, UploadResponse, TranslationRequest } from '@/types';

// API Configuration
const API_BASE_URL = __DEV__ ? 'http://127.0.0.1:8001/api/v1' : 'https://your-api-domain.com/api/v1';
const ACCESS_TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';

class ApiClient {
  private client: AxiosInstance;
  private token: string | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
    this.loadToken();
  }

  private setupInterceptors() {
    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      async (config) => {
        if (this.token) {
          config.headers.Authorization = `Bearer ${this.token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          // Token expired or invalid - try to refresh
          const refreshToken = await this.getRefreshToken();
          if (refreshToken) {
            try {
              const refreshResponse = await this.client.post('/auth/refresh', {
                refresh_token: refreshToken
              });
              
              if (refreshResponse.data.success) {
                const newToken = refreshResponse.data.data.token;
                const newRefreshToken = refreshResponse.data.data.refreshToken;
                
                // Save new tokens
                this.token = newToken;
                await AsyncStorage.setItem(ACCESS_TOKEN_KEY, newToken);
                await AsyncStorage.setItem(REFRESH_TOKEN_KEY, newRefreshToken);
                
                // Retry the original request with new token
                const originalRequest = error.config;
                if (originalRequest?.headers) {
                  originalRequest.headers.Authorization = `Bearer ${newToken}`;
                }
                return this.client(originalRequest);
              }
            } catch (refreshError) {
              // Refresh failed, clear tokens and redirect to login
              await this.clearToken();
              console.error('Token refresh failed:', refreshError);
            }
          } else {
            // No refresh token, clear auth data
            await this.clearToken();
          }
        }
        return Promise.reject(error);
      }
    );
  }

  private async loadToken() {
    try {
      const storedToken = await AsyncStorage.getItem(ACCESS_TOKEN_KEY);
      if (storedToken) {
        this.token = storedToken;
      }
    } catch (error) {
      console.error('Error loading token:', error);
    }
  }

  private async saveToken(token: string) {
    try {
      this.token = token;
      await AsyncStorage.setItem(ACCESS_TOKEN_KEY, token);
    } catch (error) {
      console.error('Error saving token:', error);
    }
  }

  private async clearToken() {
    try {
      this.token = null;
      await AsyncStorage.multiRemove([ACCESS_TOKEN_KEY, REFRESH_TOKEN_KEY]);
    } catch (error) {
      console.error('Error clearing token:', error);
    }
  }

  private async getRefreshToken(): Promise<string | null> {
    try {
      return await AsyncStorage.getItem(REFRESH_TOKEN_KEY);
    } catch (error) {
      return null;
    }
  }

  // Public method to set token externally (from AuthService)
  public setToken(token: string): void {
    this.token = token;
  }

  // Generic request methods
  private async request<T>(config: AxiosRequestConfig): Promise<ApiResponse<T>> {
    try {
      const response: AxiosResponse<ApiResponse<T>> = await this.client.request(config);
      return response.data;
    } catch (error: any) {
      return {
        success: false,
        error: error.response?.data?.message || error.message || 'Network error',
        code: error.response?.status || 500,
      };
    }
  }

  // Authentication endpoints
  async wechatLogin(code: string, userInfo: WeChatUserInfo): Promise<ApiResponse<{ user: User; token: string }>> {
    const response = await this.request<{ user: User; token: string }>({
      method: 'POST',
      url: '/auth/wechat-login',
      data: { code, userInfo },
    });

    if (response.success && response.data) {
      await this.saveToken(response.data.token);
    }

    return response;
  }

  async refreshToken(): Promise<ApiResponse<{ token: string }>> {
    const response = await this.request<{ token: string }>({
      method: 'POST',
      url: '/auth/refresh',
    });

    if (response.success && response.data) {
      await this.saveToken(response.data.token);
    }

    return response;
  }

  async logout(): Promise<ApiResponse<void>> {
    const response = await this.request<void>({
      method: 'POST',
      url: '/auth/logout',
    });

    await this.clearToken();
    return response;
  }

  // User management endpoints
  async getUserProfile(): Promise<ApiResponse<User>> {
    return this.request<User>({
      method: 'GET',
      url: '/users/profile',
    });
  }

  async updateUserProfile(updates: Partial<User>): Promise<ApiResponse<User>> {
    return this.request<User>({
      method: 'PUT',
      url: '/users/profile',
      data: updates,
    });
  }

  async getUserStatistics(): Promise<ApiResponse<any>> {
    return this.request<any>({
      method: 'GET',
      url: '/users/statistics',
    });
  }

  // Translation endpoints
  async uploadFile(file: any, fileType: string): Promise<ApiResponse<UploadResponse>> {
    const formData = new FormData();
    
    if (file.uri.startsWith('file://')) {
      formData.append('file', {
        uri: file.uri,
        type: file.mimeType || 'application/octet-stream',
        name: file.name,
      } as any);
    } else {
      // Handle blob or other formats
      formData.append('file', file);
    }

    formData.append('file_type', fileType);
    formData.append('original_filename', file.name);
    formData.append('file_size', file.size.toString());

    try {
      const response = await this.client.post('/translation/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      return {
        success: true,
        data: response.data,
      };
    } catch (error: any) {
      return {
        success: false,
        error: error.response?.data?.message || error.message || 'Upload failed',
        code: error.response?.status || 500,
      };
    }
  }

  async startTranslation(taskId: string): Promise<ApiResponse<TranslationTask>> {
    return this.request<TranslationTask>({
      method: 'POST',
      url: `/translation/${taskId}/start`,
    });
  }

  async getTranslationStatus(taskId: string): Promise<ApiResponse<TranslationTask>> {
    return this.request<TranslationTask>({
      method: 'GET',
      url: `/translation/${taskId}/status`,
    });
  }

  async getTranslationHistory(page: number = 1, perPage: number = 20): Promise<ApiResponse<{ items: TranslationTask[]; total: number; page: number; pages: number }>> {
    return this.request<any>({
      method: 'GET',
      url: '/translation/history',
      params: { page, per_page: perPage },
    });
  }

  async deleteTranslation(taskId: string): Promise<ApiResponse<void>> {
    return this.request<void>({
      method: 'DELETE',
      url: `/translation/${taskId}`,
    });
  }

  // Subscription endpoints
  async getSubscriptionPlans(): Promise<ApiResponse<SubscriptionPlan[]>> {
    return this.request<SubscriptionPlan[]>({
      method: 'GET',
      url: '/subscription/plans',
    });
  }

  async createOrder(planId: number): Promise<ApiResponse<PaymentOrder>> {
    return this.request<PaymentOrder>({
      method: 'POST',
      url: '/subscription/orders',
      data: { plan_id: planId },
    });
  }

  async initiateWechatPayment(orderId: string): Promise<ApiResponse<any>> {
    return this.request<any>({
      method: 'POST',
      url: `/subscription/payments/wechat/${orderId}`,
    });
  }

  async getQuotaStatus(): Promise<ApiResponse<QuotaStatus>> {
    return this.request<QuotaStatus>({
      method: 'GET',
      url: '/quota/status',
    });
  }

  // System endpoints
  async getSystemSettings(): Promise<ApiResponse<any[]>> {
    return this.request<any[]>({
      method: 'GET',
      url: '/system/settings',
    });
  }

  // Health check
  async healthCheck(): Promise<ApiResponse<{ status: string }>> {
    return this.request<{ status: string }>({
      method: 'GET',
      url: '/health',
    });
  }
}

export const apiClient = new ApiClient();
export default apiClient;