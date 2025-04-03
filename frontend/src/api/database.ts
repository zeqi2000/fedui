import { apiClient } from './client'

// 获取所有数据库连接
export async function getDatabaseConnections() {
  const response = await apiClient.get('/api/database/connections')
  return response.data
}

// 创建数据库连接
export async function createDatabaseConnection(data: {
  name: string
  host: string
  port: number
  username?: string
  password?: string
  description?: string
}) {
  const response = await apiClient.post('/api/database/connections', data)
  return response.data
}

// 更新数据库连接
export async function updateDatabaseConnection(id: string, data: {
  name?: string
  host?: string
  port?: number
  username?: string
  password?: string
  description?: string
}) {
  const response = await apiClient.put(`/api/database/connections/${id}`, data)
  return response.data
}

// 删除数据库连接
export async function deleteDatabaseConnection(id: string) {
  const response = await apiClient.delete(`/api/database/connections/${id}`)
  return response.data
}

// 连接到数据库
export async function apiConnectToDatabase(id: string) {
  const response = await apiClient.post(`/api/database/connections/${id}/connect`)
  return response.data
}

// 断开与数据库的连接
export async function apiDisconnectFromDatabase(id: string) {
  const response = await apiClient.post(`/api/database/connections/${id}/disconnect`)
  return response.data
}

// 获取数据库统计信息
export async function getDatabaseStatistics(id: string) {
  const response = await apiClient.get(`/api/database/connections/${id}/statistics`)
  return response.data
} 