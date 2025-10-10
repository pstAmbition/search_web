# /unified_service/routes.py

import os
import time
import calendar
import json
from flask import Blueprint, request, jsonify, current_app, make_response, Response
from werkzeug.utils import secure_filename
from datetime import datetime
from services import nebula_service, search_service, mongodb_service,neo4j_service
#from services import neo4j_service
import utils
from datetime import datetime
import random
# 创建一个Blueprint
api = Blueprint('api', __name__)

# --- NebulaGraph API Routes ---

@api.route('/executeCustomQuery', methods=['POST'])
def execute_custom_query():
    query = request.json.get('query')
    if not query:
        return jsonify({"error": "缺少必要参数: query"}), 400

    space_name = current_app.config['NEBULA_SPACE']
    result = nebula_service.execute_query(query, space_name=space_name)
    
    if isinstance(result, dict) and "error" in result:
        return jsonify(result), 500
    
    return jsonify(result)

@api.route('/getRelatedByEvent', methods=['GET'])
def get_related_by_event():
    event = request.args.get('event')
    if not event:
        return jsonify({"error": "请提供事件名称"}), 400

    current_app.logger.info(f"查询事件: {event}")
    space_name = current_app.config['NEBULA_SPACE']
    result = nebula_service.get_graph_data_by_event(event, space_name)

    if isinstance(result, dict) and "error" in result:
        return jsonify(result), 500

    return jsonify({
        "event": event,
        "results": result,
        "count": len(result) if isinstance(result, list) else 0
    })
    
@api.route('/getRelatedById', methods=['GET'])
def get_related_by_id():
    id = request.args.get('id')
    if not id:
        return jsonify({"error": "请提供微博推文ID"}), 400

    current_app.logger.info(f"查询微博推文ID: {id}")
    space_name = current_app.config['NEBULA_SPACE']
    result = nebula_service.get_graph_data_by_id(id, space_name)

    if isinstance(result, dict) and "error" in result:
        return jsonify(result), 500

    return jsonify({
        "id": id,
        "results": result,
        "count": len(result) if isinstance(result, list) else 0
    })
    
@api.route('/getOriginalTweetById', methods=['GET'])
def get_Original_Tweet_by_id():
    id = request.args.get('id')
    if not id:
        return jsonify({"error": "请提供微博推文ID"}), 400

    current_app.logger.info(f"查询微博推文ID: {id}")
    space_name = current_app.config['NEBULA_SPACE']
    result = nebula_service.get_Original_Tweet_by_id(id, space_name)

    if isinstance(result, dict) and "error" in result:
        return jsonify(result), 500

    return jsonify({
        "id": id,
        "results": result,
        "count": len(result) if isinstance(result, list) else 0
    })

@api.route('/getStartNodeInfo', methods=['GET'])
def get_start_node_info_route():
    node_id = request.args.get('node_id')
    if not node_id:
        return jsonify({"error": "请提供节点ID"}), 400

    current_app.logger.info(f"查询节点ID: {node_id}")
    space_name = current_app.config['NEBULA_SPACE']
    result = nebula_service.get_start_node_info(node_id, space_name)

    if isinstance(result, dict) and "error" in result:
        return jsonify(result), 500

    return jsonify({
        "node_id": node_id,
        "results": result
    })

# --- Search API Routes ---
# 测试:curl -X POST "http://127.0.0.1:5001/api/search/text"   -H "Content-Type: application/x-www-form-urlencoded"   -d "queryContent=BGM一响，浓浓的归意再也掩饰不住了，2025年的春运已经开始了，希望每一个人都能快快乐 乐，平平安安的到家和家人团聚。&score=0.5"
# 5192635628653361
#武大男生被诬告性骚扰#现在看，武汉大学给的处分，草率了。所以说，高校处置舆情，一定要在事实的基础上，坚守原则，不要被“舆论”裹挟，而后退，更不要和稀泥。在这方面，武大应该向大连工业大学学习。

@api.route('/search/text', methods=['POST'])
def search_text_route():
    query_content = request.form.get('queryContent','减重版司美格鲁正式在中国上市')
    score = 0.3

    if not query_content:
        return jsonify({"error": "缺少 'queryContent' 参数"}), 400
    
    # try:
    #     score = float(score_str)
    # except ValueError:
    #     return jsonify({"error": "'score' 参数必须是浮点数"}), 400

    start_time = time.time()
    results = search_service.search_text(query_content, score, current_app.config)
    print(results)
    duration = time.time() - start_time
    current_app.logger.info(f"文本 '{query_content}' 搜索耗时: {duration:.2f}s")
    
    if isinstance(results, dict) and "error" in results:
        return jsonify(results), 500

    return jsonify({"search_results": results})


