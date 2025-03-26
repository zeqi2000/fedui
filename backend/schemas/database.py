from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class DatabaseConnection(BaseModel):
    id: str
    name: str
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = "未连接"
    created_by: str
    
class DatabaseConnectionCreate(BaseModel):
    name: str
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    description: Optional[str] = None

class DatabaseConnectionUpdate(BaseModel):
    name: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    description: Optional[str] = None

class DatabaseStatus(BaseModel):
    id: str
    status: str
    details: Optional[Dict[str, Any]] = None

class Collection(BaseModel):
    name: str
    entity_count: int
    index_status: str
    description: Optional[str] = None
    
class DatabaseStatistics(BaseModel):
    collection_count: int
    total_entities: int
    collections: List[Collection] 