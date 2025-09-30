from flask import Flask,request,jsonify
import os
from uts import get_available_gpu
import torch.nn.functional as F
from transformers import *
from transformers import AutoTokenizer, AutoModelForMaskedLM
import torch
from test import run
import logging
import json
# Configure logging
logging.basicConfig(level=logging.DEBUG)
# """ 自动找一张能用的gpu """
gpu_ids = get_available_gpu()
os.environ['CUDA_VISIBLE_DEVICES'] = str(gpu_ids)

app = Flask(__name__)


# 配置JSON输出，确保中文正常显示
app.json.ensure_ascii = False # 解决中文乱码问题

# 添加CORS支持
from flask_cors import CORS
CORS(app)

@app.route('/api/text/detect',methods=['POST'])
def text_detect():
    """'文本谣言检测API - 与前端对齐的接口'"""
    try:
        data = request.json
        text = data.get('text', '') # 待检测的文本数据
        
        if not text or text.strip() == '':
            return jsonify({
                'success': False,
                'message': '文本内容不能为空',
                'data': None
            }), 400
        
        # 调用模型预测逻辑
        return_dict = rumor_detect(text)
        result, code, failed = return_dict['result'], return_dict['code'], return_dict['failed']
        
        if code > 0:  # 成功
            # 格式化返回结果以匹配前端期望
            formatted_result = {
                'type': '文本谣言检测',
                'result': '谣言' if result['labels'] == 0 else '非谣言',
                'confidence': round(result['scores'], 4),
                'details': {
                    'algorithm': 'Chinese-RoBERTa',
                    'timestamp': str(torch.cuda.Event(enable_timing=True).query() if torch.cuda.is_available() else ''),
                    'model_output': result
                }
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
@app.route('/rumordetect',methods=['POST'])
def embedding():
    """调用JSON，解析请求数据"""
    data = request.json
    task_id = data.get('task_id', 0) # 任务id，即用例编号，用于区别不同模型
    url = data.get('url', '') # 本地路径，指向测试集文件夹。如果为图像、视频、音频等文件则为必选
    data_id = data.get('data_id', 0) # 数据id，数据唯一标识
    data_type = data.get('type', '') # 数据格式 MP4 png ...
    text = data.get('text', 'rumor') # 待检测的文本数据，如果检测文本则为必选
    
    """ 调用模型预测逻辑，返回模型的实际预测结果\code\failed """
    return_dict = rumor_detect(text)
    result, code, failed = return_dict['result'], return_dict['code'],return_dict['failed']
    
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



def rumor_detect(text="detect"):
    try:
        if text == '':

            return {'result':'','code':0,'failed':'待向量化字符串为空'}
        else:
            tokenizer = AutoTokenizer.from_pretrained('chinese-roberta-wwm-ext')
            model = RobertaForSequenceClassification.from_pretrained("chinese-roberta-wwm-ext")
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            model = model.to(device)
            print(f"Using device: {device}")
            # print("checkpoint")
            checkpoint = torch.load(os.path.join("model","best-model.bin"))
            # print("checkpoint",checkpoint)
            # print("model param",{k.replace('module.', ''): v for k, v in checkpoint.items()})
            model.load_state_dict({k.replace('module.', ''): v for k, v in checkpoint.items()})
            app.logger.info(f"CUDA available: {torch.cuda.is_available()}")
            
            print("load model success")
            tokens = tokenizer.encode(text, add_special_tokens=True)
            tokens = torch.tensor(tokens).to(device)
            max_sequence_length = 256
            padding_length = max_sequence_length-len(tokens)
            padding = torch.full((padding_length,), tokenizer.pad_token_id).to(device)
            tokens = torch.cat([tokens, padding]).cuda()
    
            mask = torch.cat([torch.ones(len(tokens) - padding_length), torch.zeros(padding_length)]).cuda()
         
            outputs = model(tokens.unsqueeze(0),attention_mask=mask.unsqueeze(0))
            
            logits = outputs.logits
            probabilities = F.sigmoid(logits)
            predicted_label = torch.argmax(probabilities, dim=1).item()
            labels = ['rumor','notrumor']
            print(probabilities[:,predicted_label])
            
            result = {
                "labels":predicted_label,
                'scores':probabilities[:,predicted_label].item(),
                "results":labels[predicted_label],
            }
            return {'result': result, 'code': 1, 'failed': ''} # 成功执行
    # try:
    #     result = run()
    #     return {'result': result, 'code': 1, 'failed': ''}
    except Exception as e:
        return {'result': '', 'code': 0, 'failed': str(e)}

if __name__ == '__main__':
    app.run(debug=True,port=5011,host='0.0.0.0')
    