def _handle_file_upload(file_key, allowed_checker):
    """处理文件上传的通用逻辑"""
    if file_key not in request.files:
        return None, jsonify({"error": f"请求中缺少 '{file_key}'"}), 400

    file = request.files[file_key]
    # print(file.filename)
    if file.filename == '':
        return None, jsonify({"error": "未选择文件"}), 400
    # print(allowed_checker)
    if file and allowed_checker(file.filename):
        filename = secure_filename(file.filename)
        upload_folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        current_app.logger.info(f"文件已保存至: {filepath}")
        return filepath, None, None
    else:
        return None, jsonify({"error": "文件类型不允许"}), 400

# 测试:curl -X POST "http://127.0.0.1:5000/api/search/picture" -F "file=@/data/storage/8888/xyt/work/milvus_dataset/Image/250116/watermark_image/Fake_raw_00_00_00_1.jpg"
@api.route('/search/picture', methods=['POST'])
def search_picture_route():
    filepath, error_response, status_code = _handle_file_upload('file', utils.is_picture_file_allowed)
    if error_response:
        return error_response, status_code
        
    # try:
    #     top_k = int(top_k_str)
    # except ValueError:
    #     return jsonify({"error": "'topk' 参数必须是整数"}), 400

    results_path,results_mid = search_service.search_picture(filepath, current_app.config)
    
    if isinstance(results_path, dict) and "error" in results_path:
        return jsonify(results_path), 500
    
    # 将找到的图片路径转换为base64返回
    image_base64_list = []
    # results_path 的结构是 [[path1, path2], ...]
    if results_path and isinstance(results_path[0], list):
        for image_path in results_path[0]: 
            # 注意：这里的路径应该是可访问的绝对路径或相对路径
            # 假设 search_service 返回的路径是需要拼接的
            # full_image_path = os.path.join("/path/to/image/dataset", image_path) 
            # 此处暂时假设返回的是可以直接访问的完整路径
            image_base64 = utils.to_base64(image_path)
            if image_base64:
                image_type = "image/" + image_path.split('.')[-1]
                data_url = f"data:{image_type};base64,{image_base64}"
                image_base64_list.append(data_url)
        
    results_event = []
    if results_mid and isinstance(results_mid[0], list):
        for mid in results_mid[0]: 
            #去es找事件
            event = search_service.search_event_by_mid(mid, current_app.config)
            results_event.append(event)
    # print(results_event)

    # return jsonify({"message": "图片上传成功", "image_base64_list": image_base64_list, "search_results": results_event})
    # 展平列表
    results_event = [item for sublist in results_event for item in sublist]
    return jsonify({"search_results": results_event})

# 测试:curl -X POST "http://127.0.0.1:5001/api/search/video" -F "file=@/data/storage/8888/xyt/work/milvus_dataset/video/raw_video/douyin_raw_1.mp4" -F "topk=5"
@api.route('/search/video', methods=['POST'])
def search_video_route():
    filepath, error_response, status_code = _handle_file_upload('file', utils.is_video_file_allowed)
    if error_response:
        return error_response, status_code
        
    score = 1
    print(score)
    # try:
    #     top_k = int(top_k_str)
    # except ValueError:
    #     return jsonify({"error": "'topk' 参数必须是整数"}), 400
        
    results = search_service.search_video(filepath, score, current_app.config)

    if isinstance(results, dict) and "error" in results:
        return jsonify(results), 500

    video_base64_list = []
    if results and isinstance(results, list):
        for video_path in results:
             # 假设 search_service 返回的路径是可以直接访问的完整路径
            print(video_path)
            video_base64 = utils.to_base64(video_path)
            if video_base64:
                video_type = "video/mp4"
                data_url = f"data:{video_type};base64,{video_base64}"
                video_base64_list.append(data_url)

    return jsonify({"message": "视频上传成功", "video_base64_list": video_base64_list})

