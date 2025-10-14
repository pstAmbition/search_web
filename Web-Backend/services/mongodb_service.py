import os
import pymongo
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from datetime import datetime, date, timedelta
import json
from bson import ObjectId
import os
import logging

# 使用全局变量存储连接池，确保单例
mongodb_pool = None
mongo_db = None
mongo_collection_obj = None
logger = logging.getLogger(__name__)

def init_mongodb_pool(app_config):
    """根据配置初始化MongoDB连接池"""
    global mongodb_pool
    print("MongoDB服务初始化开始...")
    
    if mongodb_pool:
        print("MongoDB连接池已存在，直接返回")
        return True

    try:
        print("获取MongoDB配置...")
        # 获取MongoDB配置
        mongo_host = app_config.get('MONGO_HOST')
        mongo_port = app_config.get('MONGO_PORT')
        mongo_user = app_config.get('MONGO_USER')
        mongo_pass = app_config.get('MONGO_PASSWORD')
        mongo_dbname = app_config.get('MONGO_DBNAME')
        mongo_collection = app_config.get('MONGO_COLLECTION')
        
        print(f"MongoDB配置: host={mongo_host}, port={mongo_port}, dbname={mongo_dbname}, collection={mongo_collection}")
        
        print("构建连接字符串...")
        if mongo_user and mongo_pass:
            connection_string = f"mongodb://{mongo_user}:{mongo_pass}@{mongo_host}:{mongo_port}/"
        else:
            connection_string = f"mongodb://{mongo_host}:{mongo_port}/"
        
        print(f"连接字符串构建完成")
        
        print("初始化MongoDB连接池...")
        # 初始化MongoDB连接池，增加超时时间和优化连接设置
        mongodb_pool = pymongo.MongoClient(
            connection_string,
            serverSelectionTimeoutMS=60000,  # 增加到60秒
            connectTimeoutMS=60000,
            socketTimeoutMS=60000,
            maxPoolSize=50,  # 增加连接池大小
            minPoolSize=10,
            waitQueueTimeoutMS=60000,
            retryWrites=True,  # 启用写重试
            retryReads=True    # 启用读重试
        )
        
        print("MongoDB连接池对象创建成功，准备验证连接...")
        # 验证连接
        server_info = mongodb_pool.server_info()
        print(f"MongoDB连接验证成功! 服务器版本: {server_info.get('version')}")
        
        # 存储数据库和集合信息
        print("访问数据库和集合...")
        global mongo_db, mongo_collection_obj
        mongo_db = mongodb_pool[mongo_dbname]
        print(f"成功访问数据库: {mongo_dbname}")
        
        mongo_collection_obj = mongo_db[mongo_collection]
        print(f"成功访问集合: {mongo_collection}")
        # 在连接 MongoDB 后执行
        try:
            mongo_collection_obj.create_index(
                "Event",
                background=True  # 后台创建，不阻塞
            )
            print("已确保 Event 字段的索引存在")
        except Exception as e:
            print(f"创建索引失败: {e}")
        # 测试查询一个文档
        try:
            first_document = mongo_collection_obj.find_one()
            if first_document:
                print(f"集合中有文档存在，文档ID: {first_document.get('_id')}")
            else:
                print("集合中没有文档")
        except Exception as e:
            print(f"查询文档时出错: {e}")
        
        print(f"MongoDB连接池初始化成功: {mongo_host}:{mongo_port}/{mongo_dbname}/{mongo_collection}")
        print("MongoDB服务初始化完成")
        return True
        
    except ConnectionFailure as e:
        print(f"无法连接到MongoDB服务器: {e}")
        logger.error(f"连接MongoDB失败: {e}")
        return False
    except ServerSelectionTimeoutError as e:
        print(f"MongoDB服务器选择超时: {e}")
        logger.error(f"MongoDB服务器选择超时: {e}")
        return False
    except Exception as e:
        print(f"初始化MongoDB连接池时发生其他错误: {e}")
        logger.error(f"连接MongoDB失败: {e}")
        return False

class JSONEncoder(json.JSONEncoder):
    """用于处理ObjectId和其他MongoDB特殊类型的JSON编码器"""
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, datetime):
            return o.strftime('%Y-%m-%d %H:%M')
        return json.JSONEncoder.default(self, o)


