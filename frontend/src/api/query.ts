import { apiClient } from './client'
import axios from 'axios'

// 执行向量查询
export async function executeVectorQuery(data: {
  database_id: string
  collection_name: string
  vector_data: number[] | number[][]
  top_k?: number
  search_params?: any
  output_fields?: string[]
}) {
  const response = await apiClient.post('/api/query/vector', data)
  return response.data
}

// 执行跨库查询
export async function executeMultiDatabaseQuery(data: {
  database_ids: string[]
  collection_names: Record<string, string>
  vector_data: number[] | number[][]
  top_k?: number
  search_params?: any
  output_fields?: string[]
}) {
  const response = await apiClient.post('/api/query/multi', data)
  return response.data
}

// 上传向量文件进行查询
export async function uploadVectorForQuery(
  database_id: string,
  collection_name: string,
  vectorFile: File,
  top_k: number = 10
) {
  const formData = new FormData()
  formData.append('database_id', database_id)
  formData.append('collection_name', collection_name)
  formData.append('top_k', top_k.toString())
  formData.append('vector_file', vectorFile)
  
  const response = await apiClient.post('/api/query/upload-vector', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
  
  return response.data
} 