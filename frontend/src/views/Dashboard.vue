<template>
  <div class="dashboard-container">
    <el-row :gutter="20">
      <el-col :span="24">
        <el-card shadow="hover" class="welcome-card">
          <template #header>
            <div class="card-header">
              <h3>欢迎使用向量数据库管理系统</h3>
            </div>
          </template>
          <div class="welcome-content">
            <p>您已成功登录为 <strong>{{ userStore.user.username }}</strong> {{ userStore.isAdmin ? '(管理员)' : '(普通用户)' }}</p>
            <p>通过左侧菜单导航到不同功能区域</p>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" class="mt-20">
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card">
          <template #header>
            <div class="card-header">
              <h3>数据库连接</h3>
            </div>
          </template>
          <div class="stat-content">
            <el-statistic :value="databaseCount">
              <template #title>
                <div style="display: inline-flex; align-items: center">
                  总连接数
                  <el-icon style="margin-left: 4px">
                    <Monitor />
                  </el-icon>
                </div>
              </template>
            </el-statistic>
            <div class="stat-footer">
              <el-button v-if="userStore.isAdmin" type="primary" @click="navigateTo('/databases')">
                管理数据库
              </el-button>
              <el-button v-else type="info" @click="navigateTo('/query')">
                开始查询
              </el-button>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card">
          <template #header>
            <div class="card-header">
              <h3>活跃连接</h3>
            </div>
          </template>
          <div class="stat-content">
            <el-statistic :value="activeConnections">
              <template #title>
                <div style="display: inline-flex; align-items: center">
                  已连接数据库
                  <el-icon style="margin-left: 4px">
                    <Connection />
                  </el-icon>
                </div>
              </template>
            </el-statistic>
            <div class="stat-footer">
              <el-tag v-for="(conn, index) in activeConnectionList" :key="index" class="connection-tag">
                {{ conn.name }}
              </el-tag>
              <p v-if="activeConnectionList.length === 0" class="empty-text">
                暂无活跃连接
              </p>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card">
          <template #header>
            <div class="card-header">
              <h3>快速查询</h3>
            </div>
          </template>
          <div class="stat-content">
            <el-statistic :value="recentQueryCount">
              <template #title>
                <div style="display: inline-flex; align-items: center">
                  最近查询次数
                  <el-icon style="margin-left: 4px">
                    <Search />
                  </el-icon>
                </div>
              </template>
            </el-statistic>
            <div class="stat-footer">
              <el-button type="success" @click="navigateTo('/query')">
                横向联邦向量KNN查询
              </el-button>
              <el-button type="warning" @click="navigateTo('/multi-query')">
                纵向联邦向量KNN查询
              </el-button>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" class="mt-20" v-if="userStore.isAdmin">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <h3>系统状态</h3>
            </div>
          </template>
          <div id="systemStatusChart" class="chart-container"></div>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <h3>数据库拓扑结构</h3>
            </div>
          </template>
          <div id="topologyChart" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import { DataBoard, DataLine, Search, Connection, User, Monitor } from '@element-plus/icons-vue'
import { getDatabaseConnections } from '@/api/database'
import * as echarts from 'echarts'

const router = useRouter()
const userStore = useUserStore()

// 统计数据
const databaseCount = ref(0)
const activeConnections = ref(0)
const recentQueryCount = ref(0)
const activeConnectionList = ref<any[]>([])

// 获取数据库连接信息
const fetchDatabaseConnections = async () => {
  try {
    const connections = await getDatabaseConnections()
    databaseCount.value = connections.length
    activeConnectionList.value = connections.filter((conn: any) => conn.status === '已连接')
    activeConnections.value = activeConnectionList.value.length
    
    // 模拟查询次数
    recentQueryCount.value = Math.floor(Math.random() * 50) + 10
    
    if (userStore.isAdmin) {
      initSystemStatusChart(connections)
      initTopologyChart(connections)
    }
  } catch (error) {
    console.error('获取数据库连接失败:', error)
    ElMessage.error('获取数据库信息失败')
  }
}