# --- General File Upload API ---
@api.route('/upload', methods=['POST'])
def upload_file():
    """
    通用文件上传接口，用于前端上传图片或视频
    返回文件的访问 URL
    """
    # 支持图片和视频
    def allow_uploaded_file(filename):
        return (utils.is_picture_file_allowed(filename) or 
                utils.is_video_file_allowed(filename))

    filepath, error_response, status_code = _handle_file_upload('file', allow_uploaded_file)
    if error_response:
        return error_response, status_code

    filename = os.path.basename(filepath)
    file_url = f"/uploads/{filename}"  # 前端可通过此 URL 访问文件

    return jsonify({
        "message": "上传成功",
        "filename": filename,
        "url": file_url
    }), 200

# 北理工 风险事件库
# 添加新的API路由来支持更多MongoDB功能
@api.route('/getAllEvents', methods=['GET'])
def get_all_events():
    """获取所有事件，支持分页、排序和按平台、region、Time和关键字过滤"""
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))  # 增加默认限制
        sort_by = request.args.get('sort_by', 'Time')
        sort_order = int(request.args.get('sort_order', -1))
        platform = request.args.get('platform', '')
        region = request.args.get('region', '')
        start_time = request.args.get('start_time', '')
        end_time = request.args.get('end_time', '')
        keyword = request.args.get('keyword', '')
    except ValueError:
        return jsonify({"error": "分页和排序参数格式错误"}), 400
    
    # 构建查询参数
    params = {
        'platform': platform,
        'region': region,
        'start_time': start_time,
        'end_time': end_time,
        'keyword': keyword
    }
    
    # 调用mongodb_service中的函数获取查询条件
    query = mongodb_service.get_all_events_query(params)
    
    events, total = mongodb_service.search_events(query, page=page, page_size=page_size, sort_by=sort_by, sort_order=sort_order)
    
    if isinstance(events, dict) and "error" in events:
        return jsonify(events), 500
    
    return jsonify({
        "results": events,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": (total + page_size - 1) // page_size
    })

@api.route('/getRiskEvents', methods=['GET'])
def get_risk_events():
    """获取所有isRisk=true的风险事件，支持分页、排序和按平台、region、Time和关键字过滤"""
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))  # 增加默认限制
        sort_by = request.args.get('sort_by', 'Time')
        sort_order = int(request.args.get('sort_order', -1))
        platform = request.args.get('platform', '')
        region = request.args.get('region', '')
        start_time = request.args.get('start_time', '')
        end_time = request.args.get('end_time', '')
        keyword = request.args.get('keyword', '')
    except ValueError:
        return jsonify({"error": "分页和排序参数格式错误"}), 400
    
    # 构建查询参数
    params = {
        'platform': platform,
        'region': region,
        'start_time': start_time,
        'end_time': end_time,
        'keyword': keyword
    }
    
    # 调用mongodb_service中的函数获取查询条件
    query = mongodb_service.get_risk_events_query(params)
    
    events, total = mongodb_service.search_events(query, page=page, page_size=page_size, sort_by=sort_by, sort_order=sort_order)
    
    if isinstance(events, dict) and "error" in events:
        return jsonify(events), 500
    
    return jsonify({
        "results": events,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": (total + page_size - 1) // page_size
    })

@api.route('/getDatabaseStats', methods=['GET'])
def get_database_stats():
    """获取数据库统计信息"""
    
    stats = mongodb_service.get_statistics()
    
    if isinstance(stats, dict) and "error" in stats:
        return jsonify(stats), 500
    
    return jsonify(stats)

