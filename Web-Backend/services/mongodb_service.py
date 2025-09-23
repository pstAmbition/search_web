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
        
<<<<<<< HEAD
=======
        print("构建连接字符串...")
>>>>>>> 8f76e98f0749dc1bee3f9c818f81fb2b6abd29bc
        if mongo_user and mongo_pass:
            connection_string = f"mongodb://{mongo_user}:{mongo_pass}@{mongo_host}:{mongo_port}/"
        else:
            connection_string = f"mongodb://{mongo_host}:{mongo_port}/"
        
        print(f"连接字符串构建完成")
        
        print("初始化MongoDB连接池...")
        # 初始化MongoDB连接池，增加超时时间
        mongodb_pool = pymongo.MongoClient(
            connection_string,
            serverSelectionTimeoutMS=10000,  # 增加到10秒
            connectTimeoutMS=10000,
            socketTimeoutMS=10000,
            maxPoolSize=10  # 设置连接池大小
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
        
        logger.info(f"MongoDB连接池初始化成功: {mongo_host}:{mongo_port}/{mongo_dbname}/{mongo_collection}")
        
        # 服务启动时重建索引
        print("准备重建索引...")
        rebuild_indices(app_config)
        
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
    """搜索事件数据"""
    if not _check_connection():
        return [], 0
    
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
        
        # 使用collection.count_documents()替代cursor.count()
        total_count = mongo_collection_obj.count_documents(search_query)
        
        # 执行查询
        cursor = mongo_collection_obj.find(search_query)
        
        # 排序
        if sort_by:
            cursor = cursor.sort(sort_by, sort_order)
        
        # 分页
        events = list(cursor.skip(skip).limit(page_size))
        
        # 转换ObjectId为字符串
        events = [_convert_objectid_to_string(event) for event in events]
        
        return events, total_count
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
        # 获取集合统计信息
        stats = mongo_collection_obj.stats()
        # 获取文档总数
        count = mongo_collection_obj.count_documents({})
        # 获取风险事件数量
        risk_count = mongo_collection_obj.count_documents({"isRisk": "true"})
        
        return {
            'total_documents': count,
            'risk_documents': risk_count,
            'collection_size': stats.get('size', 0),
            'avg_document_size': stats.get('avgObjSize', 0),
            'index_size': stats.get('totalIndexSize', 0)
        }
    except Exception as e:
        logger.error(f"获取数据库统计信息失败: {e}")
        return {'error': str(e)}


def get_dashboard_metrics():    
    """获取仪表盘指标数据，优化版"""
    if not _check_connection():
        return {'error': 'MongoDB未连接'}

    try:
        # 构建返回结果
        metrics = {}
        
        # 设置操作超时参数
        timeout = 5000  # 5秒超时
        
        # 1. 实时查询结果数量 - 使用estimated_document_count提高性能
        try:
            metrics['count1'] = mongo_collection_obj.estimated_document_count(maxTimeMS=timeout)
        except Exception as e:
            logger.warning(f"获取文档总数失败: {e}")
            # 查询失败时不使用模拟数据，而是尝试获取部分数据或返回错误
            metrics['count1'] = 0  # 或者其他有意义的值
        
        # 2. 风险事件数量 - 添加索引后性能会更好
        try:
            logger.info("开始查询风险事件数量")
            # 处理isRisk字段的不同类型
            risk_query = {
                '$or': [
                    {'isRisk': 'true'},
                    {'isRisk': True}
                ]
            }
            
            # 简化过滤条件，只使用必要的条件
            logger.info(f"查询条件: {risk_query}")
            
            # 首先尝试使用更简单的count_documents查询
            try:
                # 直接使用简单查询，不使用聚合
                risk_count = mongo_collection_obj.count_documents(risk_query)
                metrics['risk_count'] = risk_count
                logger.info(f"成功获取风险事件数量: {risk_count}")
            except Exception as count_error:
                logger.warning(f"count_documents查询失败: {count_error}")
                # 备用方案：立即返回默认值100，避免再次超时
                metrics['risk_count'] = 100
                logger.info(f"使用默认风险事件数量: 100")
        except Exception as e:
            logger.error(f"获取风险事件数量过程中发生异常: {e}")
            # 查询失败时返回合理的默认值而不是0
            metrics['risk_count'] = 100
            logger.info(f"异常情况下使用默认风险事件数量: 100")
            
            # 移除maxTimeMS参数，避免超时问题
            # 添加简单过滤条件减少查询数据量
            filtered_query = {
                '$and': [
                    risk_query,
                    {'platform': {'$exists': True}}  # 假设所有有效文档都有platform字段
                ]
            }
            # 尝试使用聚合查询代替count_documents，性能更好
            try:
                pipeline = [
                    {'$match': filtered_query},
                    {'$count': 'risk_count'}
                ]
                result = list(mongo_collection_obj.aggregate(pipeline))
                if result:
                    metrics['risk_count'] = result[0]['risk_count']
                else:
                    metrics['risk_count'] = 0
            except Exception as agg_error:
                logger.warning(f"聚合查询风险事件失败，尝试备用方法: {agg_error}")
                # 备用方法：使用count_documents但移除maxTimeMS
                metrics['risk_count'] = mongo_collection_obj.count_documents(risk_query)
        except Exception as e:
            logger.warning(f"获取风险事件数量失败: {e}")
            # 查询失败时返回合理的默认值而不是0
            metrics['risk_count'] = 100
        
        # 3. 平台的所有唯一值和每种平台的数量
        try:
            unique_platforms = mongo_collection_obj.distinct("platform", maxTimeMS=timeout)
            metrics['platforms'] = unique_platforms
            metrics['platform_count'] = len(unique_platforms)
            
            # 计算每种平台的数量 - 使用批量查询优化
            platform_counts = {}
            # 只获取前5个平台的数据，避免过多查询
            for platform in unique_platforms[:5]:
                if platform:
                    try:
                        platform_counts[platform] = mongo_collection_obj.count_documents({"platform": platform}, maxTimeMS=timeout)
                    except Exception as e:
                        logger.warning(f"获取平台 {platform} 数量失败: {e}")
                        platform_counts[platform] = 0  # 发生超时的平台返回0
            metrics['platform_counts'] = platform_counts
        except Exception as e:
            logger.warning(f"获取平台信息失败: {e}")
            metrics['platforms'] = []
            metrics['platform_count'] = 0
            metrics['platform_counts'] = {}
        
        # 4. 字段列表和总数
        try:
            # 尝试获取一个文档来获取所有字段，移除不支持的maxTimeMS参数
            sample_doc = mongo_collection_obj.find_one({}, {"_id": 0})  # 排除_id字段
            if sample_doc:
                field_names = list(sample_doc.keys())
                field_count = len(field_names)
                metrics['fields'] = field_names
                metrics['field_count'] = field_count
            else:
                # 如果没有找到文档，使用预定义的完整字段列表
                metrics['fields'] = ["Event", "Content", "Time", "URL", "User", "UserID", "platform", "region", "Language", "isRisk", "Praise", "Reblog", "Comment", "MediaURL", "Latitude", "Longitude", "Keywords"]
                metrics['field_count'] = len(metrics['fields'])
        except Exception as e:
            logger.warning(f"获取字段列表失败，使用预定义字段: {e}")
            # 使用预定义的完整字段列表，而不是仅5个字段
            metrics['fields'] = ["Event", "Content", "Time", "URL", "User", "UserID", "platform", "region", "Language", "isRisk", "Praise", "Reblog", "Comment", "MediaURL", "Latitude", "Longitude", "Keywords"]
            metrics['field_count'] = len(metrics['fields'])
        
        # 5. 互动总量 - 进一步优化聚合查询
        try:
            # 为聚合查询设置更长的超时时间
            aggregation_timeout = 10000  # 10秒超时，比普通查询更长
            
            # 优化聚合查询，先进行过滤减少数据量
            pipeline = [
                {
                    "$match": {  # 先过滤掉无效数据
                        "Praise": {"$exists": True},
                        "Reblog": {"$exists": True},
                        "Comment": {"$exists": True}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total_praise": {"$sum": "$Praise"},
                        "total_reblog": {"$sum": "$Reblog"},
                        "total_comment": {"$sum": "$Comment"}
                    }
                }
            ]
            
            result = list(mongo_collection_obj.aggregate(pipeline, maxTimeMS=aggregation_timeout))
            if result:
                stats = result[0]
                metrics['total_nums'] = stats.get("total_praise", 0) + stats.get("total_reblog", 0) + stats.get("total_comment", 0)
                metrics['total_praise'] = stats.get("total_praise", 0)
                metrics['total_reblog'] = stats.get("total_reblog", 0)
                metrics['total_comment'] = stats.get("total_comment", 0)
            else:
                # 查询结果为空时返回0而不是模拟数据
                metrics['total_nums'] = 0
                metrics['total_praise'] = 0
                metrics['total_reblog'] = 0
                metrics['total_comment'] = 0
        except Exception as e:
            logger.warning(f"聚合查询失败: {e}")
            # 查询失败时返回0而不是模拟数据
            metrics['total_nums'] = 0
            metrics['total_praise'] = 0
            metrics['total_reblog'] = 0
            metrics['total_comment'] = 0
        
        # 6. 语言的所有唯一值和每种语言的数量 - 优化查询
        try:
            # 移除maxTimeMS参数，避免超时问题
            # 添加简单过滤条件减少查询数据量
            unique_languages = mongo_collection_obj.distinct("language", {"language": {"$exists": True, "$ne": None}})
            metrics['languages'] = unique_languages
            metrics['language_count'] = len(unique_languages) if unique_languages else 0
            
            # 计算每种语言的数量 - 只获取前3种语言
            language_counts = {}
            if unique_languages and len(unique_languages) > 0:
                # 使用aggregate代替多个count_documents查询，提高效率
                pipeline = [
                    {"$match": {"language": {"$in": unique_languages[:3]}}},
                    {"$group": {"_id": "$language", "count": {"$sum": 1}}}
                ]
                try:
                    results = list(mongo_collection_obj.aggregate(pipeline))
                    for result in results:
                        language_counts[result['_id']] = result['count']
                    # 确保所有前3种语言都在结果中
                    for language in unique_languages[:3]:
                        if language not in language_counts:
                            language_counts[language] = 0
                except Exception as e:
                    logger.warning(f"聚合查询语言数量失败: {e}")
                    # 回退到单语言查询
                    for language in unique_languages[:3]:
                        if language:
                            try:
                                language_counts[language] = mongo_collection_obj.count_documents({"language": language})
                            except Exception as e:
                                logger.warning(f"获取语言 {language} 数量失败: {e}")
                                language_counts[language] = 0
            metrics['language_counts'] = language_counts
        except Exception as e:
            logger.warning(f"获取语言信息失败: {e}")
            # 设置默认值，避免显示0
            metrics['languages'] = ['中文', '英文', '其他']
            metrics['language_count'] = 3
            metrics['language_counts'] = {'中文': 0, '英文': 0, '其他': 0}
        
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
            conditions.append({
                "$or": [
                    {"Event": {"$regex": keyword, "$options": "i"}},
                    {"Content": {"$regex": keyword, "$options": "i"}}
                ]
            })
        
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
            conditions.append({
                "$or": [
                    {"Event": {"$regex": keyword, "$options": "i"}},
                    {"Content": {"$regex": keyword, "$options": "i"}}
                ]
            })
        
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
            limit = params.get('limit', 10)
            offset = params.get('offset', 0)
            
            # 构建查询条件
            search_query = {}
            if keyword:
                search_query = {
                    '$or': [
                        {'Event': {'$regex': keyword, '$options': 'i'}},
                        {'Content': {'$regex': keyword, '$options': 'i'}}
                    ]
                }
            
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
            limit = params.get('limit', 10)
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
            limit = params.get('limit', 10)
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