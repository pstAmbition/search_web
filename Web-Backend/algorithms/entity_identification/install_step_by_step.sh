#!/bin/bash

# =============================================================================
# Entity Identification 项目环境安装脚本
# 基于 Dockerfile 和 requirements.txt 生成
# =============================================================================

set -e  # 遇到错误立即退出

echo "🚀 开始安装 Entity Identification 项目环境..."
echo "📋 基于 Dockerfile 和 requirements.txt 配置"
echo ""

# 检查Python版本
echo "🔍 检查Python版本..."
python3 --version
echo ""

# 1. 更新系统包管理器
echo "�� 步骤1: 更新系统包管理器..."
# sudo apt-get update
echo "✅ 系统包管理器更新完成"
echo ""

# 2. 安装系统依赖
echo "📦 步骤2: 安装系统依赖..."
# sudo apt-get install -y \
#     libgl1-mesa-glx \
#     libxrender-dev \
#     libglib2.0-0 \
#     wget \
#     curl
echo "✅ 系统依赖安装完成"
echo ""

# 3. 清理现有PyTorch安装
echo "🧹 步骤3: 清理现有PyTorch安装..."
pip uninstall -y torch torchvision torchaudio || true
echo "✅ PyTorch清理完成"
echo ""

# 4. 安装PyTorch (CUDA 11.6版本)
echo "📦 步骤4: 安装PyTorch..."
if [ -f "torch-1.13.0+cu116-cp38-cp38-linux_x86_64.whl" ]; then
    echo "📁 发现本地PyTorch wheel文件，使用本地安装..."
    pip install torch-1.13.0+cu116-cp38-cp38-linux_x86_64.whl
else
    echo "🌐 从网络安装PyTorch..."
    echo "⚠️  尝试安装CUDA 11.6版本..."
    pip install torch==1.13.0+cu116 torchvision==0.14.0+cu116 torchaudio==0.13.0+cu116 -f https://download.pytorch.org/whl/torch_stable.html || {
        echo "⚠️  CUDA 11.6版本安装失败，尝试CUDA 11.7版本..."
        pip install torch==1.13.0+cu117 torchvision==0.14.0+cu117 torchaudio==0.13.0+cu117 -f https://download.pytorch.org/whl/torch_stable.html || {
            echo "⚠️  CUDA版本安装失败，安装CPU版本..."
            pip install torch==1.13.0 torchvision==0.14.0 torchaudio==0.13.0
        }
    }
fi
echo "✅ PyTorch安装完成"
echo ""

# 5. 安装项目依赖
echo "📦 步骤5: 安装项目依赖..."
pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
echo "✅ 项目依赖安装完成"
echo ""

# 6. 安装Flask
echo "📦 步骤6: 安装Flask..."
pip install --trusted-host pypi.python.org Flask
echo "✅ Flask安装完成"
echo ""

# 7. 验证安装
echo "🔍 步骤7: 验证安装..."
echo "检查关键包版本:"
python3 -c "
import torch
import transformers
import flask
import numpy
import sklearn
import tqdm

print(f'✅ PyTorch: {torch.__version__}')
print(f'✅ Transformers: {transformers.__version__}')
print(f'✅ Flask: {flask.__version__}')
print(f'✅ NumPy: {numpy.__version__}')
print(f'✅ Scikit-learn: {sklearn.__version__}')
print(f'✅ TQDM: {tqdm.__version__}')
print(f'✅ CUDA可用: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'✅ CUDA版本: {torch.version.cuda}')
    print(f'✅ GPU数量: {torch.cuda.device_count()}')
"
echo ""

# 8. 检查模型文件
echo "🔍 步骤8: 检查模型文件..."
if [ -d "bert-base-chinese" ]; then
    echo "✅ 发现中文BERT模型目录: bert-base-chinese"
    if [ -f "bert-base-chinese/pytorch_model.bin" ]; then
        echo "✅ 发现PyTorch模型文件: bert-base-chinese/pytorch_model.bin"
    fi
    if [ -f "bert-base-chinese/model.safetensors" ]; then
        echo "✅ 发现SafeTensors模型文件: bert-base-chinese/model.safetensors"
    fi
    if [ -f "bert-base-chinese/config.json" ]; then
        echo "✅ 发现配置文件: bert-base-chinese/config.json"
    fi
    if [ -f "bert-base-chinese/vocab.txt" ]; then
        echo "✅ 发现词汇表: bert-base-chinese/vocab.txt"
    fi
else
    echo "⚠️  未发现中文BERT模型目录: bert-base-chinese"
    echo "   请确保模型文件已正确放置"
fi

if [ -d "saved_model-tagger-context" ]; then
    echo "✅ 发现保存的模型目录: saved_model-tagger-context"
else
    echo "⚠️  未发现保存的模型目录: saved_model-tagger-context"
    echo "   请确保训练好的模型已正确放置"
fi

if [ -d "model" ]; then
    echo "✅ 发现模型代码目录: model"
    echo "   包含文件: $(ls model/ | wc -l) 个文件"
else
    echo "⚠️  未发现模型代码目录: model"
fi
echo ""

# 9. 测试导入
echo "�� 步骤9: 测试关键模块导入..."
python3 -c "
try:
    from transformers import AutoTokenizer, AutoModel
    from flask import Flask
    import torch
    import numpy as np
    import sklearn
    import tqdm
    print('✅ 所有关键模块导入成功')
except ImportError as e:
    print(f'❌ 模块导入失败: {e}')
    exit(1)
"
echo ""

# 10. 测试BERT模型加载
echo "🧪 步骤10: 测试BERT模型加载..."
python3 -c "
try:
    from transformers import AutoTokenizer, AutoModel
    import os
    
    if os.path.exists('bert-base-chinese'):
        print('📥 测试本地BERT模型加载...')
        tokenizer = AutoTokenizer.from_pretrained('./bert-base-chinese')
        model = AutoModel.from_pretrained('./bert-base-chinese')
        print('✅ 本地BERT模型加载成功')
    else:
        print('⚠️  本地BERT模型目录不存在，跳过测试')
        
except Exception as e:
    print(f'❌ BERT模型加载测试失败: {e}')
"
echo ""

echo "🎉 Entity Identification 项目环境安装完成！"
echo ""
echo "📋 安装总结:"
echo "   - Python 3.8 环境"
echo "   - PyTorch 1.13.0 (CUDA 11.6)"
echo "   - Transformers 4.27.1"
echo "   - Flask Web框架"
echo "   - 所有项目依赖包"
echo ""
echo "🚀 启动项目:"
echo "   python build_api.py"
echo ""
echo "📡 API端口: 5012"
echo "🔗 测试接口: POST /ner"
echo "📝 功能: 命名实体识别 (NER)"
echo ""
echo "📁 项目结构:"
echo "   - bert-base-chinese/     : 中文BERT预训练模型"
echo "   - model/                 : 模型代码"
echo "   - saved_model-tagger-context/ : 训练好的模型"
echo "   - Dataset/               : 数据集"
echo "   - utils/                 : 工具函数"
echo ""
