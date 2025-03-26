import json
import os
import uuid
import time
from typing import List, Dict, Any, Optional
from pymilvus import connections, Collection, utility
from schemas.database import (
    DatabaseConnection, 
    DatabaseConnectionCreate,
    DatabaseConnectionUpdate,
    DatabaseStatus,
    DatabaseStatistics
)
from core.config import settings
from schemas.user import User

def get_db_connections() -> List[Dict]:
    """获取所有数据库连接"""
    try:
        if os.path.exists(settings.DATABASE_PATH):
            with open(settings.DATABASE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("database_connections", [])
        return []
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_db_connections(connections_data: List[Dict]) -> None:
    """保存数据库连接信息"""
    try:
        if os.path.exists(settings.DATABASE_PATH):
            with open(settings.DATABASE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {"users": []}
            
        data["database_connections"] = connections_data
        
        with open(settings.DATABASE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"保存数据库连接信息时出错: {e}")

def get_connection_by_id(connection_id: str) -> Optional[Dict]:
    """通过ID获取数据库连接"""
    connections = get_db_connections()
    for conn in connections:
        if conn["id"] == connection_id:
            return conn
    return None

def create_db_connection(connection_in: DatabaseConnectionCreate, current_user: User) -> DatabaseConnection:
    """创建新的数据库连接"""
    connections = get_db_connections()
    
    # 检查名称是否已存在
    if any(conn["name"] == connection_in.name for conn in connections):
        raise ValueError("连接名称已存在")
    
    connection_id = str(uuid.uuid4())
    new_connection = {
        "id": connection_id,
        "name": connection_in.name,
        "host": connection_in.host,
        "port": connection_in.port,
        "username": connection_in.username,
        "password": connection_in.password,
        "description": connection_in.description,
        "status": "未连接",
        "created_by": current_user.id
    }
    
    connections.append(new_connection)
    save_db_connections(connections)
    
    return DatabaseConnection(**new_connection)

def update_db_connection(connection_id: str, connection_in: DatabaseConnectionUpdate) -> Optional[DatabaseConnection]:
    """更新数据库连接信息"""
    connections = get_db_connections()
    connection = None
    
    for i, conn in enumerate(connections):
        if conn["id"] == connection_id:
            connection = conn
            
            # 更新字段
            if connection_in.name is not None:
                connection["name"] = connection_in.name
            if connection_in.host is not None:
                connection["host"] = connection_in.host
            if connection_in.port is not None:
                connection["port"] = connection_in.port
            if connection_in.username is not None:
                connection["username"] = connection_in.username
            if connection_in.password is not None:
                connection["password"] = connection_in.password
            if connection_in.description is not None:
                connection["description"] = connection_in.description
                
            connections[i] = connection
            break
            
    if connection:
        save_db_connections(connections)
        return DatabaseConnection(**connection)
    
    return None

def delete_db_connection(connection_id: str) -> bool:
    """删除数据库连接"""
    connections = get_db_connections()
    initial_count = len(connections)
    
    connections = [conn for conn in connections if conn["id"] != connection_id]
    
    if len(connections) < initial_count:
        save_db_connections(connections)
        return True
    
    return False

def connect_to_db(connection_id: str) -> DatabaseStatus:
    """连接到指定的数据库"""
    connection = get_connection_by_id(connection_id)
    if not connection:
        raise ValueError("数据库连接不存在")
    
    # 尝试连接到Milvus
    try:
        alias = f"conn_{connection_id}"
        connections.connect(
            alias=alias,
            host=connection["host"],
            port=connection["port"],
            user=connection.get("username"),
            password=connection.get("password"),
            secure=True if connection.get("username") else False
        )
        
        # 检查连接是否成功
        if utility.has_connection(alias):
            # 更新连接状态
            connection["status"] = "已连接"
            update_connection_status(connection_id, "已连接")
            
            return DatabaseStatus(
                id=connection_id,
                status="已连接",
                details={"message": "连接成功"}
            )
        else:
            update_connection_status(connection_id, "连接失败")
            return DatabaseStatus(
                id=connection_id,
                status="连接失败",
                details={"message": "无法建立连接"}
            )
    except Exception as e:
        update_connection_status(connection_id, "连接失败")
        return DatabaseStatus(
            id=connection_id,
            status="连接失败",
            details={"message": str(e)}
        )

def disconnect_from_db(connection_id: str) -> DatabaseStatus:
    """断开与指定数据库的连接"""
    connection = get_connection_by_id(connection_id)
    if not connection:
        raise ValueError("数据库连接不存在")
    
    alias = f"conn_{connection_id}"
    try:
        if utility.has_connection(alias):
            connections.disconnect(alias)
            
        update_connection_status(connection_id, "未连接")
        return DatabaseStatus(
            id=connection_id,
            status="未连接",
            details={"message": "已断开连接"}
        )
    except Exception as e:
        return DatabaseStatus(
            id=connection_id,
            status=connection["status"],
            details={"message": f"断开连接时出错: {str(e)}"}
        )

def update_connection_status(connection_id: str, status: str) -> None:
    """更新连接状态"""
    connections_data = get_db_connections()
    
    for i, conn in enumerate(connections_data):
        if conn["id"] == connection_id:
            conn["status"] = status
            connections_data[i] = conn
            break
            
    save_db_connections(connections_data)

def get_db_statistics(connection_id: str) -> DatabaseStatistics:
    """获取数据库统计信息"""
    connection = get_connection_by_id(connection_id)
    if not connection:
        raise ValueError("数据库连接不存在")
    
    alias = f"conn_{connection_id}"
    try:
        if not utility.has_connection(alias):
            # 尝试连接
            connect_to_db(connection_id)
            
        # 获取所有集合
        collection_names = utility.list_collections(alias)
        collections = []
        total_entities = 0
        
        for name in collection_names:
            try:
                col = Collection(name, alias)
                entity_count = col.num_entities
                total_entities += entity_count
                
                collections.append({
                    "name": name,
                    "entity_count": entity_count,
                    "index_status": "已创建" if col.has_index() else "未创建",
                    "description": ""
                })
            except Exception as e:
                print(f"获取集合 {name} 信息时出错: {e}")
                collections.append({
                    "name": name,
                    "entity_count": 0,
                    "index_status": "未知",
                    "description": f"错误: {str(e)}"
                })
        
        return DatabaseStatistics(
            collection_count=len(collection_names),
            total_entities=total_entities,
            collections=collections
        )
    except Exception as e:
        raise ValueError(f"获取数据库统计信息时出错: {str(e)}")