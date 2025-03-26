from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any, List, Dict, Optional

from schemas.user import User
from schemas.database import (
    DatabaseConnection, 
    DatabaseConnectionCreate,
    DatabaseConnectionUpdate,
    DatabaseStatus,
    DatabaseStatistics
)
from core.security import get_current_user, get_admin_user
from services.database import (
    get_db_connections,
    create_db_connection,
    update_db_connection,
    delete_db_connection,
    connect_to_db,
    disconnect_from_db,
    get_db_statistics
)

router = APIRouter()

@router.get("/connections", response_model=List[DatabaseConnection])
async def get_connections(current_user: User = Depends(get_current_user)) -> Any:
    """获取所有数据库连接"""
    connections = get_db_connections()
    return [DatabaseConnection(**conn) for conn in connections]

@router.post("/connections", response_model=DatabaseConnection)
async def create_connection(
    connection_in: DatabaseConnectionCreate, 
    admin: User = Depends(get_admin_user)
) -> Any:
    """创建新的数据库连接"""
    try:
        connection = create_db_connection(connection_in, admin)
        return connection
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.put("/connections/{connection_id}", response_model=DatabaseConnection)
async def update_connection(
    connection_id: str,
    connection_in: DatabaseConnectionUpdate,
    admin: User = Depends(get_admin_user)
) -> Any:
    """更新数据库连接"""
    connection = update_db_connection(connection_id, connection_in)
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="连接不存在"
        )
    return connection

@router.delete("/connections/{connection_id}", response_model=Dict[str, bool])
async def delete_connection(
    connection_id: str,
    admin: User = Depends(get_admin_user)
) -> Any:
    """删除数据库连接"""
    success = delete_db_connection(connection_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="连接不存在"
        )
    return {"success": True}

@router.post("/connections/{connection_id}/connect", response_model=DatabaseStatus)
async def connect_to_database(
    connection_id: str,
    admin: User = Depends(get_admin_user)
) -> Any:
    """连接到数据库"""
    try:
        status = connect_to_db(connection_id)
        return status
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/connections/{connection_id}/disconnect", response_model=DatabaseStatus)
async def disconnect_from_database(
    connection_id: str,
    admin: User = Depends(get_admin_user)
) -> Any:
    """断开与数据库的连接"""
    try:
        status = disconnect_from_db(connection_id)
        return status
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/connections/{connection_id}/statistics", response_model=DatabaseStatistics)
async def get_database_statistics(
    connection_id: str,
    current_user: User = Depends(get_current_user)
) -> Any:
    """获取数据库统计信息"""
    try:
        stats = get_db_statistics(connection_id)
        return stats
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) 