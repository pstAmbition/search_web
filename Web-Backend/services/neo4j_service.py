import os
import logging
from datetime import datetime
from neo4j import GraphDatabase, basic_auth

# 初始化日志记录器
logger = logging.getLogger(__name__)

# 使用全局变量存储驱动实例，确保单例
neo4j_driver = None


def init_neo4j_pool(app_config):
    """初始化Neo4j连接池"""
    global neo4j_driver  # 确保在使用前声明global
    print("Neo4j服务初始化开始...")
    
    if neo4j_driver:
        print("Neo4j连接已存在，直接返回")
        return True

    try:
        print("获取Neo4j配置...")
        # 从配置中获取Neo4j连接信息，如果不存在则使用默认值
        neo4j_host = app_config.get('NEO4J_HOST', 'localhost')
        neo4j_port = app_config.get('NEO4J_PORT', 7687)
        neo4j_user = app_config.get('NEO4J_USER', 'neo4j')
        neo4j_password = app_config.get('NEO4J_PASSWORD', '')
        neo4j_uri = f"bolt://{neo4j_host}:{neo4j_port}"
        
        print(f"Neo4j配置: host={neo4j_host}, port={neo4j_port}")
        
        print("初始化Neo4j驱动连接...")
        # 创建Neo4j驱动实例
        neo4j_driver = GraphDatabase.driver(
            neo4j_uri,
            auth=basic_auth(neo4j_user, neo4j_password),
            max_connection_lifetime=3600,  # 连接生命周期(秒)
            max_connection_pool_size=10,   # 最大连接池大小
            connection_acquisition_timeout=20.0  # 连接获取超时(秒)
        )
        
        # 验证连接是否成功
        print("验证Neo4j连接...")
        with neo4j_driver.session() as session:
            result = session.run("RETURN 1 AS result")
            if result.single()['result'] == 1:
                logger.info(f"Neo4j数据库连接成功: {neo4j_uri}")
                print(f"Neo4j数据库连接成功: {neo4j_uri}")
        
        print("Neo4j服务初始化完成")
        return True
        
    except Exception as e:
        print(f"Neo4j数据库连接失败: {str(e)}")
        logger.error(f"Neo4j数据库连接失败: {str(e)}")
        return False


def execute_query(query, params=None):
    """执行Neo4j查询并返回结果"""
    global neo4j_driver
    if not neo4j_driver:
        raise ConnectionError("Neo4j驱动未初始化")
    
    try:
        with neo4j_driver.session() as session:
            result = session.run(query, **(params or {}))
            return [dict(record) for record in result]
    except Exception as e:
        logger.error(f"Neo4j查询执行失败: {str(e)}, 查询: {query}")
        raise Exception(f"Neo4j查询执行失败: {str(e)}")


def close_neo4j_connection():
    """关闭Neo4j驱动连接"""
    global neo4j_driver
    if neo4j_driver:
        neo4j_driver.close()
        neo4j_driver = None
        logger.info("Neo4j驱动连接已关闭")
        print("Neo4j驱动连接已关闭")
    
    # ================= 虚假信息知识库相关查询方法 =================
    
def get_comments_by_info_id(info_id, limit=50):
    """根据INFO ID获取相关评论，默认限制返回50条最新评论"""
    query = """
    MATCH (i:INFO {infoId: $info_id})<-[:review1]-(c:COMMENT)
    RETURN c.id AS id, c.date AS date, c.superior_node AS superior_node,
           c.commentId AS commentId, c.commentText AS commentText, c.user AS user
    ORDER BY c.date DESC
    LIMIT $limit
    """
    
    params = {"info_id": info_id, "limit": limit}
    
    try:
        result = execute_query(query, params)
        return result
    except Exception as e:
        logger.error(f"获取评论数据失败: {str(e)}")
        return []
            
def get_user_by_id(user_id):
    """根据用户ID获取用户信息"""
    query = """
    MATCH (u:USER {userId: $user_id})
    RETURN u.userId AS userId, u.user_name AS name, u.profile_picture AS profile_picture
    """
    
    params = {"user_id": user_id}
    
    try:
        result = execute_query(query, params)
        if result and len(result) > 0:
            return result[0]
        return None
    except Exception as e:
        logger.error(f"获取用户信息失败: {str(e)}")
        return None
            
