<template>
  <div class="database-manager-container">
    <div class="header-actions">
      <el-button type="primary" @click="openCreateDialog">
        <el-icon><Plus /></el-icon> 添加联邦参与方
      </el-button>
      <el-button @click="refreshDatabases">
        <el-icon><Refresh /></el-icon> 刷新
      </el-button>
    </div>
    
    <el-card shadow="never" class="database-list">
      <template #header>
        <div class="card-header">
          <h3>联邦参与方连接列表</h3>
        </div>
      </template>
      
      <el-table
        v-loading="loading"
        :data="databaseList"
        style="width: 100%"
        border
      >
        <el-table-column prop="name" label="名称" min-width="120" />
        <el-table-column prop="host" label="主机地址" min-width="150" />
        <el-table-column prop="port" label="端口" width="100" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag
              :type="row.status === '已连接' ? 'success' : (row.status === '连接失败' ? 'danger' : 'info')"
              effect="plain"
            >
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="200">
          <template #default="{ row }">
            {{ row.description || '无描述' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button-group>
              <el-button
                v-if="row.status !== '已连接'"
                size="small"
                type="primary"
                @click="connectToDatabase(row)"
                :loading="row.connecting"
              >
                连接
              </el-button>
              <el-button
                v-else
                size="small"
                type="warning"
                @click="disconnectFromDatabase(row)"
                :loading="row.disconnecting"
              >
                断开
              </el-button>
              <el-button
                size="small"
                type="success"
                @click="showDatabaseDetails(row)"
                :disabled="row.status !== '已连接'"
              >
                统计
              </el-button>
              <el-button
                size="small"
                type="info"
                @click="editDatabase(row)"
              >
                编辑
              </el-button>
              <el-button
                size="small"
                type="danger"
                @click="confirmDeleteDatabase(row)"
              >
                删除
              </el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <!-- 创建/编辑数据库表单对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑数据库连接' : '添加数据库连接'"
      width="500px"
    >
      <el-form
        ref="databaseFormRef"
        :model="databaseForm"
        :rules="databaseRules"
        label-width="100px"
      >
        <el-form-item label="名称" prop="name">
          <el-input v-model="databaseForm.name" placeholder="输入连接名称" />
        </el-form-item>
        <el-form-item label="主机地址" prop="host">
          <el-input v-model="databaseForm.host" placeholder="输入主机地址或IP" />
        </el-form-item>
        <el-form-item label="端口" prop="port">
          <el-input-number v-model="databaseForm.port" :min="1" :max="65535" />
        </el-form-item>
        <el-form-item label="用户名">
          <el-input v-model="databaseForm.username" placeholder="输入用户名(可选)" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input
            v-model="databaseForm.password"
            type="password"
            placeholder="输入密码(可选)"
            show-password
          />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="databaseForm.description"
            type="textarea"
            :rows="3"
            placeholder="输入数据库连接描述(可选)"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitDatabaseForm" :loading="submitting">
            确定
          </el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 数据库详情对话框 -->
    <el-dialog
      v-model="detailsVisible"
      title="数据库详情"
      width="800px"
    >
      <div v-loading="loadingDetails">
        <template v-if="selectedDatabase">
          <h4>{{ selectedDatabase.name }} - 集合列表</h4>
          
          <el-table :data="databaseDetails?.collections || []" border style="width: 100%; margin-top: 20px;">
            <el-table-column prop="name" label="集合名称" min-width="150" />
            <el-table-column prop="entity_count" label="实体数量" width="120" />
            <el-table-column prop="index_status" label="索引状态" width="120">
              <template #default="{ row }">
                <el-tag
                  :type="row.index_status === '已创建' ? 'success' : 'warning'"
                  effect="plain"
                >
                  {{ row.index_status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="description" label="描述" min-width="200">
              <template #default="{ row }">
                {{ row.description || '无描述' }}
              </template>
            </el-table-column>
          </el-table>
          
          <div class="statistics-summary" v-if="databaseDetails">
            <el-descriptions title="数据库统计信息" :column="2" border>
              <el-descriptions-item label="集合总数">{{ databaseDetails.collection_count }}</el-descriptions-item>
              <el-descriptions-item label="实体总数">{{ databaseDetails.total_entities }}</el-descriptions-item>
            </el-descriptions>
          </div>
        </template>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, FormInstance } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import {
  getDatabaseConnections,
  createDatabaseConnection,
  updateDatabaseConnection,
  deleteDatabaseConnection,
  apiConnectToDatabase,
  apiDisconnectFromDatabase,
  getDatabaseStatistics
} from '@/api/database'

// 数据库列表
const databaseList = ref<any[]>([])
const loading = ref(false)

// 表单相关
const databaseFormRef = ref<FormInstance>()
const dialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const currentEditId = ref('')

const databaseForm = reactive({
  name: '',
  host: '',
  port: 19530,
  username: '',
  password: '',
  description: ''
})

const databaseRules = {
  name: [
    { required: true, message: '请输入连接名称', trigger: 'blur' }
  ],
  host: [
    { required: true, message: '请输入主机地址', trigger: 'blur' }
  ],
  port: [
    { required: true, message: '请输入端口号', trigger: 'blur' }
  ]
}

// 数据库详情
const detailsVisible = ref(false)
const loadingDetails = ref(false)
const selectedDatabase = ref<any>(null)
const databaseDetails = ref<any>(null)

// 获取数据库连接列表
const fetchDatabases = async () => {
  loading.value = true
  try {
    const data = await getDatabaseConnections()
    databaseList.value = data.map((db: any) => ({
      ...db,
      connecting: false,
      disconnecting: false
    }))
  } catch (error) {
    console.error('获取数据库连接失败:', error)
    ElMessage.error('获取数据库连接列表失败')
  } finally {
    loading.value = false
  }
}

// 刷新数据库列表
const refreshDatabases = () => {
  fetchDatabases()
}

// 打开创建数据库对话框
const openCreateDialog = () => {
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

// 打开编辑数据库对话框
const editDatabase = (row: any) => {
  isEdit.value = true
  currentEditId.value = row.id
  Object.assign(databaseForm, {
    name: row.name,
    host: row.host,
    port: row.port,
    username: row.username || '',
    password: '', // 不回显密码
    description: row.description || ''
  })
  dialogVisible.value = true
}

// 重置表单
const resetForm = () => {
  if (databaseFormRef.value) {
    databaseFormRef.value.resetFields()
  }
  databaseForm.name = ''
  databaseForm.host = ''
  databaseForm.port = 19530
  databaseForm.username = ''
  databaseForm.password = ''
  databaseForm.description = ''
  currentEditId.value = ''
}

// 提交数据库表单
const submitDatabaseForm = async () => {
  if (!databaseFormRef.value) return
  
  await databaseFormRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        if (isEdit.value && currentEditId.value) {
          // 编辑现有数据库
          const updateData = { ...databaseForm }
          // 如果密码为空，不更新密码
          if (!updateData.password) {
            delete updateData.password
          }
          await updateDatabaseConnection(currentEditId.value, updateData)
          ElMessage.success('数据库连接更新成功')
        } else {
          // 创建新数据库
          await createDatabaseConnection(databaseForm)
          ElMessage.success('数据库连接创建成功')
        }
        dialogVisible.value = false
        fetchDatabases()
      } catch (error) {
        console.error('保存数据库连接失败:', error)
        ElMessage.error('保存数据库连接失败')
      } finally {
        submitting.value = false
      }
    }
  })
}

