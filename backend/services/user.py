import json
import os
import uuid
from typing import Optional, List, Dict
from schemas.user import User, UserCreate
from core.config import settings
from core.security import get_password_hash

# 确保数据目录存在
os.makedirs(os.path.dirname(settings.DATABASE_PATH), exist_ok=True)

def get_users_db() -> List[Dict]:
    """获取用户数据库"""
    if not os.path.exists(settings.DATABASE_PATH):
        # 创建初始数据库文件
        data = {
            "users": [
                {
                    "id": str(uuid.uuid4()),
                    "username": "admin",
                    "email": "admin@example.com",
                    "full_name": "管理员",
                    "hashed_password": get_password_hash("admin123"),
                    "is_admin": True
                }
            ],
            "database_connections": []
        }
        with open(settings.DATABASE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return data["users"]
    
    try:
        with open(settings.DATABASE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("users", [])
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_users_db(users: List[Dict]) -> None:
    """保存用户数据到数据库"""
    try:
        if os.path.exists(settings.DATABASE_PATH):
            with open(settings.DATABASE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {"database_connections": []}
            
        data["users"] = users
        
        with open(settings.DATABASE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"保存用户数据时出错: {e}")

def get_user_by_username(username: str) -> Optional[User]:
    """通过用户名获取用户"""
    users = get_users_db()
    for user_data in users:
        if user_data["username"] == username:
            return User(
                id=user_data["id"],
                username=user_data["username"],
                email=user_data.get("email", ""),
                full_name=user_data.get("full_name", ""),
                is_admin=user_data.get("is_admin", False)
            )
    return None

def get_user_by_id(user_id: str) -> Optional[User]:
    """通过ID获取用户"""
    users = get_users_db()
    for user_data in users:
        if user_data["id"] == user_id:
            return User(
                id=user_data["id"],
                username=user_data["username"],
                email=user_data.get("email", ""),
                full_name=user_data.get("full_name", ""),
                is_admin=user_data.get("is_admin", False)
            )
    return None

def authenticate_user(username: str, password: str) -> Optional[User]:
    """认证用户"""
    from core.security import verify_password
    
    users = get_users_db()
    for user_data in users:
        if user_data["username"] == username:
            if verify_password(password, user_data["hashed_password"]):
                return User(
                    id=user_data["id"],
                    username=user_data["username"],
                    email=user_data.get("email", ""),
                    full_name=user_data.get("full_name", ""),
                    is_admin=user_data.get("is_admin", False)
                )
    return None

def create_user(user_in: UserCreate, is_admin: bool = False) -> User:
    """创建新用户"""
    users = get_users_db()
    
    # 检查用户名是否已存在
    if any(u["username"] == user_in.username for u in users):
        raise ValueError("用户名已存在")
    
    user_id = str(uuid.uuid4())
    new_user = {
        "id": user_id,
        "username": user_in.username,
        "email": user_in.email,
        "full_name": user_in.full_name,
        "hashed_password": get_password_hash(user_in.password),
        "is_admin": is_admin
    }
    
    users.append(new_user)
    save_users_db(users)
    
    return User(
        id=user_id,
        username=user_in.username,
        email=user_in.email,
        full_name=user_in.full_name,
        is_admin=is_admin
    ) 