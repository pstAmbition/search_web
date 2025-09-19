# /unified_service/services/nebula_service.py

import logging
from datetime import datetime
from nebula3.gclient.net import ConnectionPool
from nebula3.Config import Config as NebulaConfig

# 使用全局变量存储连接池，确保单例
connection_pool = None
logger = logging.getLogger(__name__)

# 定义属性类型映射
PROPERTY_TYPES = {
    # Event属性
    'eventstr': 'string',
    # Article属性
    'title': 'string', 'content': 'string', 'publishtimestamp': 'timestamp',
    'event': 'string', 'uid': 'string', 'pics_id': 'string',
    'pics_url': 'string', 'isrumor': 'bool', 'rumor_c': 'string',
    'datasource': 'string', 'eid': 'string',
    # Original_Tweet属性
    'forwardcount': 'int',
    # Retweet属性
    'reuid': 'string', 'retext': 'string', 'republishtime': 'timestamp',
    'rootmid': 'string', 'parentmid': 'string', 'name': 'string'
}


def init_nebula_pool(app_config):
    """根据配置初始化NebulaGraph连接池"""
    global connection_pool
    if connection_pool:
        return

    try:
        config = NebulaConfig()
        config.max_connection_pool_size = app_config.get('NEBULA_POOL_SIZE')
        connection_pool = ConnectionPool()
        if not connection_pool.init([(app_config.get('NEBULA_HOST'), app_config.get('NEBULA_PORT'))], config):
             raise ConnectionError("初始化NebulaGraph连接池失败")
        logger.info("NebulaGraph连接池初始化成功")
        
        # 服务启动时重建索引
        rebuild_indices(app_config)

    except Exception as e:
        logger.error(f"连接NebulaGraph失败: {e}")
        exit(1)


def process_value(value, prop_type):
    """根据属性类型处理NebulaGraph返回的值，适配新版客户端"""
    if value is None:
        return None
    
    try:
        processed_value = value.as_primitive()
    except Exception:
        processed_value = value

    if isinstance(processed_value, bytes):
        try:
            processed_value = processed_value.decode('utf-8')
        except UnicodeDecodeError:
            processed_value = processed_value.decode('gbk', 'replace')

    try:
        if prop_type == 'timestamp' and isinstance(processed_value, int):
            return datetime.fromtimestamp(processed_value / 1000).strftime('%Y-%m-%d %H:%M:%S')
        elif prop_type == 'bool':
            return bool(processed_value)
        elif prop_type == 'int':
            return int(processed_value)
        elif prop_type == 'float':
            return float(processed_value)
        else:
            return str(processed_value)
    except (ValueError, TypeError):
        return str(processed_value)


def execute_query(query, params=None, space_name=None):
    """执行NebulaGraph查询并返回处理后的结果"""
    if not connection_pool:
        raise ConnectionError("NebulaGraph连接池未初始化")

    try:
        with connection_pool.session_context('root', 'p') as session:
            session.execute(f'USE {space_name}')
            if params:
                if hasattr(session, 'execute_parameterized'):
                    result = session.execute_parameterized(query, params)
                    # print(result.as_primitive())
                else:
                    formatted_query = query
                    for key, value in params.items():
                        formatted_value = f"'{value}'" if isinstance(value, str) else str(value)
                        formatted_query = formatted_query.replace(f"${key}", formatted_value)
                    result = session.execute(formatted_query)
                    # print(result.as_primitive())
            else:
                result = session.execute(query)
            
            # 检查执行是否成功
            if not result.is_succeeded():
                error_msg = result.error_msg()
                if isinstance(error_msg, bytes):
                    error_msg = error_msg.decode('utf-8', errors='replace')
                self.logger.error(f"查询执行失败: {error_msg}, 查询: {query}")
                return {"error": error_msg, "query": query}
            
            # 处理结果集
            return result.as_primitive()
            # return self._process_result(result)
            
    except Exception as e:
        self.logger.error(f"执行查询时发生异常: {str(e)}, 查询: {query}")
        return {"error": str(e), "query": query}

    
def rebuild_indices(app_config):
    """重建NebulaGraph索引"""
    try:
        with connection_pool.session_context(app_config.get('NEBULA_USER'), app_config.get('NEBULA_PASSWORD')) as session:
            session.execute(f"USE {app_config.get('NEBULA_SPACE')}")
            rebuild_query = "REBUILD TAG INDEX Article_event"
            result = session.execute(rebuild_query)
            if not result.is_succeeded():
                error_msg = result.error_msg()
                if isinstance(error_msg, bytes):
                    error_msg = error_msg.decode('utf-8', 'replace')
                logger.error(f"重建索引失败: {error_msg}")
            else:
                logger.info("索引 'Article_event' 重建成功")
    except Exception as e:
        logger.error(f"重建索引时发生异常: {e}")

def get_graph_data_by_event(event, space_name):
    """根据事件查询相关图数据"""
    query = """
    
    LOOKUP ON Event WHERE Event.eventstr == $event
    YIELD id(vertex) AS vid
    | GO FROM $-.vid OVER belong REVERSELY
    YIELD src(edge) AS vid, dst(edge) AS end_vid, tags($$)[0] AS src_type, properties($$) AS src_props,
            edge AS e, rank(edge) AS e_rank, type(edge) AS e_type,
            src(edge) AS e_src, dst(edge) AS e_dst

    UNION ALL

    LOOKUP ON Event WHERE Event.eventstr == $event
    YIELD id(vertex) AS vid
    | GO FROM $-.vid OVER belong REVERSELY
    YIELD src(edge) AS vid
    | GO 1 TO 5 STEPS FROM $-.vid OVER forwarded REVERSELY
        YIELD src(edge) AS vid, dst(edge) AS end_vid, tags($$)[0] AS src_type, properties($$) AS src_props,
            edge AS e, rank(edge) AS e_rank, type(edge) AS e_type,
            src(edge) AS e_src, dst(edge) AS e_dst;
    
    """
    params = {"event": event}
    return execute_query(query, params, space_name)



def get_graph_data_by_id(id, space_name):
    """根据微博推文id生成微博的扩散图"""
    query = """
    
    GO 1 TO 10 STEPS FROM $id OVER forwarded REVERSELY 
    YIELD DISTINCT  src(edge) AS vid,dst(edge) AS end_vid,tags($$)[0] AS src_type, properties($$) AS src_props,edge AS e,rank(edge) AS e_rank,type(edge) AS e_type,src(edge) AS e_src,dst(edge) AS e_dst
    
    """
    params = {"id": id}
    return execute_query(query, params, space_name)


def get_Original_Tweet_by_id(id, space_name):
    """根据微博推文id生成微博的扩散图"""
    query = """
    
    FETCH PROP ON Original_Tweet $id
    YIELD id(vertex) AS vid, properties(vertex) AS src_v;
    
    """
    params = {"id": id}
    return execute_query(query, params, space_name)

