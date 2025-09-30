from flask import Flask,request,jsonify
import os
import json
from flask_cors import CORS
from uts import get_available_gpu
import torch.nn.functional as F
import re

from main import process_text
# """ 自动找一张能用的gpu """
# gpu_ids = get_available_gpu()
# os.environ['CUDA_VISIBLE_DEVICES'] = str(gpu_ids)

app = Flask(__name__)

# 配置JSON输出，确保中文正常显示
app.config['JSON_AS_ASCII'] = False

# 自定义JSON编码器
class CustomJSONEncoder(json.JSONEncoder):
    def __init__(self, *args, **kwargs):
        kwargs['ensure_ascii'] = False
        super(CustomJSONEncoder, self).__init__(*args, **kwargs)

app.json_encoder = CustomJSONEncoder

# 添加CORS支持
CORS(app)

@app.route('/api/entity/detect', methods=['POST'])
def entity_detect():
    """实体识别API - 支持本地文本和前端上传"""
    try:
        data = request.json
        text = data.get('text', '')
        
        # 清理文本：去除所有空格
        text = text.strip()  # 去除首尾空格
        # 去除所有空格（包括普通空格、制表符、换行符等）
        text = re.sub(r'\s+', '', text)
        
        # 添加调试信息
        print(f"收到前端文本: '{text}'")
        print(f"文本长度: {len(text)}")
        print(f"文本字符: {list(text)}")

        if not text or text.strip() == '':
            return jsonify({
                'success': False,
                'message': '文本内容不能为空',
                'data': None
            }), 400

        # 检查文本长度（限制为2000字符）
        if len(text) > 2000:
            return jsonify({
                'success': False,
                'message': '文本长度不能超过2000字符',
                'data': None
            }), 400

        # 调用模型预测逻辑
        return_dict = make_NER_detect(text)
        result, code, failed = return_dict["result"], return_dict['code'], return_dict['failed']

        if code > 0:  # 成功
            # 格式化返回结果
            formatted_result = {
                'type': '实体识别',
                'entities': format_entities(result['results']),
                'total_count': len(result['results']),
                'text_length': len(text)
            }

            return jsonify({
                'success': True,
                'message': '识别完成',
                'data': formatted_result
            })
        else:  # 失败
            return jsonify({
                'success': False,
                'message': failed or '识别失败',
                'data': None
            }), 500

    except Exception as e:
        app.logger.error(f'API错误: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}',
            'data': None
        }), 500

def format_entities(entities):
    """格式化实体识别结果"""
    formatted = []
    for entity in entities:
        if len(entity) >= 2 and entity[0] != -1:
            formatted.append({
                'text': entity[1],
                'type': entity[0],
                'type_name': get_entity_type_name(entity[0])
            })
    return formatted

def get_entity_type_name(entity_type):
    """获取实体类型的中文名称"""
    type_mapping = {
        # 人名相关
        'PER': '人名',
        'PER.NAM': '人名',
        'PER.NOM': '人名',
        'PERSON': '人名',
        
        # 地名相关
        'LOC': '地名',
        'LOC.NAM': '地名',
        'LOC.NOM': '地名',
        'GPE': '地名',
        'GPE.NAM': '地名',
        'GPE.NOM': '地名',
        'LOCATION': '地名',
        
        # 机构相关
        'ORG': '机构',
        'ORG.NAM': '机构',
        'ORG.NOM': '机构',
        'ORGANIZATION': '机构',
        
        # 其他
        'MISC': '其他',
        'MISC.NAM': '其他',
        'MISC.NOM': '其他',
        'TIME': '时间',
        'NUM': '数字',
        'DATE': '日期',
        'MONEY': '金额',
        'PERCENT': '百分比'
    }
    return type_mapping.get(entity_type, entity_type)