// 初始化系统状态图表
const initSystemStatusChart = (connections: any[]) => {
  setTimeout(() => {
    const chartDom = document.getElementById('systemStatusChart')
    if (!chartDom) return
    
    const myChart = echarts.init(chartDom)
    
    // 准备数据
    const statusData = [
      { value: activeConnections.value, name: '活跃连接', itemStyle: { color: '#91CC75' } },
      { value: databaseCount.value - activeConnections.value, name: '未连接', itemStyle: { color: '#FAC858' } }
    ]
    
    const option = {
      tooltip: {
        trigger: 'item',
        formatter: '{a} <br/>{b}: {c} ({d}%)'
      },
      legend: {
        top: '5%',
        left: 'center'
      },
      series: [
        {
          name: '连接状态',
          type: 'pie',
          radius: ['40%', '70%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 10,
            borderColor: '#fff',
            borderWidth: 2
          },
          label: {
            show: false,
            position: 'center'
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 40,
              fontWeight: 'bold'
            }
          },
          labelLine: {
            show: false
          },
          data: statusData
        }
      ]
    }
    
    myChart.setOption(option)
    
    window.addEventListener('resize', () => {
      myChart.resize()
    })
  }, 0)
}

// 初始化拓扑结构图表
const initTopologyChart = (connections: any[]) => {
  setTimeout(() => {
    const chartDom = document.getElementById('topologyChart')
    if (!chartDom) return
    
    const myChart = echarts.init(chartDom)
    
    // 准备节点数据
    const nodes = [
      { id: 'federation', name: '联邦协调方', value: '联邦', category: 0, symbolSize: 80, itemStyle: { color: '#5470C6' } }
    ]
    
    // 添加数据库节点
    connections.forEach((conn, index) => {
      nodes.push({
        id: conn.id,
        name: conn.name,
        value: conn.name,
        category: conn.status === '已连接' ? 1 : 2,
        symbolSize: 50,
        itemStyle: { 
          color: conn.status === '已连接' ? '#91CC75' : '#FAC858' 
        }
      })
    })
    
    // 准备边数据
    const edges = connections.map(conn => ({
      source: 'federation',
      target: conn.id,
      value: conn.status === '已连接' ? '已连接' : '未连接',
      lineStyle: {
        color: '#5470C6', // 所有连接线使用蓝色
        width: 2
      }
    }))
    
    const option = {
      tooltip: {
        trigger: 'item',
        formatter: '{b}'
      },
      legend: {
        data: ['联邦协调方', '活跃连接参与方', '未连接参与方']
      },
      animationDurationUpdate: 1500,
      animationEasingUpdate: 'quinticInOut' as any,
      series: [
        {
          type: 'graph',
          layout: 'force',
          data: nodes,
          links: edges,
          categories: [
            { name: '联邦协调方' },
            { name: '活跃连接参与方' },
            { name: '未连接参与方' }
          ],
          roam: true,
          label: {
            show: true,
            position: 'right',
            formatter: '{b}'
          },
          force: {
            repulsion: 100,
            gravity: 0.1,
            edgeLength: 100
          },
          lineStyle: {
            opacity: 0.9,
            width: 2,
            curveness: 0
          }
        }
      ]
    }
    
    myChart.setOption(option)
    
    window.addEventListener('resize', () => {
      myChart.resize()
    })
  }, 0)
}

// 页面导航
const navigateTo = (path: string) => {
  router.push(path)
}

onMounted(() => {
  fetchDatabaseConnections()
})
</script>

<style scoped>
.dashboard-container {
  padding: 20px;
}

.welcome-card {
  margin-bottom: 20px;
}

.welcome-content {
  padding: 10px 0;
  font-size: 16px;
  line-height: 1.6;
}

.mt-20 {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-card {
  height: 100%;
}

.stat-content {
  padding: 10px 0;
  display: flex;
  flex-direction: column;
  height: 200px;
}

.stat-footer {
  margin-top: auto;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.connection-tag {
  margin-right: 5px;
  margin-bottom: 5px;
}

.empty-text {
  color: #909399;
  font-size: 14px;
}

.chart-container {
  height: 400px;
  width: 100%;
}
</style> 