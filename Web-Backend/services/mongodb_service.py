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
            serverSelectionTimeoutMS=30000,  # 增加到30秒
            connectTimeoutMS=30000,
            socketTimeoutMS=30000,
            maxPoolSize=20,  # 增加连接池大小
            minPoolSize=5,
            waitQueueTimeoutMS=30000
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


def rebuild_indices(app_config):
    """重建MongoDB索引"""
    try:
        if not mongodb_pool:
            logger.error("MongoDB连接池未初始化，无法重建索引")
            return
        
        # 创建或重建必要的索引
        # 这里可以根据实际需求添加更多索引
        mongo_collection_obj.create_index([("Time", -1)])  # 按时间倒序索引
        mongo_collection_obj.create_index([("Source", 1)])  # 按来源索引
        mongo_collection_obj.create_index([("Title", "text")])  # 全文索引
        
        logger.info("MongoDB索引重建成功")
        
    except Exception as e:
        logger.error(f"MongoDB重建索引失败: {e}")


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


def _prepare_event_data(event_data):
    """准备事件数据，确保格式正确"""
    # 创建一个副本以避免修改原始数据
    data = event_data.copy()
    
    # 处理时间字段
    if 'Time' in data and isinstance(data['Time'], str):
        try:
            # 尝试解析时间字符串
            datetime.strptime(data['Time'], '%Y-%m-%d %H:%M')
        except ValueError:
            # 如果解析失败，设置为当前时间
            data['Time'] = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    # 确保isRisk字段是布尔值
    if 'isRisk' in data:
        if isinstance(data['isRisk'], str):
            data['isRisk'] = data['isRisk'].lower() == 'true'
        elif not isinstance(data['isRisk'], bool):
            data['isRisk'] = bool(data['isRisk'])
    
    # 确保数值字段是数字
    numeric_fields = ['Comment', 'Reblog', 'Praise']
    for field in numeric_fields:
        if field in data:
            try:
                data[field] = int(data[field])
            except (ValueError, TypeError):
                data[field] = 0
    
    return data


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


def insert_event(event_data):
    """插入单个事件数据"""
    if not _check_connection():
        return None
    
    try:
        # 确保数据格式正确
        event = _prepare_event_data(event_data)
        result = mongo_collection_obj.insert_one(event)
        return str(result.inserted_id)
    except Exception as e:
        logger.error(f"插入事件数据失败: {e}")
        return None


def insert_events(events_data):
    """批量插入事件数据"""
    if not _check_connection():
        return []
    
    try:
        # 确保数据格式正确
        events = [_prepare_event_data(event) for event in events_data]
        result = mongo_collection_obj.insert_many(events)
        return [str(id) for id in result.inserted_ids]
    except Exception as e:
        logger.error(f"批量插入事件数据失败: {e}")
        return []


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


def search_events(query=None, page=1, page_size=10, sort_by='Time', sort_order=-1):
    """搜索事件数据，增加重试机制和性能优化"""
    if not _check_connection():
        return [], 0
    
    max_retries = 3  # 最多重试3次
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # 构建查询条件
            search_query = query or {}
            
            # 特别处理isRisk字段，支持同时查询布尔值和字符串类型
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
            if page_size > 1000:
                page_size = 1000
                logger.warning(f"页面大小过大，已限制为1000")
            
            # 执行查询，使用hint强制走合适的索引
            cursor = mongo_collection_obj.find(search_query)
            
            # 排序 - 只对需要的字段排序
            if sort_by:
                try:
                    cursor = cursor.sort(sort_by, sort_order)
                except Exception as e:
                    logger.warning(f"排序失败，使用默认排序: {e}")
            
            # 分页
            events = list(cursor.skip(skip).limit(page_size))
            
            # 转换ObjectId为字符串
            events = [_convert_objectid_to_string(event) for event in events]
            
            # 优化：先获取数据，再计算总数
            try:
                # 对于空查询（获取所有数据），使用更高效的estimated_document_count
                if not search_query:
                    total_count = mongo_collection_obj.estimated_document_count()
                else:
                    # 对于复杂查询，使用count_documents获取准确总数
                    # 虽然性能可能略差，但能确保分页显示正确
                    total_count = mongo_collection_obj.count_documents(search_query)
            except Exception as e:
                logger.warning(f"获取总数失败，使用结果数量作为估计值: {e}")
                total_count = len(events)
            
            return events, total_count
        except (ServerSelectionTimeoutError, ConnectionFailure) as e:
            retry_count += 1
            logger.warning(f"搜索事件数据超时，第{retry_count}次重试: {e}")
            if retry_count >= max_retries:
                logger.error(f"搜索事件数据失败，已达到最大重试次数: {e}")
                # 返回空列表和0，前端可以处理这种情况
                return [], 0
            # 重试前等待一段时间
            import time
            time.sleep(1)
        except Exception as e:
            logger.error(f"搜索事件数据失败: {e}")
            return [], 0