def _check_connection():
    """检查MongoDB连接是否可用"""
    global mongodb_pool, mongo_db, mongo_collection_obj
    
    if not mongodb_pool:
        logger.error("MongoDB连接池未初始化")
        return False
    
    try:
        # 验证连接
        mongodb_pool.server_info()
        return True
    except ConnectionFailure as e:
        logger.error(f"MongoDB连接验证失败: {e}")
        return False
    except Exception as e:
        logger.error(f"MongoDB连接检查发生错误: {e}")
        return False


def _convert_objectid_to_string(data):
    """将数据中的ObjectId转换为字符串"""
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, ObjectId):
                data[key] = str(value)
            elif isinstance(value, dict):
                data[key] = _convert_objectid_to_string(value)
            elif isinstance(value, list):
                data[key] = [_convert_objectid_to_string(item) if isinstance(item, (dict, ObjectId)) else item for item in value]
    elif isinstance(data, ObjectId):
        return str(data)
    return data


def get_event_by_id(event_id):
    """根据ID获取事件数据"""
    if not _check_connection():
        return None
    
    try:
        # 尝试将字符串ID转换为ObjectId
        try:
            obj_id = ObjectId(event_id)
            event = mongo_collection_obj.find_one({'_id': obj_id})
        except:
            # 如果转换失败，尝试直接查找
            event = mongo_collection_obj.find_one({'_id': event_id})
            
        if event:
            return _convert_objectid_to_string(event)
        return None
    except Exception as e:
        logger.error(f"获取事件数据失败: {e}")
        return None


def search_events(query=None, page=1, page_size=100, sort_by='Time', sort_order=-1, is_export=False, streaming=False):
    """搜索事件数据，增加重试机制和性能优化"""
    logger.info(f"调用search_events: query={query}, page={page}, page_size={page_size}, is_export={is_export}, streaming={streaming}")
    
    if not _check_connection():
        logger.warning("MongoDB连接不可用，返回空结果")
        return [], 0
    
    # 保持一致的重试次数设置
    max_retries = 3  # 所有请求都重试3次
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # 构建查询条件
            search_query = query or {}
            
            logger.info(f"执行查询: search_query={search_query}")
            

            if 'isRisk' in search_query:
                is_risk_value = search_query['isRisk']
                # 如果查询条件是布尔值，同时查询布尔值和对应的字符串
                if isinstance(is_risk_value, bool):
                    str_value = 'true' if is_risk_value else 'false'
                    # 构建$or条件，同时匹配布尔值和字符串
                    search_query = {
                        '$and': [
                            {k: v for k, v in search_query.items() if k != 'isRisk'},
                            {'$or': [
                                {'isRisk': is_risk_value},
                                {'isRisk': str_value}
                            ]}
                        ]
                    }
            
            # 执行查询并分页
            skip = (page - 1) * page_size
            
            # 优化：限制页面大小，避免一次性查询过多数据
            if not is_export and page_size > 1000:
                page_size = 1000
                logger.warning(f"页面大小过大，已限制为1000")
            # 导出时可以获取更多数据，但仍设置合理上限
            elif is_export and page_size > 50000:
                page_size = 50000
                logger.info(f"导出模式，页面大小限制为50000")
            
            # 执行查询，导出模式下只选择需要的字段以提高性能
            if is_export:
                # 导出时只选择必要的字段，提高查询速度
                projection = {
                    '_id': 0,  # 不包含_id
                    'Event': 1,
                    'Time': 1,
                    'platform': 1,
                    'region': 1,
                    'content': 1,
                    'isRisk': 1,
                    # 可以根据实际需要添加更多字段
                }
                logger.info(f"导出模式，使用投影: {projection}")
                cursor = mongo_collection_obj.find(search_query, projection)
            else:
                cursor = mongo_collection_obj.find(search_query)
                
            logger.info("查询执行成功，获取到游标")
            
            # 排序 - 只对需要的字段排序
            if sort_by:
                try:
                    cursor = cursor.sort(sort_by, sort_order)
                except Exception as e:
                    logger.warning(f"排序失败，使用默认排序: {e}")
            
            # 分页
            cursor = cursor.skip(skip).limit(page_size)
            
            # 如果是流式处理模式，直接返回游标（注意：需要在外部处理）
            if streaming:
                logger.info(f"返回流式游标: search_query={search_query}, skip={skip}, limit={page_size}")
                return cursor, None
            
            # 非流式处理，正常转换数据
            events = list(cursor)
            logger.info(f"非流式处理获取到 {len(events)} 条数据")
            
            # 转换ObjectId为字符串
            events = [_convert_objectid_to_string(event) for event in events]
            
            # 优化：先获取数据，再计算总数
            try:
                # 对于空查询（获取所有数据），使用更高效的estimated_document_count
                if not search_query:
                    total_count = mongo_collection_obj.estimated_document_count()
                    logger.info(f"使用estimated_document_count获取总数: {total_count}")
                else:
                    # 对于复杂查询，使用count_documents获取准确总数
                    # 虽然性能可能略差，但能确保分页显示正确
                    total_count = mongo_collection_obj.count_documents(search_query)
                    logger.info(f"使用count_documents获取总数: {total_count}")
            except Exception as e:
                logger.warning(f"获取总数失败: {e}")
                # 改进：不再使用当前页结果数量作为总数，这样会导致分页错误
                # 而是返回一个保守的估计值，确保分页控件能正常工作
                # 如果当前有结果，返回一个较大的估计值，确保分页功能可用
                if events:
                    total_count = 1000  # 设置一个较大的估计值，确保分页功能可用
                    logger.warning(f"使用保守估计的总数: {total_count}")
                else:
                    total_count = 0
            
            return events, total_count
        except (ServerSelectionTimeoutError, ConnectionFailure) as e:
            retry_count += 1
            logger.warning(f"搜索事件数据超时，第{retry_count}次重试: {e}")
            if retry_count >= max_retries:
                logger.error(f"搜索事件数据失败，已达到最大重试次数: {e}")
                # 返回空列表和0，前端可以处理这种情况
                return [], 0
            # 重试前等待一段时间，使用指数退避策略
            import time
            wait_time = 1 * (2 ** retry_count)  # 指数退避：1s, 2s, 4s, 8s...
            if wait_time > 10:  # 最大等待时间不超过10秒
                wait_time = 10
            logger.info(f"等待{wait_time}秒后重试")
            time.sleep(wait_time)
        except Exception as e:
            logger.error(f"搜索事件数据失败: {e}")
            return [], 0

