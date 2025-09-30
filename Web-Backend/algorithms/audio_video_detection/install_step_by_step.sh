#!/bin/bash

# 分步安装脚本 - 基于完美运行的py38环境
# 专门为Python 3.8环境设计，支持CUDA 11.8

echo "🚀 音视频检测项目分步安装脚本"
echo "=================================="
echo "基于完美运行的py38环境配置"
echo ""

# 检查Python版本
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "当前Python版本: $python_version"

# 检查CUDA版本
cuda_version=$(nvidia-smi | grep "CUDA Version" | awk '{print $9}' 2>/dev/null || echo "未检测到CUDA")
echo "CUDA版本: $cuda_version"

if [[ "$python_version" != "3.8" ]]; then
    echo "⚠️  警告：此脚本专为Python 3.8设计，当前版本: $python_version"
    echo "建议使用: conda create -n audio_video_detection python=3.8"
fi

# 升级pip
echo "升级pip..."
python3 -m pip install --upgrade pip

# 第一步：清理现有PyTorch包
echo "第一步：清理现有PyTorch包..."
python3 -m pip uninstall -y torch torchvision torchaudio

# 第二步：安装核心科学计算包（使用py38环境的确切版本）
echo "第二步：安装核心科学计算包..."
python3 -m pip install numpy==1.22.4
python3 -m pip install scipy==1.7.3
python3 -m pip install scikit-learn==1.0.2

# 第三步：安装CUDA 11.8版本PyTorch（基于完美运行环境）
echo "第三步：安装CUDA 11.8版本PyTorch..."
echo "使用与py38环境完全相同的版本..."
python3 -m pip install torch==2.4.1+cu118 torchvision==0.19.1+cu118 torchaudio==2.4.1+cu118 --extra-index-url https://download.pytorch.org/whl/cu118

# 第四步：安装音频处理包
echo "第四步：安装音频处理包..."
python3 -m pip install librosa==0.9.2
python3 -m pip install soundfile==0.11.0
python3 -m pip install audioread==3.0.1

# 第五步：安装深度学习模型
echo "第五步：安装深度学习模型..."
python3 -m pip install transformers==4.24.0
python3 -m pip install tokenizers==0.11.6
python3 -m pip install huggingface-hub==0.34.4

# 第六步：安装计算机视觉包
echo "第六步：安装计算机视觉包..."
python3 -m pip install opencv-python==4.6.0.66
python3 -m pip install Pillow==8.4.0
python3 -m pip install dlib==19.24.0

# 第七步：安装人脸识别包
echo "第七步：安装人脸识别包..."
python3 -m pip install face-recognition==1.3.0
python3 -m pip install face-recognition-models==0.3.0

# 第八步：安装预训练模型支持
echo "第八步：安装预训练模型支持..."
python3 -m pip install pretrainedmodels==0.7.4
python3 -m pip install h5py==2.10.0

# 第九步：安装Web框架
echo "第九步：安装Web框架..."
python3 -m pip install Flask==2.2.5
python3 -m pip install Flask-CORS==3.0.10
python3 -m pip install Werkzeug==2.2.3
python3 -m pip install Jinja2==3.1.3

# 第十步：安装数据处理工具
echo "第十步：安装数据处理工具..."
python3 -m pip install pandas==1.4.4
python3 -m pip install tqdm==4.64.1
python3 -m pip install requests==2.28.2
python3 -m pip install PyYAML==6.0.2

# 第十一步：安装特殊依赖
echo "第十一步：安装特殊依赖..."
python3 -m pip install safetensors==0.5.3
python3 -m pip install accelerate==0.20.3

# 第十二步：安装额外依赖
echo "第十二步：安装额外依赖..."
python3 -m pip install typing-extensions==4.8.0
python3 -m pip install packaging==25.0
python3 -m pip install filelock==3.16.1
python3 -m pip install fsspec==2025.3.0

# 第十三步：安装音频处理辅助包
echo "第十三步：安装音频处理辅助包..."
python3 -m pip install resampy==0.4.3
python3 -m pip install pooch==1.8.2
python3 -m pip install numba==0.58.1
python3 -m pip install llvmlite==0.41.1

echo "✅ 所有依赖安装完成！"
echo ""
echo "🎯 验证安装："
python3 -c "import torch; print(f'PyTorch版本: {torch.__version__}')"
python3 -c "import torch; print(f'CUDA可用: {torch.cuda.is_available()}')"
python3 -c "import torch; print(f'CUDA设备数: {torch.cuda.device_count()}')"
python3 -c "import torchvision; print(f'TorchVision版本: {torchvision.__version__}')"
python3 -c "import transformers; print(f'Transformers版本: {transformers.__version__}')"
python3 -c "import librosa; print(f'Librosa版本: {librosa.__version__}')"
python3 -c "import safetensors; print(f'Safetensors版本: {safetensors.__version__}')"

echo ""
echo "🎯 下一步："
echo "1. 验证安装: python check_environment.py"
echo "2. 本地调试: python debug_local.py"
echo "3. 启动服务: python build_api.py"
echo ""
echo "📝 注意：此脚本基于完美运行的py38环境配置"
echo "   如果遇到问题，请检查CUDA版本兼容性"
