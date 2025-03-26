import axios from 'axios'

// 创建axios实例
export const apiClient = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
apiClient.interceptors.request.use(
  config => {
    // 从 localStorage 获取 token
    const token = localStorage.getItem('token')
    
    // 如果存在 token，则添加到请求头
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
      console.log(`添加令牌到请求: ${config.url}`)
    }
    
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  response => {
    console.log(`请求成功: ${response.config.url}`, response.data)
    return response
  },
  error => {
    // 处理请求错误
    if (error.response) {
      // 服务器返回了错误状态码
      console.error(`HTTP错误: ${error.response.status} - ${error.config.url}`, error.response.data)
      
      if (error.response.status === 401) {
        // 未授权 - 清除token
        console.log('收到401错误，清除token')
        localStorage.removeItem('token')
        
        // 如果不是在登录页，跳转到登录页
        if (window.location.pathname !== '/login') {
          console.log('重定向到登录页面')
          setTimeout(() => {
            window.location.href = '/login'
          }, 1000)
        }
      } else if (error.response.status === 404) {
        // API不存在
        console.error('请求的API不存在:', error.config.url)
      }
    } else if (error.request) {
      // 请求已发出，但没有收到响应
      console.error('没有收到服务器响应:', error.request)
    } else {
      // 请求配置出错
      console.error('请求配置错误:', error.message)
    }
    
    return Promise.reject(error)
  }
)