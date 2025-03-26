<template>
  <div class="user-profile-container">
    <el-row :gutter="20">
      <el-col :span="8">
        <el-card shadow="hover" class="user-info-card">
          <template #header>
            <div class="card-header">
              <h3>个人信息</h3>
              <el-button type="primary" size="small" @click="handleEdit">
                <el-icon><Edit /></el-icon>
                编辑资料
              </el-button>
            </div>
          </template>

          <div class="user-avatar">
            <el-avatar :size="100" :src="userInfo.avatar || defaultAvatar">
              {{ userInfo.username?.charAt(0).toUpperCase() }}
            </el-avatar>
          </div>

          <el-divider />

          <div class="user-details">
            <el-descriptions :column="1" border>
              <el-descriptions-item label="用户名">
                {{ userInfo.username }}
              </el-descriptions-item>
              <el-descriptions-item label="用户角色">
                <el-tag type="success" v-if="userStore.isAdmin">管理员</el-tag>
                <el-tag v-else>普通用户</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="邮箱">
                {{ userInfo.email || '未设置' }}
              </el-descriptions-item>
              <el-descriptions-item label="注册时间">
                {{ formatDate(userInfo.createdAt) }}
              </el-descriptions-item>
              <el-descriptions-item label="最后登录">
                {{ formatDate(userInfo.lastLogin) }}
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </el-card>
      </el-col>

      <el-col :span="16">
        <el-card shadow="hover" class="activity-card">
          <template #header>
            <div class="card-header">
              <h3>最近活动</h3>
            </div>
          </template>

          <el-empty v-if="!recentActivities.length" description="暂无活动记录" />

          <el-timeline v-else>
            <el-timeline-item
              v-for="(activity, index) in recentActivities"
              :key="index"
              :timestamp="formatDate(activity.time)"
              :type="getActivityType(activity.type)"
            >
              {{ activity.description }}
              <div class="activity-details" v-if="activity.details">
                <el-tag size="small">{{ activity.details }}</el-tag>
              </div>
            </el-timeline-item>
          </el-timeline>
        </el-card>

        <el-card shadow="hover" class="security-card" style="margin-top: 20px">
          <template #header>
            <div class="card-header">
              <h3>账号安全</h3>
            </div>
          </template>

          <div class="security-options">
            <div class="security-item">
              <div class="security-item-info">
                <h4>修改密码</h4>
                <p>定期修改密码可以提高账号安全性</p>
              </div>
              <el-button @click="showPasswordDialog = true">修改密码</el-button>
            </div>

            <el-divider />

            <div class="security-item">
              <div class="security-item-info">
                <h4>登录设备管理</h4>
                <p>查看并管理您的登录设备</p>
              </div>
              <el-button @click="showDevicesDialog = true">查看设备</el-button>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 编辑个人信息对话框 -->
    <el-dialog v-model="showEditDialog" title="编辑个人信息" width="500px">
      <el-form :model="editForm" label-width="80px" :rules="editRules" ref="editFormRef">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="editForm.username" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="editForm.email" />
        </el-form-item>
        <el-form-item label="头像">
          <el-upload
            class="avatar-uploader"
            action="#"
            :auto-upload="false"
            :show-file-list="false"
            :on-change="handleAvatarChange"
          >
            <img v-if="avatarUrl" :src="avatarUrl" class="avatar-preview" />
            <el-icon v-else class="avatar-uploader-icon"><Plus /></el-icon>
          </el-upload>
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showEditDialog = false">取消</el-button>
          <el-button type="primary" @click="updateProfile" :loading="updating">
            保存
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 修改密码对话框 -->
    <el-dialog v-model="showPasswordDialog" title="修改密码" width="500px">
      <el-form :model="passwordForm" label-width="100px" :rules="passwordRules" ref="passwordFormRef">
        <el-form-item label="当前密码" prop="currentPassword">
          <el-input v-model="passwordForm.currentPassword" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码" prop="newPassword">
          <el-input v-model="passwordForm.newPassword" type="password" show-password />
        </el-form-item>
        <el-form-item label="确认新密码" prop="confirmPassword">
          <el-input v-model="passwordForm.confirmPassword" type="password" show-password />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showPasswordDialog = false">取消</el-button>
          <el-button type="primary" @click="updatePassword" :loading="updating">
            确认修改
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 设备管理对话框 -->
    <el-dialog v-model="showDevicesDialog" title="登录设备管理" width="600px">
      <el-empty v-if="!loginDevices.length" description="暂无设备信息" />

      <el-table v-else :data="loginDevices" style="width: 100%">
        <el-table-column prop="deviceName" label="设备" width="150" />
        <el-table-column prop="location" label="地点" width="150" />
        <el-table-column prop="lastLogin" label="最后登录时间" />
        <el-table-column label="操作" width="100">
          <template #default="scope">
            <el-button
              type="danger"
              size="small"
              @click="logoutDevice(scope.row)"
              :disabled="scope.row.current"
            >
              退出
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { Edit, Plus } from '@element-plus/icons-vue'
import { ElMessage, FormInstance } from 'element-plus'
import { useUserStore } from '@/stores/user'
import defaultAvatar from '@/assets/default-avatar.png'

