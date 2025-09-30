from flask import Flask, request, jsonify
import logging
import json
import os
from flask_cors import CORS
import tempfile
import shutil

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

"""
curl -X POST http://localhost:5001/predict -H "Content-Type: application/json" -d '{"task_id": "rhfx-001", "text_url": "data/twitter/test_text_with_label.npz", "image_url": "data/twitter/test_image_with_label.npz", "data_id": 0}'
curl -X POST http://localhost:5001/predict -H "Content-Type: application/json" -d '{"task_id": "rhfx-001", "text_url": "BREAKING: Nancy Pelosi Was Just Taken From Her Office In Handcuffs", "image_url": "./fake_news.png"}'

curl -X POST http://localhost:5001/api/multimodal/detect -H "Content-Type: application/json" -d '{"text": "BREAKING: Nancy Pelosi Was Just Taken From Her Office In Handcuffs", "image_url": "./fake_news.png"}'
"""
from uts import get_available_gpu

""" 自动找一张能用的gpu """
gpu_ids = get_available_gpu(min_free_memory_mb=10240)
os.environ['CUDA_VISIBLE_DEVICES'] = str(gpu_ids)

""" 导入测试用例rhfx-001所用函数 """
from test import multimodal_classification_for_one_sample, multimodal_classification_for_one_sample_with_raw_input # 对接API的函数

@app.route('/api/multimodal/detect', methods=['POST'])
def multimodal_detect():
    """多模态假新闻检测API - 支持本地路径和前端上传"""
    try:
        # 检查请求类型
        if request.content_type and 'multipart/form-data' in request.content_type:
            # 前端文件上传
            text = request.form.get('text', '')
            image_file = request.files.get('image')
            
            print(f"前端上传 - 文本: '{text}'")
            print(f"前端上传 - 图片文件名: {image_file.filename if image_file else 'None'}")
            print(f"前端上传 - 图片大小: {image_file.content_length if image_file else 'None'}")
            
            if not text or text.strip() == '':
                return jsonify({
                    'success': False,
                    'message': '文本内容不能为空',
                    'data': None
                }), 400
            
            if not image_file:
                return jsonify({
                    'success': False,
                    'message': '请上传图片文件',
                    'data': None
                }), 400
            
            # 保存上传的图片到临时文件
            temp_dir = tempfile.mkdtemp()
            temp_image_path = os.path.join(temp_dir, 'uploaded_image.jpg')
            image_file.save(temp_image_path)
            
            print(f"临时图片路径: {temp_image_path}")
            print(f"临时图片大小: {os.path.getsize(temp_image_path)} bytes")
            
            try:
                # 调用模型预测
                return_dict = multimodal_classification_001(text, temp_image_path, 0)
                result, code, failed = return_dict['result'], return_dict['code'], return_dict['failed']
                
                print(f"预测结果: {result}")
                
                if code > 0:  # 成功
                    # 格式化返回结果
                    formatted_result = {
                        'type': '多模态假新闻检测',
                        'result': result['labels'],
                        'confidence': result['scores']
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
                    
            finally:
                # 清理临时文件
                shutil.rmtree(temp_dir, ignore_errors=True)
                
        else:
            # JSON请求（本地测试）
            data = request.json
            text = data.get('text', '')
            image_url = data.get('image_url', '')
            
            print(f"本地测试 - 文本: '{text}'")
            print(f"本地测试 - 图片路径: {image_url}")
            print(f"本地测试 - 图片大小: {os.path.getsize(image_url) if os.path.exists(image_url) else 'File not found'} bytes")
            
            if not text or text.strip() == '':
                return jsonify({
                    'success': False,
                    'message': '文本内容不能为空',
                    'data': None
                }), 400
            
            if not image_url:
                return jsonify({
                    'success': False,
                    'message': '图片路径不能为空',
                    'data': None
                }), 400
            
            # 调用模型预测
            return_dict = multimodal_classification_001(text, image_url, 0)
            result, code, failed = return_dict['result'], return_dict['code'], return_dict['failed']
            
            print(f"预测结果: {result}")
            
            if code > 0:  # 成功
                # 格式化返回结果
                formatted_result = {
                    'type': '多模态假新闻检测',
                    'result': result['labels'],
                    'confidence': result['scores']
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

@app.route('/predict', methods=['POST']) # 根据URL的[path]区分测试用例
def predict():
    """ 解析JSON调用数据格式 """
    print("收到请求：", request.json)
    data = request.json 
    task_id = data.get('task_id', 0) # 任务id，即用例编号，用于区别不同模型
    text_url = data.get('text_url', 'data/twitter/test_text_with_label.npz') # 本地路径，指向测试集文件夹。如果为图像、视频、音频等文件则为必选
    image_url = data.get('image_url', 'data/twitter/test_image_with_label.npz')
    data_id = data.get('data_id', 0) # 数据id，数据唯一标识

    """ 配置日志记录器 """
    # logging.basicConfig(filename=f'log/{task_id}.log', level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')

    """ 调用模型预测逻辑，返回模型的实际预测结果\code\failed """
    return_dict = multimodal_classification_001(text_url, image_url, data_id)
    
    result, code, failed = return_dict['result'], return_dict['code'],return_dict['failed']
    print('result', result)
    
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

def multimodal_classification_001(text_url, image_url, data_id):
    try:
        if text_url.endswith(".npz") and image_url.endswith(".npz"):
            prediction, label, probs = multimodal_classification_for_one_sample(text_url, image_url, data_id)
            return {'result': {'labels': "FAKE" if prediction == 1 else "REAL", 'ground_truth': "FAKE" if label == 1 else "REAL", 'scores': probs}, 'code': 1, 'failed': ''} # 成功执行
        else:
            prediction, probs = multimodal_classification_for_one_sample_with_raw_input(text_url, image_url)
            return {'result': {'labels': "FAKE" if prediction == 1 else "REAL", 'scores': probs}, 'code': 1, 'failed': ''} # 成功执行
    except Exception as e:
        return {'result': '', 'code': 0, 'failed': str(e)}
    
if __name__ == '__main__':
    app.json.ensure_ascii = False
    app.run(debug=True, host='0.0.0.0', port=5017)
