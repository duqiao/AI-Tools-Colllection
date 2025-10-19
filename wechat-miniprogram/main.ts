import { createSSRApp } from 'vue'
import App from './App.vue'
import { createPinia } from 'pinia'

export function createApp() {
  const app = createSSRApp(App)
  
  // 创建状态管理
  const pinia = createPinia()
  app.use(pinia)
  
  return {
    app,
    pinia
  }
}