@api.route('/exportEvents', methods=['GET'])
def export_events():
    """导出事件数据，支持按条件筛选"""
    try:
        # 获取查询参数
        keyword = request.args.get('keyword', '')
        region = request.args.get('region', '')
        start_time = request.args.get('start_time', '')
        end_time = request.args.get('end_time', '')
        is_risk = request.args.get('is_risk', '')
        platform = request.args.get('platform', '')
        export_format = request.args.get('format', 'json')  # 导出格式：json 
        
        current_app.logger.info(f"接收到导出请求: keyword={keyword}, region={region}, start_time={start_time}, end_time={end_time}, is_risk={is_risk}, platform={platform}, format={export_format}")
        
        # 构建查询条件
        query = {}
        conditions = []
        
        if keyword:
            conditions.append({"Event": {"$regex": keyword, "$options": "i"}})
        
        if region:
            conditions.append({"region": region})
        
        # 处理时间范围查询，支持按年月筛选 (格式：YYYY-MM)
        if start_time:
            if len(start_time) == 7 and start_time[4] == '-':  # 检查是否是年月格式 (YYYY-MM)
                # 年月格式，设置为当月第一天
                conditions.append({"Time": {"$gte": f"{start_time}-01 00:00"}})
            else:
                conditions.append({"Time": {"$gte": start_time}})
        
        if end_time:
            if len(end_time) == 7 and end_time[4] == '-':  # 检查是否是年月格式 (YYYY-MM)
                # 年月格式，设置为当月最后一天
                year, month = map(int, end_time.split('-'))
                last_day = calendar.monthrange(year, month)[1]
                conditions.append({"Time": {"$lte": f"{year}-{month:02d}-{last_day} 23:59"}})
            else:
                conditions.append({"Time": {"$lte": end_time}})
        
        if is_risk:
            conditions.append({"isRisk": is_risk})
        
        if platform:
            conditions.append({"platform": platform})
        
        # 组合查询条件
        if len(conditions) > 0:
            if len(conditions) > 1:
                query = {"$and": conditions}
            else:
                query = conditions[0]
        
        current_app.logger.info(f"构建的查询条件: {query}")
        
        # 尝试使用流式处理进行导出
        try:
            # 使用流式模式，获取游标而不是一次性加载所有数据
            cursor, _ = mongodb_service.search_events(query, page=1, page_size=100000, is_export=True, streaming=True)
            
            # 如果使用了流式处理，返回生成器响应
            def generate():
                count = 0
                for event in cursor:
                    # 转换ObjectId为字符串
                    event = mongodb_service._convert_objectid_to_string(event)
                    count += 1
                    # 生成JSON行
                    yield json.dumps(event, ensure_ascii=False) + '\n'
                # 添加总数信息到最后一行（可选）
                # yield json.dumps({"total_records": count}, ensure_ascii=False) + '\n'
            
            # 创建流式响应
            response = Response(generate(), content_type='application/jsonl')
            response.headers['Content-Disposition'] = 'attachment; filename="events_export.jsonl"'
            return response
        except Exception as e:
            current_app.logger.warning(f"流式导出失败，回退到常规导出: {str(e)}")
            # 回退到常规导出方式
            events, total = mongodb_service.search_events(query, page=1, page_size=100000, is_export=True)
            
            if isinstance(events, dict) and "error" in events:
                return jsonify(events), 500
            
            # 根据导出格式返回不同的响应
            if export_format.lower() == 'jsonl' or export_format.lower() == 'json':
                # 生成JSONL格式的响应
                jsonl_content = ''
                for event in events:
                    # 确保event是可JSON序列化的
                    if isinstance(event, dict):
                        jsonl_content += json.dumps(event, ensure_ascii=False) + '\n'
                    else:
                        # 如果event不是dict，尝试转换
                        try:
                            jsonl_content += json.dumps(dict(event), ensure_ascii=False) + '\n'
                        except:
                            # 忽略无法序列化的条目
                            continue
                
                # 创建响应对象，设置适当的头部
                response = make_response(jsonl_content)
                response.headers['Content-Type'] = 'application/jsonl'
                response.headers['Content-Disposition'] = 'attachment; filename="events_export.jsonl"'
                response.headers['X-Total-Records'] = str(total)
                return response
            else:
                # 默认返回JSON格式
                return jsonify({
                    "results": events,
                    "total": total,
                    "export_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
        
    except Exception as e:
        current_app.logger.error(f"Export events error: {str(e)}")
        return jsonify({"error": str(e)}), 500    

@api.route('/getDashboardMetrics', methods=['GET'])
def get_dashboard_metrics():
    """
    获取仪表盘指标数据
    """
    try:
        # 调用mongodb_service中的函数获取仪表盘指标
        metrics = mongodb_service.get_dashboard_metrics()
        
        if isinstance(metrics, dict) and "error" in metrics:
            # 如果MongoDB连接失败，返回错误信息
            current_app.logger.error(f"获取仪表盘指标失败: {metrics['error']}")
            return jsonify(metrics), 500
        
        return jsonify(metrics)
        
    except Exception as e:
        current_app.logger.error(f"获取仪表盘指标错误: {str(e)}")
        # 发生异常时返回错误信息
        return jsonify({"error": str(e)}), 500

# --- Fake Knowledge Base API Routes ---
# 目标ID列表常量
TARGET_INFO_IDS = [
    "5192635628653361", "4886584313704035", "4912258166066719",
    "4815950411571499", "4915713952610498", "4740853557094429",
    "4979050738470336", "4923310393691170", "4802345311345219",
    "4801783500287421"
]

# 生成模拟数据函数
def generate_mock_fake_news():
    """生成模拟的虚假信息数据"""
    # 根据TARGET_INFO_IDS生成模拟数据
    mock_data = []
    for fake_id in TARGET_INFO_IDS:
        mock_data.append({
            "id": fake_id,
            "title": f"模拟虚假信息标题_{fake_id[-4:]}",
            "source": "模拟数据",
            "publish_date": "2023-07-15",
            "tags": ["虚假", "谣言", "误导"],
            "summary": "这是一条模拟的虚假信息数据，用于测试目的。",
            "truth": "真实情况与传播内容不符，请注意辨别。",
            "url": f"https://example.com/fake/{fake_id}"
        })
    return mock_data

def generate_mock_fake_news():
    """生成模拟的虚假新闻数据"""
    mock_topics = ["政治", "经济", "社会", "健康", "科技", "教育"]
    mock_info_classes = ["虚假报道", "误导信息", "谣言", "虚假声明", "篡改事实"]
    mock_sources = ["微博", "微信", "论坛", "新闻网站", "短视频平台"]
    mock_users = ["user123", "news_fan", "info_sharer", "social_media_user", "rumor_spreader"]
    mock_modals = ["文本", "图片", "视频", "混合"]
    
    mock_news = []
    for i, info_id in enumerate(TARGET_INFO_IDS):
        mock_news.append({
            "id": str(1000000000000000 + i),
            "infoId": info_id,
            "text": f"这是一条模拟的虚假信息 #{i+1}，包含误导性内容和不实陈述。这条信息在社交媒体上广泛传播，造成了不良影响。",
            "title": f"模拟虚假信息标题 #{i+1}",
            "date": f"2024-{random.randint(1, 12)}-{random.randint(1, 28)}",
            "reposts_num": random.randint(100, 10000),
            "comments_num": random.randint(50, 5000),
            "likes_num": random.randint(200, 20000),
            "element_topic": random.choice(mock_topics),
            "info_class": random.choice(mock_info_classes),
            "source": random.choice(mock_sources),
            "user": random.choice(mock_users),
            "modal": random.choice(mock_modals),
            "picture_url": [],
            "video_url": []
        })
    
    return mock_news
@api.route('/fake-knowledge/detail/<fake_id>', methods=['GET'])
def get_fake_info_detail_api(fake_id):
    """
    获取虚假信息详情
    """
    if not fake_id:
        return jsonify({
            "success": False,
            "error": "请提供虚假信息ID"
        }), 400
    
    if not neo4j_service:
        return jsonify({
            "success": False,
            "error": "Neo4j服务未可用"
        }), 503
    
    try:
        service = neo4j_service.get_neo4j_service(current_app.config)
        if service is None:
            return jsonify({
                "success": False,
                "message": "Neo4j服务初始化失败"
            })
            
        detail = service.get_fake_info_detail(fake_id)
        
        current_app.logger.info(f"获取虚假信息 {fake_id} 的详情成功")
        return jsonify({
            "success": True,
            "data": detail
        })
    except Exception as e:
        current_app.logger.error(f"获取虚假信息 {fake_id} 的详情失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@api.route('/fake-knowledge/all', methods=['GET'])
def get_all_fake_knowledge_handler():
    """处理获取所有虚假信息的请求"""
    if not neo4j_service:
        return jsonify({
            "success": False,
            "error": "Neo4j服务未可用",
            "data": generate_mock_fake_news()
        })
    
    try:
        service = neo4j_service.get_neo4j_service(current_app.config)
        if service is None:
            return jsonify({
                "success": False,
                "error": "Neo4j服务初始化失败",
                "data": generate_mock_fake_news()
            })
            
        all_fake_info = service.get_all_fake_info()
        
        # 优先匹配目标ID的信息
        matched_info = []
        other_info = []
        
        for info in all_fake_info:
            # 检查infoId或id是否在目标列表中
            if (info.get('infoId') and info['infoId'] in TARGET_INFO_IDS) or \
               (info.get('id') and info['id'] in TARGET_INFO_IDS):
                matched_info.append(info)
            else:
                other_info.append(info)
        
        # 合并结果：先返回匹配的信息，再返回其他信息
        result_info = matched_info + other_info
        
        current_app.logger.info(f"成功获取所有虚假信息，共 {len(result_info)} 条")
        return jsonify({
            "success": True,
            "data": result_info
        })
    except Exception as e:
        current_app.logger.error(f"获取所有虚假信息失败: {str(e)}")
        # 返回模拟数据作为降级方案
        return jsonify({
            "success": False,
            "error": str(e),
            "data": generate_mock_fake_news()
        })

@api.route('/fake-knowledge/search', methods=['GET'])
def search_fake_knowledge_handler():
    """处理搜索虚假信息的请求"""
    keyword = request.args.get('keyword', '').strip()
    
    if not keyword:
        return jsonify({
            "success": True,
            "data": []
        })
    
    if not neo4j_service:
        return jsonify({
            "success": False,
            "error": "Neo4j服务未可用",
            "data": []
        })
    
    try:
        # 调用Neo4j服务进行搜索
        service = neo4j_service.get_neo4j_service()
        if service is None:
            return jsonify({
                "success": False,
                "error": "Neo4j服务初始化失败",
                "data": []
            })
            
        all_fake_info = service.get_all_fake_info()
        
        # 简单的关键词过滤
        search_results = []
        for info in all_fake_info:
            # 在多个字段中搜索关键词
            if (
                (info.get('text') and keyword.lower() in info['text'].lower()) or
                (info.get('title') and keyword.lower() in info['title'].lower()) or
                (info.get('element_topic') and keyword.lower() in info['element_topic'].lower()) or
                (info.get('info_class') and keyword.lower() in info['info_class'].lower())
            ):
                search_results.append(info)
        
        current_app.logger.info(f"搜索虚假信息成功，关键词: {keyword}，找到 {len(search_results)} 条结果")
        return jsonify({
            "success": True,
            "data": search_results
        })
    except Exception as e:
        current_app.logger.error(f"搜索虚假信息失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "data": []
        })

@api.route('/fake-knowledge/media/<fake_id>', methods=['GET'])
def get_fake_media_handler(fake_id):
    """处理获取虚假信息多媒体资源的请求"""
    import os
    
    # 初始化媒体资源对象
    media = {
        "pictures": [],
        "videos": []
    }
    
    try:
        # 定义本地媒体文件路径
        root_path = os.path.dirname(os.path.abspath(__file__))
        img_dir = os.path.join(root_path, 'fake', 'img')
        video_dir = os.path.join(root_path, 'fake', 'video')
        
        # 检查并添加本地图片文件
        if os.path.exists(img_dir):
            # 查找所有以fake_id开头或等于fake_id的图片文件
            for filename in os.listdir(img_dir):
                if filename.startswith(fake_id) or filename == fake_id:
                    # 构建相对URL路径
                    img_url = f"/uploads/{filename}"
                    media["pictures"].append(img_url)
                    current_app.logger.info(f"找到本地图片文件: {filename}")
        
        # 检查并添加本地视频文件
        if os.path.exists(video_dir):
            # 查找所有以fake_id开头或等于fake_id的视频文件
            for filename in os.listdir(video_dir):
                if filename.startswith(fake_id) or filename == fake_id:
                    # 构建相对URL路径
                    video_url = f"/uploads/{filename}"
                    media["videos"].append(video_url)
                    current_app.logger.info(f"找到本地视频文件: {filename}")
        
        # 如果本地没有找到，尝试从Neo4j获取
        if not media["pictures"] and not media["videos"]:
            if neo4j_service:
                try:
                    service = neo4j_service.get_neo4j_service()
                    if service:
                        detail = service.get_fake_info_detail(fake_id)
                        
                        if detail:
                            # 从Neo4j获取图片URL
                            if detail.get('picture_url'):
                                picture_url = detail['picture_url']
                                if isinstance(picture_url, list):
                                    media["pictures"] = [p for p in picture_url if p and p.strip() and p.lower() != '空']
                                elif isinstance(picture_url, str) and picture_url.lower() != '空' and picture_url.strip():
                                    if picture_url.startswith('['):
                                        try:
                                            parsed_list = json.loads(picture_url)
                                            if isinstance(parsed_list, list):
                                                media["pictures"] = [p for p in parsed_list if p and p.strip() and p.lower() != '空']
                                            else:
                                                media["pictures"] = [picture_url]
                                        except:
                                            media["pictures"] = [picture_url]
                                    else:
                                        media["pictures"] = [picture_url]
                            
                            # 从Neo4j获取视频URL
                            if detail.get('video_url'):
                                video_url = detail['video_url']
                                if isinstance(video_url, list):
                                    media["videos"] = [v for v in video_url if v and v.strip() and v.lower() != '空']
                                elif isinstance(video_url, str) and video_url.lower() != '空' and video_url.strip():
                                    if video_url.startswith('['):
                                        try:
                                            parsed_list = json.loads(video_url)
                                            if isinstance(parsed_list, list):
                                                media["videos"] = [v for v in parsed_list if v and v.strip() and v.lower() != '空']
                                            else:
                                                media["videos"] = [video_url]
                                        except:
                                            media["videos"] = [video_url]
                                    else:
                                        media["videos"] = [video_url]
                except Exception as e:
                    current_app.logger.warning(f"从Neo4j获取媒体资源失败: {str(e)}, fake_id: {fake_id}")
        
        # 确保文件路径的正确性
        # 检查uploads目录是否存在对应的文件
        uploads_dir = os.path.join(root_path, 'uploads')
        valid_pictures = []
        valid_videos = []
        
        # 确保uploads目录存在
        os.makedirs(uploads_dir, exist_ok=True)
        
        for img_url in media["pictures"]:
            filename = os.path.basename(img_url)
            if os.path.exists(os.path.join(uploads_dir, filename)):
                valid_pictures.append(img_url)
            else:
                # 尝试直接使用文件名
                if os.path.exists(os.path.join(img_dir, filename)):
                    # 如果文件在fake/img中但不在uploads中，复制过去
                    try:
                        import shutil
                        shutil.copy2(os.path.join(img_dir, filename), uploads_dir)
                        valid_pictures.append(img_url)
                        current_app.logger.info(f"已复制图片文件到uploads目录: {filename}")
                    except Exception as e:
                        current_app.logger.error(f"复制图片文件失败: {str(e)}")
        
        for video_url in media["videos"]:
            filename = os.path.basename(video_url)
            if os.path.exists(os.path.join(uploads_dir, filename)):
                valid_videos.append(video_url)
            else:
                # 尝试直接使用文件名
                if os.path.exists(os.path.join(video_dir, filename)):
                    # 如果文件在fake/video中但不在uploads中，复制过去
                    try:
                        import shutil
                        shutil.copy2(os.path.join(video_dir, filename), uploads_dir)
                        valid_videos.append(video_url)
                        current_app.logger.info(f"已复制视频文件到uploads目录: {filename}")
                    except Exception as e:
                        current_app.logger.error(f"复制视频文件失败: {str(e)}")
        
        media["pictures"] = valid_pictures
        media["videos"] = valid_videos
        
        current_app.logger.info(f"返回媒体资源: 图片{len(media['pictures'])}个, 视频{len(media['videos'])}个")
        
        return jsonify({
            "success": True,
            "data": media
        })
    except Exception as e:
        current_app.logger.error(f"获取虚假信息多媒体资源时发生错误: {str(e)}, fake_id: {fake_id}")
        return jsonify({
            "success": True,
            "data": {
                "pictures": [],
                "videos": []
            }
        })


@api.route('/test/neo4j/<fake_id>', methods=['GET'])
def test_neo4j_handler(fake_id):
    """处理测试Neo4j服务的请求"""
    if not neo4j_service:
        return jsonify({
            "success": False,
            "message": "Neo4j服务未可用"
        })
    
    try:
        service = neo4j_service.get_neo4j_service()
        detail = service.get_fake_info_detail(fake_id)
        
        if detail:
            return jsonify({
                "success": True,
                "message": "Neo4j服务正常",
                "data": detail
            })
        else:
            return jsonify({
                "success": False,
                "message": f"未找到ID为 {fake_id} 的虚假信息"
            })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Neo4j服务异常",
            "error": str(e)
        })

