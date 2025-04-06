<template>
  <div class="query-parameter-container">
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card shadow="never" class="parameter-panel">
          <template #header>
            <div class="card-header">
              <h3>查询参数设置</h3>
            </div>
          </template>
          
          <el-form
            ref="queryFormRef"
            :model="queryForm"
            :rules="queryRules"
            label-position="top"
          >
            <!-- 数据库选择 -->
            <el-form-item label="选择数据库" prop="database_ids">
              <div class="database-selection">
                <el-checkbox
                  v-model="selectAllDatabases"
                  @change="handleSelectAllDatabases"
                  :disabled="availableDatabases.length === 0"
                >
                  全选
                </el-checkbox>
                
                <el-divider />
                
                <el-checkbox-group v-model="queryForm.database_ids">
                  <div v-for="db in availableDatabases" :key="db.id" class="database-item">
                    <el-checkbox 
                      :label="db.id"
                      :disabled="db.status !== '已连接'"
                    >
                      {{ db.name }}
                      <el-tag
                        size="small"
                        :type="db.status === '已连接' ? 'success' : 'info'"
                        effect="plain"
                        class="db-status"
                      >
                        {{ db.status }}
                      </el-tag>
                    </el-checkbox>
                    
                    <el-select
                      v-if="queryForm.database_ids.includes(db.id)"
                      v-model="queryForm.collection_mapping[db.id]"
                      placeholder="选择集合"
                      size="small"
                      class="collection-select"
                      @change="() => validateCollectionMapping()"
                    >
                      <el-option
                        v-for="col in getCollectionsForDatabase(db.id)"
                        :key="col.name"
                        :label="col.name"
                        :value="col.name"
                      >
                        {{ col.name }} ({{ col.entity_count }}条)
                      </el-option>
                    </el-select>
                  </div>
                </el-checkbox-group>
              </div>
            </el-form-item>
            
            <!-- 查询类型选择 -->
            <el-form-item label="查询类型" prop="query_type">
              <el-radio-group v-model="queryForm.query_type">
                <el-radio label="horizontal">横向查询</el-radio>
                <el-radio label="vertical">纵向查询</el-radio>
              </el-radio-group>
            </el-form-item>
            
            <!-- 向量输入 -->
            <el-form-item label="向量输入方式" prop="input_type">
              <el-radio-group v-model="queryForm.input_type">
                <el-radio label="manual">手动输入</el-radio>
                <el-radio label="upload">文件上传</el-radio>
              </el-radio-group>
            </el-form-item>
            
            <template v-if="queryForm.input_type === 'manual'">
              <el-form-item label="向量数据" prop="vector_data">
                <el-input
                  v-model="queryForm.vector_data_text"
                  type="textarea"
                  :rows="5"
                  placeholder="输入向量数据，如 [0.1, 0.2, 0.3, ...]"
                  @input="handleVectorDataInput"
                />
              </el-form-item>
            </template>
            
            <template v-else>
              <el-form-item label="向量文件" prop="vector_file">
                <el-upload
                  class="upload-demo"
                  drag
                  action="#"
                  :auto-upload="false"
                  :on-change="handleFileChange"
                  :limit="1"
                >
                  <el-icon class="el-icon--upload"><upload-filled /></el-icon>
                  <div class="el-upload__text">
                    拖拽文件到此处，或 <em>点击上传</em>
                  </div>
                  <template #tip>
                    <div class="el-upload__tip">
                      支持JSON文件，包含向量数据的数组
                    </div>
                  </template>
                </el-upload>
              </el-form-item>
            </template>
            
            <el-form-item label="Top K" prop="top_k">
              <el-input-number
                v-model="queryForm.top_k"
                :min="1"
                :max="100"
                style="width: 100%"
              />
            </el-form-item>
            
            <el-form-item>
              <el-button
                type="primary"
                style="width: 100%"
                @click="submitQuery"
                :loading="submitting"
                :disabled="!canQuery"
              >
                提交查询
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card shadow="never" class="history-panel">
          <template #header>
            <div class="card-header">
              <h3>历史查询记录</h3>
            </div>
          </template>
          
          <el-table
            :data="queryHistory"
            style="width: 100%"
            border
            stripe
            max-height="600"
          >
            <el-table-column type="index" label="#" width="60" />
            <el-table-column prop="timestamp" label="查询时间" width="180">
              <template #default="{ row }">
                {{ formatTimestamp(row.timestamp) }}
              </template>
            </el-table-column>
            <el-table-column prop="database_count" label="数据库数量" width="100" />
            <el-table-column prop="top_k" label="Top K" width="80" />
            <el-table-column label="数据库" min-width="200">
              <template #default="{ row }">
                <div class="database-list">
                  <el-tag
                    v-for="dbId in row.database_ids"
                    :key="dbId"
                    size="small"
                    class="database-tag"
                  >
                    {{ getDatabaseName(dbId) }}
                  </el-tag>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120" fixed="right">
              <template #default="{ row }">
                <el-button
                  link
                  type="primary"
                  size="small"
                  @click="viewQueryDetails(row)"
                >
                  详情
                </el-button>
                <el-button
                  link
                  type="primary"
                  size="small"
                  @click="viewQueryResults(row)"
                >
                  查看结果
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 查询详情对话框 -->
    <el-dialog
      v-model="detailsVisible"
      title="查询详情"
      width="600px"
    >
      <div v-if="selectedQuery">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="查询时间">
            {{ formatTimestamp(selectedQuery.timestamp) }}
          </el-descriptions-item>
          <el-descriptions-item label="数据库数量">
            {{ selectedQuery.database_count }}
          </el-descriptions-item>
          <el-descriptions-item label="Top K">
            {{ selectedQuery.top_k }}
          </el-descriptions-item>
          <el-descriptions-item label="数据库列表">
            <div v-for="dbId in selectedQuery.database_ids" :key="dbId" class="database-info">
              <el-tag size="small">{{ getDatabaseName(dbId) }}</el-tag>
              <span class="collection-name">
                (集合: {{ selectedQuery.collection_mapping[dbId] }})
              </span>
            </div>
          </el-descriptions-item>
          <el-descriptions-item label="向量数据">
            <pre>{{ JSON.stringify(selectedQuery.vector_data, null, 2) }}</pre>
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, FormInstance } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { getDatabaseConnections, getDatabaseStatistics } from '@/api/database'
import { executeMultiDatabaseQuery } from '@/api/query'

