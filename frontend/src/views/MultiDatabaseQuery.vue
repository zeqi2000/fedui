<template>
  <div class="multi-query-container">
    <el-row :gutter="20">
      <el-col :span="7">
        <el-card shadow="never" class="query-panel">
          <template #header>
            <div class="card-header">
              <h3>跨库查询参数</h3>
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
                @click="executeQuery"
                :loading="querying"
                :disabled="!canQuery"
              >
                执行跨库查询
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
      
      <el-col :span="17">
        <el-card shadow="never" class="results-panel">
          <template #header>
            <div class="card-header">
              <h3>跨库查询结果</h3>
              <div v-if="queryResults.length > 0">
                <el-button size="small" @click="clearResults">清除结果</el-button>
              </div>
            </div>
          </template>
          
          <div v-if="querying" class="loading-container">
            <el-skeleton :rows="10" animated />
          </div>
          
          <div v-else-if="queryResults.length === 0" class="empty-results">
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
              <el-table-column prop="database_id" label="数据库ID" width="100">
                <template #default="{ row }">
                  <el-tooltip :content="getDatabaseName(row.database_id)" placement="top" effect="light">
                    <el-tag size="small">{{ formatDatabaseId(row.database_id) }}</el-tag>
                  </el-tooltip>
                </template>
              </el-table-column>
              <el-table-column prop="collection_name" label="集合" width="120" />
              <el-table-column prop="id" label="实体ID" min-width="120" />
              <el-table-column prop="distance" label="距离" width="120">
                <template #default="{ row }">
                  {{ row.distance.toFixed(6) }}
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
      </el-col>
    </el-row>
    
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
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { ElMessage, FormInstance } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { getDatabaseConnections, getDatabaseStatistics } from '@/api/database'
import { executeMultiDatabaseQuery } from '@/api/query'

// 表单相关
const queryFormRef = ref<FormInstance>()
const queryForm = reactive({
  database_ids: [] as string[],
  collection_mapping: {} as Record<string, string>,
  input_type: 'manual',
  vector_data_text: '',
  vector_data: [] as number[],
  vector_file: null as File | null,
  top_k: 10
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

// 查询结果
const querying = ref(false)
const queryResults = ref<any[]>([])
const queryMetrics = ref<any>({})
const additionalFields = ref<string[]>([])

// 结果详情
const detailsVisible = ref(false)
const selectedResult = ref<any>(null)

// 计算属性
const canQuery = computed(() => {
  // 检查是否选择了数据库
  if (queryForm.database_ids.length === 0) {
    return false
  }
  
  // 检查是否为每个选择的数据库都指定了集合
  const hasAllCollections = queryForm.database_ids.every(dbId => 
    queryForm.collection_mapping[dbId]
  )
  
  if (!hasAllCollections) {
    return false
  }
  
  // 检查向量数据
  if (queryForm.input_type === 'manual') {
    return queryForm.vector_data.length > 0
  } else {
    return queryForm.vector_file !== null
  }
})

// 监视数据库选择变化
watch(() => queryForm.database_ids, (newVal, oldVal) => {
  // 移除未选择的数据库的集合映射
  const oldIdSet = new Set(oldVal)
  const newIdSet = new Set(newVal)
  
  // 找到被移除的数据库ID
  oldVal.forEach(id => {
    if (!newIdSet.has(id)) {
      delete queryForm.collection_mapping[id]
    }
  })
  
  // 对于新添加的数据库，如果只有一个集合，则自动选择它
  newVal.forEach(id => {
    if (!oldIdSet.has(id)) {
      const collections = databaseCollections.value[id] || []
      if (collections.length === 1) {
        queryForm.collection_mapping[id] = collections[0].name
      }
    }
  })
  
  // 更新全选状态
  updateSelectAllState()
}, { deep: true })

// 获取可用的数据库
const fetchDatabases = async () => {
  loadingDatabases.value = true
  try {
    const databases = await getDatabaseConnections()
    availableDatabases.value = databases.filter((db: any) => db.status === '已连接')
    
    // 为每个可用的数据库获取集合
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
      // 尝试解析用户输入的向量数据
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
    
    // 预览文件内容
    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const content = e.target?.result as string
        const parsed = JSON.parse(content)
        if (Array.isArray(parsed) && parsed.every(v => typeof v === 'number')) {
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
    // 选择所有可用的数据库
    queryForm.database_ids = availableDatabases.value
      .filter(db => db.status === '已连接')
      .map(db => db.id)
  } else {
    // 取消选择所有数据库
    queryForm.database_ids = []
  }
}

// 更新全选状态
const updateSelectAllState = () => {
  const availableDbIds = availableDatabases.value
    .filter(db => db.status === '已连接')
    .map(db => db.id)
  
  // 如果选中的数据库包含所有可用的数据库，则全选状态为true
  selectAllDatabases.value = availableDbIds.length > 0 && 
    availableDbIds.every(id => queryForm.database_ids.includes(id))
}

// 验证集合映射
const validateCollectionMapping = () => {
  if (queryFormRef.value) {
    queryFormRef.value.validateField('database_ids')
  }
}

// 执行查询
const executeQuery = async () => {
  if (!queryFormRef.value) return
  
  await queryFormRef.value.validate(async (valid) => {
    if (valid) {
      querying.value = true
      queryResults.value = []
      queryMetrics.value = {}
      additionalFields.value = []
      
      try {
        // 准备查询参数
        const queryParams = {
          database_ids: queryForm.database_ids,
          collection_names: queryForm.collection_mapping,
          vector_data: queryForm.vector_data,
          top_k: queryForm.top_k
        }
        
        // 执行跨库查询
        const result = await executeMultiDatabaseQuery(queryParams)
        
        if (result) {
          queryResults.value = result.aggregated_results
          queryMetrics.value = result.metrics
          
          // 提取额外字段
          if (queryResults.value.length > 0) {
            additionalFields.value = Object.keys(queryResults.value[0])
              .filter(key => !['database_id', 'collection_name', 'id', 'distance'].includes(key))
          }
          
          ElMessage.success('跨库查询成功')
        }
      } catch (error) {
        console.error('执行跨库查询失败:', error)
        ElMessage.error('执行跨库查询失败')
      } finally {
        querying.value = false
      }
    }
  })
}

// 清除结果
const clearResults = () => {
  queryResults.value = []
  queryMetrics.value = {}
  additionalFields.value = []
}

// 显示结果详情
const showResultDetails = (row: any) => {
  selectedResult.value = row
  detailsVisible.value = true
}

// 格式化数据库ID（取前8位）
const formatDatabaseId = (id: string) => {
  return id ? id.substring(0, 8) + '...' : ''
}

// 获取数据库名称
const getDatabaseName = (id: string) => {
  const db = availableDatabases.value.find(db => db.id === id)
  return db ? db.name : id
}

onMounted(() => {
  fetchDatabases()
})
</script>

<style scoped>
.multi-query-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.query-panel {
  height: 100%;
}

.results-panel {
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

.metrics-summary {
  margin-bottom: 20px;
}

.error-summary {
  margin-top: 10px;
}

.results-content {
  padding: 10px 0;
}
</style> 