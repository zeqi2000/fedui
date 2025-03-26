from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from typing import Any, List
import logging

from schemas.user import User, UserCreate, Token
from core.security import create_access_token, get_current_user, get_admin_user
from core.config import settings
from services.user import authenticate_user, create_user, get_user_by_username

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/login", response_model=Token)
async def login_access_token(form_data: OAuth2PasswordRequestForm = Depends()) -> Any:
    """获取OAuth2兼容的token"""
    logger.info(f"尝试OAuth2登录: {form_data.username}")
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        logger.warning(f"OAuth2登录失败: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.username, expires_delta=access_token_expires
    )
    logger.info(f"OAuth2登录成功: {form_data.username}")
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/simple-login", response_model=Token)
async def simple_login(
    username: str = Form(...),
    password: str = Form(...)
) -> Any:
    """简单表单登录，获取访问令牌"""
    logger.info(f"尝试简单登录: {username}")
    user = authenticate_user(username, password)
    if not user:
        logger.warning(f"简单登录失败: {username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.username, expires_delta=access_token_expires
    )
    logger.info(f"简单登录成功: {username}")
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=User)
async def register_user(user_in: UserCreate, admin: User = Depends(get_admin_user)) -> Any:
    """注册新用户（仅管理员）"""
    # 检查用户名是否已存在
    existing_user = get_user_by_username(user_in.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 创建新用户
    try:
        user = create_user(user_in)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/me", response_model=User)
async def read_current_user(current_user: User = Depends(get_current_user)) -> Any:
    """获取当前用户信息"""
    return current_user 