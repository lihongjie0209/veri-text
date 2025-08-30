# 多阶段构建 - 生产级敏感词检测服务
FROM python:3.11-slim AS builder

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir --user -r requirements.txt

# 生产镜像
FROM python:3.11-slim AS production

# 创建非root用户
RUN groupadd -r veritext && useradd -r -g veritext veritext

# 设置工作目录
WORKDIR /app

# 安装运行时依赖
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 从构建阶段复制Python包
COPY --from=builder /root/.local /home/veritext/.local

# 复制应用代码
COPY --chown=veritext:veritext . .

# 设置Python路径
ENV PATH=/home/veritext/.local/bin:$PATH
ENV PYTHONPATH=/app

# 创建必要的目录
RUN mkdir -p /app/logs /app/data && \
    chown -R veritext:veritext /app

# 切换到非root用户
USER veritext

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/api/v1/health/ || exit 1

# 暴露端口
EXPOSE ${PORT:-8000}

# 设置环境变量
ENV PYTHONPATH=/app
ENV PRODUCTION=true

# Gunicorn配置环境变量
ENV GUNICORN_BIND=0.0.0.0:8000
ENV GUNICORN_WORKERS=4
ENV GUNICORN_WORKER_CLASS=uvicorn.workers.UvicornWorker
ENV GUNICORN_TIMEOUT=30
ENV GUNICORN_KEEPALIVE=2
ENV GUNICORN_MAX_REQUESTS=1000
ENV GUNICORN_ACCESS_LOGFILE=-
ENV GUNICORN_ERROR_LOGFILE=-

# 启动命令 - 使用环境变量配置Gunicorn
CMD ["sh", "-c", "gunicorn --bind ${GUNICORN_BIND} --workers ${GUNICORN_WORKERS} --worker-class ${GUNICORN_WORKER_CLASS} --timeout ${GUNICORN_TIMEOUT} --keep-alive ${GUNICORN_KEEPALIVE} --max-requests ${GUNICORN_MAX_REQUESTS} --access-logfile ${GUNICORN_ACCESS_LOGFILE} --error-logfile ${GUNICORN_ERROR_LOGFILE} src.main:app"]
