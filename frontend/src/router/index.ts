import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '../stores/user'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      component: () => import('@/views/Layout.vue'),
      children: [
        {
          path: '',
          name: 'dashboard',
          component: () => import('@/views/Dashboard.vue'),
          meta: { requiresAuth: true, title: '仪表盘' }
        },
        {
          path: 'databases',
          name: 'databases',
          component: () => import('@/views/DatabaseManager.vue'),
          meta: { requiresAuth: true, requiresAdmin: true, title: '数据库管理' }
        },
        {
          path: 'query',
          name: 'query',
          component: () => import('@/views/VectorQuery.vue'),
          meta: { requiresAuth: true, title: '向量查询' }
        },
        {
          path: 'multi-query',
          name: 'multi-query',
          component: () => import('@/views/MultiDatabaseQuery.vue'),
          meta: { requiresAuth: true, title: '跨库查询' }
        },
        {
          path: 'multi-query-v',
          name: 'multi-query-v',
          component: () => import('@/views/MultiDatabaseQuery_V.vue'),
          meta: { requiresAuth: true, title: '跨库查询' }
        },
        {
          path: 'profile',
          name: 'profile',
          component: () => import('@/views/UserProfile.vue'),
          meta: { requiresAuth: true, title: '个人信息' }
        },
        {
          path: 'query-parameter',
          name: 'QueryParameter',
          component: () => import('@/views/QueryParameter.vue'),
          meta: {
            title: '查询参数设置',
            requiresAuth: true
          }
        },
        {
          path: 'query-result/:queryId',
          name: 'QueryResult',
          component: () => import('@/views/QueryResult.vue'),
          meta: {
            title: '查询结果',
            requiresAuth: true
          }
        }
      ]
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/Login.vue'),
      meta: { title: '登录' }
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'NotFound',
      redirect: '/'
    }
  ]
})

// 简化导航守卫
router.beforeEach((to, from, next) => {
  // 设置页面标题
  document.title = `${to.meta.title || '首页'} - 向量数据库管理系统`
  
  const userStore = useUserStore()
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth)
  const requiresAdmin = to.matched.some(record => record.meta.requiresAdmin)
  
  // 检查用户认证状态
  if (requiresAuth && !userStore.isLoggedIn) {
    next({ name: 'login' })
  } else if (requiresAdmin && !userStore.isAdmin) {
    next({ name: 'dashboard' }) // 如果需要管理员权限但用户不是管理员，重定向到仪表盘
  } else {
    next()
  }
})

export default router 