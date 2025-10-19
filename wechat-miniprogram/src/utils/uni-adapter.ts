// Browser-compatible utilities for uni-app APIs

// Toast notifications
export const showToast = (options: { title: string; icon?: string; duration?: number }) => {
  // Create toast element
  const toast = document.createElement('div')
  toast.style.cssText = `
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: rgba(0, 0, 0, 0.8);
    color: white;
    padding: 12px 24px;
    border-radius: 8px;
    z-index: 10000;
    font-size: 14px;
    max-width: 80%;
    text-align: center;
  `
  toast.textContent = options.title
  document.body.appendChild(toast)
  
  setTimeout(() => {
    if (toast.parentNode) {
      toast.parentNode.removeChild(toast)
    }
  }, options.duration || 2000)
}

export const showLoading = (options: { title: string } = { title: '加载中...' }) => {
  let loadingElement = document.getElementById('global-loading')
  if (!loadingElement) {
    loadingElement = document.createElement('div')
    loadingElement.id = 'global-loading'
    loadingElement.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.5);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 10000;
    `
    
    const spinner = document.createElement('div')
    spinner.style.cssText = `
      width: 40px;
      height: 40px;
      border: 4px solid #f3f3f3;
      border-top: 4px solid #4CAF50;
      border-radius: 50%;
      animation: spin 1s linear infinite;
    `
    
    const text = document.createElement('div')
    text.style.cssText = `
      color: white;
      margin-top: 16px;
      font-size: 14px;
    `
    text.textContent = options.title
    
    const container = document.createElement('div')
    container.style.cssText = `
      display: flex;
      flex-direction: column;
      align-items: center;
    `
    container.appendChild(spinner)
    container.appendChild(text)
    
    loadingElement.appendChild(container)
    document.body.appendChild(loadingElement)
    
    // Add animation
    const style = document.createElement('style')
    style.textContent = `
      @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
      }
    `
    document.head.appendChild(style)
  }
}

export const hideLoading = () => {
  const loadingElement = document.getElementById('global-loading')
  if (loadingElement && loadingElement.parentNode) {
    loadingElement.parentNode.removeChild(loadingElement)
  }
}

// Modal dialogs
export const showModal = (options: {
  title: string
  content: string
  showCancel?: boolean
  confirmText?: string
  cancelText?: string
  success?: (res: { confirm: boolean }) => void
}) => {
  const result = confirm(`${options.title}\n\n${options.content}`)
  if (options.success) {
    options.success({ confirm: result })
  }
  return Promise.resolve({ confirm: result })
}

export const showActionSheet = (options: {
  itemList: string[]
  success: (res: { tapIndex: number }) => void
}) => {
  // Create action sheet
  const actionSheet = document.createElement('div')
  actionSheet.style.cssText = `
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: white;
    border-radius: 16px 16px 0 0;
    z-index: 10000;
    max-height: 50vh;
    overflow-y: auto;
  `
  
  const title = document.createElement('div')
  title.style.cssText = `
    padding: 16px;
    border-bottom: 1px solid #eee;
    font-weight: 600;
    text-align: center;
  `
  title.textContent = '选择操作'
  
  const cancel = document.createElement('div')
  cancel.style.cssText = `
    padding: 16px;
    border-top: 8px solid #f5f5f5;
    text-align: center;
    color: #666;
    cursor: pointer;
  `
  cancel.textContent = '取消'
  cancel.onclick = () => {
    document.body.removeChild(actionSheet)
    document.body.removeChild(overlay)
  }
  
  actionSheet.appendChild(title)
  
  options.itemList.forEach((item, index) => {
    const button = document.createElement('div')
    button.style.cssText = `
      padding: 16px;
      border-bottom: 1px solid #eee;
      cursor: pointer;
      text-align: center;
    `
    button.textContent = item
    button.onclick = () => {
      document.body.removeChild(actionSheet)
      document.body.removeChild(overlay)
      options.success({ tapIndex: index })
    }
    actionSheet.appendChild(button)
  })
  
  actionSheet.appendChild(cancel)
  
  const overlay = document.createElement('div')
  overlay.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    z-index: 9999;
  `
  overlay.onclick = () => {
    document.body.removeChild(actionSheet)
    document.body.removeChild(overlay)
  }
  
  document.body.appendChild(overlay)
  document.body.appendChild(actionSheet)
}

// Navigation
export const navigateTo = (options: { url: string }) => {
  if (window.navigateTo) {
    window.navigateTo(options)
  } else {
    console.warn('Navigation system not available')
  }
}

export const navigateBack = (options: { delta?: number } = {}) => {
  if (window.navigateBack) {
    window.navigateBack()
  } else {
    window.history.back()
  }
}

export const redirectTo = (options: { url: string }) => {
  if (window.redirectTo) {
    window.redirectTo(options)
  } else {
    console.warn('Navigation system not available')
  }
}

export const switchTab = (options: { url: string }) => {
  if (window.navigateTo) {
    window.navigateTo(options)
  } else {
    console.warn('Tab navigation not available')
  }
}

export const reLaunch = (options: { url: string }) => {
  window.location.href = options.url
}

// Clipboard
export const setClipboardData = (options: { data: string; success?: () => void }) => {
  navigator.clipboard.writeText(options.data).then(() => {
    if (options.success) {
      options.success()
    }
  }).catch(() => {
    // Fallback for older browsers
    const textArea = document.createElement('textarea')
    textArea.value = options.data
    document.body.appendChild(textArea)
    textArea.select()
    document.execCommand('copy')
    document.body.removeChild(textArea)
    if (options.success) {
      options.success()
    }
  })
}

// File picker
export const chooseMedia = (options: {
  count?: number
  mediaType?: string[]
  sourceType?: string[]
  success: (res: { tempFiles: any[] }) => void
  fail?: (error: any) => void
}) => {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = options.mediaType?.includes('video') ? 'video/*' : 'audio/*,image/*'
  input.multiple = (options.count || 1) > 1
  
  input.onchange = (e) => {
    const files = Array.from((e.target as HTMLInputElement).files || [])
    const tempFiles = files.map(file => ({
      name: file.name,
      size: file.size,
      tempFilePath: URL.createObjectURL(file),
      file: file
    }))
    options.success({ tempFiles })
  }
  
  input.onerror = (error) => {
    if (options.fail) {
      options.fail(error)
    }
  }
  
  input.click()
}

// File save
export const saveFile = (options: {
  tempFilePath: string
  success: () => void
  fail?: () => void
}) => {
  // For web environment, just trigger download
  const a = document.createElement('a')
  a.href = options.tempFilePath
  a.download = 'translation-result.txt'
  a.click()
  options.success()
}

// System info
export const canIUse = (api: string) => {
  const unsupportedApis = ['getUpdateManager']
  return !unsupportedApis.includes(api)
}

// Pull down refresh
export const startPullDownRefresh = () => {
  console.log('Pull down refresh started')
}

export const stopPullDownRefresh = () => {
  console.log('Pull down refresh stopped')
}

// Create uni namespace
export const uni = {
  showToast,
  showLoading,
  hideLoading,
  showModal,
  showActionSheet,
  navigateTo,
  navigateBack,
  redirectTo,
  switchTab,
  reLaunch,
  setClipboardData,
  chooseMedia,
  saveFile,
  canIUse,
  startPullDownRefresh,
  stopPullDownRefresh
}