from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union

class VectorQuery(BaseModel):
    database_id: str
    collection_name: str
    vector_data: Union[List[float], List[List[float]]]
    top_k: int = 10
    search_params: Optional[Dict[str, Any]] = None
    output_fields: Optional[List[str]] = None
    
class TextToVectorQuery(BaseModel):
    database_id: str
    collection_name: str
    text: str
    top_k: int = 10
    search_params: Optional[Dict[str, Any]] = None
    output_fields: Optional[List[str]] = None
    
class FileToVectorQuery(BaseModel):
    database_id: str
    collection_name: str
    # 文件会通过Form数据上传
    top_k: int = 10
    search_params: Optional[Dict[str, Any]] = None
    output_fields: Optional[List[str]] = None
    
class QueryResult(BaseModel):
    database_id: str
    collection_name: str
    results: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    
class MultiDatabaseQuery(BaseModel):
    database_ids: List[str]
    collection_names: Dict[str, str]  # 数据库ID到集合名称的映射
    vector_data: Union[List[float], List[List[float]]]
    top_k: int = 10
    search_params: Optional[Dict[str, Any]] = None
    output_fields: Optional[List[str]] = None
    
class MultiDatabaseQueryResult(BaseModel):
    results: Dict[str, QueryResult]  # 数据库ID到查询结果的映射
    aggregated_results: List[Dict[str, Any]]
    metrics: Dict[str, Any] 