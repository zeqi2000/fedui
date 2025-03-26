from fastapi import FastAPI, Depends, HTTPException, status, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
import uvicorn
import logging
from datetime import timedelta
from routes import auth, database, query
from core.config import settings
from services.user import authenticate_user
from schemas.user import Token
from core.security import create_access_token

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="向量数据库管理系统",
    description="多向量数据库管理与KNN查询系统",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源，以便于前端开发
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(database.router, prefix="/api/database", tags=["数据库管理"])
app.include_router(query.router, prefix="/api/query", tags=["向量查询"])

@app.get("/")
async def root():
    logger.info("访问根路径")
    return {"message": "向量数据库管理系统API"}

@app.get("/api/test")
async def test():
    logger.info("访问测试端点")
    return {"status": "ok", "message": "API服务器正常运行"}

@app.get("/debug")
async def debug():
    """调试端点，返回所有路由信息"""
    routes = []
    for route in app.routes:
        routes.append({
            "path": route.path,
            "name": route.name,
            "methods": getattr(route, "methods", None)
        })
    return {"routes": routes}

# 直接在主应用中添加登录端点
@app.post("/api/direct-login", response_model=Token)
async def direct_login(
    username: str = Form(...),
    password: str = Form(...)
):
    """直接登录端点，绕过路由模块"""
    logger.info(f"尝试直接登录: {username}")
    user = authenticate_user(username, password)
    if not user:
        logger.warning(f"直接登录失败: {username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.username, expires_delta=access_token_expires
    )
    logger.info(f"直接登录成功: {username}")
    return {"access_token": access_token, "token_type": "bearer"}

if __name__ == "__main__":
    logger.info("启动服务器...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 