#!/bin/bash

# 多模态检测项目分步安装脚本（修复版）
# 基于Dockerfile、requirements.txt和environment.yml配置
# 专门为Python 3.8环境设计，支持CUDA 11.6

echo "🚀 多模态检测项目分步安装脚本（修复版）"
echo "=================================="
echo "基于Dockerfile、requirements.txt和environment.yml配置"
echo ""

# 检查Python版本
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "当前Python版本: $python_version"

# 检查CUDA版本
cuda_version=$(nvidia-smi | grep "CUDA Version" | awk '{print $9}' 2>/dev/null || echo "未检测到CUDA")
echo "CUDA版本: $cuda_version"

if [[ "$python_version" != "3.8" ]]; then
    echo "⚠️  警告：此脚本专为Python 3.8设计，当前版本: $python_version"
    echo "建议使用: conda create -n multimodal_detection python=3.8"
fi

# 升级pip
echo "升级pip..."
python3 -m pip install --upgrade pip

# 第一步：安装系统依赖
echo "第一步：安装系统依赖..."
echo "注意：以下命令需要sudo权限，如果失败请手动安装："
echo "sudo apt-get update"
echo "sudo apt-get install -y libgl1-mesa-glx libxrender-dev libglib2.0-0"

# 检查系统依赖
if command -v apt-get &> /dev/null; then
    echo "检测到apt包管理器，尝试安装系统依赖..."
    # sudo apt-get update
    # sudo apt-get install -y libgl1-mesa-glx libxrender-dev libglib2.0-0
else
    echo "⚠️  未检测到apt包管理器，请手动安装系统依赖"
fi

# 第二步：清理现有PyTorch包
echo "第二步：清理现有PyTorch包..."
python3 -m pip uninstall -y torch torchvision torchaudio

# 第三步：安装CUDA 11.6版本PyTorch（修复版本冲突）
echo "第三步：安装CUDA 11.6版本PyTorch..."
echo "使用兼容的版本组合..."

# 方案1：使用environment.yml中的版本
echo "尝试方案1：使用environment.yml中的版本..."
python3 -m pip install torch==1.12.1+cu116 torchvision==0.13.1+cu116 torchaudio==0.12.1+cu116 --extra-index-url https://download.pytorch.org/whl/cu116

# 如果方案1失败，尝试方案2
if [ $? -ne 0 ]; then
    echo "方案1失败，尝试方案2：使用Dockerfile中的版本..."
    python3 -m pip install torch==1.12.0+cu116 --extra-index-url https://download.pytorch.org/whl/cu116
    python3 -m pip install torchvision==0.13.0+cu116 --extra-index-url https://download.pytorch.org/whl/cu116
    python3 -m pip install torchaudio==0.12.0+cu116 --extra-index-url https://download.pytorch.org/whl/cu116
fi

# 如果方案2也失败，尝试方案3
if [ $? -ne 0 ]; then
    echo "方案2失败，尝试方案3：使用最新兼容版本..."
    python3 -m pip install torch==1.12.1+cu116 --extra-index-url https://download.pytorch.org/whl/cu116
    python3 -m pip install torchvision==0.13.1+cu116 --extra-index-url https://download.pytorch.org/whl/cu116
    python3 -m pip install torchaudio==0.12.1+cu116 --extra-index-url https://download.pytorch.org/whl/cu116
fi

# 第四步：安装requirements.txt中的基础依赖
echo "第四步：安装基础依赖包..."
python3 -m pip install blinker==1.7.0
python3 -m pip install click==8.1.7
python3 -m pip install Flask==3.0.2
python3 -m pip install Flask-CORS==3.0.10
python3 -m pip install importlib-metadata==7.0.1
python3 -m pip install itsdangerous==2.1.2
python3 -m pip install Jinja2==3.1.3
python3 -m pip install joblib==1.3.2
python3 -m pip install MarkupSafe==2.1.5
python3 -m pip install numpy==1.24.4
python3 -m pip install scikit-learn==1.3.2
python3 -m pip install scipy==1.10.1
python3 -m pip install threadpoolctl==3.3.0
python3 -m pip install tqdm==4.66.2
python3 -m pip install typing_extensions==4.10.0
python3 -m pip install Werkzeug==3.0.1
python3 -m pip install zipp==3.17.0

# 第五步：安装environment.yml中的额外依赖
echo "第五步：安装额外依赖包..."
python3 -m pip install blessed==1.21.0
python3 -m pip install certifi==2024.2.2
python3 -m pip install charset-normalizer==3.3.2
python3 -m pip install filelock==3.14.0
python3 -m pip install fsspec==2024.5.0
python3 -m pip install gpustat==1.1.1
python3 -m pip install huggingface-hub==0.23.2
python3 -m pip install idna==3.7
python3 -m pip install nvidia-ml-py==13.580.65
python3 -m pip install packaging==24.0
python3 -m pip install pillow==10.3.0
python3 -m pip install psutil==7.0.0
python3 -m pip install pyyaml==6.0.1
python3 -m pip install regex==2024.5.15
python3 -m pip install requests==2.32.3
python3 -m pip install safetensors==0.4.3
python3 -m pip install tokenizers==0.19.1
python3 -m pip install transformers==4.41.1
python3 -m pip install urllib3==2.2.1
python3 -m pip install wcwidth==0.2.13

# 第六步：安装多模态检测可能需要的额外包
echo "第六步：安装多模态检测额外依赖..."
python3 -m pip install opencv-python
python3 -m pip install matplotlib
python3 -m pip install seaborn
python3 -m pip install pandas

echo "✅ 所有依赖安装完成！"
echo ""
echo "🎯 验证安装："
python3 -c "import torch; print(f'PyTorch版本: {torch.__version__}')"
python3 -c "import torch; print(f'CUDA可用: {torch.cuda.is_available()}')"
python3 -c "import torch; print(f'CUDA设备数: {torch.cuda.device_count()}')"
python3 -c "import torchvision; print(f'TorchVision版本: {torchvision.__version__}')"
python3 -c "import numpy; print(f'NumPy版本: {numpy.__version__}')"
python3 -c "import flask; print(f'Flask版本: {flask.__version__}')"
python3 -c "import transformers; print(f'Transformers版本: {transformers.__version__}')"
python3 -c "import sklearn; print(f'Scikit-learn版本: {sklearn.__version__}')"

echo ""
echo "🎯 下一步："
echo "1. 检查模型文件: ls -la *.pt"
echo "2. 启动服务: python build_api.py"
echo "3. 测试API: curl -X POST http://localhost:5001/predict"
echo ""
echo "📝 注意："
echo "   - 此脚本基于Dockerfile、requirements.txt和environment.yml配置"
echo "   - 使用CUDA 11.6版本的PyTorch"
echo "   - 端口5001用于API服务"
echo "   - 确保detection_module.pt和similarity_module.pt模型文件存在"
echo "   - 如果遇到系统依赖问题，请手动安装libgl1-mesa-glx等包"