@api.route('/health', methods=['GET'])
def health_check_handler():
    """处理健康检查请求"""
    # 检查各个服务的状态
    services_status = {
        "neo4j": "unhealthy" if not neo4j_service else "unknown",
        "nebula": "unhealthy" if not nebula_service else "unknown",
        "search": "unhealthy" if not search_service else "unknown"
    }
    
    # 尝试获取Neo4j统计数据来验证服务状态
    if neo4j_service:
        try:
            service = neo4j_service.get_neo4j_service()
            if service is None:
                services_status["neo4j"] = "unhealthy"
            else:
                stats = service.get_fake_knowledge_stats()
                services_status["neo4j"] = "healthy" if stats else "unhealthy"
        except:
            services_status["neo4j"] = "unhealthy"
    
    # 判断整体状态
    overall_status = "healthy" if all(status == "healthy" for status in services_status.values()) else "degraded"
    
    return jsonify({
        'status': overall_status,
        'service': 'Unified Knowledge Service',
        'version': '1.0.0',
        'services': services_status
    })

@api.route('/fake-static/<filename>', methods=['GET'])
def serve_fake_static_handler(filename):
    """处理虚假信息库静态文件的访问"""
    static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'fake')
    # 确保目录存在
    os.makedirs(static_folder, exist_ok=True)
    from flask import send_from_directory
    return send_from_directory(static_folder, filename)