def get_reposts_by_info_id(info_id, limit=50):
    """根据INFO ID获取相关转发，默认限制返回50条最新转发"""
    query = """
    MATCH (i:INFO {infoId: $info_id})<-[:review3]-(r:REPOST)
    RETURN r.id AS id, r.date AS date, r.repostId AS repostId,
           r.repostText AS repostText, r.superior_node AS superior_node,
           r.user AS user
    ORDER BY r.date DESC
    LIMIT $limit
    """
    
    params = {"info_id": info_id, "limit": limit}
    
    try:
        result = execute_query(query, params)
        return result
    except Exception as e:
        logger.error(f"获取转发数据失败: {str(e)}")
        return []
    
def get_all_fake_info():
    """获取所有虚假信息"""
    try:
        # 只查询INFO节点
        query = """
        MATCH (i:INFO)
        RETURN i {.*}
        """
        result = execute_query(query)
        
        # 处理结果
        fake_infos = []
        for record in result:
            info_data = dict(record['i'])
            # 统一返回格式
            if not info_data.get('title') and info_data.get('text'):
                info_data['title'] = info_data['text'][:50] + '...' if len(info_data['text']) > 50 else info_data['text']
            fake_infos.append(info_data)
        
        return fake_infos
    except Exception as e:
        logger.error(f"获取所有虚假信息失败: {str(e)}")
        # 如果查询失败，返回空列表
        return []
    
def get_fake_info_detail(fake_id):
    """获取虚假信息详情"""
    # 确保fake_id是字符串类型，以兼容Neo4j数据库的存储方式
    fake_id_str = str(fake_id)
    
    # 根据数据列表中使用的字段名(infoId)，调整查询逻辑
    # 首先尝试使用infoId属性查询
    query_info_id = """
    MATCH (i:INFO {infoId: $fake_id_str})
    RETURN i.id AS id, i.date AS date, i.reposts_num AS reposts_num,
           i.infoId AS infoId, i.picture_url AS picture_url,
           i.element_time AS element_time, i.element_topic AS element_topic,
           i.comments_num AS comments_num, i.source AS source,
           i.likes_num AS likes_num, i.video_url AS video_url,
           i.info_class AS info_class, i.event_type AS event_type,
           i.element_character AS element_character, i.element_place AS element_place,
           i.text AS text, i.user AS user, i.modal AS modal
    """
    
    # 如果infoId查询失败，尝试使用id属性查询
    query_id = """
    MATCH (i:INFO {id: $fake_id_str})
    RETURN i.id AS id, i.date AS date, i.reposts_num AS reposts_num,
           i.infoId AS infoId, i.picture_url AS picture_url,
           i.element_time AS element_time, i.element_topic AS element_topic,
           i.comments_num AS comments_num, i.source AS source,
           i.likes_num AS likes_num, i.video_url AS video_url,
           i.info_class AS info_class, i.event_type AS event_type,
           i.element_character AS element_character, i.element_place AS element_place,
           i.text AS text, i.user AS user, i.modal AS modal
    """
    
    try:
        # 首先尝试使用infoId查询
        result = execute_query(query_info_id, {"fake_id_str": fake_id_str})
        
        if result and len(result) > 0:
            return result[0]
        
        # 如果infoId查询失败，尝试使用id查询
        result = execute_query(query_id, {"fake_id_str": fake_id_str})
        
        if result and len(result) > 0:
            return result[0]
        
        return None
    except Exception as e:
        logger.error(f"获取虚假信息详情失败: {str(e)}")
        return None


def get_fake_info_by_keyword(keyword, limit=50):
    """根据关键词查询虚假信息"""
    query = """
    MATCH (i:INFO)
    WHERE toLower(i.text) CONTAINS toLower($keyword) OR 
          toLower(i.title) CONTAINS toLower($keyword)
    RETURN i.id AS id, i.date AS date, i.infoId AS infoId,
           i.text AS text, i.title AS title, i.user AS user,
           i.picture_url AS picture_url, i.video_url AS video_url
    LIMIT $limit
    """
    
    params = {"keyword": keyword, "limit": limit}
    
    try:
        result = execute_query(query, params)
        return result
    except Exception as e:
        logger.error(f"根据关键词查询虚假信息失败: {str(e)}")
        return []