def get_statistics():
    """获取数据库统计信息"""
    if not _check_connection():
        return {'error': 'MongoDB未连接'}

    try:
        # 获取文档总数
        count = mongo_collection_obj.count_documents({})
        
        # 获取风险事件数量
        risk_query = {
            '$or': [
                {'isRisk': 'true'},
                {'isRisk': True}
            ]
        }
        risk_count = mongo_collection_obj.count_documents(risk_query)
        
        # 不使用索引相关功能，避免超时问题
        # 使用db.command获取集合统计信息，而不是直接调用stats()
        stats = mongo_db.command("collStats", mongo_collection_obj.name)
        
        return {
            'total_documents': count,
            'risk_documents': risk_count,
            'collection_size': stats.get('size', 0),
            'avg_document_size': stats.get('avgObjSize', 0),
            # 不返回索引大小相关信息
        }
    except Exception as e:
        logger.error(f"获取数据库统计信息失败: {e}")
        # 出错时返回基本统计信息，避免API完全不可用
        return {
            'total_documents': count if 'count' in locals() else 0,
            'risk_documents': risk_count if 'risk_count' in locals() else 0,
            'collection_size': 0,
            'avg_document_size': 0
        }

def get_all_events_query(params=None):
    """构建获取所有事件的查询条件"""
    try:
        # 确保params不为None
        params = params or {}
        
        # 获取查询参数
        platform = params.get('platform', '')
        region = params.get('region', '')
        start_time = params.get('start_time', '')
        end_time = params.get('end_time', '')
        keyword = params.get('keyword', '')
        
        # 构建查询条件
        query = {}
        conditions = []
        
        # 如果提供了平台参数，添加到查询条件中
        if platform:
            conditions.append({"platform": platform})
        
        # 如果提供了region参数，添加到查询条件中
        if region:
            conditions.append({"region": region})
        
        # 处理时间范围查询，支持按年月筛选 (格式：YYYY-MM)
        if start_time:
            if len(start_time) == 7 and start_time[4] == '-':  # 检查是否是年月格式 (YYYY-MM)
                # 年月格式，设置为当月第一天
                year_month = start_time
                # 直接使用日期范围查询，不使用正则匹配
                conditions.append({"Time": {"$gte": f"{year_month}-01 00:00"}})
            else:
                conditions.append({"Time": {"$gte": start_time}})
        if end_time:
            if len(end_time) == 7 and end_time[4] == '-':  # 检查是否是年月格式 (YYYY-MM)
                # 年月格式，设置为当月最后一天
                year_month = end_time
                # 解析年月
                year, month = map(int, year_month.split('-'))
                # 计算当月最后一天
                if month == 12:
                    last_day = 31
                else:
                    last_day = (date(year, month + 1, 1) - timedelta(days=1)).day
                # 直接使用日期范围查询，不使用正则匹配
                conditions.append({"Time": {"$lte": f"{year_month}-{last_day} 23:59"}})
            else:
                conditions.append({"Time": {"$lte": end_time}})
        
        # 如果提供了关键词参数，添加到查询条件中（不区分大小写）
        if keyword:
            # 改为前缀匹配，确保能用索引
            conditions.append({"Event": {"$regex": f"^{keyword}", "$options": "i"}})
        
        # 组合查询条件
        if len(conditions) > 0:
            if len(conditions) > 1:
                query = {"$and": conditions}
            else:
                query = conditions[0]
        
        return query
    except Exception as e:
        logger.error(f"构建查询条件失败: {e}")
        return {}


