"""
Gunicorn配置文件 - 生产环境优化
"""
import os
import multiprocessing

# 基本配置
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
workers = int(os.getenv('WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = int(os.getenv('WORKER_CONNECTIONS', '1000'))

# 性能配置
max_requests = int(os.getenv('MAX_REQUESTS', '1000'))
max_requests_jitter = int(os.getenv('MAX_REQUESTS_JITTER', '100'))
preload_app = os.getenv('PRELOAD_APP', 'true').lower() == 'true'
keepalive = int(os.getenv('KEEPALIVE', '2'))

# 超时配置
timeout = int(os.getenv('TIMEOUT', '30'))
graceful_timeout = int(os.getenv('GRACEFUL_TIMEOUT', '30'))

# 日志配置
loglevel = os.getenv('LOG_LEVEL', 'info').lower()
accesslog = os.getenv('ACCESS_LOG', '-')  # - 表示stdout
errorlog = os.getenv('ERROR_LOG', '-')    # - 表示stderr
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# 进程配置
pidfile = os.getenv('PID_FILE', '/tmp/gunicorn.pid')
user = os.getenv('USER', None)
group = os.getenv('GROUP', None)

# SSL配置（可选）
keyfile = os.getenv('SSL_KEYFILE', None)
certfile = os.getenv('SSL_CERTFILE', None)

# 开发模式配置
if os.getenv('DEBUG', 'false').lower() == 'true':
    reload = True
    workers = 1
    loglevel = 'debug'

print(f"Gunicorn配置:")
print(f"  绑定地址: {bind}")
print(f"  工作进程: {workers}")
print(f"  工作类: {worker_class}")
print(f"  日志级别: {loglevel}")
print(f"  预加载应用: {preload_app}")