// 确认删除数据库
const confirmDeleteDatabase = (row: any) => {
  ElMessageBox.confirm(
    `确认删除数据库连接 "${row.name}" 吗？此操作不可逆。`,
    '警告',
    {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      await deleteDatabaseConnection(row.id)
      ElMessage.success('数据库连接删除成功')
      fetchDatabases()
    } catch (error) {
      console.error('删除数据库连接失败:', error)
      ElMessage.error('删除数据库连接失败')
    }
  }).catch(() => {
    // 用户取消操作
  })
}

// 连接到数据库
const connectToDatabase = async (row: any) => {
  const index = databaseList.value.findIndex(item => item.id === row.id)
  if (index === -1) return
  
  databaseList.value[index].connecting = true
  try {
    const result = await apiConnectToDatabase(row.id)
    databaseList.value[index].status = result.status
    // consolo.log("连接结果")
    console.log(result)
    ElMessage.success(`连接到数据库 ${row.name} 成功`)
    fetchDatabases() // 刷新列表以更新状态
  } catch (error) {
    console.error(`连接到数据库 ${row.name} 失败:`, error)
    ElMessage.error(`连接到数据库 ${row.name} 失败`)
  } finally {
    databaseList.value[index].connecting = false
  }
}

// 断开与数据库的连接
const disconnectFromDatabase = async (row: any) => {
  const index = databaseList.value.findIndex(item => item.id === row.id)
  if (index === -1) return
  
  databaseList.value[index].disconnecting = true
  try {
    const result = await apiDisconnectFromDatabase(row.id)
    databaseList.value[index].status = result.status
    ElMessage.success(`已断开与数据库 ${row.name} 的连接`)
    fetchDatabases() // 刷新列表以更新状态
  } catch (error) {
    console.error(`断开与数据库 ${row.name} 的连接失败:`, error)
    ElMessage.error(`断开与数据库 ${row.name} 的连接失败`)
  } finally {
    databaseList.value[index].disconnecting = false
  }
}

// 显示数据库详情
const showDatabaseDetails = async (row: any) => {
  selectedDatabase.value = row
  detailsVisible.value = true
  loadingDetails.value = true
  
  try {
    const data = await getDatabaseStatistics(row.id)
    databaseDetails.value = data
  } catch (error) {
    console.error('获取数据库统计信息失败:', error)
    ElMessage.error('获取数据库统计信息失败')
  } finally {
    loadingDetails.value = false
  }
}

onMounted(() => {
  fetchDatabases()
})
</script>

<style scoped>
.database-manager-container {
  padding: 20px;
}

.header-actions {
  margin-bottom: 20px;
  display: flex;
  gap: 10px;
}

.database-list {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.statistics-summary {
  margin-top: 30px;
}
</style> 