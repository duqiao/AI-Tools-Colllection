// pages/index/index.js
const app = getApp()

Page({
  data: {
    // User info
    userInfo: null,
    isLoggedIn: false,
    
    // Quota info
    quotaInfo: null,
    
    // Quick actions
    recentTranslations: [],
    showQuickActions: false,
    
    // App info
    appVersion: '1.0.0'
  },

  onLoad() {
    console.log('Index page loaded')
    this.checkLoginStatus()
    this.loadRecentTranslations()
  },

  onShow() {
    // Refresh data when page is shown
    this.checkLoginStatus()
    this.loadRecentTranslations()
  },

  // Check login status
  checkLoginStatus() {
    const token = wx.getStorageSync('token')
    const userInfo = wx.getStorageSync('userInfo')
    const quotaInfo = wx.getStorageSync('quota_info')
    
    this.setData({
      isLoggedIn: !!token,
      userInfo: userInfo || null,
      quotaInfo: quotaInfo || null
    })
  },

  // Load recent translations
  loadRecentTranslations() {
    if (!this.data.isLoggedIn) {
      return
    }

    const token = wx.getStorageSync('token')
    if (!token) {
      return
    }

    wx.request({
      url: `${app.globalData.apiBaseUrl}/translation/history`,
      method: 'GET',
      header: {
        'Authorization': `Bearer ${token}`
      },
      data: {
        limit: 3
      },
      success: (res) => {
        if (res.statusCode === 200 && res.data.success) {
          this.setData({
            recentTranslations: res.data.data || [],
            showQuickActions: res.data.data && res.data.data.length > 0
          })
        }
      },
      fail: (error) => {
        console.error('Failed to load recent translations:', error)
      }
    })
  },

  // Navigate to upload page
  goToUpload() {
    wx.navigateTo({
      url: '/pages/upload/upload'
    })
  },

  // Navigate to history page
  goToHistory() {
    wx.switchTab({
      url: '/pages/history/history'
    })
  },

  // Navigate to profile page
  goToProfile() {
    wx.switchTab({
      url: '/pages/profile/profile'
    })
  },

  // Navigate to VIP page
  goToVip() {
    wx.navigateTo({
      url: '/pages/vip/vip'
    })
  },

  // Handle login
  handleLogin() {
    // In a real implementation, this would trigger WeChat login
    // For now, just show a message
    wx.showToast({
      title: '请先完成登录流程',
      icon: 'none',
      duration: 2000
    })
  },

  // View translation details
  viewTranslationDetail(translation) {
    wx.navigateTo({
      url: `/pages/result/result?task_id=${translation.task_id}`
    })
  },

  // Show app features
  showFeatures() {
    wx.showActionSheet({
      itemList: [
        '支持多种音频格式',
        '支持视频文件翻译',
        '高质量语音识别',
        '实时翻译进度',
        '翻译结果编辑',
        '分享功能'
      ],
      success: (res) => {
        console.log('Selected feature:', res.tapIndex)
      }
    })
  },

  // Show help
  showHelp() {
    wx.showModal({
      title: '使用帮助',
      content: '1. 点击"开始翻译"上传音频或视频文件\n2. 等待系统自动识别语音内容\n3. 查看翻译结果并可编辑分享\n4. 免费用户每月1次翻译机会',
      showCancel: false,
      confirmText: '知道了'
    })
  },

  // Show about
  showAbout() {
    wx.showModal({
      title: '关于我们',
      content: `媒体翻译器 v${this.data.appVersion}\n\n专业的语音识别服务\n支持多种媒体格式\n准确率高，处理快速`,
      showCancel: false,
      confirmText: '确定'
    })
  },

  // Check app update
  checkUpdate() {
    if (wx.canIUse('getUpdateManager')) {
      const updateManager = wx.getUpdateManager()
      
      updateManager.onCheckForUpdate((res) => {
        console.log('Update available:', res.hasUpdate)
        
        if (res.hasUpdate) {
          updateManager.onUpdateReady(() => {
            wx.showModal({
              title: '更新提示',
              content: '新版本已经准备好，是否重启应用？',
              success(res) {
                if (res.confirm) {
                  updateManager.applyUpdate()
                }
              }
            })
          })
        } else {
          wx.showToast({
            title: '已是最新版本',
            icon: 'success'
          })
        }
      })
    }
  },

  // On share app message
  onShareAppMessage() {
    return {
      title: '媒体翻译器 - 语音识别转文字',
      desc: '专业的语音识别服务，支持多种音频视频格式',
      path: '/pages/index/index',
      imageUrl: '/static/share/app.png'
    }
  },

  // On share to timeline
  onShareTimeline() {
    return {
      title: '媒体翻译器 - 专业语音识别服务',
      imageUrl: '/static/share/app.png'
    }
  }
})