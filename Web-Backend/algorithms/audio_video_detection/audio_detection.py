"""
音频伪造检测模块
基于 Hemgg/Deepfake-audio-detection 预训练模型
支持音频分类和特征提取
"""

import torch
import torch.nn.functional as F
import torchaudio
import numpy as np
import os
from transformers import Wav2Vec2ForSequenceClassification, Wav2Vec2Model, Wav2Vec2FeatureExtractor
import librosa
import soundfile as sf
from typing import Dict, Tuple, Union, List


class AudioFakeDetector:
    """音频伪造检测器"""
    
    def __init__(self, model_path: str = "models/Deepfake-audio-detection"):
        """
        初始化音频检测器
        
        Args:
            model_path: 模型路径，默认从 models/Deepfake-audio-detection 加载
        """
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model_path = model_path
        
        # 加载模型
        self.classifier = None
        self.feature_extractor = None
        self.preprocessor = None
        
        try:
            self._load_models()
        except Exception as e:
            print(f"模型加载失败: {e}")
            print("请确保模型已下载到正确路径")
    
    def _load_models(self):
        """加载预训练模型"""
        print(f"正在加载音频检测模型...")
        
        try:
            # 优先尝试使用safetensors直接加载（基于用户发现的代码）
            if self._load_safetensors_direct():
                print("✅ 使用safetensors直接加载成功！")
                return
        except Exception as e:
            print(f"safetensors直接加载失败: {e}")
        
        try:
            # 备用方案1：使用HuggingFace在线模型
            print("尝试使用HuggingFace在线模型: Hemgg/Deepfake-audio-detection")
            
            # 加载分类器
            self.classifier = Wav2Vec2ForSequenceClassification.from_pretrained(
                "Hemgg/Deepfake-audio-detection",
                cache_dir="models/Deepfake-audio-detection"
            ).to(self.device)
            
            # 加载特征提取器
            self.feature_extractor = Wav2Vec2Model.from_pretrained(
                "Hemgg/Deepfake-audio-detection",
                cache_dir="models/Deepfake-audio-detection"
            ).to(self.device)
            
            # 加载预处理器
            self.preprocessor = Wav2Vec2FeatureExtractor.from_pretrained(
                "Hemgg/Deepfake-audio-detection",
                cache_dir="models/Deepfake-audio-detection"
            )
            
            # 设置为评估模式
            self.classifier.eval()
            self.feature_extractor.eval()
            
            print("✅ 音频检测模型加载成功！")
            
        except Exception as e:
            print(f"❌ HuggingFace在线模型加载失败: {e}")
            print("尝试备用方案...")
            
            # 备用方案2：尝试本地文件
            try:
                if self._try_load_local_models():
                    print("✅ 本地模型加载成功！")
                    return
            except Exception as local_e:
                print(f"❌ 本地模型也失败: {local_e}")
            
            raise Exception("无法加载音频检测模型")
    
    def _load_safetensors_direct(self):
        """使用safetensors直接加载模型（基于用户发现的代码）"""
        print("尝试使用safetensors直接加载...")
        
        try:
            from safetensors.torch import load_file
            
            # 检查safetensors文件
            safetensors_file = os.path.join(self.model_path, "model.safetensors")
            if not os.path.exists(safetensors_file):
                raise Exception("model.safetensors文件不存在")
            
            print(f"找到safetensors文件: {safetensors_file}")
            
            # 加载配置
            config_file = os.path.join(self.model_path, "config.json")
            if not os.path.exists(config_file):
                raise Exception("config.json文件不存在")
            
            # 修复：使用from_pretrained创建模型，然后替换权重
            print("正在创建模型架构...")
            
            # 创建分类器（使用from_pretrained确保架构正确）
            self.classifier = Wav2Vec2ForSequenceClassification.from_pretrained(
                self.model_path,
                local_files_only=True,
                ignore_mismatched_sizes=True
            ).to(self.device)
            
            # 创建特征提取器
            self.feature_extractor = Wav2Vec2Model.from_pretrained(
                self.model_path,
                local_files_only=True,
                ignore_mismatched_sizes=True
            ).to(self.device)
            
            # 加载预处理器
            self.preprocessor = Wav2Vec2FeatureExtractor.from_pretrained(
                self.model_path,
                local_files_only=True
            )
            
            # 设置为评估模式
            self.classifier.eval()
            self.feature_extractor.eval()
            
            print("✅ safetensors直接加载成功！")
            return True
            
        except Exception as e:
            print(f"safetensors直接加载失败: {e}")
            return False
    
    def _try_load_local_models(self):
        """尝试加载本地模型文件"""
        print("尝试加载本地模型文件...")
        
        # 检查是否有可用的本地文件
        local_files = os.listdir(self.model_path)
        print(f"本地文件: {local_files}")
        
        # 如果有pytorch_model.bin，尝试加载
        if "pytorch_model.bin" in local_files:
            return self._load_pytorch_format()
        elif "model.safetensors" in local_files:
            # 直接使用我们新的safetensors加载方法
            return self._load_safetensors_direct()
        else:
            raise Exception("本地没有可用的模型文件")
    
    def _load_pytorch_format(self):
        """加载PyTorch格式模型"""
        # 检查pytorch_model.bin是否存在
        pytorch_model_file = os.path.join(self.model_path, "pytorch_model.bin")
        if not os.path.exists(pytorch_model_file):
            raise Exception("pytorch_model.bin不存在")
        
        # 加载分类器
        self.classifier = Wav2Vec2ForSequenceClassification.from_pretrained(
            self.model_path,
            local_files_only=True
        ).to(self.device)
        
        # 加载特征提取器
        self.feature_extractor = Wav2Vec2Model.from_pretrained(
            self.model_path,
            local_files_only=True
        ).to(self.device)
        
        # 加载预处理器
        self.preprocessor = Wav2Vec2FeatureExtractor.from_pretrained(
            self.model_path,
            local_files_only=True
        )
        
        # 设置为评估模式
        self.classifier.eval()
        self.feature_extractor.eval()
        
        return True
    
    # 移除旧的safetensors加载方法，使用新的_load_safetensors_direct方法
    
    def _load_from_huggingface(self):
        """从HuggingFace下载模型"""
        print("尝试从HuggingFace下载模型...")
        
        # 加载分类器
        self.classifier = Wav2Vec2ForSequenceClassification.from_pretrained(
            "Hemgg/Deepfake-audio-detection"
        ).to(self.device)
        
        # 加载特征提取器
        self.feature_extractor = Wav2Vec2Model.from_pretrained(
            "Hemgg/Deepfake-audio-detection"
        ).to(self.device)
        
        # 加载预处理器
        self.preprocessor = Wav2Vec2FeatureExtractor.from_pretrained(
            "Hemgg/Deepfake-audio-detection"
        )
        
        # 设置为评估模式
        self.classifier.eval()
        self.feature_extractor.eval()
        
        return True
    
    def preprocess_audio_from_array(self, audio_array: np.ndarray, sample_rate: int) -> torch.Tensor:
        """
        从数组预处理音频（用于调试测试）
        
        Args:
            audio_array: 音频数组
            sample_rate: 采样率
            
        Returns:
            预处理后的音频张量
        """
        try:
            # 重采样到 16kHz
            if sample_rate != 16000:
                audio_array = librosa.resample(audio_array, orig_sr=sample_rate, target_sr=16000)
            
            # 确保音频长度合适
            if len(audio_array) < 16000:  # 少于1秒
                audio_array = np.tile(audio_array, int(16000 / len(audio_array)) + 1)
                audio_array = audio_array[:16000]
            elif len(audio_array) > 160000:  # 超过10秒
                start = (len(audio_array) - 160000) // 2
                audio_array = audio_array[start:start + 160000]
            
            # 转换为张量
            audio_tensor = torch.tensor(audio_array, dtype=torch.float32)
            
            return audio_tensor
            
        except Exception as e:
            raise Exception(f"音频数组预处理失败: {e}")
    
    def preprocess_audio(self, audio_path: str) -> torch.Tensor:
        """
        音频预处理
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            预处理后的音频张量
        """
        try:
            # 支持多种音频格式
            if audio_path.endswith(('.mp3', '.m4a', '.flac')):
                # 使用 librosa 读取
                audio, sr = librosa.load(audio_path, sr=16000)
            elif audio_path.endswith('.wav'):
                # 使用 soundfile 读取
                audio, sr = sf.read(audio_path)
                if len(audio.shape) > 1:
                    audio = audio[:, 0]  # 取第一个声道
                if sr != 16000:
                    audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)
            else:
                raise ValueError(f"不支持的音频格式: {audio_path}")
            
            # 确保音频长度合适（模型要求）
            if len(audio) < 16000:  # 少于1秒
                # 重复音频到1秒
                audio = np.tile(audio, int(16000 / len(audio)) + 1)
                audio = audio[:16000]
            elif len(audio) > 160000:  # 超过10秒
                # 截取中间部分
                start = (len(audio) - 160000) // 2
                audio = audio[start:start + 160000]
            
            # 转换为张量
            audio_tensor = torch.tensor(audio, dtype=torch.float32)
            
            return audio_tensor
            
        except Exception as e:
            raise Exception(f"音频预处理失败: {e}")
    
    def detect_fake_audio(self, audio_path: str) -> Dict:
        """
        检测音频是否为伪造
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            检测结果字典
        """
        try:
            # 预处理音频
            audio_tensor = self.preprocess_audio(audio_path)
            
            # 使用预处理器
            inputs = self.preprocessor(
                audio_tensor, 
                sampling_rate=16000, 
                return_tensors="pt"
            ).to(self.device)
            
            # 模型推理
            with torch.no_grad():
                outputs = self.classifier(**inputs)
                logits = outputs.logits
                probabilities = F.softmax(logits, dim=1)
            
            # 解析结果
            # 正确：0=伪造, 1=真实
            fake_prob = float(probabilities[0][0])
            real_prob = float(probabilities[0][1])
            
            # 确定预测结果
            if fake_prob > real_prob:
                prediction = "fake"
                confidence = fake_prob
            else:
                prediction = "real"
                confidence = real_prob
            
            return {
                "prediction": prediction,
                "confidence": confidence,
                "fake_probability": fake_prob,
                "real_probability": real_prob,
                "status": "success"
            }
            
        except Exception as e:
            return {
                "prediction": "error",
                "confidence": 0.0,
                "error": str(e),
                "status": "failed"
            }
    
    def extract_audio_embedding(self, audio_path: str) -> Dict:
        """
        提取音频特征表示
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            特征提取结果字典
        """
        try:
            # 预处理音频
            audio_tensor = self.preprocess_audio(audio_path)
            
            # 使用预处理器
            inputs = self.preprocessor(
                audio_tensor, 
                sampling_rate=16000, 
                return_tensors="pt"
            ).to(self.device)
            
            # 提取特征
            with torch.no_grad():
                features = self.feature_extractor(**inputs).last_hidden_state
                # 平均池化得到固定维度特征
                embedding = features.mean(dim=1).squeeze().cpu().numpy()
            
            return {
                "embedding": embedding.tolist(),
                "embedding_dim": len(embedding),
                "status": "success"
            }
            
        except Exception as e:
            return {
                "embedding": [],
                "embedding_dim": 0,
                "error": str(e),
                "status": "failed"
            }
    
    def get_audio_info(self, audio_path: str) -> Dict:
        """
        获取音频文件信息
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            音频信息字典
        """
        try:
            if audio_path.endswith(('.mp3', '.m4a', '.flac')):
                audio, sr = librosa.load(audio_path, sr=None)
            elif audio_path.endswith('.wav'):
                audio, sr = sf.read(audio_path)
                if len(audio.shape) > 1:
                    audio = audio[:, 0]
            else:
                raise ValueError(f"不支持的音频格式: {audio_path}")
            
            duration = len(audio) / sr
            channels = 1 if len(audio.shape) == 1 else audio.shape[1]
            
            return {
                "duration": duration,
                "sample_rate": sr,
                "channels": channels,
                "samples": len(audio),
                "format": os.path.splitext(audio_path)[1],
                "status": "success"
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "status": "failed"
            }


# 全局检测器实例
_audio_detector = None

def get_audio_detector() -> AudioFakeDetector:
    """获取音频检测器实例（单例模式）"""
    global _audio_detector
    if _audio_detector is None:
        _audio_detector = AudioFakeDetector()
    return _audio_detector

def detect_fake_audio(audio_path: str) -> Dict:
    """音频伪造检测接口函数"""
    detector = get_audio_detector()
    return detector.detect_fake_audio(audio_path)

def extract_audio_embedding(audio_path: str) -> Dict:
    """音频特征提取接口函数"""
    detector = get_audio_detector()
    return detector.extract_audio_embedding(audio_path)

def get_audio_info(audio_path: str) -> Dict:
    """音频信息获取接口函数"""
    detector = get_audio_detector()
    return detector.get_audio_info(audio_path) 