def update_event(event_id, update_data):
    """更新事件数据"""
    if not _check_connection():
        return False
    
    try:
        # 尝试将字符串ID转换为ObjectId
        try:
            obj_id = ObjectId(event_id)
            result = mongo_collection_obj.update_one({'_id': obj_id}, {'$set': update_data})
        except:
            result = mongo_collection_obj.update_one({'_id': event_id}, {'$set': update_data})
            
        return result.modified_count > 0
    except Exception as e:
        logger.error(f"更新事件数据失败: {e}")
        return False


def delete_event(event_id):
    """删除事件数据"""
    if not _check_connection():
        return False
    
    try:
        # 尝试将字符串ID转换为ObjectId
        try:
            obj_id = ObjectId(event_id)
            result = mongo_collection_obj.delete_one({'_id': obj_id})
        except:
            result = mongo_collection_obj.delete_one({'_id': event_id})
            
        return result.deleted_count > 0
    except Exception as e:
        logger.error(f"删除事件数据失败: {e}")
        return False


def export_to_json(file_path, query=None):
    """导出数据到JSON文件"""
    if not _check_connection():
        return False
    
    try:
        events, _ = search_events(query)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(events, f, ensure_ascii=False, cls=JSONEncoder, indent=2)
        return True
    except Exception as e:
        logger.error(f"导出数据到JSON文件失败: {e}")
        return False


def import_from_json(file_path):
    """从JSON文件导入数据"""
    if not _check_connection():
        return False, 0
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            events = json.load(f)
            
        # 确保是列表格式
        if not isinstance(events, list):
            events = [events]
            
        # 插入数据
        inserted_ids = insert_events(events)
        return True, len(inserted_ids)
    except Exception as e:
        logger.error(f"从JSON文件导入数据失败: {e}")
        return False, 0


def create_index(field, unique=False):
    """创建索引以提高查询性能"""
    if not _check_connection():
        return False
    
    try:
        mongo_collection_obj.create_index(field, unique=unique)
        return True
    except Exception as e:
        logger.error(f"创建索引失败: {e}")
        return False


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
            conditions.append({"Event": {"$regex": keyword, "$options": "i"}})
        
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
            conditions.append({"Event": {"$regex": keyword, "$options": "i"}})
        
        # 组合查询条件
        if len(conditions) > 1:
            query = {"$and": conditions}
        else:
            query = conditions[0]
        
        return query
    except Exception as e:
        logger.error(f"构建风险事件查询条件失败: {e}")
        return {"isRisk": "true"}


