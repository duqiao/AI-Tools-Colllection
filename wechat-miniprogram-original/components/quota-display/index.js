// components/quota-display/index.js
Component({
  /**
   * Component properties
   */
  properties: {
    // 是否显示详细信息
    showDetails: {
      type: Boolean,
      value: false
    },
    // 自定义样式类
    customClass: {
      type: String,
      value: ''
    }
  },

  /**
   * Component initial data
   */
  data: {
    quotaInfo: null,
    loading: true,
    error: null
  },

  /**
   * Component lifecycle
   */
  lifetimes: {
    attached() {
      this.loadQuotaStatus();
    }
  },

  /**
   * Component methods
   */
  methods: {
    /**
     * 加载配额状态
     */
    async loadQuotaStatus() {
      try {
        this.setData({ loading: true, error: null });
        
        const app = getApp();
        if (!app.globalData.isLoggedIn) {
          this.setData({
            loading: false,
            error: '请先登录'
          });
          return;
        }

        const res = await wx.request({
          url: `${app.globalData.baseUrl}/api/v1/quota/status`,
          method: 'GET',
          header: {
            'Authorization': `Bearer ${app.globalData.token}`
          }
        });

        if (res.statusCode === 200 && res.data) {
          this.setData({
            quotaInfo: res.data,
            loading: false
          });
        } else {
          this.setData({
            loading: false,
            error: '获取配额信息失败'
          });
        }
      } catch (error) {
        console.error('Load quota status error:', error);
        this.setData({
          loading: false,
          error: '网络请求失败'
        });
      }
    },

    /**
     * 刷新配额状态
     */
    refreshQuota() {
      this.loadQuotaStatus();
    },

    /**
     * 显示详细信息
     */
    showDetails() {
      this.setData({
        showDetails: true
      });
    },

    /**
     * 隐藏详细信息
     */
    hideDetails() {
      this.setData({
        showDetails: false
      });
    },

    /**
     * 点击升级按钮
     */
    onUpgradeTap() {
      this.triggerEvent('upgrade', {
        quotaInfo: this.data.quotaInfo
      });
    },

    /**
     * 点击查看详情
     */
    onDetailsTap() {
      this.showDetails();
      this.triggerEvent('details', {
        quotaInfo: this.data.quotaInfo
      });
    }
  }
});