#!/bin/bash

# =============================================================================
# Text Detection 项目环境安装脚本
# 基于 Dockerfile 和 requirements.txt 生成
# =============================================================================

set -e  # 遇到错误立即退出

echo "🚀 开始安装 Text Detection 项目环境..."
echo "📋 基于 Dockerfile 和 requirements.txt 配置"
echo ""

# 检查Python版本
echo "🔍 检查Python版本..."
python3 --version
echo ""

# 1. 更新系统包管理器
echo "📦 步骤1: 更新系统包管理器..."
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

# 4. 安装triton (PyTorch依赖)
echo "📦 步骤4: 安装triton..."
pip install triton==2.1.0 -i https://pypi.tuna.tsinghua.edu.cn/simple
echo "✅ triton安装完成"
echo ""

# 5. 安装PyTorch (CUDA 11.8版本)
echo "📦 步骤5: 安装PyTorch..."
if [ -f "torch-2.1.1+cu118-cp38-cp38-linux_x86_64.whl" ]; then
    echo "📁 发现本地PyTorch wheel文件，使用本地安装..."
    pip install torch-2.1.1+cu118-cp38-cp38-linux_x86_64.whl
else
    echo "🌐 从网络安装PyTorch..."
    pip install torch==2.1.1+cu118 torchvision==0.16.1+cu118 torchaudio==2.1.1+cu118 -f https://download.pytorch.org/whl/torch_stable.html
fi
echo "✅ PyTorch安装完成"
echo ""

# 6. 安装项目依赖
echo "📦 步骤6: 安装项目依赖..."
pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
echo "✅ 项目依赖安装完成"
echo ""

# 7. 安装Flask
echo "📦 步骤7: 安装Flask..."
pip install --trusted-host pypi.python.org Flask
echo "✅ Flask安装完成"
echo ""

# 8. 验证安装
echo "🔍 步骤8: 验证安装..."
echo "检查关键包版本:"
python3 -c "
import torch
import transformers
import flask
import pandas
import sklearn
import tqdm
import requests
import fire
import tensorboard
import sentencepiece

print(f'✅ PyTorch: {torch.__version__}')
print(f'✅ Transformers: {transformers.__version__}')
print(f'✅ Flask: {flask.__version__}')
print(f'✅ Pandas: {pandas.__version__}')
print(f'✅ Scikit-learn: {sklearn.__version__}')
print(f'✅ CUDA可用: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'✅ CUDA版本: {torch.version.cuda}')
    print(f'✅ GPU数量: {torch.cuda.device_count()}')
"
echo ""

# 9. 检查模型文件
echo "🔍 步骤9: 检查模型文件..."
if [ -f "model/best-model.bin" ]; then
    echo "✅ 发现模型文件: model/best-model.bin"
else
    echo "⚠️  未发现模型文件: model/best-model.bin"
    echo "   请确保模型文件已正确放置"
fi

if [ -d "chinese-roberta-wwm-ext" ]; then
    echo "✅ 发现中文RoBERTa模型目录: chinese-roberta-wwm-ext"
else
    echo "⚠️  未发现中文RoBERTa模型目录: chinese-roberta-wwm-ext"
    echo "   请确保模型文件已正确放置"
fi
echo ""

# 10. 测试导入
echo "🧪 步骤10: 测试关键模块导入..."
python3 -c "
try:
    from transformers import AutoTokenizer, AutoModelForMaskedLM
    from flask import Flask
    import torch
    print('✅ 所有关键模块导入成功')
except ImportError as e:
    print(f'❌ 模块导入失败: {e}')
    exit(1)
"
echo ""

echo "🎉 Text Detection 项目环境安装完成！"
echo ""
echo "�� 安装总结:"
echo "   - Python 3.8 环境"
echo "   - PyTorch 2.1.1 (CUDA 11.8)"
echo "   - Transformers 4.35.2"
echo "   - Flask Web框架"
echo "   - 所有项目依赖包"
echo ""
echo "🚀 启动项目:"
echo "   python build_api.py"
echo ""
echo "📡 API端口: 5011"
echo "🔗 测试接口: POST /rumordetect"
echo ""
