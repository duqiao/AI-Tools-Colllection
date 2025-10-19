// components/upgrade-prompt/index.js
Component({
  /**
   * Component properties
   */
  properties: {
    // 是否显示弹窗
    show: {
      type: Boolean,
      value: false
    },
    // 配额信息
    quotaInfo: {
      type: Object,
      value: null
    },
    // 弹窗类型：'exhausted', 'warning', 'upgrade'
    type: {
      type: String,
      value: 'upgrade'
    },
    // 自定义标题
    title: {
      type: String,
      value: ''
    },
    // 自定义消息
    message: {
      type: String,
      value: ''
    }
  },

  /**
   * Component initial data
   */
  data: {
    plans: [
      {
        id: 'basic',
        name: '基础版',
        price: '9.9',
        quota: 10,
        period: '月',
        features: ['每月10次翻译', '基础语音识别', '标准处理速度'],
        recommended: false
      },
      {
        id: 'pro',
        name: '专业版',
        price: '29.9',
        quota: 50,
        period: '月',
        features: ['每月50次翻译', '高精度语音识别', '优先处理', '支持更多格式'],
        recommended: true
      },
      {
        id: 'premium',
        name: '高级版',
        price: '99.9',
        quota: 200,
        period: '月',
        features: ['每月200次翻译', '最高精度识别', '极速处理', '全部格式支持', '客服支持'],
        recommended: false
      }
    ],
    selectedPlan: null,
    loading: false
  },

  /**
   * Component observers
   */
  observers: {
    'show': function(show) {
      if (show) {
        this.setData({
          selectedPlan: this.data.plans.find(plan => plan.recommended) || this.data.plans[0]
        });
      }
    }
  },

  /**
   * Component methods
   */
  methods: {
    /**
     * 阻止冒泡
     */
    stopPropagation() {
      // 阻止点击遮罩层关闭弹窗
    },

    /**
     * 关闭弹窗
     */
    onClose() {
      this.setData({
        show: false
      });
      this.triggerEvent('close');
    },

    /**
     * 选择套餐
     */
    onPlanSelect(e) {
      const planId = e.currentTarget.dataset.plan;
      const plan = this.data.plans.find(p => p.id === planId);
      this.setData({
        selectedPlan: plan
      });
    },

    /**
     * 立即升级
     */
    async onUpgrade() {
      if (!this.data.selectedPlan) {
        wx.showToast({
          title: '请选择套餐',
          icon: 'none'
        });
        return;
      }

      try {
        this.setData({ loading: true });

        // 触发升级事件
        this.triggerEvent('upgrade', {
          plan: this.data.selectedPlan,
          quotaInfo: this.data.quotaInfo
        });

        // 这里可以集成支付流程
        // await this.processPayment(this.data.selectedPlan);

        wx.showToast({
          title: '升级成功',
          icon: 'success'
        });

        this.onClose();

      } catch (error) {
        console.error('Upgrade error:', error);
        wx.showToast({
          title: '升级失败，请重试',
          icon: 'none'
        });
      } finally {
        this.setData({ loading: false });
      }
    },

    /**
     * 暂时跳过
     */
    onSkip() {
      this.onClose();
      this.triggerEvent('skip');
    },

    /**
     * 查看套餐详情
     */
    onViewDetails() {
      this.triggerEvent('viewDetails', {
        plan: this.data.selectedPlan
      });
    },

    /**
     * 获取默认标题
     */
    getDefaultTitle() {
      if (this.properties.title) {
        return this.properties.title;
      }

      switch (this.properties.type) {
        case 'exhausted':
          return '翻译次数已用完';
        case 'warning':
          return '翻译次数即将用完';
        case 'upgrade':
        default:
          return '升级您的套餐';
      }
    },

    /**
     * 获取默认消息
     */
    getDefaultMessage() {
      if (this.properties.message) {
        return this.properties.message;
      }

      switch (this.properties.type) {
        case 'exhausted':
          return '您的翻译次数已用完，升级套餐即可继续享受服务';
        case 'warning':
          return '您的翻译次数即将用完，建议提前升级以免影响使用';
        case 'upgrade':
        default:
          return '升级到更高级的套餐，享受更多翻译次数和更好的服务';
      }
    }
  }
});