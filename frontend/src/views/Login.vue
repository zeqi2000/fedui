<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <h2>向量数据库管理系统</h2>
        <p>使用您的凭据登录</p>
      </div>
      
      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        class="login-form"
        label-position="top"
      >
        <el-form-item prop="username" label="用户名">
          <el-input
            v-model="loginForm.username"
            placeholder="输入用户名"
            prefix-icon="User"
          />
        </el-form-item>
        
        <el-form-item prop="password" label="密码">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="输入密码"
            prefix-icon="Lock"
            show-password
          />
        </el-form-item>
        
        <el-form-item>
          <el-button
            type="primary"
            class="login-button"
            :loading="loading"
            @click="handleLogin"
          >
            登录
          </el-button>
        </el-form-item>
        
        <el-form-item>
          <el-button
            type="warning"
            class="login-button"
            @click="bypassLogin"
          >
            开发模式登录 (绕过验证)
          </el-button>
        </el-form-item>
      </el-form>
      
      <div class="login-info">
        <p>默认管理员账号: admin / admin123</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, FormInstance } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import axios from 'axios'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const loginFormRef = ref<FormInstance>()
const loading = ref(false)

const loginForm = reactive({
  username: '',
  password: ''
})

const loginRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' }
  ]
}

// 直接在组件中实现登录逻辑
const directLogin = async () => {
  loading.value = true
  try {
    // 使用FormData对象
    const formData = new FormData()
    formData.append('username', loginForm.username)
    formData.append('password', loginForm.password)
    
    // 直接调用API
    const response = await axios.post('http://localhost:8000/api/direct-login', formData)
    
    console.log('Login response:', response.data)
    
    if (!response.data.access_token) {
      throw new Error('登录失败: 未获取到有效的访问令牌')
    }
    
    // 保存令牌
    const token = response.data.access_token
    localStorage.setItem('token', token)
    
    // 更新用户状态并使用延迟跳转
    try {
      await userStore.fetchUserInfo()
      
      // 登录成功提示
      ElMessage.success('登录成功')
      
      // 延迟执行跳转，确保状态更新完成
      setTimeout(() => {
        // 强制页面跳转 (使用原生方法而不是Vue Router)
        window.location.href = '/'
      }, 500)
    } catch (userInfoError) {
      console.error('获取用户信息失败:', userInfoError)
      ElMessage.error('登录后获取用户信息失败')
      // 清理token
      localStorage.removeItem('token')
    }
  } catch (error) {
    console.error('Login failed:', error)
    ElMessage.error('登录失败，请检查用户名和密码')
  } finally {
    loading.value = false
  }
}

// 开发模式 - 绕过登录
const bypassLogin = async () => {
  loading.value = true
  try {
    // 创建一个模拟的JWT令牌（不是真正有效的，但前端会接受它）
    const fakeToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6OTk5OTk5OTk5OX0.dGhpcyBpcyBhIGZha2UgdG9rZW4='
    localStorage.setItem('token', fakeToken)
    
    // 设置用户信息
    userStore.updateUserInfo({
      id: '1',
      username: 'admin',
      email: 'admin@example.com',
      full_name: '开发者模式',
      is_admin: true
    })
    
    // 延迟执行跳转，确保状态更新完成
    setTimeout(() => {
      ElMessage.warning('使用开发者模式登录 (部分功能可能受限)')
      window.location.href = '/'
    }, 500)
  } catch (error) {
    console.error('开发者模式登录失败:', error)
    ElMessage.error('登录失败')
  } finally {
    loading.value = false
  }
}

const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      // 使用直接登录方法
      directLogin()
    }
  })
}
</script>

<style scoped>
.login-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f0f2f5;
}

.login-card {
  width: 400px;
  padding: 40px;
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.login-header h2 {
  margin-bottom: 10px;
  color: #409EFF;
}

.login-form {
  margin-bottom: 20px;
}

.login-button {
  width: 100%;
}

.login-info {
  color: #909399;
  font-size: 13px;
  text-align: center;
}
</style> 