from flask import Flask, request, jsonify
import torch
import os
import json
import tempfile
import cv2
import numpy as np
from werkzeug.utils import secure_filename

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
from flask_cors import CORS
CORS(app)

from uts import get_available_gpu

""" 自动找一张能用的gpu """
gpu_ids = get_available_gpu()
os.environ['CUDA_VISIBLE_DEVICES'] = str(gpu_ids)

""" 导入测试用例flfx-003所用函数 """
from FaceForensics.classification.detect_from_video import video_classification_main_function # 对接API的函数
from FaceForensics.classification.detect_from_video import load_model #加载模型

""" 导入音频检测模块 """
from audio_detection import detect_fake_audio, extract_audio_embedding, get_audio_info

@app.route('/api/audiovideo/detect', methods=['POST'])
def audiovideo_detect():
    """音视频伪造检测API - 支持本地路径和文件上传"""
    try:
        # 检查请求类型
        if request.content_type and 'multipart/form-data' in request.content_type:
            # 方式1：处理上传的文件
            if 'file' not in request.files:
                return jsonify({
                    'success': False,
                    'message': '没有找到音视频文件',
                    'data': None
                }), 400

            file = request.files['file']
            if file.filename == '':
                return jsonify({
                    'success': False,
                    'message': '没有选择文件',
                    'data': None
                }), 400

            # 获取文件扩展名
            filename = secure_filename(file.filename)
            file_ext = os.path.splitext(filename)[1].lower().lstrip('.')

            # 保存临时文件
            with tempfile.NamedTemporaryFile(suffix=f'.{file_ext}', delete=False) as tmp_file:
                file.save(tmp_file.name)
                temp_path = tmp_file.name

            try:
                return_dict = process_media_file(temp_path, file_ext)
            finally:
                # 清理临时文件
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        else:
            # 方式2：处理本地路径
            data = request.json
            file_path = data.get('file_path', '')

            if not file_path or file_path.strip() == '':
                return jsonify({
                    'success': False,
                    'message': '文件路径不能为空',
                    'data': None
                }), 400

            # 获取文件扩展名
            file_ext = os.path.splitext(file_path)[1].lower().lstrip('.')
            return_dict = process_media_file(file_path, file_ext)

        result, code, failed = return_dict['result'], return_dict['code'], return_dict['failed']

        if code > 0:  # 成功
            # 格式化返回结果
            formatted_result = {
                'type': '音视频伪造检测',
                'result': '真实' if result.get('label') == 'Real' else '伪造',
                'confidence': round(result.get('scores', 0), 4),
                'media_type': '音频' if file_ext in ['mp3', 'wav', 'flac', 'm4a'] else '视频'
            }

            return jsonify({
                'success': True,
                'message': '检测完成',
                'data': formatted_result
            })
        else:  # 失败
            return jsonify({
                'success': False,
                'message': failed or '检测失败',
                'data': None
            }), 500

    except Exception as e:
        app.logger.error(f'API错误: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}',
            'data': None
        }), 500

def process_media_file(file_path, file_ext):
    """根据文件类型处理音视频文件"""
    try:
        print(f"处理文件: {file_path}, 类型: {file_ext}")

        if file_ext in ['mp3', 'wav', 'flac', 'm4a']:
            # 音频文件 -> 音频伪造检测
            print(f"检测到音频文件: {file_ext}")
            result_dict = detect_fake_audio(file_path)
            if result_dict['status'] == 'success':
                result = {
                    'label': 'Fake' if result_dict['prediction'] == 'fake' else 'Real',
                    'scores': result_dict['confidence']
                }
                return {'result': result, 'code': 1, 'failed': ''}
            else:
                return {'result': '', 'code': 0, 'failed': result_dict.get('error', '音频检测失败')}

        elif file_ext in ['mp4', 'avi', 'mov', 'mkv', 'flv']:
            # 视频文件 -> 人脸伪造检测
            print(f"检测到视频文件: {file_ext}")
            result_dict = video_classification_003(file_path)
            if result_dict['code'] == 1:
                result = result_dict['result']
                return {'result': result, 'code': 1, 'failed': ''}
            else:
                return {'result': '', 'code': 0, 'failed': result_dict.get('failed', '视频检测失败')}
        else:
            return {'result': '', 'code': 0, 'failed': f'不支持的文件格式: {file_ext}'}

    except Exception as e:
        return {'result': '', 'code': 0, 'failed': str(e)}

