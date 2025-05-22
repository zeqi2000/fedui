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
              <div class="table-vector-container" @click="toggleTableVectorExpand(row)">
                <span class="vector-toggle-button">{{ tableExpandedRows[row.id] ? '收起' : '展开' }}</span>
                <span v-if="!tableExpandedRows[row.id]">
                  {{ formatVector(getVectorData(row), false) }}
                </span>
                <span v-else class="full-vector-preview">
                  {{ formatVector(getVectorData(row), true) }}
                </span>
              </div>
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
          
          <div v-for="(fieldName, index) in Object.keys(selectedResult)" :key="index">
            <el-descriptions-item
              v-if="!['database_id', 'collection_name', 'id', 'distance'].includes(fieldName)"
              :label="fieldName"
            >
              <template v-if="isVectorField(fieldName, selectedResult[fieldName])">
                <div class="vector-container">
                  <div class="vector-preview-container" @click="toggleVectorExpand(fieldName)">
                    <span class="vector-toggle-button">{{ expandedFields[fieldName] ? '收起' : '展开' }}</span>
                    <span v-if="!expandedFields[fieldName]">
                      [{{ selectedResult[fieldName].slice(0, 5).map((v: number) => typeof v === 'number' ? v.toFixed(4) : v).join(', ') }}...]
                      <span class="vector-length">(长度: {{ selectedResult[fieldName].length }})</span>
                    </span>
                    <div v-else class="full-vector">
                      [{{ selectedResult[fieldName].map((v: number) => typeof v === 'number' ? v.toFixed(4) : v).join(', ') }}]
                    </div>
                  </div>
                </div>
              </template>
              <template v-else>
                {{ typeof selectedResult[fieldName] === 'object' ? JSON.stringify(selectedResult[fieldName]) : selectedResult[fieldName] }}
              </template>
            </el-descriptions-item>
          </div>
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
const expandedFields = ref<Record<string, boolean>>({})  // 记录每个字段的展开状态

// 数据库信息
const availableDatabases = ref<any[]>([])

// 表格向量展开状态
const tableExpandedRows = ref<Record<string, boolean>>({})

// 获取数据库名称
const getDatabaseName = (id: string) => {
  const db = availableDatabases.value.find(db => db.id === id)
  return db ? db.name : id
}

// 格式化数据库ID
const formatDatabaseId = (id: string) => {
  return id ? id.substring(0, 8) + '...' : ''
}

// 判断字段是否为向量字段
const isVectorField = (fieldName: string, value: any): boolean => {
  // 检查字段名是否为已知的向量字段名
  const knownVectorFields = ['emb', 'vector', 'embedding', 'vec']
  
  // 判断值是否为数值数组（向量）
  const isVectorValue = Array.isArray(value) && 
                        value.length > 0 && 
                        value.every((v: any) => typeof v === 'number')
  
  return isVectorValue && (knownVectorFields.includes(fieldName) || value.length > 10)
}

// 切换向量展开状态
const toggleVectorExpand = (fieldName: string) => {
  expandedFields.value = {
    ...expandedFields.value,
    [fieldName]: !expandedFields.value[fieldName]
  }
}

// 切换表格向量展开状态
const toggleTableVectorExpand = (row: any) => {
  const rowId = row.id
  tableExpandedRows.value = {
    ...tableExpandedRows.value,
    [rowId]: !tableExpandedRows.value[rowId]
  }
}

// 显示结果详情
const showResultDetails = (row: any) => {
  selectedResult.value = row
  detailsVisible.value = true
  expandedFields.value = {}  // 重置所有字段的展开状态
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
  // 首先检查emb字段，因为这是后端查询中使用的字段
  if (row.emb) return row.emb
  
  // 然后检查其他可能的向量字段
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
  
  // 如果没有找到向量，返回空数组
  return []
}

// 修改格式化向量的函数
const formatVector = (vector: number[], expanded: boolean = false) => {
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
  
  if (expanded) {
    // 展开状态：显示全部元素
    return `[${formatted.join(', ')}]`
  } else {
    // 折叠状态：只显示前几个元素
    return `[${formatted.slice(0, 3).join(', ')}${vector.length > 3 ? ', ...' : ''}] (长度: ${vector.length})`
  }
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
            .filter(key => !['database_id', 'collection_name', 'id', 'distance', 'vector', 'embedding', 'vec', 'emb'].includes(key))
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
                .filter(key => !['database_id', 'collection_name', 'id', 'distance', 'vector', 'embedding', 'vec', 'emb'].includes(key))
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

.vector-length {
  color: #909399;
  font-size: 0.9em;
  margin-left: 5px;
}

.vector-container {
  max-width: 100%;
  overflow: hidden;
}

.vector-preview-container {
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.vector-preview-container:hover {
  background-color: #f5f7fa;
}

.vector-toggle-button {
  color: #409EFF;
  margin-right: 8px;
  font-weight: bold;
}

.full-vector {
  max-height: 200px;
  overflow-y: auto;
  font-family: monospace;
  white-space: pre-wrap;
  word-break: break-all;
  margin-top: 5px;
  padding: 8px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.table-vector-container {
  cursor: pointer;
  padding: 2px 0;
  transition: background-color 0.3s;
  font-family: monospace;
}

.table-vector-container:hover {
  background-color: #f5f7fa;
}

.full-vector-preview {
  display: block;
  max-height: 100px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-all;
  background-color: #f5f7fa;
  padding: 4px;
  border-radius: 4px;
  margin-top: 4px;
}
</style> 