@api.route('/', methods=['GET'])
def index_handler():
    """处理根路由请求，提供系统基本信息"""
    return jsonify({
        "message": "虚假信息统一服务平台",
        "version": "1.0.0",
        "apis": [
            "/api/fake-knowledge/all - 获取所有虚假信息",
            "/api/fake-knowledge/search?keyword=关键词 - 搜索虚假信息",
            "/api/fake-knowledge/detail/<fake_id> - 获取虚假信息详情",
            "/api/fake-knowledge/stats - 获取虚假信息库统计数据",
            "/api/fake-knowledge/media/<fake_id> - 获取虚假信息多媒体资源",
            "/api/test/neo4j/<fake_id> - 测试Neo4j服务",
            "/api/executeCustomQuery - 执行自定义Nebula查询",
            "/api/getRelatedByEvent - 根据事件获取相关信息",
            "/api/getRelatedById - 根据ID获取相关信息",
            "/api/getOriginalTweetById - 根据ID获取原始推文",
            "/api/search/text - 文本搜索",
            "/api/search/picture - 图片搜索",
            "/api/search/video - 视频搜索",
            "/api/upload - 文件上传",
            "/health - 健康检查"
        ]
    })

@api.route('/fake-news/all', methods=['GET'])
def redirect_fake_news_handler():
    """处理旧API路径重定向"""
    return jsonify({
        "success": False,
        "error": "API路径已更新，请使用 /api/fake-knowledge/all",
        "redirect_to": "/api/fake-knowledge/all"
    }), 301