def execute_query(query_type, params=None):
    """执行查询操作，与db_adapter.py保持兼容性"""
    if not _check_connection():
        return {'error': 'MongoDB未连接'}

    try:
        # 确保params不为None
        params = params or {}

        if query_type == 'getEventsByKeyword':
            # 根据关键词获取事件列表
            keyword = params.get('keyword', '')
            limit = params.get('limit', 100)  # 增加默认限制
            offset = params.get('offset', 0)
            
            # 构建查询条件
            search_query = {}
            if keyword:
                search_query = {'Event': {'$regex': keyword, '$options': 'i'}}
            
            # 计算页码
            page = 1
            if offset > 0 and limit > 0:
                page = (offset // limit) + 1
            
            # 执行查询
            events, total = search_events(
                search_query, 
                page=page, 
                page_size=limit,
                sort_by='Time',
                sort_order=-1
            )
            
            return {'events': events, 'total': total}
        
        elif query_type == 'getEventDetail':
            # 获取事件详情
            event_id = params.get('event_id')
            if not event_id:
                return {'error': '缺少事件ID'}
            
            event = get_event_by_id(event_id)
            return event if event else None
        
        elif query_type == 'getRelatedEvents':
            # 获取相关事件
            event_id = params.get('event_id')
            limit = params.get('limit', 5)
            
            if not event_id:
                return {'error': '缺少事件ID'}
            
            # 首先获取当前事件
            current_event = get_event_by_id(event_id)
            
            if not current_event:
                return {'events': [], 'total': 0}
            
            # 提取关键词（这里简化处理，实际应用可能需要更复杂的文本分析）
            keywords = []
            if 'Event' in current_event:
                keywords.extend(current_event['Event'].split())
            if 'Content' in current_event:
                keywords.extend(current_event['Content'].split())
            
            # 构建查询条件，排除当前事件
            search_query = {
                '_id': {'$ne': current_event['_id']},
                '$or': [
                    {'Event': {'$in': keywords}},
                    {'Content': {'$in': keywords}}
                ]
            }
            
            # 执行查询
            events, total = search_events(
                search_query,
                page=1,
                page_size=limit,
                sort_by='Time',
                sort_order=-1
            )
            
            return {'events': events, 'total': total}
        
        elif query_type == 'searchEvents':
            # 高级搜索事件
            keywords = params.get('keywords', [])
            date_range = params.get('date_range', {})
            sources = params.get('sources', [])
            categories = params.get('categories', [])
            limit = params.get('limit', 100)  # 增加默认限制
            offset = params.get('offset', 0)
            
            # 计算页码
            page = 1
            if offset > 0 and limit > 0:
                page = (offset // limit) + 1
            
            # 构建查询条件
            search_query = {}
            conditions = []
            
            # 处理关键词
            if keywords:
                keyword_conditions = []
                for keyword in keywords:
                    keyword_conditions.append({
                        '$or': [
                            {'Event': {'$regex': keyword, '$options': 'i'}},
                            {'Content': {'$regex': keyword, '$options': 'i'}}
                        ]
                    })
                if len(keyword_conditions) > 1:
                    conditions.append({'$and': keyword_conditions})
                elif keyword_conditions:
                    conditions.append(keyword_conditions[0])
            
            # 处理日期范围
            if date_range.get('start'):
                conditions.append({'Time': {'$gte': date_range['start']}})
            if date_range.get('end'):
                conditions.append({'Time': {'$lte': date_range['end']}})
            
            # 处理来源
            if sources:
                conditions.append({'Source': {'$in': sources}})
            
            # 处理分类
            if categories:
                conditions.append({'Category': {'$in': categories}})
            
            # 组合查询条件
            if len(conditions) > 1:
                search_query = {'$and': conditions}
            elif conditions:
                search_query = conditions[0]
            
            # 执行查询
            events, total = search_events(
                search_query,
                page=page,
                page_size=limit,
                sort_by='Time',
                sort_order=-1
            )
            
            return {'events': events, 'total': total}
        
        elif query_type.startswith('custom:'):
            # 自定义查询，这里是一个示例，实际应用可能需要更复杂的处理
            custom_query = params.get('query', {})
            limit = params.get('limit', 100)  # 增加默认限制
            offset = params.get('offset', 0)
            
            # 计算页码
            page = 1
            if offset > 0 and limit > 0:
                page = (offset // limit) + 1
            
            results, total = search_events(
                custom_query,
                page=page,
                page_size=limit
            )
            
            return {'items': results, 'total': total}
        
        else:
            # 默认查询，直接传递给search_events方法
            results, total = search_events(query_type)
            
            return results
        
    except Exception as e:
        logging.error(f"MongoDB查询错误: {str(e)}")
        return {'error': str(e)}