def get_risk_events_query(params=None):
    """构建获取风险事件的查询条件"""
    try:
        # 确保params不为None
        params = params or {}
        
        # 获取查询参数
        platform = params.get('platform', '')
        region = params.get('region', '')
        start_time = params.get('start_time', '')
        end_time = params.get('end_time', '')
        keyword = params.get('keyword', '')
        
        # 构建查询条件，只获取isRisk=true的事件（true是以字符串形式存储）
        conditions = [{"isRisk": "true"}]
        
        # 如果提供了平台参数，添加到查询条件中
        if platform:
            conditions.append({"platform": platform})
            
        # 如果提供了region参数，添加到查询条件中
        if region:
            conditions.append({"region": region})
        
        # 处理时间范围查询，支持按年月筛选 (格式：YYYY-MM)
        if start_time:
            if len(start_time) == 7 and start_time[4] == '-':  # 检查是否是年月格式 (YYYY-MM)
                # 年月格式，设置为当月第一天
                year_month = start_time
                # 直接使用日期范围查询，不使用正则匹配
                conditions.append({"Time": {"$gte": f"{year_month}-01 00:00"}})
            else:
                conditions.append({"Time": {"$gte": start_time}})
        if end_time:
            if len(end_time) == 7 and end_time[4] == '-':  # 检查是否是年月格式 (YYYY-MM)
                # 年月格式，设置为当月最后一天
                year_month = end_time
                # 解析年月
                year, month = map(int, year_month.split('-'))
                # 计算当月最后一天
                if month == 12:
                    last_day = 31
                else:
                    last_day = (date(year, month + 1, 1) - timedelta(days=1)).day
                # 直接使用日期范围查询，不使用正则匹配
                conditions.append({"Time": {"$lte": f"{year_month}-{last_day} 23:59"}})
            else:
                conditions.append({"Time": {"$lte": end_time}})
        
        # 如果提供了关键词参数，添加到查询条件中（不区分大小写）
        if keyword:
            # 改为前缀匹配，确保能用索引
            conditions.append({"Event": {"$regex": f"^{keyword}", "$options": "i"}})
        
        # 组合查询条件
        if len(conditions) > 1:
            query = {"$and": conditions}
        else:
            query = conditions[0]
        
        return query
    except Exception as e:
        logger.error(f"构建风险事件查询条件失败: {e}")
        return {"isRisk": "true"}

