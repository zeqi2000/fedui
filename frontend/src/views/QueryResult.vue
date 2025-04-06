<template>
  <div class="query-result-container">
    <el-card shadow="never" class="result-panel">
      <template #header>
        <div class="card-header">
          <h3>查询结果</h3>
          <div class="header-actions">
            <el-button size="small" @click="goBack">返回</el-button>
            <el-button size="small" @click="exportResults">导出结果</el-button>
          </div>
        </div>
      </template>
      
      <div v-if="loading" class="loading-container">
        <el-skeleton :rows="10" animated />
      </div>
      
      <div v-else-if="!queryResult" class="empty-results">
        <el-empty description="暂无查询结果" />
      </div>
      
      <div v-else class="results-content">
        <div class="metrics-summary">
          <el-alert
            title="跨库查询成功"
            type="success"
            :closable="false"
            show-icon
          >
            <template #default>
              执行时间: {{ queryMetrics.total_execution_time?.toFixed(4) || 0 }}s，
              结果数量: {{ queryMetrics.total_results || 0 }}，
              查询数据库: {{ queryMetrics.database_count || 0 }} 个
            </template>
          </el-alert>
          
          <div v-if="queryMetrics.errors && queryMetrics.errors.length > 0" class="error-summary">
            <el-alert
              title="部分查询出现错误"
              type="warning"
              :closable="false"
              show-icon
            >
              <template #default>
                <div v-for="(error, index) in queryMetrics.errors" :key="index">
                  {{ error }}
                </div>
              </template>
            </el-alert>
          </div>
        </div>
        
        <el-table
          :data="queryResults"
          style="width: 100%; margin-top: 15px"
          border
          stripe
          max-height="500"
        >
          <el-table-column type="index" label="#" width="60" />
          <el-table-column prop="distance" label="距离" width="120">
            <template #default="{ row }">
              {{ row.distance.toFixed(6) }}
            </template>
          </el-table-column>
          
          <el-table-column label="向量" min-width="300">
            <template #default="{ row }">
              <el-tooltip :content="JSON.stringify(getVectorData(row))" placement="top" effect="light">
                <span class="vector-preview">
                  {{ formatVector(getVectorData(row)) }}
                </span>
              </el-tooltip>
            </template>
          </el-table-column>
          
          <el-table-column
            v-for="field in additionalFields"
            :key="field"
            :prop="field"
            :label="field"
            min-width="150"
          />
          
          <el-table-column label="详情" width="80" fixed="right">
            <template #default="{ row }">
              <el-button
                link
                type="primary"
                size="small"
                @click="showResultDetails(row)"
              >
                详情
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>
    
    <!-- 结果详情对话框 -->
    <el-dialog
      v-model="detailsVisible"
      title="结果详情"
      width="600px"
    >
      <div v-if="selectedResult">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="数据库">
            {{ getDatabaseName(selectedResult.database_id) }}
          </el-descriptions-item>
          <el-descriptions-item label="集合">
            {{ selectedResult.collection_name }}
          </el-descriptions-item>
          <el-descriptions-item label="实体ID">
            {{ selectedResult.id }}
          </el-descriptions-item>
          <el-descriptions-item label="距离">
            {{ selectedResult.distance.toFixed(6) }}
          </el-descriptions-item>
          
          <el-descriptions-item
            v-for="(value, key) in selectedResult"
            :key="key"
            :label="key"
            v-if="!['database_id', 'collection_name', 'id', 'distance'].includes(key)"
          >
            {{ typeof value === 'object' ? JSON.stringify(value) : value }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getDatabaseConnections } from '@/api/database'

const route = useRoute()
const router = useRouter()

// 查询结果
const loading = ref(false)
const queryResult = ref<any>(null)
const queryResults = ref<any[]>([])
const queryMetrics = ref<any>({})
const additionalFields = ref<string[]>([])

// 结果详情
const detailsVisible = ref(false)
const selectedResult = ref<any>(null)

// 数据库信息
const availableDatabases = ref<any[]>([])

// 获取数据库名称
const getDatabaseName = (id: string) => {
  const db = availableDatabases.value.find(db => db.id === id)
  return db ? db.name : id
}

// 格式化数据库ID
const formatDatabaseId = (id: string) => {
  return id ? id.substring(0, 8) + '...' : ''
}

// 显示结果详情
const showResultDetails = (row: any) => {
  selectedResult.value = row
  detailsVisible.value = true
}

// 返回上一页
const goBack = () => {
  router.back()
}

