from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import Any, List, Dict, Optional, Union
import json

from schemas.user import User
from schemas.query import (
    VectorQuery,
    TextToVectorQuery,
    QueryResult,
    MultiDatabaseQuery,
    MultiDatabaseQueryResult
)
from core.security import get_current_user
from services.query import execute_vector_query, execute_multi_db_query

router = APIRouter()

@router.post("/vector", response_model=QueryResult)
async def query_vector(
    query: VectorQuery,
    current_user: User = Depends(get_current_user)
) -> Any:
    """执行向量查询"""
    try:
        result = execute_vector_query(
            database_id=query.database_id,
            collection_name=query.collection_name,
            vector_data=query.vector_data,
            top_k=query.top_k,
            search_params=query.search_params,
            output_fields=query.output_fields
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/multi", response_model=MultiDatabaseQueryResult)
async def query_multiple_databases(
    query: MultiDatabaseQuery,
    current_user: User = Depends(get_current_user)
) -> Any:
    """在多个数据库上执行查询"""
    try:
        result = execute_multi_db_query(
            database_ids=query.database_ids,
            collection_names=query.collection_names,
            vector_data=query.vector_data,
            top_k=query.top_k,
            search_params=query.search_params,
            output_fields=query.output_fields
        )
        print("route:query_multiple_databases")
        print(result)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/upload-vector", response_model=QueryResult)
async def query_with_uploaded_vector(
    database_id: str = Form(...),
    collection_name: str = Form(...),
    top_k: int = Form(10),
    vector_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
) -> Any:
    """通过上传向量文件进行查询"""
    try:
        # 读取上传的向量文件
        vector_data = json.loads(await vector_file.read())
        
        # 执行查询
        result = execute_vector_query(
            database_id=database_id,
            collection_name=collection_name,
            vector_data=vector_data,
            top_k=top_k
        )
        return result
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的向量文件格式，请提供有效的JSON"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) 