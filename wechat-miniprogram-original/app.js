// app.js - WeChat Mini-Program Entry Point

App({
  onLaunch() {
    console.log('WeChat Media Translator Mini-Program launched')
    
    // Check for updates
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
        }
      })
    }
    
    // Initialize global data
    this.globalData = {
      apiBaseUrl: process.env.NODE_ENV === 'development' 
        ? 'http://localhost:8000/api/v1'
        : 'https://api.yourdomain.com/api/v1',
      userInfo: null,
      token: null,
      isLoggedIn: false
    }
  },

  onShow() {
    console.log('App shown')
    // Check login status
    this.checkLoginStatus()
  },

  onHide() {
    console.log('App hidden')
  },

  onError(msg) {
    console.error('App error:', msg)
  },

  methods: {
    checkLoginStatus() {
      const token = wx.getStorageSync('token')
      if (token) {
        this.globalData.token = token
        this.globalData.isLoggedIn = true
        // Verify token with backend
        this.verifyToken(token)
      }
    },

    async verifyToken(token) {
      try {
        const res = await wx.request({
          url: `${this.globalData.apiBaseUrl}/auth/me`,
          method: 'GET',
          header: {
            'Authorization': `Bearer ${token}`
          }
        })
        
        if (res.statusCode === 200 && res.data.success) {
          this.globalData.userInfo = res.data.data
          console.log('User logged in:', res.data.data)
        } else {
          // Token invalid, clear local storage
          wx.removeStorageSync('token')
          this.globalData.token = null
          this.globalData.isLoggedIn = false
          this.globalData.userInfo = null
        }
      } catch (error) {
        console.error('Token verification failed:', error)
      }
    },

    setUserInfo(userInfo) {
      this.globalData.userInfo = userInfo
    },

    setToken(token) {
      this.globalData.token = token
      this.globalData.isLoggedIn = true
      wx.setStorageSync('token', token)
    },

    logout() {
      wx.removeStorageSync('token')
      this.globalData.token = null
      this.globalData.isLoggedIn = false
      this.globalData.userInfo = null
    }
  }
})