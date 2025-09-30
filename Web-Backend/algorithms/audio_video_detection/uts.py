import torch
import subprocess

def get_available_gpu(min_free_memory_mb=10480):
    # 使用nvidia-smi命令以JSON格式获取GPU信息
    smi_output = subprocess.check_output(['nvidia-smi', '--query-gpu=index,memory.free', '--format=csv,noheader,nounits'], encoding='utf-8')
    
    # 解析输出，初始化符合条件的GPU列表
    eligible_gpus = []
    
    # 分行处理nvidia-smi输出
    for line in smi_output.strip().split('\n'):
        gpu_index, free_memory = line.split(', ')
        free_memory = int(free_memory)  # 将空闲内存转换为整数
        
        # 检查空闲内存是否达到阈值
        if free_memory >= min_free_memory_mb:
            eligible_gpus.append(int(gpu_index))  # 添加符合条件的GPU编号
    
    return eligible_gpus[0]

if __name__ == '__main__':
    gpu_ids = get_available_gpu()
