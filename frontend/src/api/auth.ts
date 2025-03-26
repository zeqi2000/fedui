import axios from 'axios'
import { apiClient } from './client'

// 使用直接登录API
export async function login(username: string, password: string) {
  // 使用FormData对象
  const formData = new FormData()
  formData.append('username', username)
  formData.append('password', password)
  
  try {
    // 使用直接登录端点
    const response = await axios.post('/api/direct-login', formData, {
      baseURL: 'http://localhost:8000'
    })
    
    console.log('Login response:', response.data)
    return response.data
  } catch (error) {
    console.error('Login request failed:', error)
    throw error
  }
}

// 获取用户信息
export async function getUserInfo() {
  try {
    // 修改为后端实际提供的API路径
    const response = await apiClient.get('/api/auth/me')
    console.log('User info response:', response.data)
    return response.data
  } catch (error) {
    console.error('Failed to get user info:', error)
    throw error
  }
}

// 退出登录
export function logout() {
  // 本地退出登录，清除令牌
  localStorage.removeItem('token')
}

// 注册新用户（仅管理员）
export async function registerUser(userData: {
  username: string
  password: string
  email?: string
  full_name?: string
}) {
  const response = await apiClient.post('/api/auth/register', userData)
  return response.data
} 