@api.route('/fake-news/search', methods=['GET'])
def redirect_fake_news_search_handler():
    """处理旧搜索API路径重定向"""
    keyword = request.args.get('keyword', '')
    return jsonify({
        "success": False,
        "error": "API路径已更新，请使用 /api/fake-knowledge/search",
        "redirect_to": f"/api/fake-knowledge/search?keyword={keyword}"
    }), 301

@api.route('/fake-knowledge/stats', methods=['GET'])
def get_fake_knowledge_stats_api():
    """
    获取虚假信息知识库统计数据（实体数、关系数等）
    """
    if not neo4j_service:
        return jsonify({
            "success": False,
            "error": "Neo4j服务未可用"
        }), 503
    
    try:
        # 传入current_app.config确保服务能够正确初始化
        service = neo4j_service.get_neo4j_service(current_app.config)
        if service is None:
            return jsonify({
                "success": False,
                "error": "Neo4j服务初始化失败"
            }), 503
            
        stats = service.get_fake_knowledge_stats()
        
        current_app.logger.info("获取虚假信息知识库统计数据成功")
        return jsonify({
            "success": True,
            "data": stats
        })
    except Exception as e:
        current_app.logger.error(f"获取虚假信息知识库统计数据失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": "服务暂时不可用"
        }), 500

@api.route('/fake-knowledge/graph/<fake_id>', methods=['GET'])
def get_fake_info_graph_api(fake_id):
    """
    获取虚假信息传播图谱数据
    """
    if not fake_id:
        return jsonify({
            "success": False,
            "error": "请提供虚假信息ID"
        }), 400
    
    if not neo4j_service:
        return jsonify({
            "success": False,
            "error": "Neo4j服务未可用"
        }), 503
    
    try:
        service = neo4j_service.get_neo4j_service(current_app.config)
        if service is None:
            return jsonify({
                "success": False,
                "error": "Neo4j服务初始化失败"
            }), 503
            
        graph_data = service.get_fake_info_graph(fake_id)
        
        current_app.logger.info(f"获取虚假信息 {fake_id} 的传播图谱成功")
        return jsonify({
            "success": True,
            "data": graph_data
        })
    except Exception as e:
        current_app.logger.error(f"获取虚假信息 {fake_id} 的传播图谱失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500