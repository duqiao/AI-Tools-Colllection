import { defineStore } from 'pinia'
import type { TranslationTask, TranslationHistoryParams } from '@/types'

interface TranslationState {
  currentTask: TranslationTask | null
  taskHistory: TranslationTask[]
  isProcessing: boolean
  processingProgress: number
  uploadProgress: number
  error: string | null
  pollingInterval: number | null
}

export const useTranslationStore = defineStore('translation', {
  state: (): TranslationState => ({
    currentTask: null,
    taskHistory: [],
    isProcessing: false,
    processingProgress: 0,
    uploadProgress: 0,
    error: null,
    pollingInterval: null
  }),

  getters: {
    currentTaskId: (state) => state.currentTask?.task_id || null,
    isTaskCompleted: (state) => state.currentTask?.processing_status === 'completed',
    isTaskFailed: (state) => state.currentTask?.processing_status === 'failed',
    recentTranslations: (state) => state.taskHistory.slice(0, 5)
  },

  actions: {
    // 创建翻译任务
    async createTranslationTask(fileData: {
      file_type: string
      original_filename: string
      file_size: number
      file_url: string
      duration_seconds?: number
    }) {
      try {
        const token = uni.getStorageSync('token')
        if (!token) {
          throw new Error('用户未登录')
        }

        const response = await uni.request({
          url: `${this.getBaseUrl()}/translation/create`,
          method: 'POST',
          data: fileData,
          header: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          }
        })

        if (response.statusCode === 200 && response.data.success) {
          this.currentTask = response.data.data
          return { success: true, data: response.data.data }
        } else {
          throw new Error(response.data.message || '创建任务失败')
        }
      } catch (error) {
        console.error('Create translation task error:', error)
        this.error = error.message || '创建任务失败'
        throw error
      }
    },

    // 上传文件
    async uploadFile(filePath: string, taskData: any) {
      try {
        this.uploadProgress = 0
        this.error = null

        const token = uni.getStorageSync('token')
        if (!token) {
          throw new Error('用户未登录')
        }

        const response = await uni.uploadFile({
          url: `${this.getBaseUrl()}/translation/upload`,
          filePath: filePath,
          name: 'file',
          formData: {
            file_type: taskData.file_type,
            original_filename: taskData.original_filename,
            file_size: taskData.file_size
          },
          header: {
            'Authorization': `Bearer ${token}`
          },
          success: (res) => {
            console.log('Upload success:', res)
          },
          fail: (error) => {
            console.error('Upload failed:', error)
            this.error = '文件上传失败'
            throw new Error('文件上传失败')
          }
        })

        if (response.statusCode === 200) {
          const data = JSON.parse(response.data)
          if (data.success) {
            return { success: true, data: data.data }
          } else {
            throw new Error(data.message || '上传失败')
          }
        } else {
          throw new Error('上传失败')
        }
      } catch (error) {
        console.error('Upload file error:', error)
        this.error = error.message || '文件上传失败'
        throw error
      }
    },

    // 开始翻译
    async startTranslation(taskId: string, options: {
      language?: string
      provider?: string
    } = {}) {
      try {
        if (!this.currentTask || this.currentTask.task_id !== taskId) {
          throw new Error('无效的任务ID')
        }

        this.isProcessing = true
        this.processingProgress = 0
        this.error = null

        const token = uni.getStorageSync('token')
        if (!token) {
          throw new Error('用户未登录')
        }

        const response = await uni.request({
          url: `${this.getBaseUrl()}/translation/start`,
          method: 'POST',
          data: {
            task_id: taskId,
            language: options.language || 'zh-CN',
            provider: options.provider || 'alibaba'
          },
          header: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          }
        })

        if (response.statusCode === 200 && response.data.success) {
          // 开始轮询状态
          this.startStatusPolling(taskId)
          return { success: true, data: response.data.data }
        } else {
          throw new Error(response.data.message || '开始翻译失败')
        }
      } catch (error) {
        console.error('Start translation error:', error)
        this.isProcessing = false
        this.error = error.message || '开始翻译失败'
        throw error
      }
    },

    // 轮询翻译状态
    async startStatusPolling(taskId: string) {
      const pollInterval = setInterval(async () => {
        try {
          const status = await this.getTranslationStatus(taskId)
          
          if (status.processing_status === 'completed' || 
              status.processing_status === 'failed') {
            clearInterval(pollInterval)
            this.isProcessing = false
            this.processingProgress = status.processing_status === 'completed' ? 100 : 0
          } else if (status.progress_percentage) {
            this.processingProgress = status.progress_percentage
          }
        } catch (error) {
          console.error('Status polling error:', error)
          clearInterval(pollInterval)
          this.isProcessing = false
        }
      }, 2000)

      // 存储轮询ID以便清理
      this.pollingInterval = pollInterval
    },

    // 获取翻译状态
    async getTranslationStatus(taskId: string) {
      try {
        const token = uni.getStorageSync('token')
        if (!token) {
          throw new Error('用户未登录')
        }

        const response = await uni.request({
          url: `${this.getBaseUrl()}/translation/${taskId}/status`,
          method: 'GET',
          header: {
            'Authorization': `Bearer ${token}`
          }
        })

        if (response.statusCode === 200) {
          const statusData = response.data
          if (this.currentTask && this.currentTask.task_id === taskId) {
            this.currentTask = { ...this.currentTask, ...statusData }
          }
          return statusData
        } else {
          throw new Error('获取状态失败')
        }
      } catch (error) {
        console.error('Get translation status error:', error)
        throw error
      }
    },

    // 获取翻译历史
    async getTranslationHistory(params: TranslationHistoryParams = {}) {
      try {
        const token = uni.getStorageSync('token')
        if (!token) {
          throw new Error('用户未登录')
        }

        const response = await uni.request({
          url: `${this.getBaseUrl()}/translation/history`,
          method: 'GET',
          data: {
            limit: params.limit || 20,
            offset: params.offset || 0,
            status: params.status
          },
          header: {
            'Authorization': `Bearer ${token}`
          }
        })

        if (response.statusCode === 200 && response.data.success) {
          this.taskHistory = response.data.data || []
          return response.data
        } else {
          throw new Error(response.data.message || '获取历史记录失败')
        }
      } catch (error) {
        console.error('Get translation history error:', error)
        throw error
      }
    },

    // 取消翻译
    async cancelTranslation(taskId: string) {
      try {
        if (this.pollingInterval) {
          clearInterval(this.pollingInterval)
          this.pollingInterval = null
        }

        this.isProcessing = false
        this.processingProgress = 0

        // 这里可以调用取消API
        console.log('Translation cancelled:', taskId)
        
        return { success: true }
      } catch (error) {
        console.error('Cancel translation error:', error)
        throw error
      }
    },

    // 清除错误
    clearError() {
      this.error = null
    },

    // 重置状态
    resetState() {
      this.currentTask = null
      this.isProcessing = false
      this.processingProgress = 0
      this.uploadProgress = 0
      this.error = null
      
      if (this.pollingInterval) {
        clearInterval(this.pollingInterval)
        this.pollingInterval = null
      }
    },

    // 获取API基础URL
    getBaseUrl(): string {
      return localStorage.getItem('baseUrl') || 'http://localhost:8000/api/v1'
    }
  }
})