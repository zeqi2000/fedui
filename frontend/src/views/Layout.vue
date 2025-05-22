<template>
  <el-container class="layout-container">
    <!-- 侧边栏 -->
    <el-aside width="250px" class="aside">
      <div class="logo">
        <img src="@/assets/logo.svg" alt="Logo" />
        <h1>联邦向量KNN</h1>
      </div>
      
      <el-menu
        :default-active="activeMenu"
        class="el-menu-vertical"
        :collapse="isCollapse"
        router
        background-color="#001529"
        text-color="#fff"
        active-text-color="#409EFF"
      >
        <el-menu-item index="/">
          <el-icon><HomeFilled /></el-icon>
          <template #title>仪表盘</template>
        </el-menu-item>
        
        <el-menu-item index="/databases" v-if="userStore.isAdmin">
          <el-icon><Connection /></el-icon>
          <template #title>联邦参与方管理</template>
        </el-menu-item>
        
        <!-- <el-menu-item index="/query">
          <el-icon><Search /></el-icon>
          <template #title>向量查询</template>
        </el-menu-item> -->
        
        <el-menu-item index="/query-parameter">
          <el-icon><Document /></el-icon>
          <template #title>查询参数</template>
        </el-menu-item>
        
        <!-- <el-menu-item index="/multi-query">
          <el-icon><Connection /></el-icon>
          <span>横向联邦查询</span>
        </el-menu-item> -->

        <!-- <el-menu-item index="/multi-query-v">
          <el-icon><Connection /></el-icon>
          <span>纵向联邦查询</span>
        </el-menu-item> -->
        
        <el-menu-item index="/profile">
          <el-icon><User /></el-icon>
          <template #title>个人信息</template>
        </el-menu-item>
      </el-menu>
    </el-aside>
    
    <!-- 内容区 -->
    <el-container>
      <!-- 顶部导航 -->
      <el-header height="64px" class="header">
        <div class="header-left">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item>{{ currentPageTitle }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        
        <div class="header-right">
          <el-dropdown @command="handleCommand">
            <span class="user-dropdown-link">
              {{ userStore.user.username }}
              <el-icon class="el-icon--right"><arrow-down /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人信息</el-dropdown-item>
                <el-dropdown-item command="settings">设置</el-dropdown-item>
                <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      
      <!-- 主内容区 -->
      <el-main>
        <router-view />
      </el-main>
      
      <!-- 页脚 -->
      <el-footer height="50px" class="footer">
        <p>© 2025 向量数据库管理系统 - 版权所有</p>
      </el-footer>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { DataBoard, DataLine, Search, Connection, User, ArrowDown, HomeFilled, Document } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const isCollapse = ref(false)
const activeMenuItem = ref('')

// 计算当前激活的菜单项
const activeMenu = computed(() => route.path)

// 获取当前页面标题
const currentPageTitle = computed(() => {
  return route.meta.title || '首页'
})

// 计算属性
const userInfo = computed(() => userStore.user)
const isAdmin = computed(() => userStore.isAdmin)

// 处理菜单项点击
const handleMenuSelect = (index: string) => {
  router.push(index)
}

// 退出登录
const handleLogout = () => {
  userStore.logout()
  ElMessage.success('已退出登录')
  router.push('/login')
}

// 在组件挂载时检查用户状态
onMounted(async () => {
  if (userStore.isLoggedIn) {
    try {
      await userStore.fetchUserInfo()
      console.log('Layout组件已加载用户信息:', userStore.user)
    } catch (error) {
      console.error('加载用户信息失败:', error)
    }
  } else {
    console.log('用户未登录，请先登录')
    router.push('/login')
  }
})

// 处理下拉菜单命令
const handleCommand = (command: string) => {
  if (command === 'logout') {
    ElMessageBox.confirm(
      '确定要退出登录吗?',
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    ).then(() => {
      handleLogout()
    }).catch(() => {})
  } else if (command === 'profile') {
    router.push('/profile')
  } else if (command === 'settings') {
    ElMessage.info('设置功能开发中')
  }
}
</script>

<style scoped>
.layout-container {
  min-height: 100vh;
}

.aside {
  background-color: #001529;
  color: white;
  height: 100vh;
  overflow-y: auto;
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  z-index: 10;
}

.logo {
  height: 64px;
  display: flex;
  align-items: center;
  padding: 0 20px;
  color: white;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.logo img {
  width: 32px;
  margin-right: 10px;
}

.logo h1 {
  font-size: 18px;
  margin: 0;
  white-space: nowrap;
}

.el-menu {
  border-right: none;
}

.header {
  background-color: white;
  box-shadow: 0 1px 4px rgba(0,21,41,.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  position: fixed;
  top: 0;
  left: 250px;
  right: 0;
  z-index: 9;
}

.header-left, .header-right {
  display: flex;
  align-items: center;
}

.user-dropdown-link {
  cursor: pointer;
  display: flex;
  align-items: center;
  color: #333;
}

.el-main {
  padding: 84px 20px 70px 20px;
  margin-left: 250px;
  background-color: #f5f7fa;
  min-height: 100vh;
}

.footer {
  background-color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-left: 250px;
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 8;
  border-top: 1px solid #f0f0f0;
}
</style>