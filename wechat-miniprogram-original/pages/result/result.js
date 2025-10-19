// pages/result/result.js
const app = getApp()

Page({
  data: {
    // Translation data
    taskId: '',
    translationData: null,
    
    // UI state
    loading: true,
    error: false,
    errorMessage: '',
    
    // Text editing
    isEditing: false,
    editedText: '',
    originalText: '',
    
    // Actions
    copyingText: false,
    sharingResult: false,
    
    // Related translations
    canShare: true,
    canEdit: true
  },

  onLoad(options) {
    console.log('Result page loaded with options:', options)
    
    if (options.task_id) {
      this.setData({
        taskId: options.task_id
      })
      this.loadTranslationResult(options.task_id)
    } else {
      this.showError('缺少翻译任务ID')
    }
  },

  onShow() {
    // Refresh data when page is shown
    if (this.data.taskId) {
      this.loadTranslationResult(this.data.taskId)
    }
  },

  // Load translation result
  loadTranslationResult(taskId) {
    this.setData({
      loading: true,
      error: false
    })

    const token = wx.getStorageSync('token')
    if (!token) {
      this.showError('请先登录')
      return
    }

    wx.request({
      url: `${app.globalData.apiBaseUrl}/translation/${taskId}/result`,
      method: 'GET',
      header: {
        'Authorization': `Bearer ${token}`
      },
      success: (res) => {
        if (res.statusCode === 200 && res.data.success) {
          this.handleResultLoaded(res.data.data)
        } else {
          this.showError(res.data.message || '获取翻译结果失败')
        }
      },
      fail: (error) => {
        console.error('Failed to load translation result:', error)
        this.showError('网络错误，请重试')
      }
    })
  },

  // Handle successful result loading
  handleResultLoaded(data) {
    console.log('Translation result loaded:', data)
    
    this.setData({
      translationData: data,
      loading: false,
      error: false,
      originalText: data.transcribed_text || '',
      editedText: data.transcribed_text || ''
    })
  },

  // Handle errors
  showError(message) {
    this.setData({
      loading: false,
      error: true,
      errorMessage: message
    })
  },

  // Retry loading result
  retryLoading() {
    if (this.data.taskId) {
      this.loadTranslationResult(this.data.taskId)
    }
  },

  // Start editing text
  startEditing() {
    this.setData({
      isEditing: true,
      editedText: this.data.originalText
    })
  },

  // Handle text input
  onTextInput(e) {
    this.setData({
      editedText: e.detail.value
    })
  },

  // Save edited text
  saveEdit() {
    const editedText = this.data.editedText.trim()
    
    if (!editedText) {
      wx.showToast({
        title: '文本不能为空',
        icon: 'none'
      })
      return
    }

    if (editedText === this.data.originalText) {
      // No changes made
      this.cancelEdit()
      return
    }

    // Update local data (in production, this would save to server)
    this.setData({
      isEditing: false,
      'translationData.transcribed_text': editedText,
      originalText: editedText
    })

    wx.showToast({
      title: '保存成功',
      icon: 'success'
    })
  },

  // Cancel editing
  cancelEdit() {
    this.setData({
      isEditing: false,
      editedText: this.data.originalText
    })
  },

  // Copy text to clipboard
  copyText() {
    const text = this.data.translationData?.transcribed_text || ''
    
    if (!text) {
      wx.showToast({
        title: '没有可复制的文本',
        icon: 'none'
      })
      return
    }

    wx.setClipboardData({
      data: text,
      success: () => {
        this.setData({ copyingText: true })
        wx.showToast({
          title: '已复制到剪贴板',
          icon: 'success'
        })
        
        // Reset copying state after delay
        setTimeout(() => {
          this.setData({ copyingText: false })
        }, 2000)
      },
      fail: () => {
        wx.showToast({
          title: '复制失败',
          icon: 'none'
        })
      }
    })
  },

  // Share translation result
  shareResult() {
    const translationData = this.data.translationData
    
    if (!translationData || !translationData.transcribed_text) {
      wx.showToast({
        title: '没有可分享的内容',
        icon: 'none'
      })
      return
    }

    this.setData({ sharingResult: true })

    // Generate share content
    const shareContent = {
      title: '语音翻译结果',
      desc: `识别文本: ${translationData.transcribed_text.substring(0, 50)}${translationData.transcribed_text.length > 50 ? '...' : ''}`,
      path: `/pages/result/result?task_id=${this.data.taskId}`,
      imageUrl: '/static/share/result.png'
    }

    // Show share options
    wx.showActionSheet({
      itemList: ['分享给微信好友', '保存到相册'],
      success: (res) => {
        if (res.tapIndex === 0) {
          // Share to WeChat friends
          this.shareToWeChat(shareContent)
        } else if (res.tapIndex === 1) {
          // Save to album
          this.saveToAlbum()
        }
      },
      complete: () => {
        this.setData({ sharingResult: false })
      }
    })
  },

  // Share to WeChat
  shareToWeChat(shareContent) {
    // This would typically trigger WeChat's share functionality
    // For now, just show a success message
    wx.showToast({
      title: '分享成功',
      icon: 'success'
    })
  },

  // Save to album (save text as image)
  saveToAlbum() {
    // In a real implementation, this would generate an image
    // from the text and save it to the photo album
    wx.showToast({
      title: '保存成功',
      icon: 'success'
    })
  },

  // Go back to upload page
  goBack() {
    wx.navigateBack()
  },

  // Upload new file
  uploadNew() {
    wx.redirectTo({
      url: '/pages/upload/upload'
    })
  },

  // View translation history
  viewHistory() {
    wx.switchTab({
      url: '/pages/history/history'
    })
  },

  // Show text details
  showTextDetails() {
    const translationData = this.data.translationData
    
    if (!translationData) return

    const details = [
      `字数: ${translationData.word_count || 0}`,
      `置信度: ${Math.round((translationData.confidence_score || 0) * 100)}%`,
      `处理时间: ${translationData.processing_time || 0}秒`,
      `服务商: ${translationData.service_provider || '未知'}`
    ]

    wx.showModal({
      title: '翻译详情',
      content: details.join('\n'),
      showCancel: false,
      confirmText: '确定'
    })
  },

  // Provide feedback on translation quality
  provideFeedback() {
    wx.showActionSheet({
      itemList: ['很满意', '满意', '一般', '不满意', '很差'],
      success: (res) => {
        const feedbackOptions = ['很满意', '满意', '一般', '不满意', '很差']
        const feedback = feedbackOptions[res.tapIndex]
        
        this.submitFeedback(feedback)
      }
    })
  },

  // Submit feedback
  submitFeedback(feedback) {
    const token = wx.getStorageSync('token')
    if (!token) {
      wx.showToast({
        title: '请先登录',
        icon: 'none'
      })
      return
    }

    wx.request({
      url: `${app.globalData.apiBaseUrl}/translation/${this.data.taskId}/feedback`,
      method: 'POST',
      header: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      data: {
        feedback: feedback,
        rating: this.getRatingFromFeedback(feedback)
      },
      success: () => {
        wx.showToast({
          title: '感谢您的反馈',
          icon: 'success'
        })
      },
      fail: () => {
        wx.showToast({
          title: '反馈提交失败',
          icon: 'none'
        })
      }
    })
  },

  // Convert feedback to rating (1-5)
  getRatingFromFeedback(feedback) {
    const ratingMap = {
      '很满意': 5,
      '满意': 4,
      '一般': 3,
      '不满意': 2,
      '很差': 1
    }
    return ratingMap[feedback] || 3
  },

  // Report issue with translation
  reportIssue() {
    wx.showActionSheet({
      itemList: ['识别错误', '内容不全', '质量问题', '其他问题'],
      success: (res) => {
        const issueTypes = ['识别错误', '内容不全', '质量问题', '其他问题']
        const issueType = issueTypes[res.tapIndex]
        
        this.reportTranslationIssue(issueType)
      }
    })
  },

  // Report translation issue
  reportTranslationIssue(issueType) {
    wx.showModal({
      title: '问题报告',
      content: `请简要描述${issueType}的具体情况`,
      editable: true,
      placeholderText: '请输入问题描述...',
      success: (res) => {
        if (res.confirm && res.content) {
          this.submitIssueReport(issueType, res.content)
        }
      }
    })
  },

  // Submit issue report
  submitIssueReport(issueType, description) {
    const token = wx.getStorageSync('token')
    if (!token) {
      wx.showToast({
        title: '请先登录',
        icon: 'none'
      })
      return
    }

    wx.request({
      url: `${app.globalData.apiBaseUrl}/translation/${this.data.taskId}/report`,
      method: 'POST',
      header: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      data: {
        issue_type: issueType,
        description: description
      },
      success: () => {
        wx.showToast({
          title: '问题已报告',
          icon: 'success'
        })
      },
      fail: () => {
        wx.showToast({
          title: '报告失败',
          icon: 'none'
        })
      }
    })
  },

  // On share app message
  onShareAppMessage() {
    const translationData = this.data.translationData
    
    if (!translationData || !translationData.transcribed_text) {
      return {
        title: '语音翻译结果',
        desc: '查看我的语音翻译结果',
        path: `/pages/result/result?task_id=${this.data.taskId}`
      }
    }

    return {
      title: '语音翻译结果',
      desc: translationData.transcribed_text.substring(0, 50) + 
             (translationData.transcribed_text.length > 50 ? '...' : ''),
      path: `/pages/result/result?task_id=${this.data.taskId}`,
      imageUrl: '/static/share/result.png'
    }
  },

  // On share to timeline
  onShareTimeline() {
    return {
      title: '语音翻译结果',
      query: `task_id=${this.data.taskId}`,
      imageUrl: '/static/share/result.png'
    }
  }
})