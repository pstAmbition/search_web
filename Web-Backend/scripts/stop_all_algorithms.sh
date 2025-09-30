#!/bin/bash

echo "🛑 停止所有算法服务..."

# 获取脚本目录和日志目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
LOGS_DIR="$BACKEND_DIR/logs"

# 优雅停止（通过PID文件）
if [ -d "$LOGS_DIR" ]; then
    for pidfile in "$LOGS_DIR"/*.pid; do
        if [ -f "$pidfile" ]; then
            pid=$(cat "$pidfile")
            service_name=$(basename "$pidfile" .pid)
            echo "停止 $service_name (PID: $pid)..."
            kill "$pid" 2>/dev/null && rm "$pidfile" && echo "✅ $service_name 已停止"
        fi
    done
fi

# 强制停止残留进程
pkill -f "python.*build_api.py" 2>/dev/null && echo "✅ 清理残留进程"

echo "🎯 所有服务已停止"