const router = useRouter()

// 表单相关
const queryFormRef = ref<FormInstance>()
const queryForm = reactive({
  database_ids: [] as string[],
  collection_mapping: {} as Record<string, string>,
  input_type: 'manual',
  vector_data_text: '',
  vector_data: [] as number[],
  vector_file: null as File | null,
  top_k: 10,
  query_type: 'horizontal'
})

const queryRules = {
  database_ids: [
    { 
      required: true, 
      message: '请至少选择一个数据库', 
      trigger: 'change',
      validator: (_: any, value: string[]) => value.length > 0
    }
  ],
  vector_data: [
    {
      validator: (_: any, value: any) => {
        if (queryForm.input_type === 'manual' && (!value || value.length === 0)) {
          return false
        }
        return true
      },
      message: '请输入有效的向量数据',
      trigger: 'blur'
    }
  ]
}

// 数据库和集合
const selectAllDatabases = ref(false)
const loadingDatabases = ref(false)
const databaseCollections = ref<Record<string, any[]>>({})
const availableDatabases = ref<any[]>([])

// 查询历史
const queryHistory = ref<any[]>([])
const detailsVisible = ref(false)
const selectedQuery = ref<any>(null)
const submitting = ref(false)

// 计算属性
const canQuery = computed(() => {
  if (queryForm.database_ids.length === 0) {
    return false
  }
  
  const hasAllCollections = queryForm.database_ids.every(dbId => 
    queryForm.collection_mapping[dbId]
  )
  
  if (!hasAllCollections) {
    return false
  }
  
  if (queryForm.input_type === 'manual') {
    return queryForm.vector_data.length > 0
  } else {
    return queryForm.vector_file !== null
  }
})

// 获取可用的数据库
const fetchDatabases = async () => {
  loadingDatabases.value = true
  try {
    const databases = await getDatabaseConnections()
    availableDatabases.value = databases.filter((db: any) => db.status === '已连接')
    
    for (const db of availableDatabases.value) {
      await fetchCollectionsForDatabase(db.id)
    }
  } catch (error) {
    console.error('获取数据库列表失败:', error)
    ElMessage.error('获取数据库列表失败')
  } finally {
    loadingDatabases.value = false
  }
}

// 获取指定数据库的集合
const fetchCollectionsForDatabase = async (dbId: string) => {
  try {
    const stats = await getDatabaseStatistics(dbId)
    databaseCollections.value[dbId] = stats.collections || []
  } catch (error) {
    console.error(`获取数据库 ${dbId} 的集合失败:`, error)
    databaseCollections.value[dbId] = []
  }
}

// 获取数据库的集合
const getCollectionsForDatabase = (dbId: string) => {
  return databaseCollections.value[dbId] || []
}

// 处理向量数据输入
const handleVectorDataInput = (value: string) => {
  try {
    if (value) {
      const parsed = JSON.parse(value.replace(/'/g, '"'))
      if (Array.isArray(parsed) && parsed.every(v => typeof v === 'number')) {
        queryForm.vector_data = parsed
      } else {
        queryForm.vector_data = []
      }
    } else {
      queryForm.vector_data = []
    }
  } catch (error) {
    queryForm.vector_data = []
  }
}

// 处理文件上传
const handleFileChange = (file: any) => {
  if (file && file.raw) {
    queryForm.vector_file = file.raw
    
    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const content = e.target?.result as string
        const parsed = JSON.parse(content)
        if (Array.isArray(parsed) && parsed.every(v => typeof v === 'number')) {
          queryForm.vector_data = parsed
          ElMessage.success('文件解析成功')
        } else {
          ElMessage.warning('文件格式不正确，应为数字数组')
        }
      } catch (error) {
        ElMessage.error('无法解析文件，请确保文件包含有效的JSON数组')
      }
    }
    reader.readAsText(file.raw)
  }
}