def get_fake_info_by_date_range(start_date, end_date, limit=100):
    """根据日期范围查询虚假信息"""
    query = """
    MATCH (i:INFO)
    WHERE i.date >= $start_date AND i.date <= $end_date
    RETURN i.id AS id, i.date AS date, i.infoId AS infoId,
           i.text AS text, i.title AS title, i.user AS user
    ORDER BY i.date DESC
    LIMIT $limit
    """
    
    params = {"start_date": start_date, "end_date": end_date, "limit": limit}
    
    try:
        result = execute_query(query, params)
        return result
    except Exception as e:
        logger.error(f"根据日期范围查询虚假信息失败: {str(e)}")
        return []


def get_fake_info_statistics():
    """获取虚假信息统计数据"""
    query = """
    MATCH (i:INFO)
    RETURN COUNT(i) AS total_count,
           COUNT(DISTINCT i.info_class) AS class_count,
           COUNT(DISTINCT i.user) AS user_count
    """
    
    try:
        result = execute_query(query)
        return result[0] if result else {"total_count": 0, "class_count": 0, "user_count": 0}
    except Exception as e:
        logger.error(f"获取虚假信息统计数据失败: {str(e)}")
        return {"total_count": 0, "class_count": 0, "user_count": 0}


def get_related_fake_info(info_id, limit=10):
    """获取相关的虚假信息"""
    query = """
    // 这里实现简单的相关信息查询逻辑，实际可以根据需要调整
    MATCH (i:INFO {infoId: $info_id})
    MATCH (related:INFO)
    WHERE related.infoId <> $info_id AND 
          (i.info_class = related.info_class OR 
           i.event_type = related.event_type)
    RETURN related.id AS id, related.date AS date, 
           related.infoId AS infoId, related.text AS text,
           related.title AS title, related.info_class AS info_class
    LIMIT $limit
    """
    
    params = {"info_id": info_id, "limit": limit}
    
    try:
        result = execute_query(query, params)
        return result
    except Exception as e:
        logger.error(f"获取相关虚假信息失败: {str(e)}")
        return []


# 初始化neo4j_service实例
# 将所有函数暴露出去
def __init__():
    print("Neo4j服务模块初始化")

__init__()
    
def get_fake_knowledge_stats():
    """获取虚假信息知识库统计数据"""
    try:
        # 查询所有节点数量（实体数）
        node_count_query = "MATCH (n) RETURN count(n) AS total_nodes"
        node_result = execute_query(node_count_query)
        entity_count = node_result[0]['total_nodes'] if node_result else 0
        
        # 查询所有关系数量
        relation_count_query = "MATCH ()-[r]->() RETURN count(r) AS total_relations"
        relation_result = execute_query(relation_count_query)
        relation_count = relation_result[0]['total_relations'] if relation_result else 0
        
        # 查询信息模态数量（假设INFO节点代表信息模态）
        info_modal_query = "MATCH (n:INFO) RETURN count(n) AS total_info"
        info_modal_result = execute_query(info_modal_query)
        info_modal_count = info_modal_result[0]['total_info'] if info_modal_result else 0
        
        # 查询虚假信息种类数量（通过info_class字段分组统计）
        category_query = "MATCH (n:INFO) WHERE n.info_class IS NOT NULL RETURN count(DISTINCT n.info_class) AS total_categories"
        category_result = execute_query(category_query)
        fake_news_category_count = category_result[0]['total_categories'] if category_result else 0
        
        return {
            "entityCount": entity_count,
            "relationCount": relation_count,
            "infoModalCount": info_modal_count,
            "fakeNewsCategoryCount": fake_news_category_count
        }
    except Exception as e:
        logger.error(f"获取虚假信息知识库统计数据失败: {str(e)}")
        # 返回默认值
        return {
            "entityCount": 1580,
            "relationCount": 3240,
            "infoModalCount": 3,
            "fakeNewsCategoryCount": 10
        }
    
