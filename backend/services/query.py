import time
from typing import List, Dict, Any, Optional, Union
from pymilvus import Collection, utility, connections
from services.database import get_connection_by_id, connect_to_db
from schemas.query import QueryResult, MultiDatabaseQueryResult

def execute_vector_query(
    database_id: str,
    collection_name: str,
    vector_data: Union[List[float], List[List[float]]],
    top_k: int = 10,
    search_params: Optional[Dict[str, Any]] = None,
    output_fields: Optional[List[str]] = None
) -> QueryResult:
    """在指定数据库和集合上执行向量查询"""
    try:
        # 检查连接是否存在
        connection = get_connection_by_id(database_id)
        if not connection:
            raise ValueError("数据库连接不存在")
        
        alias = f"conn_{database_id}"
        # 确保连接
        if not connections.has_connection(alias):
            connect_to_db(database_id)
            
        # 准备查询参数
        if search_params is None:
            search_params = {"metric_type": "L2"}
        print(11)
        print(vector_data)
        if not isinstance(vector_data[0], list):
            # 单个向量，转为列表
            vector_data = [vector_data]
        
    # try:
        start_time = time.time()
        
        # 获取集合
        collection = Collection(collection_name, using=alias)
        collection.load()
        print(1)
        # 执行查询
        search_result = collection.search(
            data=vector_data,
            anns_field="emb",  # 假设向量字段名为"vector"
            param=search_params,
            limit=top_k,
            output_fields=output_fields
        )
        
        # 处理结果
        results = []
        for hits in search_result:
            for hit in hits:
                hit_data = {"id": hit.id, "distance": hit.distance}
                if output_fields:
                    for field in output_fields:
                        if hasattr(hit, "entity"):
                            hit_data[field] = hit.entity.get(field)
                results.append(hit_data)
        
        end_time = time.time()
        execution_time = end_time - start_time
        print("result:",results)
        # 返回结果
        return QueryResult(
            database_id=database_id,
            collection_name=collection_name,
            results=results,
            metrics={
                "execution_time": execution_time,
                "total_results": len(results)
            }
        )
    except Exception as e:
        print(e)
        raise ValueError(f"查询执行失败: {str(e)}")

def execute_multi_db_query(
    database_ids: List[str],
    collection_names: Dict[str, str],
    vector_data: Union[List[float], List[List[float]]],
    top_k: int = 10,
    search_params: Optional[Dict[str, Any]] = None,
    output_fields: Optional[List[str]] = None
) -> MultiDatabaseQueryResult:
    """在多个数据库上执行查询并合并结果"""
    print("service")
    print("multi:",database_ids,collection_names,vector_data)

    start_time = time.time()
    results = {}
    errors = []
    
    # 对每个数据库执行查询
    for db_id in database_ids:
        try:
            print("for start")
            collection_name = collection_names.get(db_id)
            print(collection_name)
            if not collection_name:
                errors.append(f"数据库ID {db_id} 未提供集合名称")
                continue
            print(1)
            query_result = execute_vector_query(
                database_id=db_id,
                collection_name=collection_name,
                vector_data=vector_data,
                top_k=top_k,
                search_params=search_params,
                output_fields=output_fields
            )
            print(2)
            # print("multi:",db_id,query_result)
            results[db_id] = query_result
            print(3)
        except Exception as e:
            errors.append(f"数据库 {db_id} 查询失败: {str(e)}")
    
    # 聚合结果
    all_results = []
    for db_id, result in results.items():
        for item in result.results:
            all_results.append({
                "database_id": db_id,
                "collection_name": result.collection_name,
                **item
            })
    
    # 根据距离排序
    all_results.sort(key=lambda x: x["distance"])
    # 保留前top_k个结果
    all_results = all_results[:top_k]
    
    end_time = time.time()
    total_time = end_time - start_time
    
    return MultiDatabaseQueryResult(
        results=results,
        aggregated_results=all_results,
        metrics={
            "total_execution_time": total_time,
            "database_count": len(results),
            "errors": errors,
            "total_results": len(all_results)
        }
    ) 