#!/bin/bash

# 算法模块统一启动脚本
echo "🚀 启动所有算法模块..."

# 初始化conda
source /home/lihr/anaconda3/etc/profile.d/conda.sh

# 定义算法模块配置：模块名->端口
declare -A ALGORITHMS=(
    ["text_detection"]="5011"
    ["image_detection"]="5013" 
    ["audio_video_detection"]="5014"
    ["entity_identification"]="5016"
    ["multimodal_detection"]="5017"
)

# 创建日志目录（包含PID文件）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
LOGS_DIR="$BACKEND_DIR/logs"

mkdir -p "$LOGS_DIR"

# 停止之前可能运行的服务
echo "🛑 停止现有服务..."
pkill -f "python.*build_api.py" 2>/dev/null || true
sleep 2

# 启动每个算法模块
for algorithm in "${!ALGORITHMS[@]}"; do
    port=${ALGORITHMS[$algorithm]}
    env_name="${algorithm}"
    
    echo "📡 启动 $algorithm 服务 (端口: $port, 环境: $env_name)..."
    
    # 设置工作目录
    if [ "$algorithm" = "multimodal_detection" ]; then
        work_dir="$BACKEND_DIR/algorithms/multimodal_detection/test_api"
    else
        work_dir="$BACKEND_DIR/algorithms/${algorithm}"
    fi
    
    # 在新的bash子进程中启动服务（避免环境变量冲突）
    (
        # 激活conda环境
        conda activate "$env_name" || {
            echo "❌ 无法激活环境: $env_name"
            exit 1
        }
        
        # 切换到工作目录
        cd "$work_dir" || {
            echo "❌ 无法切换到目录: $work_dir"
            exit 1
        }
        
        # 检查启动文件是否存在
        if [ ! -f "build_api.py" ]; then
            echo "❌ 启动文件不存在: $work_dir/build_api.py"
            exit 1
        fi
        
        # 启动服务并记录PID到logs目录
        python build_api.py > "$LOGS_DIR/${algorithm}.log" 2>&1 &
        echo $! > "$LOGS_DIR/${algorithm}.pid"
        
        echo "✅ $algorithm 服务已启动 (PID: $!, 端口: $port)"
    ) &
    
    # 给每个服务启动一点间隔
    sleep 1
done

# 等待所有后台进程完成
wait

echo ""
echo "🎉 所有算法模块启动完成！"
echo "⏳ 等待服务初始化（模型加载到GPU）..."

# 智能健康检查函数
check_services_health() {
    local all_healthy=true
    local failed_services=()
    
    for algorithm in "${!ALGORITHMS[@]}"; do
        port=${ALGORITHMS[$algorithm]}
        if curl -s --connect-timeout 3 http://localhost:$port/health >/dev/null 2>&1; then
            echo "  ✅ $algorithm (端口 $port): 运行正常"
        else
            echo "  ⚠️  $algorithm (端口 $port): 服务异常或健康检查接口不存在"
            all_healthy=false
            failed_services+=("$algorithm")
        fi
    done
    
    if [ "$all_healthy" = true ]; then
        return 0  # 所有服务都正常
    else
        echo "  🔄 异常服务: ${failed_services[*]}"
        return 1  # 有服务异常
    fi
}

# 进行3轮健康检查，每轮间隔5秒
echo ""
echo "📊 服务健康检查（共3轮，每轮间隔5秒）："

for round in 1 2 3; do
    echo ""
    echo "🔍 第 $round 轮检查："
    
    if check_services_health; then
        echo ""
        echo "🎉 所有服务运行正常！"
        break
    else
        if [ $round -lt 3 ]; then
            echo ""
            echo "⏳ 等待5秒后进行下一轮检查..."
            sleep 5
        else
            echo ""
            echo "⚠️  经过3轮检查，仍有服务异常，但继续运行..."
            echo "💡 提示：可以稍后使用 'bash ./scripts/check_services.sh' 再次检查"
        fi
    fi
done

echo ""
echo "🔧 管理命令："
echo "  查看日志:    tail -f $LOGS_DIR/*.log"
echo "  停止所有服务: bash ./scripts/stop_all_algorithms.sh"
echo "  查看进程:    ps aux | grep 'python.*build_api.py'"
echo "  检查状态:    bash ./scripts/check_services.sh"
echo "  日志位置:    $LOGS_DIR"