@app.route('/predict', methods=['POST']) # 根据URL的[path]区分测试用例
def predict():
    """ 解析JSON调用数据格式 """
    data = request.json
    task_id = data.get('task_id', 0) # 任务id，即用例编号，用于区别不同模型
    url = data.get('url', '') # 本地路径，指向测试集文件夹。如果为图像、视频、音频等文件则为必选
    data_id = data.get('data_id', 0) # 数据id，数据唯一标识
    data_type = data.get('type', '') # 数据格式 MP4 png ...
    text = data.get('text', '') # 待检测的文本数据，如果检测文本则为必选

    """ 配置日志记录器 """
    # logging.basicConfig(filename=f'log/{task_id}.log', level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')

    """ 智能路由：根据文件类型选择检测方法 """
    try:
        # 添加调试信息
        print(f"接收到的数据: task_id={task_id}, data_type='{data_type}', url='{url}'")

        # 清理文件类型：移除开头的点号
        clean_data_type = data_type.strip('.') if data_type else ''
        print(f"清理后的文件类型: '{clean_data_type}'")

        if clean_data_type.lower() in ['mp3', 'wav', 'flac', 'm4a']:
            # 音频文件 -> 音频伪造检测
            print(f"检测到音频文件: {clean_data_type}")
            result_dict = detect_fake_audio(url)
            if result_dict['status'] == 'success':
                # 恢复原来的逻辑：使用模型的原始预测结果
                result = {
                    'label': 'Fake' if result_dict['prediction'] == 'fake' else 'Real',
                    'scores': result_dict['confidence']
                }
                code = 1
                failed = ''
            else:
                result = {'error': result_dict.get('error', '音频检测失败')}
                code = 0
                failed = result_dict.get('error', '音频检测失败')

        elif clean_data_type.lower() in ['mp4', 'avi', 'mov', 'mkv', 'flv']:
            # 视频文件 -> 人脸伪造检测（现有功能）
            print(f"检测到视频文件: {clean_data_type}")
            result_dict = video_classification_003(url)
            if result_dict['code'] == 1:
                # 恢复原来的逻辑：直接使用视频检测结果
                result = result_dict['result']
                code = 1
                failed = ''
            else:
                result = {'error': result_dict.get('failed', '视频检测失败')}
                code = 0
                failed = result_dict.get('failed', '视频检测失败')

        else:
            # 不支持的文件格式
            result = {'error': f'不支持的文件格式: {data_type} (清理后: {clean_data_type})'}
            code = 0
            failed = f'不支持的文件格式: {data_type} (清理后: {clean_data_type})'

    except Exception as e:
        result = {'error': f'检测过程发生错误: {str(e)}'}
        code = 0
        failed = str(e)

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


@app.route('/audio/detect', methods=['POST'])
def audio_detect():
    """ 专门的音频伪造检测接口 """
    data = request.json
    task_id = data.get('task_id', 0)
    url = data.get('url', '')
    data_id = data.get('data_id', 0)

    try:
        result_dict = detect_fake_audio(url)
        if result_dict['status'] == 'success':
            # 恢复原来的逻辑：使用模型的原始预测结果
            result = {
                'label': 'Fake' if result_dict['prediction'] == 'fake' else 'Real',
                'scores': result_dict['confidence']
            }
            code = 1
            failed = ''
        else:
            result = {'error': result_dict.get('error', '音频检测失败')}
            code = 0
            failed = result_dict.get('error', '音频检测失败')

    except Exception as e:
        result = {'error': f'音频检测发生错误: {str(e)}'}
        code = 0
        failed = str(e)

    response = {
        'task_id': task_id,
        'data_id': data_id,
        'content': result,
        'status': {
            "code": code,
            "failed": failed,
        }
    }
    return response


@app.route('/audio/embedding', methods=['POST'])
def audio_embedding():
    """ 音频特征提取接口 """
    data = request.json
    task_id = data.get('task_id', 0)
    url = data.get('url', '')
    data_id = data.get('data_id', 0)

    try:
        result_dict = extract_audio_embedding(url)
        if result_dict['status'] == 'success':
            result = {
                'extraction_type': 'audio_embedding',
                'embedding_dim': result_dict['embedding_dim'],
                'embedding': result_dict['embedding'][:10],  # 只返回前10个值作为示例
                'full_embedding_available': True
            }
            code = 1
            failed = ''
        else:
            result = {'error': result_dict.get('error', '特征提取失败')}
            code = 0
            failed = result_dict.get('error', '特征提取失败')

    except Exception as e:
        result = {'error': f'特征提取发生错误: {str(e)}'}
        code = 0
        failed = str(e)

    response = {
        'task_id': task_id,
        'data_id': data_id,
        'content': result,
        'status': {
            "code": code,
            "failed": failed,
        }
    }
    return response


@app.route('/audio/info', methods=['POST'])
def audio_info():
    """ 获取音频文件信息接口 """
    data = request.json
    task_id = data.get('task_id', 0)
    url = data.get('url', '')
    data_id = data.get('data_id', 0)

    try:
        result_dict = get_audio_info(url)
        if result_dict['status'] == 'success':
            result = {
                'info_type': 'audio_info',
                'duration': result_dict['duration'],
                'sample_rate': result_dict['sample_rate'],
                'channels': result_dict['channels'],
                'samples': result_dict['samples'],
                'format': result_dict['format']
            }
            code = 1
            failed = ''
        else:
            result = {'error': result_dict.get('error', '信息获取失败')}
            code = 0
            failed = result_dict.get('error', '信息获取失败')

    except Exception as e:
        result = {'error': f'信息获取发生错误: {str(e)}'}
        code = 0
        failed = str(e)

    response = {
        'task_id': task_id,
        'data_id': data_id,
        'content': result,
        'status': {
            "code": code,
            "failed": failed,
        }
    }
    return response


def video_classification_003(url):
    try:
        model = load_model()
        result = video_classification_main_function(model=model, url=url)
        return {'result': result, 'code': 1, 'failed': ''} # 成功执行
    except Exception as e:
        return {'result': '', 'code': 0, 'failed': str(e)}

if __name__ == '__main__':
    app.run(debug=True, port=5014, host='0.0.0.0')
