import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { login as apiLogin, getUserInfo } from '@/api/auth'
import { ElMessage } from 'element-plus'

export const useUserStore = defineStore('user', () => {
  // 状态
  const token = ref(localStorage.getItem('token') || '')
  const user = ref({
    id: '',
    username: '',
    email: '',
    full_name: '',
    is_admin: false
  })
  const isLoading = ref(false)
  const lastError = ref('')
  
  // 计算属性
  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value.is_admin)
  
  // 调试用：监听令牌变化
  watch(token, (newToken, oldToken) => {
    console.log(`令牌变化: ${oldToken.slice(0, 10)} -> ${newToken.slice(0, 10)}`)
    
    if (newToken) {
      console.log('令牌已设置，用户已登录状态')
    } else {
      console.log('令牌已清除，用户已登出状态')
      // 重置用户信息
      user.value = {
        id: '',
        username: '',
        email: '',
        full_name: '',
        is_admin: false
      }
    }
  })
  
  // 操作
  async function login(username: string, password: string) {
    if (isLoading.value) {
      console.log('登录请求正在进行中，忽略重复请求')
      return false
    }
    
    isLoading.value = true
    lastError.value = ''
    
    try {
      console.log(`尝试登录: ${username}`)
      const response = await apiLogin(username, password)
      console.log('登录响应:', response)
      
      if (!response.access_token) {
        throw new Error('登录失败: 未获取到访问令牌')
      }
      
      // 保存令牌
      token.value = response.access_token
      localStorage.setItem('token', token.value)
      console.log('令牌已保存到本地存储')
      
      // 获取用户信息
      await fetchUserInfo()
      
      return true
    } catch (error: any) {
      console.error('登录失败:', error)
      lastError.value = error.message || '登录失败，请重试'
      return false
    } finally {
      isLoading.value = false
    }
  }
  
  async function fetchUserInfo() {
    if (!token.value) {
      console.warn('获取用户信息失败: 未设置令牌')
      return
    }
    
    if (isLoading.value) {
      console.log('已有请求正在进行中，忽略重复请求')
      return
    }
    
    isLoading.value = true
    lastError.value = ''
    
    try {
      console.log('正在获取用户信息...')
      const userData = await getUserInfo()
      console.log('获取到用户信息:', userData)
      
      // 更新用户信息
      user.value = userData
      
      return userData
    } catch (error: any) {
      console.error('获取用户信息失败:', error)
      lastError.value = error.message || '获取用户信息失败'
      
      // 如果是401或者404错误，可能是令牌无效或过期
      if (error.response && (error.response.status === 401 || error.response.status === 404)) {
        console.warn('令牌可能已过期或无效，正在登出')
        ElMessage.error('会话已过期，请重新登录')
        logout()
      }
      
      throw error
    } finally {
      isLoading.value = false
    }
  }
  
  function logout() {
    console.log('执行登出操作')
    token.value = ''
    localStorage.removeItem('token')
    
    // 重置用户信息
    user.value = {
      id: '',
      username: '',
      email: '',
      full_name: '',
      is_admin: false
    }
    
    // 重置错误状态
    lastError.value = ''
  }
  
  // 检查用户是否已登录并获取用户信息
  async function checkAuth() {
    const storedToken = localStorage.getItem('token')
    console.log(`检查认证状态，令牌存在: ${!!storedToken}`)
    
    if (storedToken) {
      token.value = storedToken
      
      try {
        await fetchUserInfo()
        return true
      } catch (error) {
        console.error('验证登录状态失败:', error)
        return false
      }
    }
    
    return false
  }
  
  // 更新用户信息
  function updateUserInfo(newUserInfo: any) {
    console.log('更新用户信息:', newUserInfo)
    user.value = { ...user.value, ...newUserInfo }
  }
  
  return {
    token,
    user,
    isLoggedIn,
    isAdmin,
    isLoading,
    lastError,
    login,
    fetchUserInfo,
    logout,
    checkAuth,
    updateUserInfo
  }
}) 