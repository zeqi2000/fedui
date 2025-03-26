<template>
  <div class="query-container">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card shadow="never" class="query-panel">
          <template #header>
            <div class="card-header">
              <h3>查询参数</h3>
            </div>
          </template>
          
          <el-form
            ref="queryFormRef"
            :model="queryForm"
            :rules="queryRules"
            label-position="top"
          >
            <el-form-item label="数据库" prop="database_id">
              <el-select
                v-model="queryForm.database_id"
                placeholder="选择数据库"
                style="width: 100%"
                @change="handleDatabaseChange"
                :loading="loadingDatabases"
              >
                <el-option
                  v-for="db in availableDatabases"
                  :key="db.id"
                  :label="db.name"
                  :value="db.id"
                  :disabled="db.status !== '已连接'"
                >
                  <span>{{ db.name }}</span>
                  <span style="float: right; color: #8492a6; font-size: 13px">
                    {{ db.status }}
                  </span>
                </el-option>
              </el-select>
            </el-form-item>
            
            <el-form-item label="集合" prop="collection_name" v-if="queryForm.database_id">
              <el-select
                v-model="queryForm.collection_name"
                placeholder="选择集合"
                style="width: 100%"
                :loading="loadingCollections"
              >
                <el-option
                  v-for="col in availableCollections"
                  :key="col.name"
                  :label="col.name"
                  :value="col.name"
                >
                  <span>{{ col.name }}</span>
                  <span style="float: right; color: #8492a6; font-size: 13px">
                    {{ col.entity_count }} 条
                  </span>
                </el-option>
              </el-select>
            </el-form-item>
            
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
                执行查询
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
      
      <el-col :span="18">
        <el-card shadow="never" class="results-panel">
          <template #header>
            <div class="card-header">
              <h3>查询结果</h3>
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
                title="查询成功"
                type="success"
                :closable="false"
                show-icon
              >
                <template #default>
                  执行时间: {{ queryMetrics.execution_time?.toFixed(4) || 0 }}s，
                  结果数量: {{ queryMetrics.total_results || 0 }}
                </template>
              </el-alert>
            </div>
            
            <el-table
              :data="queryResults"
              style="width: 100%; margin-top: 15px"
              border
              stripe
              max-height="500"
            >
              <el-table-column type="index" label="#" width="60" />
              <el-table-column prop="id" label="ID" min-width="120" />
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
          <el-descriptions-item label="ID">{{ selectedResult.id }}</el-descriptions-item>
          <el-descriptions-item label="距离">{{ selectedResult.distance.toFixed(6) }}</el-descriptions-item>
          <el-descriptions-item
            v-for="(value, key) in selectedResult"
            :key="key"
            :label="key"
            v-if="key !== 'id' && key !== 'distance'"
          >
            {{ typeof value === 'object' ? JSON.stringify(value) : value }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, FormInstance } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { getDatabaseConnections, getDatabaseStatistics } from '@/api/database'
import { executeVectorQuery, uploadVectorForQuery } from '@/api/query'

// 表单相关
const queryFormRef = ref<FormInstance>()
const queryForm = reactive({
  database_id: '',
  collection_name: '',
  input_type: 'manual',
  vector_data_text: '',
  vector_data: [] as number[],
  vector_file: null as File | null,
  top_k: 10
})

const queryRules = {
  database_id: [
    { required: true, message: '请选择数据库', trigger: 'change' }
  ],
  collection_name: [
    { required: true, message: '请选择集合', trigger: 'change' }
  ]
}

// 数据库和集合
const loadingDatabases = ref(false)
const loadingCollections = ref(false)
const availableDatabases = ref<any[]>([])
const availableCollections = ref<any[]>([])

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
  if (!queryForm.database_id || !queryForm.collection_name) {
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
    availableDatabases.value = databases
  } catch (error) {
    console.error('获取数据库列表失败:', error)
    ElMessage.error('获取数据库列表失败')
  } finally {
    loadingDatabases.value = false
  }
}

// 获取所选数据库的集合
const fetchCollections = async (dbId: string) => {
  loadingCollections.value = true
  try {
    const stats = await getDatabaseStatistics(dbId)
    availableCollections.value = stats.collections || []
    
    // 如果当前选择的集合不在列表中，清空选择
    if (queryForm.collection_name && !availableCollections.value.find(c => c.name === queryForm.collection_name)) {
      queryForm.collection_name = ''
    }
  } catch (error) {
    console.error('获取集合列表失败:', error)
    ElMessage.error('获取集合列表失败')
  } finally {
    loadingCollections.value = false
  }
}

// 处理数据库切换
const handleDatabaseChange = (dbId: string) => {
  queryForm.collection_name = ''
  if (dbId) {
    fetchCollections(dbId)
  } else {
    availableCollections.value = []
  }
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
        let result
        
        if (queryForm.input_type === 'manual') {
          // 执行手动输入的向量查询
          result = await executeVectorQuery({
            database_id: queryForm.database_id,
            collection_name: queryForm.collection_name,
            vector_data: queryForm.vector_data,
            top_k: queryForm.top_k
          })
        } else if (queryForm.vector_file) {
          // 执行文件上传的向量查询
          result = await uploadVectorForQuery(
            queryForm.database_id,
            queryForm.collection_name,
            queryForm.vector_file,
            queryForm.top_k
          )
        }
        
        if (result) {
          queryResults.value = result.results
          queryMetrics.value = result.metrics
          
          // 提取额外字段
          if (queryResults.value.length > 0) {
            additionalFields.value = Object.keys(queryResults.value[0])
              .filter(key => key !== 'id' && key !== 'distance')
          }
          
          ElMessage.success('查询成功')
        }
      } catch (error) {
        console.error('执行查询失败:', error)
        ElMessage.error('执行查询失败')
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

onMounted(() => {
  fetchDatabases()
})
</script>

<style scoped>
.query-container {
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

.metrics-summary {
  margin-bottom: 20px;
}

.results-content {
  padding: 10px 0;
}
</style> 