// 用户信息
const userStore = useUserStore()
const userInfo = computed(() => userStore.user || {})

// 格式化日期
const formatDate = (dateString: string | undefined | null) => {
  if (!dateString) return '未知'
  const date = new Date(dateString)
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date)
}

// 最近活动
interface Activity {
  time: string
  type: 'login' | 'query' | 'database' | 'other'
  description: string
  details?: string
}

const recentActivities = ref<Activity[]>([
  {
    time: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
    type: 'login',
    description: '登录系统'
  },
  {
    time: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
    type: 'query',
    description: '执行向量查询',
    details: '集合: users, 结果: 15条'
  },
  {
    time: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(),
    type: 'database',
    description: '连接数据库',
    details: 'milvus-dev-01'
  }
])

// 获取活动类型对应的样式
const getActivityType = (type: string) => {
  switch (type) {
    case 'login':
      return 'success'
    case 'query':
      return 'primary'
    case 'database':
      return 'warning'
    default:
      return 'info'
  }
}

// 编辑资料
const showEditDialog = ref(false)
const updating = ref(false)
const editFormRef = ref<FormInstance>()
const avatarUrl = ref('')

const editForm = reactive({
  username: '',
  email: '',
  avatar: null as File | null
})

const editRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  email: [
    { required: false, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ]
}

const handleEdit = () => {
  editForm.username = userInfo.value.username || ''
  editForm.email = userInfo.value.email || ''
  avatarUrl.value = userInfo.value.avatar || ''
  showEditDialog.value = true
}

const handleAvatarChange = (file: any) => {
  editForm.avatar = file.raw
  avatarUrl.value = URL.createObjectURL(file.raw)
}

const updateProfile = async () => {
  if (!editFormRef.value) return

  await editFormRef.value.validate(async (valid) => {
    if (valid) {
      updating.value = true
      try {
        // 这里应该调用API更新用户资料
        await new Promise(resolve => setTimeout(resolve, 1000)) // 模拟API调用

        // 更新用户信息
        userStore.updateUserInfo({
          ...userInfo.value,
          username: editForm.username,
          email: editForm.email,
          avatar: avatarUrl.value
        })

        ElMessage.success('个人信息更新成功')
        showEditDialog.value = false
      } catch (error) {
        ElMessage.error('更新失败，请重试')
      } finally {
        updating.value = false
      }
    }
  })
}

// 修改密码
const showPasswordDialog = ref(false)
const passwordFormRef = ref<FormInstance>()

const passwordForm = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const validateConfirmPassword = (rule: any, value: string, callback: any) => {
  if (value !== passwordForm.newPassword) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const passwordRules = {
  currentPassword: [
    { required: true, message: '请输入当前密码', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少为6个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const updatePassword = async () => {
  if (!passwordFormRef.value) return

  await passwordFormRef.value.validate(async (valid) => {
    if (valid) {
      updating.value = true
      try {
        // 这里应该调用API更新密码
        await new Promise(resolve => setTimeout(resolve, 1000)) // 模拟API调用

        ElMessage.success('密码修改成功')
        showPasswordDialog.value = false
        passwordForm.currentPassword = ''
        passwordForm.newPassword = ''
        passwordForm.confirmPassword = ''
      } catch (error) {
        ElMessage.error('密码修改失败，请重试')
      } finally {
        updating.value = false
      }
    }
  })
}

// 设备管理
const showDevicesDialog = ref(false)
const loginDevices = ref([
  {
    deviceName: '当前设备',
    os: 'Windows 10',
    browser: 'Chrome',
    location: '北京',
    ip: '192.168.1.1',
    lastLogin: formatDate(new Date().toISOString()),
    current: true
  },
  {
    deviceName: 'iPhone 13',
    os: 'iOS 15',
    browser: 'Safari',
    location: '上海',
    ip: '192.168.2.2',
    lastLogin: formatDate(new Date(Date.now() - 1000 * 60 * 60 * 24 * 2).toISOString()),
    current: false
  }
])

const logoutDevice = (device: any) => {
  // 这里应该调用API退出指定设备
  ElMessage.success(`已退出设备: ${device.deviceName}`)
  loginDevices.value = loginDevices.value.filter(d => d !== device)
}

// 加载用户数据
onMounted(() => {
  // 这里应该从API获取用户信息、活动记录和登录设备等
})
</script>

<style scoped>
.user-profile-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.user-avatar {
  display: flex;
  justify-content: center;
  margin: 20px 0;
}

.user-details {
  margin-top: 15px;
}

.activity-details {
  margin-top: 5px;
}

.security-options {
  padding: 10px 0;
}

.security-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
}

.security-item-info h4 {
  margin-bottom: 5px;
  font-weight: 500;
}

.security-item-info p {
  color: #999;
  font-size: 12px;
}

.avatar-uploader {
  width: 100px;
  height: 100px;
  border: 1px dashed #d9d9d9;
  border-radius: 50%;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  display: flex;
  justify-content: center;
  align-items: center;
}

.avatar-uploader:hover {
  border-color: var(--el-color-primary);
}

.avatar-uploader-icon {
  font-size: 28px;
  color: #8c939d;
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.avatar-preview {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
</style> 