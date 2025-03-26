from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List

class UserBase(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    
class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    
class User(UserBase):
    id: str
    is_admin: bool = False
    
    class Config:
        orm_mode = True 