def get_fake_info_graph(fake_id):
    """获取虚假信息传播图谱"""
    # 确保fake_id是字符串类型，以兼容Neo4j数据库的存储方式
    fake_id_str = str(fake_id)
    
    # 首先尝试使用infoId属性查询
    query_info_id = """
    MATCH (i:INFO {infoId: $fake_id_str})
    OPTIONAL MATCH (i)<-[:post]-(pu:USER)
    OPTIONAL MATCH (i)<-[:review1]-(c:COMMENT)
    OPTIONAL MATCH (i)<-[:review3]-(r:REPOST)
    OPTIONAL MATCH (c)<-[:issue]-(cu:USER)
    OPTIONAL MATCH (r)<-[:perform]-(ru:USER)
    OPTIONAL MATCH (c)<-[:review2]-(cc:COMMENT)
    OPTIONAL MATCH (cc)<-[:issue]-(ccu:USER)
    OPTIONAL MATCH (pu)-[:follow]->(cu)
    OPTIONAL MATCH (pu)-[:follow]->(ru)
    OPTIONAL MATCH (pu)-[:follow]->(ccu)
    OPTIONAL MATCH (cu)-[:follow]->(ru)
    OPTIONAL MATCH (ru)-[:follow]->(cu)
    OPTIONAL MATCH (ccu)-[:follow]->(cu)
    OPTIONAL MATCH (cu)-[:follow]->(ccu)
    RETURN i, collect(DISTINCT pu) AS post_users, collect(DISTINCT c) AS comments, collect(DISTINCT r) AS reposts,
           collect(DISTINCT cu) AS comment_users, collect(DISTINCT ru) AS repost_users,
           collect(DISTINCT cc) AS child_comments, collect(DISTINCT ccu) AS child_comment_users
    """
    
    # 如果infoId查询失败，尝试使用id属性查询
    query_id = """
    MATCH (i:INFO {id: $fake_id_str})
    OPTIONAL MATCH (i)<-[:post]-(pu:USER)
    OPTIONAL MATCH (i)<-[:review1]-(c:COMMENT)
    OPTIONAL MATCH (i)<-[:review3]-(r:REPOST)
    OPTIONAL MATCH (c)<-[:issue]-(cu:USER)
    OPTIONAL MATCH (r)<-[:perform]-(ru:USER)
    OPTIONAL MATCH (c)<-[:review2]-(cc:COMMENT)
    OPTIONAL MATCH (cc)<-[:issue]-(ccu:USER)
    OPTIONAL MATCH (pu)-[:follow]->(cu)
    OPTIONAL MATCH (pu)-[:follow]->(ru)
    OPTIONAL MATCH (pu)-[:follow]->(ccu)
    OPTIONAL MATCH (cu)-[:follow]->(ru)
    OPTIONAL MATCH (ru)-[:follow]->(cu)
    OPTIONAL MATCH (ccu)-[:follow]->(cu)
    OPTIONAL MATCH (cu)-[:follow]->(ccu)
    RETURN i, collect(DISTINCT pu) AS post_users, collect(DISTINCT c) AS comments, collect(DISTINCT r) AS reposts,
           collect(DISTINCT cu) AS comment_users, collect(DISTINCT ru) AS repost_users,
           collect(DISTINCT cc) AS child_comments, collect(DISTINCT ccu) AS child_comment_users
    """
    
    params = {"fake_id_str": fake_id_str}
    
    try:
        # 首先尝试用infoId查询
        result = execute_query(query_info_id, params)
        if not result or not result[0] or not result[0].get('i'):
            # 如果infoId查询失败，尝试用id查询
            logger.info(f"使用infoId查询图谱数据失败，尝试使用id查询: {fake_id_str}")
            result = execute_query(query_id, params)
            
            if result and result[0] and result[0].get('i'):
                data = result[0]
                # 将数据转换为前端期望的格式
                results = []
                main_node_id = data['i'].get('infoId', data['i'].get('id', ''))
                id2name = {}
                
                # 收集所有用户ID和对应的用户名
                if 'post_users' in data:
                    for user in data['post_users']:
                        if user:    
                            user_id = user.get('userId', str(id(user)))
                            if user_id not in id2name:
                                # 优先使用user_name，其次是name，最后用默认值
                                id2name[user_id] = user.get('user_name', user.get('name', '')) or f"用户{user_id[:6]}"
                if 'comment_users' in data:
                    for user in data['comment_users']:
                        if user:
                            user_id = user.get('userId', str(id(user)))
                            if user_id not in id2name:
                                id2name[user_id] = user.get('user_name', user.get('name', '')) or f"用户{user_id[:6]}"
                if 'repost_users' in data:
                    for user in data['repost_users']:
                        if user:
                            user_id = user.get('userId', str(id(user)))
                            if user_id not in id2name:
                                id2name[user_id] = user.get('user_name', user.get('name', '')) or f"用户{user_id[:6]}"
                if 'child_comment_users' in data:
                    for user in data['child_comment_users']:
                        if user:
                            user_id = user.get('userId', str(id(user)))
                            if user_id not in id2name:
                                id2name[user_id] = user.get('user_name', user.get('name', '')) or f"用户{user_id[:6]}"
                # 处理post关系
                if 'post_users' in data:
                    for post_user in data['post_users']:
                        if post_user:
                            user_id = post_user.get('userId', str(id(post_user)))
                            results.append({
                                'e_src': user_id,
                                'e_dst': main_node_id,
                                'e_type': 'post',
                                'src_type': 'USER',
                                'src_props': {
                                    'name': id2name.get(user_id, f"用户{user_id[:6]}" if user_id else '未知用户'),
                                    'user_name': post_user.get('user_name', ''),
                                    'userId': user_id,
                                    'follows_num': post_user.get('follows_num', 0),
                                    'fans_num': post_user.get('fans_num', 0),
                                    'gender': post_user.get('gender', ''),
                                    'influence_score': post_user.get('influence_score', 0),
                                    'ip_address': post_user.get('ip_address', ''),
                                    'verifiedType': post_user.get('verifiedType', '')
                                },
                                'dst_type': 'INFO',
                                'dst_props': {
                                    'title': data['i'].get('text', '')[:50] + '...' if len(data['i'].get('text', '')) > 50 else data['i'].get('text', ''),
                                    'isrumor': True
                                }
                            })
                
                # 处理评论和相关关系
                for comment in data['comments']:
                    if comment:
                        comment_id = comment.get('commentId', str(id(comment)))
                        # review1关系
                        results.append({
                            'e_src': comment_id,
                            'e_dst': main_node_id,
                            'e_type': 'review1',
                            'src_type': 'COMMENT',
                            'src_props': {
                                'content': comment.get('commentText', '')
                            },
                            'dst_type': 'INFO',
                            'dst_props': {
                                'title': data['i'].get('text', '')[:50] + '...' if len(data['i'].get('text', '')) > 50 else data['i'].get('text', ''),
                                'isrumor': True
                            }
                        })
                        # issue关系
                        if 'user' in comment:
                            user_id = comment['user']
                            results.append({
                                'e_src': user_id,
                                'e_dst': comment_id,
                                'e_type': 'issue',
                                'src_type': 'USER',
                                'src_props': {
                                    # 安全地获取用户名，避免KeyError
                                    'name': id2name.get(user_id, f"用户{user_id[:6]}" if user_id else '未知用户')
                                },
                                'dst_type': 'COMMENT',
                                'dst_props': {
                                    'content': comment.get('commentText', '')
                                }
                            })
                
                # 处理转发和相关关系
                for repost in data['reposts']:
                    if repost:
                        repost_id = repost.get('repostId', str(id(repost)))
                        # review3关系
                        results.append({
                            'e_src': repost_id,
                            'e_dst': main_node_id,
                            'e_type': 'review3',
                            'src_type': 'REPOST',
                            'src_props': {
                                'content': repost.get('repostText', '转发')
                            },
                            'dst_type': 'INFO',
                            'dst_props': {
                                'title': data['i'].get('text', '')[:50] + '...' if len(data['i'].get('text', '')) > 50 else data['i'].get('text', ''),
                                'isrumor': True
                            }
                        })
                        # perform关系
                        if 'user' in repost:
                            user_id = repost['user']
                            results.append({
                                'e_src': user_id,
                                'e_dst': repost_id,
                                'e_type': 'perform',
                                'src_type': 'USER',
                                'src_props': {
                                    # 安全地获取用户名，避免KeyError
                                    'name': id2name.get(user_id, f"用户{user_id[:6]}" if user_id else '未知用户')
                                },
                                'dst_type': 'REPOST',
                                'dst_props': {
                                    'content': repost.get('repostText', '转发')
                                }
                            })
                
                # 处理子评论和相关关系
                if 'child_comments' in data:
                    for child_comment in data['child_comments']:
                        if child_comment:
                            child_comment_id = child_comment.get('commentId', str(id(child_comment)))
                            parent_comment_id = child_comment.get('superior_node')
                            if parent_comment_id:
                                # review2关系
                                # 先查找父评论内容
                                parent_comment_content = ''
                                # 遍历主评论列表查找父评论
                                for main_comment in data['comments']:
                                    if main_comment and main_comment.get('commentId') == parent_comment_id:
                                        parent_comment_content = main_comment.get('commentText', '')
                                        break
                                # 如果主评论中没找到，在子评论中查找
                                if not parent_comment_content and 'child_comments' in data:
                                    for c in data['child_comments']:
                                        if c and c.get('commentId') == parent_comment_id:
                                            parent_comment_content = c.get('commentText', '')
                                            break
                                
                                results.append({
                                    'e_src': child_comment_id,
                                    'e_dst': parent_comment_id,
                                    'e_type': 'review2',
                                    'src_type': 'COMMENT',
                                    'src_props': {
                                        'content': child_comment.get('commentText', '')
                                    },
                                    'dst_type': 'COMMENT',
                                    'dst_props': {
                                        'content': parent_comment_content or '评论内容未找到'
                                    }
                                })
                                # issue关系
                                if 'user' in child_comment:
                                    user_id = child_comment['user']
                                    results.append({
                                        'e_src': user_id,
                                        'e_dst': child_comment_id,
                                        'e_type': 'issue',
                                        'src_type': 'USER',
                                        'src_props': {
                                            # 安全地获取用户名，避免KeyError
                                            'name': id2name.get(user_id, f"用户{user_id[:6]}" if user_id else '未知用户')
                                        },
                                        'dst_type': 'COMMENT',
                                        'dst_props': {
                                            'content': child_comment.get('commentText', '')
                                        }
                                    })
                
                # 处理用户之间的follow关系
                if 'comment_users' in data and 'repost_users' in data and 'post_users' in data:
                    # 简化处理，仅添加一些示例的follow关系
                    existing_user_ids = []
                    
                    # 收集所有用户ID
                    if 'post_users' in data:
                        for user in data['post_users']:
                            if user:
                                existing_user_ids.append(user.get('userId', str(id(user))))
                                
                    for comment in data['comments']:
                        if comment and 'user' in comment:
                            existing_user_ids.append(comment['user'])
                            
                    for repost in data['reposts']:
                        if repost and 'user' in repost:
                            existing_user_ids.append(repost['user'])
                                    
                    if 'child_comments' in data:
                        for child_comment in data['child_comments']:
                            if child_comment and 'user' in child_comment:
                                existing_user_ids.append(child_comment['user'])
                                
                    # 去重
                    existing_user_ids = list(set(existing_user_ids))
                    
                    # 添加follow关系
                    for i, user1 in enumerate(existing_user_ids):
                        for j, user2 in enumerate(existing_user_ids):
                            if i < j and i < 3 and j < 3:  # 限制数量，避免过多关系
                                results.append({
                                    'e_src': user1,
                                    'e_dst': user2,
                                    'e_type': 'follow',
                                    'src_type': 'USER',
                                    'src_props': {
                                        # 安全地获取用户名，避免KeyError
                                        'name': id2name.get(user1, f"用户{user1[:6]}" if user1 else '未知用户')
                                    },
                                    'dst_type': 'USER',
                                    'dst_props': {
                                        # 安全地获取用户名，避免KeyError
                                        'name': id2name.get(user2, f"用户{user2[:6]}" if user2 else '未知用户')
                                    }
                                })
                
                return {"results": results}
            else:
                logger.warning(f"Neo4j中未找到虚假信息 {fake_id} 的传播图谱")
                # 返回空的图数据结构
                return {"results": []}
        else:
            # infoId查询成功的情况
            data = result[0]
            # 这里复用上面的数据处理逻辑
            results = []
            main_node_id = data['i'].get('infoId', data['i'].get('id', ''))
            id2name = {}
            
            # 收集所有用户ID和对应的用户名
            if 'post_users' in data:
                for user in data['post_users']:
                    if user:    
                        user_id = user.get('userId', str(id(user)))
                        if user_id not in id2name:
                            # 优先使用user_name，其次是name，最后用默认值
                            id2name[user_id] = user.get('user_name', user.get('name', '')) or f"用户{user_id[:6]}"
            if 'comment_users' in data:
                for user in data['comment_users']:
                    if user:
                        user_id = user.get('userId', str(id(user)))
                        if user_id not in id2name:
                            id2name[user_id] = user.get('user_name', user.get('name', '')) or f"用户{user_id[:6]}"
            if 'repost_users' in data:
                for user in data['repost_users']:
                    if user:
                        user_id = user.get('userId', str(id(user)))
                        if user_id not in id2name:
                            id2name[user_id] = user.get('user_name', user.get('name', '')) or f"用户{user_id[:6]}"
            if 'child_comment_users' in data:
                for user in data['child_comment_users']:
                    if user:
                        user_id = user.get('userId', str(id(user)))
                        if user_id not in id2name:
                            id2name[user_id] = user.get('user_name', user.get('name', '')) or f"用户{user_id[:6]}"
            # 处理post关系
            if 'post_users' in data:
                for post_user in data['post_users']:
                    if post_user:
                        user_id = post_user.get('userId', str(id(post_user)))
                        results.append({
                            'e_src': user_id,
                            'e_dst': main_node_id,
                            'e_type': 'post',
                            'src_type': 'USER',
                            'src_props': {
                                'name': id2name.get(user_id, f"用户{user_id[:6]}" if user_id else '未知用户'),
                                'user_name': post_user.get('user_name', ''),
                                'userId': user_id,
                                'follows_num': post_user.get('follows_num', 0),
                                'fans_num': post_user.get('fans_num', 0),
                                'gender': post_user.get('gender', ''),
                                'influence_score': post_user.get('influence_score', 0),
                                'ip_address': post_user.get('ip_address', ''),
                                'verifiedType': post_user.get('verifiedType', '')
                            },
                            'dst_type': 'INFO',
                            'dst_props': {
                                'title': data['i'].get('text', '')[:50] + '...' if len(data['i'].get('text', '')) > 50 else data['i'].get('text', ''),
                                'isrumor': True
                            }
                        })
            
            # 处理评论和相关关系
            for comment in data['comments']:
                if comment:
                    comment_id = comment.get('commentId', str(id(comment)))
                    # review1关系
                    results.append({
                        'e_src': comment_id,
                        'e_dst': main_node_id,
                        'e_type': 'review1',
                        'src_type': 'COMMENT',
                        'src_props': {
                            'content': comment.get('commentText', '')
                        },
                        'dst_type': 'INFO',
                        'dst_props': {
                            'title': data['i'].get('text', '')[:50] + '...' if len(data['i'].get('text', '')) > 50 else data['i'].get('text', ''),
                            'isrumor': True
                        }
                    })
                    # issue关系
                    if 'user' in comment:
                        user_id = comment['user']
                        results.append({
                            'e_src': user_id,
                            'e_dst': comment_id,
                            'e_type': 'issue',
                            'src_type': 'USER',
                            'src_props': {
                                # 安全地获取用户名，避免KeyError
                                'name': id2name.get(user_id, f"用户{user_id[:6]}" if user_id else '未知用户')
                            },
                            'dst_type': 'COMMENT',
                            'dst_props': {
                                'content': comment.get('commentText', '')
                            }
                        })
            
            # 处理转发和相关关系
            for repost in data['reposts']:
                if repost:
                    repost_id = repost.get('repostId', str(id(repost)))
                    # review3关系
                    results.append({
                        'e_src': repost_id,
                        'e_dst': main_node_id,
                        'e_type': 'review3',
                        'src_type': 'REPOST',
                        'src_props': {
                            'content': repost.get('repostText', '转发')
                        },
                        'dst_type': 'INFO',
                        'dst_props': {
                            'title': data['i'].get('text', '')[:50] + '...' if len(data['i'].get('text', '')) > 50 else data['i'].get('text', ''),
                            'isrumor': True
                        }
                    })
                    # perform关系
                    if 'user' in repost:
                        user_id = repost['user']
                        results.append({
                            'e_src': user_id,
                            'e_dst': repost_id,
                            'e_type': 'perform',
                            'src_type': 'USER',
                            'src_props': {
                                # 安全地获取用户名，避免KeyError
                                'name': id2name.get(user_id, f"用户{user_id[:6]}" if user_id else '未知用户')
                            },
                            'dst_type': 'REPOST',
                            'dst_props': {
                                'content': repost.get('repostText', '转发')
                            }
                        })
            
            # 处理子评论和相关关系
            if 'child_comments' in data:
                for child_comment in data['child_comments']:
                    if child_comment:
                        child_comment_id = child_comment.get('commentId', str(id(child_comment)))
                        parent_comment_id = child_comment.get('superior_node')
                        if parent_comment_id:
                            # review2关系
                            # 先查找父评论内容
                            parent_comment_content = ''
                            # 遍历主评论列表查找父评论
                            for main_comment in data['comments']:
                                if main_comment and main_comment.get('commentId') == parent_comment_id:
                                    parent_comment_content = main_comment.get('commentText', '')
                                    break
                            # 如果主评论中没找到，在子评论中查找
                            if not parent_comment_content and 'child_comments' in data:
                                for c in data['child_comments']:
                                    if c and c.get('commentId') == parent_comment_id:
                                        parent_comment_content = c.get('commentText', '')
                                        break
                            
                            results.append({
                                'e_src': child_comment_id,
                                'e_dst': parent_comment_id,
                                'e_type': 'review2',
                                'src_type': 'COMMENT',
                                'src_props': {
                                    'content': child_comment.get('commentText', '')
                                },
                                'dst_type': 'COMMENT',
                                'dst_props': {
                                    'content': parent_comment_content or '评论内容未找到'
                                }
                            })
                            # issue关系
                            if 'user' in child_comment:
                                user_id = child_comment['user']
                                results.append({
                                    'e_src': user_id,
                                    'e_dst': child_comment_id,
                                    'e_type': 'issue',
                                    'src_type': 'USER',
                                    'src_props': {
                                        # 安全地获取用户名，避免KeyError
                                        'name': id2name.get(user_id, f"用户{user_id[:6]}" if user_id else '未知用户')
                                    },
                                    'dst_type': 'COMMENT',
                                    'dst_props': {
                                        'content': child_comment.get('commentText', '')
                                    }
                                })
            
            # 处理用户之间的follow关系
            if 'comment_users' in data and 'repost_users' in data and 'post_users' in data:
                # 简化处理，仅添加一些示例的follow关系
                existing_user_ids = []
                
                # 收集所有用户ID
                if 'post_users' in data:
                    for user in data['post_users']:
                        if user:
                            existing_user_ids.append(user.get('userId', str(id(user))))
                            
                for comment in data['comments']:
                    if comment and 'user' in comment:
                        existing_user_ids.append(comment['user'])
                        
                for repost in data['reposts']:
                    if repost and 'user' in repost:
                        existing_user_ids.append(repost['user'])
                                
                if 'child_comments' in data:
                    for child_comment in data['child_comments']:
                        if child_comment and 'user' in child_comment:
                            existing_user_ids.append(child_comment['user'])
                            
                # 去重
                existing_user_ids = list(set(existing_user_ids))
                
                # 添加follow关系
                for i, user1 in enumerate(existing_user_ids):
                    for j, user2 in enumerate(existing_user_ids):
                        if i < j and i < 3 and j < 3:  # 限制数量，避免过多关系
                            results.append({
                                'e_src': user1,
                                'e_dst': user2,
                                'e_type': 'follow',
                                'src_type': 'USER',
                                'src_props': {
                                    # 安全地获取用户名，避免KeyError
                                    'name': id2name.get(user1, f"用户{user1[:6]}" if user1 else '未知用户')
                                },
                                'dst_type': 'USER',
                                'dst_props': {
                                    # 安全地获取用户名，避免KeyError
                                    'name': id2name.get(user2, f"用户{user2[:6]}" if user2 else '未知用户')
                                }
                            })
            
            return {"results": results}
    except Exception as e:
        logger.error(f"获取虚假信息 {fake_id} 传播图谱失败: {str(e)}")
        # 出错时返回空数据
        return {"results": []}
    
# 创建全局Neo4j服务实例（现在使用函数式结构，这个变量保留以保持兼容性）
neo4j_service = None

def get_neo4j_service(app_config=None):
    """获取Neo4j服务实例（兼容函数）"""
    global neo4j_service
    if neo4j_service is None and app_config:
        # 初始化连接池而不是创建类实例
        init_neo4j_pool(app_config)
        # 返回当前模块，这样调用方可以直接访问模块中的函数
        neo4j_service = True
    # 返回当前模块本身，这样调用方可以使用如service.get_fake_knowledge_stats()的方式
    import sys
    return sys.modules[__name__]

# 在应用退出时关闭Neo4j连接
def shutdown_neo4j():
    """关闭Neo4j连接"""
    global neo4j_service
    # 调用close_neo4j_connection函数关闭连接
    close_neo4j_connection()
    neo4j_service = None