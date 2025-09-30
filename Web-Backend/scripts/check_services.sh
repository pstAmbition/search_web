#!/bin/bash

echo "🔍 检查服务状态..."

# 获取脚本目录和日志目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
LOGS_DIR="$BACKEND_DIR/logs"

declare -A ALGORITHMS=(
    ["text_detection"]="5011"
    ["image_detection"]="5013"
    ["audio_video_detection"]="5014" 
    ["entity_identification"]="5016"
    ["multimodal_detection"]="5017"
)

echo "📊 服务状态："
for algorithm in "${!ALGORITHMS[@]}"; do
    port=${ALGORITHMS[$algorithm]}
    pidfile="$LOGS_DIR/${algorithm}.pid"
    
    if [ -f "$pidfile" ]; then
        pid=$(cat "$pidfile")
        if ps -p "$pid" >/dev/null 2>&1; then
            echo "  ✅ $algorithm (端口 $port): 运行中 (PID: $pid)"
        else
            echo "  ❌ $algorithm (端口 $port): PID文件存在但进程不存在"
        fi
    else
        echo "  ⚠️  $algorithm (端口 $port): 未运行 (无PID文件)"
    fi
done

echo ""
echo "🌐 网络连通性检查："
for algorithm in "${!ALGORITHMS[@]}"; do
    port=${ALGORITHMS[$algorithm]}
    if curl -s --connect-timeout 3 http://localhost:$port/health >/dev/null 2>&1; then
        echo "  ✅ $algorithm (端口 $port): 服务响应正常"
    else
        echo "  ❌ $algorithm (端口 $port): 服务无响应"
    fi
done