// 导出结果
const exportResults = () => {
  if (!queryResults.value.length) {
    ElMessage.warning('没有可导出的结果')
    return
  }
  
  try {
    const data = JSON.stringify(queryResults.value, null, 2)
    const blob = new Blob([data], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `query_results_${route.params.queryId}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  }
}

// 获取向量数据的函数
const getVectorData = (row: any) => {
  // 首先检查是否有直接的向量字段
  if (row.vector) return row.vector
  if (row.embedding) return row.embedding
  if (row.vec) return row.vec
  
  // 如果没有直接的向量字段，检查是否有其他包含向量的字段
  const vectorFields = Object.keys(row).filter(key => {
    const value = row[key]
    return Array.isArray(value) && 
           value.length > 0 && 
           value.every((v: any) => typeof v === 'number')
  })
  
  if (vectorFields.length > 0) {
    // 返回第一个找到的向量字段
    return row[vectorFields[0]]
  }
  
  // 如果还是没有找到，尝试从查询结果中查找
  if (queryResult.value?.aggregated_results?.length > 0) {
    const firstResult = queryResult.value.aggregated_results[0]
    const resultVectorFields = Object.keys(firstResult).filter(key => {
      const value = firstResult[key]
      return Array.isArray(value) && 
             value.length > 0 && 
             value.every((v: any) => typeof v === 'number')
    })
    
    if (resultVectorFields.length > 0) {
      return firstResult[resultVectorFields[0]]
    }
  }
  
  return []
}

// 修改格式化向量的函数
const formatVector = (vector: number[]) => {
  if (!vector || !Array.isArray(vector)) return '无向量数据'
  if (vector.length === 0) return '空向量'
  
  // 格式化向量显示
  const formatted = vector.map(v => {
    // 如果数字太小，使用科学计数法
    if (Math.abs(v) < 0.0001 && v !== 0) {
      return v.toExponential(2)
    }
    return v.toFixed(4)
  })
  
  return `[${formatted.slice(0, 3).join(', ')}${vector.length > 3 ? ', ...' : ''}]`
}

// 修改加载查询结果的函数
const loadQueryResult = async () => {
  loading.value = true
  try {
    // 从路由查询参数中获取查询结果
    const resultStr = route.query.result as string
    if (resultStr) {
      try {
        const result = JSON.parse(resultStr)
        queryResult.value = result
        queryResults.value = result.aggregated_results || []
        queryMetrics.value = result.metrics || {}
        
        // 提取额外字段，排除向量相关字段
        if (queryResults.value.length > 0) {
          additionalFields.value = Object.keys(queryResults.value[0])
            .filter(key => !['database_id', 'collection_name', 'id', 'distance', 'vector', 'embedding', 'vec'].includes(key))
        }
        
        // 打印查询结果，用于调试
        console.log('查询结果:', queryResults.value)
      } catch (error) {
        console.error('解析查询结果失败:', error)
        ElMessage.error('解析查询结果失败')
        router.push('/query-parameter')
      }
    } else {
      // 尝试从本地存储获取查询结果
      const queryId = route.params.queryId as string
      if (queryId) {
        const storedResult = localStorage.getItem(`queryResult_${queryId}`)
        if (storedResult) {
          try {
            const result = JSON.parse(storedResult)
            queryResult.value = result
            queryResults.value = result.aggregated_results || []
            queryMetrics.value = result.metrics || {}
            
            // 提取额外字段，排除向量相关字段
            if (queryResults.value.length > 0) {
              additionalFields.value = Object.keys(queryResults.value[0])
                .filter(key => !['database_id', 'collection_name', 'id', 'distance', 'vector', 'embedding', 'vec'].includes(key))
            }
            
            // 打印查询结果，用于调试
            console.log('查询结果:', queryResults.value)
          } catch (error) {
            console.error('解析存储的查询结果失败:', error)
            ElMessage.error('无法加载查询结果')
            router.push('/query-parameter')
          }
        } else {
          ElMessage.warning('未找到该次查询的结果')
          router.push('/query-parameter')
        }
      } else {
        ElMessage.warning('未找到查询结果，请重新提交查询')
        router.push('/query-parameter')
      }
    }
  } catch (error) {
    console.error('加载查询结果失败:', error)
    ElMessage.error('加载查询结果失败')
    router.push('/query-parameter')
  } finally {
    loading.value = false
  }
}

// 获取数据库列表
const fetchDatabases = async () => {
  try {
    const databases = await getDatabaseConnections()
    availableDatabases.value = databases
  } catch (error) {
    console.error('获取数据库列表失败:', error)
  }
}

onMounted(async () => {
  await fetchDatabases()
  await loadQueryResult()
})
</script>

<style scoped>
.query-result-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.result-panel {
  min-height: 600px;
}

.loading-container {
  padding: 20px 0;
}

.empty-results {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 400px;
}

.metrics-summary {
  margin-bottom: 20px;
}

.error-summary {
  margin-top: 10px;
}

.results-content {
  padding: 10px 0;
}

.vector-preview {
  font-family: monospace;
  color: #666;
  cursor: pointer;
}
</style> 