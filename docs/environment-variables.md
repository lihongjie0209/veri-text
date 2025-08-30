# 敏感词检测服务 - 环境变量配置文档

## Gunicorn 服务器配置

### 基础配置

| 环境变量 | 默认值 | 说明 | 示例 |
|---------|--------|------|------|
| `GUNICORN_BIND` | `0.0.0.0:8000` | 绑定地址和端口 | `0.0.0.0:8080`, `127.0.0.1:8000` |
| `GUNICORN_WORKERS` | `4` | 工作进程数量 | `1`, `2`, `4`, `8` |
| `GUNICORN_WORKER_CLASS` | `uvicorn.workers.UvicornWorker` | 工作进程类型 | `uvicorn.workers.UvicornWorker` |

### 性能配置

| 环境变量 | 默认值 | 说明 | 示例 |
|---------|--------|------|------|
| `GUNICORN_TIMEOUT` | `30` | 工作进程超时时间（秒） | `30`, `60`, `120` |
| `GUNICORN_KEEPALIVE` | `2` | Keep-Alive 连接保持时间（秒） | `2`, `5`, `10` |
| `GUNICORN_MAX_REQUESTS` | `1000` | 工作进程最大请求数 | `500`, `1000`, `2000` |

### 日志配置

| 环境变量 | 默认值 | 说明 | 示例 |
|---------|--------|------|------|
| `GUNICORN_ACCESS_LOGFILE` | `-` | 访问日志文件路径 | `-` (标准输出), `/app/logs/access.log` |
| `GUNICORN_ERROR_LOGFILE` | `-` | 错误日志文件路径 | `-` (标准输出), `/app/logs/error.log` |

## 应用配置

| 环境变量 | 默认值 | 说明 | 示例 |
|---------|--------|------|------|
| `PRODUCTION` | `true` | 生产环境标识 | `true`, `false` |
| `LOG_LEVEL` | `INFO` | 日志级别 | `DEBUG`, `INFO`, `WARNING`, `ERROR` |

## 使用示例

### 1. 开发环境配置
```bash
docker run -d \
  -p 8080:8000 \
  -e GUNICORN_WORKERS=1 \
  -e GUNICORN_TIMEOUT=60 \
  -e LOG_LEVEL=DEBUG \
  veri-text:latest
```

### 2. 生产环境配置
```bash
docker run -d \
  -p 8888:8000 \
  -e GUNICORN_WORKERS=4 \
  -e GUNICORN_TIMEOUT=30 \
  -e GUNICORN_MAX_REQUESTS=1000 \
  -e LOG_LEVEL=INFO \
  veri-text:latest
```

### 3. 高性能配置
```bash
docker run -d \
  -p 8888:8000 \
  -e GUNICORN_WORKERS=8 \
  -e GUNICORN_TIMEOUT=60 \
  -e GUNICORN_KEEPALIVE=5 \
  -e GUNICORN_MAX_REQUESTS=2000 \
  veri-text:latest
```

### 4. 自定义端口配置
```bash
docker run -d \
  -p 9090:9090 \
  -e GUNICORN_BIND=0.0.0.0:9090 \
  -e GUNICORN_WORKERS=2 \
  veri-text:latest
```

### 5. 文件日志配置
```bash
docker run -d \
  -p 8888:8000 \
  -e GUNICORN_ACCESS_LOGFILE=/app/logs/access.log \
  -e GUNICORN_ERROR_LOGFILE=/app/logs/error.log \
  -v $(pwd)/logs:/app/logs \
  veri-text:latest
```

## 性能调优建议

### 工作进程数量（GUNICORN_WORKERS）
- **CPU密集型应用**: `(2 × CPU核心数) + 1`
- **IO密集型应用**: `(4 × CPU核心数) + 1`
- **推荐起始值**: 4个工作进程
- **最大建议值**: 不超过16个工作进程

### 超时时间（GUNICORN_TIMEOUT）
- **轻量级请求**: 30秒
- **复杂检测**: 60-120秒
- **批量处理**: 300秒以上

### 最大请求数（GUNICORN_MAX_REQUESTS）
- **防止内存泄漏**: 1000-2000请求后重启worker
- **高频应用**: 500-1000请求
- **低频应用**: 可设置更高值

## 监控和健康检查

服务提供健康检查端点：
```
GET /api/v1/health
```

响应示例：
```json
{
  "success": true,
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 3600,
  "components": {
    "rule_detector": {
      "loaded": true,
      "enabled_wordlists": 8,
      "total_words": 50000
    }
  }
}
```

## 故障排除

### 1. 端口绑定失败
检查端口是否被占用：
```bash
netstat -an | grep :8000
```

### 2. 工作进程启动失败
检查内存是否充足：
```bash
docker stats veri-text-container
```

### 3. 连接超时
增加超时时间：
```bash
-e GUNICORN_TIMEOUT=120
```

### 4. 性能问题
- 增加工作进程数量
- 优化最大请求数设置
- 检查系统资源使用情况
