<template>
  <view class="app">
    <view id="app">
      <!-- uni-app app container -->
    </view>
  </view>
</template>

<script setup lang="ts">
import { onLaunch, onShow, onHide } from '@dcloudio/uni-app'

onLaunch(() => {
  console.log('App Launch')
  // 应用启动时的初始化逻辑
  initializeApp()
})

onShow(() => {
  console.log('App Show')
})

onHide(() => {
  console.log('App Hide')
})

// 应用初始化
function initializeApp() {
  // 检查登录状态
  checkLoginStatus()
  
  // 初始化全局配置
  initGlobalConfig()
  
  // 设置全局错误处理
  setupGlobalErrorHandling()
}

// 检查登录状态
function checkLoginStatus() {
  const token = uni.getStorageSync('token')
  if (!token) {
    // 未登录，跳转到登录页
    console.log('User not logged in')
  } else {
    // 已登录，获取用户信息
    console.log('User already logged in')
  }
}

// 初始化全局配置
function initGlobalConfig() {
  // 设置API基础URL
  const baseUrl = process.env.NODE_ENV === 'development' 
    ? 'http://localhost:8000/api/v1' 
    : 'https://api.example.com/api/v1'
  
  uni.setStorageSync('baseUrl', baseUrl)
}

// 设置全局错误处理
function setupGlobalErrorHandling() {
  // Vue错误处理
  app.config.errorHandler = (err, vm, info) => {
    console.error('Vue Error:', err, info)
    // 可以在这里添加错误上报逻辑
  }
  
  // uni-app错误处理
  uni.onError((err) => {
    console.error('uni-app Error:', err)
    // 可以在这里添加错误上报逻辑
  })
}
</script>

<style>
/* 全局样式 */
.app {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* 通用样式 */
page {
  background-color: #f5f5f5;
}

/* 安全区域适配 */
.safe-area-top {
  padding-top: constant(safe-area-inset-top);
  padding-top: env(safe-area-inset-top);
}

.safe-area-bottom {
  padding-bottom: constant(safe-area-inset-bottom);
  padding-bottom: env(safe-area-inset-bottom);
}

/* 响应式布局 */
.container {
  padding: 32rpx;
}

@media (max-width: 400px) {
  .container {
    padding: 24rpx;
  }
}
</style>