@app.route('/ner',methods=['POST'])
def NER():
    """调用JSON，解析请求数据"""
    data = request.json
    task_id = data.get('task_id', 0) # 任务id，即用例编号，用于区别不同模型
    url = data.get('url', '') # 本地路径，指向测试集文件夹。如果为图像、视频、音频等文件则为必选
    data_id = data.get('data_id', 0) # 数据id，数据唯一标识
    data_type = data.get('type', '') # 数据格式 MP4 png ...
    text = data.get('text', 'text') # 待检测的文本数据，如果检测文本则为必选

    """ 调用模型预测逻辑，返回模型的实际预测结果\code\failed """
    return_dict = make_NER_detect(text)
    result, code, failed = return_dict["result"], return_dict['code'],return_dict['failed']

    """ 设置响应报文格式 """
    response = {
        'task_id': task_id,
        'data_id': data_id,
        'content': result, # 算法运行结果，根据不同算法进行适配调整
        'status': {
            # code值大于0，表示正常；failed，填写错误信息
            "code": code,
            "failed": failed,
        }
    }
    # logging.info("测试输出：%s", json.dumps(response))
    return response

def make_NER_detect(text):
    try:
        pred_labels,scores = process_text(text)
        entity = get_entity(pred_labels,text)
        result = {
                "labels":pred_labels,
                "scores":scores,
                'results':entity
            }
        return {'result': result, 'code': 1, 'failed': ''} # 成功执行
    except Exception as e:
        return {'result': '', 'code': 0, 'failed': str(e)}


def get_entity(pred_labels, source_text):
    chunks = []
    chunk = [-1, -1, -1]
    length = len(pred_labels)
    
    print(f"原始标签: {pred_labels}")
    print(f"文本字符: {list(source_text)}")
    
    # 跳过特殊token，只处理实际字符的标签
    start_idx = 1  # 跳过[CLS]
    end_idx = length - 1  # 跳过[SEP]
    
    for idx in range(start_idx, end_idx):
        if idx >= len(pred_labels):
            break
        value = pred_labels[idx]
        char_idx = idx - 1  # 字符索引
        
        print(f"处理 idx={idx}, char_idx={char_idx}, char='{source_text[char_idx] if char_idx < len(source_text) else 'N/A'}', label='{value}'")
        
        if value.startswith('B-'):
            if chunk[0] != -1:
                chunks.append(chunk)
            category = value.split('-')[-1]
            chunk = [category, char_idx, char_idx]

            if idx == end_idx - 1:
                chunks.append(chunk)
        elif value.startswith('I-'):
            category = value.split('-')[-1]
            pre_category = chunk[0]
            if category == pre_category:
                chunk[-1] = char_idx
            else:
                if chunk[0] != -1:
                    chunks.append(chunk)
                chunk = [category, char_idx, char_idx]
            if idx == end_idx - 1:
                chunks.append(chunk)
        else:
            if chunk[0] != -1:
                chunks.append(chunk)
                chunk = [-1, -1, -1]
    
    print(f"合并前chunks: {chunks}")
    
    # 后处理：合并相邻的同类型实体
    merged_chunks = []
    if chunks:
        current_chunk = chunks[0]
        
        for i in range(1, len(chunks)):
            next_chunk = chunks[i]
            
            # 如果两个chunk类型相同且位置相邻（中间只隔1-2个字符），则合并
            if (current_chunk[0] == next_chunk[0] and 
                next_chunk[1] - current_chunk[2] <= 3):  # 允许中间隔1-2个字符
                print(f"合并: {current_chunk} + {next_chunk}")
                current_chunk[2] = next_chunk[2]
            else:
                merged_chunks.append(current_chunk)
                current_chunk = next_chunk
        
        merged_chunks.append(current_chunk)
    else:
        merged_chunks = chunks
    
    print(f"合并后chunks: {merged_chunks}")
    
    # 生成实体列表，确保索引不超出文本范围
    entity = []
    for c in merged_chunks:
        if c[0] != -1 and c[1] >= 0 and c[2] < len(source_text):
            entity_text = source_text[c[1]:c[2]+1]
            print(f"实体: {c} -> '{entity_text}'")
            entity.append([c[0], entity_text])
    
    return entity

if __name__ == '__main__':
    app.json.ensure_ascii = False
    app.run(debug=True,host='0.0.0.0',port=5016)
    
    
    
    
    