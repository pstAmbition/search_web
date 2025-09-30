from flask import Flask, request, jsonify
import os
import json
import logging
import io
import cv2
import numpy as np
from PIL import Image

app = Flask(__name__)

# 配置JSON输出，确保中文正常显示
app.json.ensure_ascii = False # 解决中文乱码问题

# 添加CORS支持
from flask_cors import CORS
CORS(app)

from uts import get_available_gpu

""" 自动找一张能用的gpu """
gpu_ids = get_available_gpu()
os.environ['CUDA_VISIBLE_DEVICES'] = str(gpu_ids)

""" 导入测试用例flfx-002所用函数 """
from ImageFornsicsOSN.test_flfx002 import image_classification_main_function # 对接API的函数
from ImageFornsicsOSN.test_flfx002 import Model as image_classification_model

@app.route('/api/image/detect', methods=['POST'])
def image_detect():
    """图像伪造检测API - 支持两种方式"""
    try:
        # 检查请求类型
        if request.content_type and 'multipart/form-data' in request.content_type:
            # 方式1：处理上传的文件
            if 'image' not in request.files:
                return jsonify({
                    'success': False,
                    'message': '没有找到图像文件',
                    'data': None
                }), 400

            file = request.files['image']
            if file.filename == '':
                return jsonify({
                    'success': False,
                    'message': '没有选择文件',
                    'data': None
                }), 400

            return_dict = image_classification_from_memory(file)
        else:
            # 方式2：处理本地路径
            data = request.json
            image_url = data.get('image_url', '')
            
            if not image_url or image_url.strip() == '':
                return jsonify({
                    'success': False,
                    'message': '图像文件路径不能为空',
                    'data': None
                }), 400

            return_dict = image_classification_001(image_url)

        result, code, failed = return_dict['result'], return_dict['code'], return_dict['failed']

        if code > 0:  # 成功
            formatted_result = {
                'type': '图像伪造检测',
                'result': '真实' if result['labels'] == 'Real' else '伪造',
                'confidence': round(result['scores'], 4),
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

def image_classification_from_memory(file):
    """直接从内存中的文件进行图像检测"""
    try:
        # 将上传的文件转换为OpenCV格式
        file_bytes = np.frombuffer(file.read(), np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

        if img is None:
            return {'result': '', 'code': 0, 'failed': '无效的图像文件'}

        # 保存临时文件（简化处理）
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            cv2.imwrite(tmp_file.name, img)
            temp_path = tmp_file.name
        
        try:
            # 初始化模型
            model = image_classification_model().cuda()
            model.load()
            model.eval()
            
            # 调用原有检测函数
            result = image_classification_main_function(model=model, url=temp_path)
            return {'result': result, 'code': 1, 'failed': ''}
        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except Exception as e:
        return {'result': '', 'code': 0, 'failed': str(e)}

def image_classification_001(url):
    """本地路径检测"""
    try:
        model = image_classification_model().cuda()
        model.load()
        model.eval()
        result = image_classification_main_function(model=model, url=url)
        return {'result': result, 'code': 1, 'failed': ''}
    except Exception as e:
        return {'result': '', 'code': 0, 'failed': str(e)}

if __name__ == '__main__':
    app.run(debug=True, port=5013, host='0.0.0.0')