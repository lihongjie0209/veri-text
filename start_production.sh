#!/bin/bash
#!/bin/bash

#     # 使用Gunicorn启动
    exec gunicorn \
        --config gunicorn.conf.py \
        wsgi:app本
# 支持环境变量配置和多种运行模式

set -e

# 默认环境变量
export HOST=${HOST:-"0.0.0.0"}
export PORT=${PORT:-"8000"}
export WORKERS=${WORKERS:-"4"}
export LOG_LEVEL=${LOG_LEVEL:-"info"}
export DEBUG=${DEBUG:-"false"}

# 检查运行模式
PRODUCTION=${PRODUCTION:-"true"}

if [ "$PRODUCTION" = "true" ]; then
    echo "🚀 启动生产模式 (Gunicorn)"
    echo "配置信息:"
    echo "  地址: $HOST:$PORT"
    echo "  工作进程: $WORKERS"
    echo "  日志级别: $LOG_LEVEL"
    echo "  调试模式: $DEBUG"
    echo "----------------------------------------"
    
    # 使用Gunicorn启动
    exec gunicorn 
        --config gunicorn.conf.py 
        --bind $HOST:$PORT 
        --workers $WORKERS 
        --log-level $LOG_LEVEL 
        src.main:app
else
    echo "🔧 启动开发模式 (Uvicorn)"
    echo "配置信息:"
    echo "  地址: $HOST:$PORT"
    echo "  调试模式: $DEBUG"
    echo "----------------------------------------"
    
    # 使用Uvicorn启动（开发模式）
    exec uvicorn 
        src.main:app 
        --host $HOST 
        --port $PORT 
        --log-level $(echo $LOG_LEVEL | tr '[:upper:]' '[:lower:]') 
        $(if [ "$DEBUG" = "true" ]; then echo "--reload"; fi)
fi
