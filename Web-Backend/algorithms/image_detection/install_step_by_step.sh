#!/bin/bash

# 图片检测项目分步安装脚本
# 基于Dockerfile和requirements.txt配置
# 专门为Python 3.8环境设计，支持CUDA 11.6

echo "🚀 图片检测项目分步安装脚本"
echo "=================================="
echo "基于Dockerfile和requirements.txt配置"
echo ""

# 检查Python版本
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "当前Python版本: $python_version"

# 检查CUDA版本
cuda_version=$(nvidia-smi | grep "CUDA Version" | awk '{print $9}' 2>/dev/null || echo "未检测到CUDA")
echo "CUDA版本: $cuda_version"

if [[ "$python_version" != "3.8" ]]; then
    echo "⚠️  警告：此脚本专为Python 3.8设计，当前版本: $python_version"
    echo "建议使用: conda create -n image_detection python=3.8"
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

# 第三步：安装CUDA 11.6版本PyTorch（基于Dockerfile配置）
echo "第三步：安装CUDA 11.6版本PyTorch..."
echo "使用Dockerfile中指定的版本..."
python3 -m pip install torch==1.12.0+cu116 torchvision==0.13.0+cu116 torchaudio==0.12.0 --extra-index-url https://download.pytorch.org/whl/cu116

# 第四步：安装requirements.txt中的基础依赖
echo "第四步：安装基础依赖包..."
python3 -m pip install blessed==1.20.0
python3 -m pip install certifi==2023.7.22
python3 -m pip install charset-normalizer==3.3.2
python3 -m pip install gpustat==1.1.1
python3 -m pip install idna==3.4
python3 -m pip install joblib==1.3.2
python3 -m pip install numpy==1.24.4
python3 -m pip install nvidia-ml-py==12.535.133
python3 -m pip install opencv-python==4.8.1.78
python3 -m pip install Pillow==10.1.0
python3 -m pip install psutil==5.9.6
python3 -m pip install requests==2.31.0
python3 -m pip install scikit-learn==1.3.2
python3 -m pip install scipy==1.10.1
python3 -m pip install six==1.16.0
python3 -m pip install threadpoolctl==3.2.0
python3 -m pip install typing_extensions==4.8.0
python3 -m pip install urllib3==2.1.0
python3 -m pip install wcwidth==0.2.10
python3 -m pip install Flask-CORS>=3.0.0

# 第五步：安装Flask（Dockerfile中单独安装）
echo "第五步：安装Web框架..."
python3 -m pip install Flask

# 第六步：安装额外依赖（图片处理可能需要）
echo "第六步：安装额外依赖..."
python3 -m pip install matplotlib
python3 -m pip install tqdm

echo "✅ 所有依赖安装完成！"
echo ""
echo "🎯 验证安装："
python3 -c "import torch; print(f'PyTorch版本: {torch.__version__}')"
python3 -c "import torch; print(f'CUDA可用: {torch.cuda.is_available()}')"
python3 -c "import torch; print(f'CUDA设备数: {torch.cuda.device_count()}')"
python3 -c "import torchvision; print(f'TorchVision版本: {torchvision.__version__}')"
python3 -c "import cv2; print(f'OpenCV版本: {cv2.__version__}')"
python3 -c "import numpy; print(f'NumPy版本: {numpy.__version__}')"
python3 -c "import PIL; print(f'Pillow版本: {PIL.__version__}')"
python3 -c "import flask; print(f'Flask版本: {flask.__version__}')"

echo ""
echo "🎯 下一步："
echo "1. 检查项目结构: ls -la ImageFornsicsOSN/"
echo "2. 启动服务: python build_api.py"
echo "3. 测试API: curl -X POST http://localhost:5000/predict"
echo ""
echo "📝 注意："
echo "   - 此脚本基于Dockerfile和requirements.txt配置"
echo "   - 使用CUDA 11.6版本的PyTorch"
echo "   - 如果遇到系统依赖问题，请手动安装libgl1-mesa-glx等包"
echo "   - 确保ImageFornsicsOSN目录下有完整的模型文件"
