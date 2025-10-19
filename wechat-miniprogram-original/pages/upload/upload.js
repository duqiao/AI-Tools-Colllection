// pages/upload/upload.js
const app = getApp()

Page({
  data: {
    // File upload state
    selectedFile: null,
    uploading: false,
    uploadProgress: 0,
    
    // Translation state
    translationTask: null,
    processing: false,
    processingProgress: 0,
    processingStatus: '',
    
    // UI state
    showFileSelector: true,
    showUploading: false,
    showProcessing: false,
    showResult: false,
    showError: false,
    
    // Error handling
    errorMessage: '',
    retryCount: 0,
    maxRetries: 3,
    
    // File validation
    maxFileSize: 200 * 1024 * 1024, // 200MB for videos
    supportedFormats: [
      'mp3', 'wav', 'aac', 'm4a', 'flac', 'ogg', // Audio
      'mp4', 'avi', 'mov', 'wmv', 'flv', 'webm'  // Video
    ],
    
    // User quota info
    quotaInfo: null,
    showUpgradePrompt: false,
    upgradePromptType: 'upgrade',
    currentQuotaInfo: null
  },

  onLoad() {
    console.log('Upload page loaded')
    this.loadUserQuota()
  },

  onShow() {
    // Reset state when page is shown
    this.resetState()
    this.loadUserQuota()
  },

  // Load user quota information
  loadUserQuota() {
    try {
      const quotaInfo = wx.getStorageSync('quota_info')
      if (quotaInfo) {
        this.setData({
          quotaInfo: quotaInfo
        })
      }
    } catch (error) {
      console.error('Failed to load quota info:', error)
    }
  },

  // Reset page state
  resetState() {
    this.setData({
      selectedFile: null,
      uploading: false,
      uploadProgress: 0,
      translationTask: null,
      processing: false,
      processingProgress: 0,
      processingStatus: '',
      showFileSelector: true,
      showUploading: false,
      showProcessing: false,
      showResult: false,
      showError: false,
      errorMessage: '',
      retryCount: 0
    })
  },

  // Check if user has quota available
  checkQuotaAvailable() {
    if (!this.data.quotaInfo) {
      return true // Allow upload for testing
    }
    
    const remainingQuota = this.data.quotaInfo.remaining || 0
    if (remainingQuota <= 0) {
      this.showUpgradePrompt()
      return false
    }
    
    return true
  },

  // Show upgrade prompt when quota is exhausted
  showUpgradePrompt() {
    this.setData({
      showUpgradePrompt: true
    })
  },

  // Hide upgrade prompt
  hideUpgradePrompt() {
    this.setData({
      showUpgradePrompt: false
    })
  },

  // Navigate to upgrade page
  goToUpgrade() {
    wx.navigateTo({
      url: '/pages/vip/vip'
    })
  },

  // File selection methods
  chooseMedia() {
    if (!this.checkQuotaAvailable()) {
      return
    }

    wx.chooseMedia({
      count: 1,
      mediaType: ['mix'],
      sourceType: ['album', 'camera'],
      maxDuration: 300, // 5 minutes max
      camera: 'back',
      success: (res) => {
        this.handleFileSelection(res.tempFiles[0])
      },
      fail: (error) => {
        console.error('File selection failed:', error)
        this.showError('文件选择失败，请重试')
      }
    })
  },

  chooseMessageFile() {
    if (!this.checkQuotaAvailable()) {
      return
    }

    wx.chooseMessageFile({
      count: 1,
      type: 'file',
      success: (res) => {
        this.handleFileSelection(res.tempFiles[0])
      },
      fail: (error) => {
        console.error('Message file selection failed:', error)
        this.showError('文件选择失败，请重试')
      }
    })
  },

  // Handle file selection
  handleFileSelection(file) {
    console.log('File selected:', file)
    
    // Validate file
    const validationResult = this.validateFile(file)
    if (!validationResult.valid) {
      this.showError(validationResult.error)
      return
    }

    // Store selected file
    this.setData({
      selectedFile: {
        ...file,
        type: this.getFileType(file.path),
        size: file.size,
        duration: file.duration || null
      },
      showFileSelector: false,
      showError: false,
      errorMessage: ''
    })
  },

  // Validate selected file
  validateFile(file) {
    // Check file size
    if (file.size > this.data.maxFileSize) {
      return {
        valid: false,
        error: `文件太大，最大支持${Math.round(this.data.maxFileSize / 1024 / 1024)}MB`
      }
    }

    // Check file format
    const fileExtension = this.getFileExtension(file.path)
    if (!this.data.supportedFormats.includes(fileExtension)) {
      return {
        valid: false,
        error: `不支持的文件格式: ${fileExtension}`
      }
    }

    return { valid: true }
  },

  // Get file type from path
  getFileType(filePath) {
    const videoExtensions = ['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm']
    const audioExtensions = ['mp3', 'wav', 'aac', 'm4a', 'flac', 'ogg']
    
    const extension = this.getFileExtension(filePath)
    
    if (videoExtensions.includes(extension)) {
      return 'video'
    } else if (audioExtensions.includes(extension)) {
      return 'audio'
    }
    
    return 'unknown'
  },

  // Get file extension from path
  getFileExtension(filePath) {
    return filePath.split('.').pop().toLowerCase()
  },

  // Start file upload
  startUpload() {
    if (!this.data.selectedFile) {
      this.showError('请先选择文件')
      return
    }

    if (!this.checkQuotaAvailable()) {
      return
    }

    this.setData({
      uploading: true,
      showUploading: true,
      uploadProgress: 0
    })

    this.uploadFile()
  },

  // Upload file to server
  uploadFile() {
    const token = wx.getStorageSync('token')
    if (!token) {
      this.showError('请先登录')
      return
    }

    wx.uploadFile({
      url: `${app.globalData.apiBaseUrl}/translation/upload`,
      filePath: this.data.selectedFile.path,
      name: 'file',
      formData: {
        file_type: this.data.selectedFile.type,
        original_filename: this.data.selectedFile.name
      },
      header: {
        'Authorization': `Bearer ${token}`
      },
      success: (res) => {
        try {
          const data = JSON.parse(res.data)
          if (data.success) {
            this.handleUploadSuccess(data.data)
          } else {
            this.showError(data.message || '上传失败')
          }
        } catch (error) {
          console.error('Upload response parse error:', error)
          this.showError('上传响应解析失败')
        }
      },
      fail: (error) => {
        console.error('Upload failed:', error)
        this.showError('文件上传失败，请检查网络连接')
      }
    })
  },

  // Handle upload success
  handleUploadSuccess(uploadData) {
    console.log('Upload success:', uploadData)
    
    this.setData({
      uploading: false,
      showUploading: false,
      translationTask: uploadData.task_id,
      showProcessing: true,
      processing: true,
      processingProgress: 0,
      processingStatus: '准备开始翻译...'
    })

    // Start processing
    this.startTranslation(uploadData.task_id)
  },

  // Start translation processing
  startTranslation(taskId) {
    const token = wx.getStorageSync('token')
    if (!token) {
      this.showError('请先登录')
      return
    }

    wx.request({
      url: `${app.globalData.apiBaseUrl}/translation/start`,
      method: 'POST',
      header: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      data: {
        task_id: taskId,
        language: 'zh-CN',
        provider: 'alibaba'
      },
      success: (res) => {
        if (res.statusCode === 200 && res.data.success) {
          this.handleTranslationStart(res.data.data)
        } else {
          this.showError(res.data.message || '翻译启动失败')
        }
      },
      fail: (error) => {
        console.error('Translation start failed:', error)
        this.showError('翻译启动失败，请重试')
      }
    })
  },

  // Handle translation start
  handleTranslationStart(translationData) {
    console.log('Translation started:', translationData)
    
    this.setData({
      processingStatus: translationData.status || '正在处理中...'
    })

    // Start polling for status
    this.startStatusPolling(translationData.task_id)
  },

  // Start polling for translation status
  startStatusPolling(taskId) {
    const pollInterval = setInterval(() => {
      this.checkTranslationStatus(taskId, pollInterval)
    }, 2000) // Poll every 2 seconds

    // Store interval ID for cleanup
    this.statusPollInterval = pollInterval
  },

  // Check translation status
  checkTranslationStatus(taskId, pollInterval) {
    const token = wx.getStorageSync('token')
    if (!token) {
      clearInterval(pollInterval)
      this.showError('请先登录')
      return
    }

    wx.request({
      url: `${app.globalData.apiBaseUrl}/translation/${taskId}/status`,
      method: 'GET',
      header: {
        'Authorization': `Bearer ${token}`
      },
      success: (res) => {
        if (res.statusCode === 200) {
          this.handleStatusUpdate(res.data)
          
          // Stop polling if completed or failed
          if (res.data.processing_status === 'completed' || 
              res.data.processing_status === 'failed') {
            clearInterval(pollInterval)
          }
        }
      },
      fail: (error) => {
        console.error('Status check failed:', error)
      }
    })
  },

  // Handle status update
  handleStatusUpdate(statusData) {
    const status = statusData.processing_status
    const progress = statusData.progress_percentage || 0

    this.setData({
      processingProgress: progress,
      processingStatus: this.getStatusText(status)
    })

    if (status === 'completed') {
      this.handleTranslationCompleted(statusData)
    } else if (status === 'failed') {
      this.handleTranslationFailed(statusData)
    }
  },

  // Get status text in Chinese
  getStatusText(status) {
    const statusMap = {
      'pending': '等待处理',
      'processing': '正在翻译',
      'completed': '翻译完成',
      'failed': '翻译失败'
    }
    return statusMap[status] || status
  },

  // Handle translation completed
  handleTranslationCompleted(statusData) {
    console.log('Translation completed:', statusData)
    
    this.setData({
      processing: false,
      showProcessing: false,
      showResult: true,
      processingStatus: '翻译完成'
    })

    // Navigate to result page
    setTimeout(() => {
      wx.navigateTo({
        url: `/pages/result/result?task_id=${this.data.translationTask}`
      })
    }, 1500)
  },

  // Handle translation failed
  handleTranslationFailed(statusData) {
    console.error('Translation failed:', statusData)
    
    const errorMessage = statusData.error_message || '翻译失败，请重试'
    
    // Check if this is a quota-related error
    if (errorMessage.includes('quota') || errorMessage.includes('配额') || errorMessage.includes('次数不足')) {
      this.setData({
        processing: false,
        showProcessing: false,
        showUpgradePrompt: true,
        upgradePromptType: 'exhausted'
      })
    } else {
      this.setData({
        processing: false,
        showProcessing: false,
        showError: true,
        errorMessage: errorMessage
      })
    }
  },

  // Retry translation
  retryTranslation() {
    if (this.data.retryCount >= this.data.maxRetries) {
      this.showError('重试次数过多，请选择其他文件')
      return
    }

    this.setData({
      retryCount: this.data.retryCount + 1,
      showError: false,
      errorMessage: '',
      showProcessing: true,
      processing: true,
      processingProgress: 0,
      processingStatus: '重新开始翻译...'
    })

    // Restart translation
    this.startTranslation(this.data.translationTask)
  },

  // Show error message
  showError(message) {
    this.setData({
      showError: true,
      errorMessage: message,
      uploading: false,
      processing: false,
      showUploading: false,
      showProcessing: false
    })
  },

  // Hide error message
  hideError() {
    this.setData({
      showError: false,
      errorMessage: ''
    })
  },

  // Cancel current operation
  cancelOperation() {
    // Clear any ongoing polling
    if (this.statusPollInterval) {
      clearInterval(this.statusPollInterval)
    }

    // Reset state
    this.resetState()
  },

  // Go back to file selection
  selectNewFile() {
    this.resetState()
  },

  // Navigate to history page
  goToHistory() {
    wx.switchTab({
      url: '/pages/history/history'
    })
  },

  // Preview selected file (for images/videos)
  previewFile() {
    if (!this.data.selectedFile) return

    if (this.data.selectedFile.type === 'image') {
      wx.previewImage({
        urls: [this.data.selectedFile.path],
        current: this.data.selectedFile.path
      })
    } else if (this.data.selectedFile.type === 'video') {
      wx.previewMedia({
        sources: [{
          url: this.data.selectedFile.path,
          type: 'video'
        }]
      })
    }
  },

  // Quota component event handlers
  onQuotaUpgrade(e) {
    const quotaInfo = e.detail.quotaInfo
    console.log('Quota upgrade requested:', quotaInfo)
    
    this.setData({
      showUpgradePrompt: true,
      upgradePromptType: 'upgrade',
      currentQuotaInfo: quotaInfo
    })
  },

  onQuotaDetails(e) {
    const quotaInfo = e.detail.quotaInfo
    console.log('Quota details requested:', quotaInfo)
    // Can navigate to a detailed quota page if needed
  },

  // Upgrade prompt component event handlers
  onUpgradeClose() {
    this.setData({
      showUpgradePrompt: false
    })
  },

  onUpgradeConfirm(e) {
    const plan = e.detail.plan
    console.log('Upgrade confirmed:', plan)
    
    // Here you would integrate with payment service
    wx.showToast({
      title: '正在跳转到支付...',
      icon: 'none',
      duration: 2000
    })

    // For now, just close the prompt
    setTimeout(() => {
      this.setData({
        showUpgradePrompt: false
      })
    }, 2000)
  },

  onUpgradeSkip() {
    this.setData({
      showUpgradePrompt: false
    })
  },

  onUnload() {
    // Clean up polling when page unloads
    if (this.statusPollInterval) {
      clearInterval(this.statusPollInterval)
    }
  }
})