def get_dashboard_metrics():    
    """获取仪表盘指标数据，高效查询真实数据"""
    if not _check_connection():
        return {'error': 'MongoDB未连接'}

    try:
        # 构建返回结果
        metrics = {}
        
        # 1. 文档总数 - 使用最高效的查询方法
        try:
            # 使用estimated_document_count，这是获取总数最快的方法
            metrics['count1'] = mongo_collection_obj.estimated_document_count()
            logger.info(f"成功获取文档总数: {metrics['count1']}")
        except Exception as e:
            logger.warning(f"获取文档总数失败: {e}")
            # 查询失败时返回0
            metrics['count1'] = 0
        
        # 2. 风险事件数量 - 优化查询
        try:
            logger.info("开始查询风险事件数量")
            # 处理isRisk字段的不同类型
            risk_query = {
                '$or': [
                    {'isRisk': 'true'},
                    {'isRisk': True}
                ]
            }
            
            # 使用count_documents查询风险事件数量
            risk_count = mongo_collection_obj.count_documents(risk_query, limit=100000)  # 设置上限避免查询过大
            metrics['risk_count'] = risk_count
            logger.info(f"成功获取风险事件数量: {risk_count}")
        except Exception as e:
            logger.warning(f"获取风险事件数量失败: {e}")
            metrics['risk_count'] = 0
        
        # 3. 平台分布 - 使用更高效的方法获取真实数据，增加超时时间和重试机制
        try:
            logger.info("开始查询平台分布数据")
            
            # 优化的平台分布查询，使用更大的超时时间
            pipeline = [
                # 只包含有platform字段的文档
                {'$match': {'platform': {'$exists': True, '$ne': None, '$ne': ''}}},
                # 按platform分组并计数
                {'$group': {'_id': '$platform', 'count': {'$sum': 1}}},
                # 按计数降序排列
                {'$sort': {'count': -1}},
                # 只返回前10个平台
                {'$limit': 10}
            ]
            
            # 增加超时时间到30秒，确保有足够时间完成查询
            platform_results = list(mongo_collection_obj.aggregate(pipeline, maxTimeMS=30000))
            
            # 处理结果
            platform_counts = {}
            unique_platforms = []
            
            for result in platform_results:
                platform = result['_id']
                count = result['count']
                platform_counts[platform] = count
                unique_platforms.append(platform)
            
            metrics['platforms'] = unique_platforms
            metrics['platform_count'] = len(unique_platforms)
            metrics['platform_counts'] = platform_counts
            
            logger.info(f"成功获取平台分布数据: {len(unique_platforms)}个平台")
        except Exception as e:
            logger.warning(f"获取平台信息失败: {e}")
            # 增加查询重试机制
            try:
                logger.info("尝试使用更简单的查询获取平台数据")
                # 改进重试机制：使用distinct获取所有平台，然后单独统计数量
                platform_counts = {}
                
                try:
                    # 先获取所有唯一的平台值
                    all_platforms = mongo_collection_obj.distinct('platform')
                    
                    # 为每个平台单独统计数量（限制为前20个以避免过多查询）
                    for platform in all_platforms:
                        if platform and platform != '':
                            count = mongo_collection_obj.count_documents({'platform': platform})
                            platform_counts[platform] = count
                    
                    # 按计数排序并取前10个
                    sorted_platforms = sorted(platform_counts.items(), key=lambda x: x[1], reverse=True)[:10]
                    
                    unique_platforms = [p[0] for p in sorted_platforms]
                    platform_counts = dict(sorted_platforms)
                    
                except Exception as distinct_e:
                    logger.warning(f"distinct方法失败，回退到采样方法: {distinct_e}")
                    # 如果distinct方法失败，回退到采样方法，但增加样本量
                    sample_docs = mongo_collection_obj.find(
                        {'platform': {'$exists': True, '$ne': None, '$ne': ''}},
                        {'platform': 1}
                    ).limit(5000)
                    
                    # 手动统计样本中的平台分布
                    platform_counts = {}
                    for doc in sample_docs:
                        platform = doc.get('platform')
                        if platform:
                            platform_counts[platform] = platform_counts.get(platform, 0) + 1
                    
                    # 按计数排序并取前10个
                    sorted_platforms = sorted(platform_counts.items(), key=lambda x: x[1], reverse=True)[:10]
                    
                    unique_platforms = [p[0] for p in sorted_platforms]
                    platform_counts = dict(sorted_platforms)
                
                # 设置结果
                metrics['platforms'] = unique_platforms
                metrics['platform_count'] = len(unique_platforms)
                metrics['platform_counts'] = platform_counts
                
                logger.info(f"成功使用简单查询获取平台分布数据: {len(unique_platforms)}个平台")
            except Exception as retry_e:
                logger.error(f"重试获取平台信息也失败: {retry_e}")
                # 查询失败时返回空数据
                metrics['platforms'] = []
                metrics['platform_count'] = 0
                metrics['platform_counts'] = {}
        
        # 4. 字段列表和总数
        try:
            # 获取一个文档来获取所有字段
            sample_doc = mongo_collection_obj.find_one({}, {"_id": 0})
            if sample_doc:
                field_names = list(sample_doc.keys())
                field_count = len(field_names)
                metrics['fields'] = field_names
                metrics['field_count'] = field_count
            else:
                # 如果没有找到文档，使用预定义的字段列表
                metrics['fields'] = ["Event", "Content", "Time", "URL", "User", "UserID", "platform", "region", "Language", "isRisk", "Praise", "Reblog", "Comment", "MediaURL", "Latitude", "Longitude", "Keywords"]
                metrics['field_count'] = len(metrics['fields'])
        except Exception as e:
            logger.warning(f"获取字段列表失败: {e}")
            metrics['fields'] = ["Event", "Content", "Time", "URL", "User", "UserID", "platform", "region", "Language", "isRisk", "Praise", "Reblog", "Comment", "MediaURL", "Latitude", "Longitude", "Keywords"]
            metrics['field_count'] = len(metrics['fields'])
        
        # 5. 互动总量 - 优化聚合查询，使用采样方法
        try:
            logger.info("开始查询互动总量数据")
            
            # 优化的数据总数查询，包括data_num和转赞评总量
            pipeline = [
                # 分组计算总和 - 不使用match和sample以提高性能
                {'$group': {
                    '_id': None,
                    'total_data_num': {'$sum': {'$ifNull': ['$data_num', 0]}},
                    'total_praise': {'$sum': {'$ifNull': ['$Praise', 0]}},
                    'total_reblog': {'$sum': {'$ifNull': ['$Reblog', 0]}},
                    'total_comment': {'$sum': {'$ifNull': ['$Comment', 0]}}
                }}
            ]
            
            # 增加超时时间到30秒
            result = list(mongo_collection_obj.aggregate(pipeline, maxTimeMS=30000))
            
            if result:
                stats = result[0]
                # 计算data_num总和和转赞评总和
                total_data_num = stats.get("total_data_num", 0)
                total_praise = stats.get("total_praise", 0)
                total_reblog = stats.get("total_reblog", 0)
                total_comment = stats.get("total_comment", 0)
                
                # 按照用户需求：数据总数 = 每个数据的data_num + 转赞评的总量
                interaction_sum = total_praise + total_reblog + total_comment
                total_nums = total_data_num + interaction_sum
                
                metrics['total_data_num'] = total_data_num
                metrics['total_praise'] = total_praise
                metrics['total_reblog'] = total_reblog
                metrics['total_comment'] = total_comment
                metrics['interaction_sum'] = interaction_sum
                metrics['total_nums'] = total_nums
                
                logger.info(f"成功获取互动总量数据")
            else:
                metrics['total_nums'] = 0
                metrics['total_praise'] = 0
                metrics['total_reblog'] = 0
                metrics['total_comment'] = 0
        except Exception as e:
            logger.warning(f"聚合查询失败: {e}")
            # 增加查询重试机制
            try:
                logger.info("尝试使用更简单的查询获取互动数据")
                # 使用更简单的查询，只获取少量样本
                sample_docs = mongo_collection_obj.find(
                    {'$and': [
                        {'Praise': {'$exists': True}},
                        {'Reblog': {'$exists': True}},
                        {'Comment': {'$exists': True}}
                    ]},
                    {'Praise': 1, 'Reblog': 1, 'Comment': 1}
                ).limit(1000)
                
                # 手动计算样本中的data_num总和和转赞评总和
                total_data_num = 0
                total_praise = 0
                total_reblog = 0
                total_comment = 0
                
                for doc in sample_docs:
                    # 确保data_num的值被正确计算，即使为None也处理为0
                    data_num_value = doc.get('data_num', 0)
                    if isinstance(data_num_value, (int, float)):
                        total_data_num += data_num_value
                    else:
                        # 尝试转换非数字类型的值
                        try:
                            total_data_num += int(data_num_value)
                        except (ValueError, TypeError):
                            total_data_num += 0
                    
                    total_praise += doc.get('Praise', 0)
                    total_reblog += doc.get('Reblog', 0)
                    total_comment += doc.get('Comment', 0)
                
                # 按照用户需求：数据总数 = 每个数据的data_num + 转赞评的总量
                interaction_sum = total_praise + total_reblog + total_comment
                total_nums = total_data_num + interaction_sum
                
                metrics['total_data_num'] = total_data_num
                metrics['total_praise'] = total_praise
                metrics['total_reblog'] = total_reblog
                metrics['total_comment'] = total_comment
                metrics['interaction_sum'] = interaction_sum
                metrics['total_nums'] = total_nums
                
                logger.info(f"成功使用简单查询获取互动总量数据")
            except Exception as retry_e:
                logger.error(f"重试获取互动数据也失败: {retry_e}")
                # 查询失败时返回0值
                metrics['total_nums'] = 0
                metrics['total_data_num'] = 0
                metrics['total_praise'] = 0
                metrics['total_reblog'] = 0
                metrics['total_comment'] = 0
                metrics['interaction_sum'] = 0
        
        # 6. 语言分布 - 使用更高效的方法获取真实数据，增加超时时间
        try:
            logger.info("开始查询语言分布数据")
            
            # 优化的语言分布查询，使用更大的超时时间
            pipeline = [
                # 只包含有language字段的文档
                {'$match': {'language': {'$exists': True, '$ne': None, '$ne': ''}}},
                # 按language分组并计数
                {'$group': {'_id': '$language', 'count': {'$sum': 1}}},
                # 按计数降序排列
                {'$sort': {'count': -1}},
                # 只返回前5种语言
                {'$limit': 5}
            ]
            
            # 增加超时时间到30秒，确保有足够时间完成查询
            language_results = list(mongo_collection_obj.aggregate(pipeline, maxTimeMS=30000))
            
            # 处理结果
            language_counts = {}
            unique_languages = []
            
            for result in language_results:
                language = result['_id']
                count = result['count']
                language_counts[language] = count
                unique_languages.append(language)
            
            metrics['languages'] = unique_languages
            metrics['language_count'] = len(unique_languages)
            metrics['language_counts'] = language_counts
            
            logger.info(f"成功获取语言分布数据: {len(unique_languages)}种语言")
        except Exception as e:
            logger.warning(f"获取语言信息失败: {e}")
            # 增加查询重试机制
            try:
                logger.info("尝试使用更简单的查询获取语言数据")
                # 改进重试机制：使用distinct获取所有语言，然后单独统计数量
                language_counts = {}
                
                try:
                    # 先获取所有唯一的语言值
                    all_languages = mongo_collection_obj.distinct('language')
                    
                    # 为每个语言单独统计数量
                    for language in all_languages:
                        if language and language != '':
                            count = mongo_collection_obj.count_documents({'language': language})
                            language_counts[language] = count
                    
                    # 按计数排序并取前5个
                    sorted_languages = sorted(language_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                    
                    unique_languages = [l[0] for l in sorted_languages]
                    language_counts = dict(sorted_languages)
                    
                except Exception as distinct_e:
                    logger.warning(f"distinct方法失败，回退到采样方法: {distinct_e}")
                    # 如果distinct方法失败，回退到采样方法，但增加样本量
                    sample_docs = mongo_collection_obj.find(
                        {'language': {'$exists': True, '$ne': None, '$ne': ''}},
                        {'language': 1}
                    ).limit(5000)
                    
                    # 手动统计样本中的语言分布
                    language_counts = {}
                    for doc in sample_docs:
                        language = doc.get('language')
                        if language:
                            language_counts[language] = language_counts.get(language, 0) + 1
                    
                    # 按计数排序并取前5个
                    sorted_languages = sorted(language_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                    
                    unique_languages = [l[0] for l in sorted_languages]
                    language_counts = dict(sorted_languages)
                
                # 设置结果
                metrics['languages'] = unique_languages
                metrics['language_count'] = len(unique_languages)
                metrics['language_counts'] = language_counts
                
                logger.info(f"成功使用简单查询获取语言分布数据: {len(unique_languages)}种语言")
            except Exception as retry_e:
                logger.error(f"重试获取语言信息也失败: {retry_e}")
                # 查询失败时返回空数据
                metrics['languages'] = []
                metrics['language_count'] = 0
                metrics['language_counts'] = {}
        
        # 添加当前数据库集合信息
        try:
            metrics['collections'] = mongo_db.list_collection_names()
        except Exception as e:
            logger.warning(f"获取集合列表失败: {e}")
            metrics['collections'] = []
        
        # 添加数据库状态信息
        metrics['db_status'] = 'connected'
        
        return metrics
    except Exception as e:
        logger.error(f"获取仪表盘指标失败: {e}")
        return {'error': str(e), 'db_status': 'error'}

