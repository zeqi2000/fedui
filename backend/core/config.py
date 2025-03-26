import os
from typing import List
from pydantic import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # 基本设置
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "向量数据库管理系统"
    
    # 安全设置
    SECRET_KEY: str = os.getenv("SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7天
    ALGORITHM: str = "HS256"
    
    # CORS设置
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",  # Vite默认端口
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    # 数据库设置
    DATABASE_PATH: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data/database.json")

settings = Settings() 