// 处理全选数据库
const handleSelectAllDatabases = (val: boolean) => {
  if (val) {
    queryForm.database_ids = availableDatabases.value
      .filter(db => db.status === '已连接')
      .map(db => db.id)
  } else {
    queryForm.database_ids = []
  }
}

// 更新全选状态
const updateSelectAllState = () => {
  const availableDbIds = availableDatabases.value
    .filter(db => db.status === '已连接')
    .map(db => db.id)
  
  selectAllDatabases.value = availableDbIds.length > 0 && 
    availableDbIds.every(id => queryForm.database_ids.includes(id))
}

// 验证集合映射
const validateCollectionMapping = () => {
  if (queryFormRef.value) {
    queryFormRef.value.validateField('database_ids')
  }
}

// 加载历史记录
const loadHistory = () => {
  try {
    const historyStr = localStorage.getItem('queryHistory')
    if (historyStr) {
      queryHistory.value = JSON.parse(historyStr)
    }
  } catch (error) {
    console.error('加载历史记录失败:', error)
    queryHistory.value = []
  }
}

// 保存历史记录
const saveHistory = () => {
  try {
    localStorage.setItem('queryHistory', JSON.stringify(queryHistory.value))
  } catch (error) {
    console.error('保存历史记录失败:', error)
  }
}

// 提交查询
const submitQuery = async () => {
  if (!queryFormRef.value) return
  
  await queryFormRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      
      try {
        const queryParams = {
          database_ids: queryForm.database_ids,
          collection_names: queryForm.collection_mapping,
          vector_data: queryForm.vector_data,
          top_k: queryForm.top_k,
          query_type: queryForm.query_type
        }
        
        const result = await executeMultiDatabaseQuery(queryParams)
        
        if (result) {
          // 保存查询记录
          const queryRecord = {
            id: Date.now().toString(),
            timestamp: new Date().toISOString(),
            database_count: queryForm.database_ids.length,
            ...queryParams
          }
          
          // 添加到历史记录
          queryHistory.value.unshift(queryRecord)
          // 保存到本地存储
          saveHistory()
          
          // 保存查询结果，确保包含查询参数
          const resultWithParams = {
            ...result,
            query_params: queryParams
          }
          localStorage.setItem(`queryResult_${queryRecord.id}`, JSON.stringify(resultWithParams))
          
          // 跳转到结果页面，并传递查询结果
          router.push({
            name: 'QueryResult',
            params: { queryId: queryRecord.id },
            query: { result: JSON.stringify(resultWithParams) }
          })
        }
      } catch (error) {
        console.error('提交查询失败:', error)
        ElMessage.error('提交查询失败')
      } finally {
        submitting.value = false
      }
    }
  })
}

// 查看查询详情
const viewQueryDetails = (query: any) => {
  selectedQuery.value = {
    ...query,
    database_ids: query.database_ids || [],
    collection_mapping: query.collection_mapping || {},
    vector_data: query.vector_data || [],
    top_k: query.top_k || 10
  }
  detailsVisible.value = true
}

// 查看查询结果
const viewQueryResults = (query: any) => {
  if (!query.id) {
    ElMessage.warning('查询记录缺少ID，无法查看结果')
    return
  }
  
  // 从本地存储中获取查询结果
  const resultStr = localStorage.getItem(`queryResult_${query.id}`)
  if (resultStr) {
    try {
      const result = JSON.parse(resultStr)
      // 跳转到结果页面，并传递查询结果
      router.push({
        name: 'QueryResult',
        params: { queryId: query.id },
        query: { result: resultStr }
      })
    } catch (error) {
      console.error('解析查询结果失败:', error)
      ElMessage.error('无法查看历史查询结果')
    }
  } else {
    ElMessage.warning('未找到该次查询的结果')
  }
}

// 格式化时间戳
const formatTimestamp = (timestamp: string) => {
  return new Date(timestamp).toLocaleString()
}

// 获取数据库名称
const getDatabaseName = (dbId: string) => {
  const db = availableDatabases.value.find(db => db.id === dbId)
  return db ? db.name : '未知数据库'
}

onMounted(() => {
  fetchDatabases()
  loadHistory()
})
</script>

<style scoped>
.query-parameter-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.parameter-panel,
.history-panel {
  height: 100%;
}

.database-selection {
  margin-bottom: 10px;
}

.database-item {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
  justify-content: space-between;
}

.db-status {
  margin-left: 5px;
}

.collection-select {
  flex: 1;
  margin-left: 10px;
  max-width: 200px;
}

.database-info {
  margin-bottom: 5px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.collection-name {
  color: #666;
  font-size: 0.9em;
}

pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  background-color: #f5f7fa;
  padding: 10px;
  border-radius: 4px;
  max-height: 200px;
  overflow-y: auto;
}

.database-list {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.database-tag {
  margin-right: 5px;
  margin-bottom: 5px;
}
</style> 