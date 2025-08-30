# VeriText - 敏感词检测服务

[![CI Build](https://github.com/lihongjie0209/veri-text/actions/workflows/ci-build.yml/badge.svg)](https://github.com/lihongjie0209/veri-text/actions/workflows/ci-build.yml)
[![Docker Build](https://github.com/lihongjie0209/veri-text/actions/workflows/docker-build.yml/badge.svg)](https://github.com/lihongjie0209/veri-text/actions/workflows/docker-build.yml)
[![Docker Hub](https://img.shields.io/docker/v/lihongjie0209/veri-text?label=docker&logo=docker)](https://hub.docker.com/r/lihongjie0209/veri-text)

一个高性能的企业级敏感词检测API服务，支持动态配置、智能仲裁算法和完整的CI/CD流水线。

## ✨ 核心特性

- 🚀 **高性能**: FastAPI + Gunicorn，支持多进程并发
- 🧠 **智能仲裁**: 贪心算法结果合并，支持动态权重配置
- 🔧 **动态配置**: YAML配置文件，支持热重载和环境变量
- 🐳 **容器化**: Docker多阶段构建，生产就绪
- 🔄 **CI/CD**: GitHub Actions自动化测试和发布
- 🎯 **多种检测模式**: 规则匹配、语义检测、混合模式
- 📊 **完整监控**: 健康检查、请求追踪、结构化日志
- 🌐 **Web界面**: 直观的检测界面和API文档

## 🚀 快速启动

### 方式一：Docker 部署（推荐）

```bash
# 拉取最新镜像
docker pull lihongjie0209/veri-text:latest

# 运行容器
docker run -d \
  --name veri-text \
  -p 8000:8000 \
  -e GUNICORN_WORKERS=4 \
  -e GUNICORN_LOG_LEVEL=info \
  lihongjie0209/veri-text:latest

# 验证服务
curl http://localhost:8000/api/v1/health/
```

### 方式二：本地开发

```bash
# 克隆项目
git clone https://github.com/lihongjie0209/veri-text.git
cd veri-text

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境 (Windows)
.venv\Scripts\activate
# 激活虚拟环境 (Unix/Linux/macOS)  
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
python start_server.py --port 8888 --debug
```

## 🔧 配置说明

### Docker 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `GUNICORN_BIND` | 绑定地址 | 0.0.0.0:8000 |
| `GUNICORN_WORKERS` | 工作进程数 | 4 |
| `GUNICORN_WORKER_CLASS` | 工作进程类型 | uvicorn.workers.UvicornWorker |
| `GUNICORN_LOG_LEVEL` | 日志级别 | info |
| `GUNICORN_TIMEOUT` | 超时时间 | 120 |
| `GUNICORN_KEEPALIVE` | 保活时间 | 2 |
| `GUNICORN_MAX_REQUESTS` | 最大请求数 | 1000 |
| `GUNICORN_PRELOAD` | 预加载应用 | true |

### YAML 动态配置

项目使用 `config/sensitive_words.yaml` 进行动态配置：

```yaml
# 检测权重配置 (70-100)
detection_weights:
  political: 85      # 政治敏感
  pornographic: 90   # 色情内容  
  violent: 80        # 暴力内容
  terrorism: 95      # 恐怖主义
  drugs: 85         # 毒品相关
  gambling: 75      # 赌博相关
  fraud: 80         # 欺诈相关
  spam: 70          # 垃圾信息

# 词库配置
wordlists:
  political:
    file: "political.txt"
    enabled: true
  pornographic:
    file: "pornographic.txt" 
    enabled: true
  # ... 更多配置
```

### 便捷启动脚本

#### Windows (start.bat)
```cmd
start.bat          # 默认模式
start.bat dev      # 开发模式 (端口8080)
start.bat prod     # 生产模式 (端口80)
start.bat test     # 测试模式 (端口9000)
```

#### Unix/Linux/macOS (start.sh)
```bash
./start.sh         # 默认模式
./start.sh dev     # 开发模式
./start.sh prod    # 生产模式  
./start.sh test    # 测试模式
```

## 📚 API 使用指南

### Web 界面
- 检测界面: http://localhost:8000
- API文档: http://localhost:8000/docs  
- 健康检查: http://localhost:8000/api/v1/health/

### API 端点

#### 敏感词检测
```bash
curl -X POST "http://localhost:8000/api/v1/detect/" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "这是一个测试文本",
    "config": {
      "detection_mode": "rule",
      "categories": ["political", "pornographic"],
      "return_positions": true,
      "strictness_level": "standard"
    }
  }'
```

**响应示例：**
```json
{
  "success": true,
  "data": {
    "is_sensitive": false,
    "risk_level": "low", 
    "categories": [],
    "hits": [],
    "summary": {
      "total_hits": 0,
      "processing_time_ms": 15.2,
      "algorithm": "greedy_merge"
    }
  },
  "request_id": "abc123"
}
```

#### 健康检查
```bash
curl "http://localhost:8000/api/v1/health/"
```

#### 配置重载
```bash
# 重载规则配置
curl -X POST "http://localhost:8000/api/v1/reload/rules"

# 重载词库配置  
curl -X POST "http://localhost:8000/api/v1/reload/wordlists"
```

## 🧠 智能检测算法

### 贪心仲裁算法
项目实现了先进的贪心算法进行结果仲裁，支持：

- **最大匹配优先**: 优先选择覆盖文本最多的匹配结果
- **动态权重**: 基于YAML配置的类别权重 (70-100分)
- **重叠处理**: 智能处理重叠匹配，避免重复计分
- **多层排序**: 权重→长度→位置的复合排序策略

### 检测模式

| 模式 | 说明 | 使用场景 |
|------|------|----------|
| `rule` | 纯规则匹配 | 高精度场景 |
| `semantic` | 语义检测 | 复杂语境理解 |
| `hybrid` | 混合模式 | 平衡精度和召回 |

### 敏感词类别

| 类别 | 默认权重 | 说明 |
|------|----------|------|
| `political` | 85 | 政治敏感内容 |
| `pornographic` | 90 | 色情相关内容 |
| `violent` | 80 | 暴力相关内容 |
| `terrorism` | 95 | 恐怖主义相关 |
| `drugs` | 85 | 毒品相关内容 |
| `gambling` | 75 | 赌博相关内容 |
| `fraud` | 80 | 欺诈相关内容 |
| `spam` | 70 | 垃圾广告信息 |

## 🐳 Docker 部署

### 生产环境部署

```bash
# 创建配置目录
mkdir -p ./config ./data

# 自定义配置（可选）
cp config/sensitive_words.yaml ./config/

# 运行生产容器
docker run -d \
  --name veri-text-prod \
  -p 8000:8000 \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/data:/app/data \
  -e GUNICORN_WORKERS=8 \
  -e GUNICORN_LOG_LEVEL=warn \
  --restart unless-stopped \
  lihongjie0209/veri-text:latest
```

### Docker Compose

```yaml
version: '3.8'
services:
  veri-text:
    image: lihongjie0209/veri-text:latest
    container_name: veri-text
    ports:
      - "8000:8000"
    environment:
      - GUNICORN_WORKERS=4
      - GUNICORN_LOG_LEVEL=info
    volumes:
      - ./config:/app/config
      - ./data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health/"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### 镜像版本

| 标签 | 说明 | 使用场景 |
|------|------|----------|
| `latest` | 最新稳定版 | 生产环境 |
| `v1.0.x` | 具体版本 | 版本锁定 |
| `main` | 开发版本 | 测试环境 |

## 📊 监控和日志

### 健康检查
```bash
# 基础健康检查
curl http://localhost:8000/api/v1/health/

# 响应示例
{
  "status": "healthy",
  "version": "1.0.0", 
  "timestamp": "2025-08-30T05:22:44.832590Z",
  "uptime_seconds": 125.5,
  "system": {
    "cpu_percent": 15.2,
    "memory_percent": 45.8
  }
}
```

### 结构化日志
```json
{
  "timestamp": "2025-08-30T05:22:40.742212",
  "level": "INFO", 
  "logger": "veri_text",
  "message": "请求处理完成",
  "module": "main",
  "function": "add_request_id",
  "line": 91,
  "request_id": "fdf8f9df-2fe0-4f32-b134-c3658f945e58",
  "processing_time_ms": 15.2
}
```

### 性能指标
- **请求ID追踪**: 每个请求唯一标识符
- **处理时间**: 毫秒级性能监控  
- **并发控制**: 支持高并发请求处理
- **资源监控**: CPU和内存使用率监控

## 🔄 CI/CD 流水线

### GitHub Actions

项目配置了完整的CI/CD流水线：

#### CI构建流水线 (`.github/workflows/ci-build.yml`)
- **触发条件**: 代码推送到任意分支
- **测试内容**: 
  - 代码语法检查
  - 依赖安装测试
  - Docker镜像构建
  - 健康检查测试
  - 基础功能测试

#### Docker发布流水线 (`.github/workflows/docker-build.yml`)  
- **触发条件**: 推送版本标签 (`v*`)
- **发布内容**:
  - 多平台构建 (linux/amd64, linux/arm64)
  - 自动化测试验证
  - 发布到Docker Hub
  - 版本标签管理

### 自动化测试

```bash
# 本地运行测试
pytest tests/ -v

# 集成测试
python -m pytest tests/integration/ -v

# 性能测试  
python -m pytest tests/performance/ -v
```

## 🛠️ 开发指南

### 项目结构
```
veri-text/
├── src/                    # 源代码
│   ├── api/               # API路由
│   ├── core/              # 核心配置
│   ├── models/            # 数据模型
│   ├── services/          # 业务服务
│   └── utils/             # 工具函数
├── config/                # 配置文件
├── tests/                 # 测试文件
├── .github/workflows/     # CI/CD配置
├── Dockerfile            # Docker构建
└── requirements.txt      # 依赖列表
```

### 添加新词库
1. 在 `src/data/wordlists/` 添加词库文件
2. 更新 `config/sensitive_words.yaml` 配置
3. 重启服务或调用重载API

### 自定义检测算法
1. 继承 `BaseDetector` 类
2. 实现检测逻辑
3. 在服务中注册新检测器

### 扩展API
1. 在 `src/api/routes/` 添加新路由
2. 定义请求/响应模型
3. 更新API文档

## 📋 故障排除

### 常见问题

#### Docker 相关
```bash
# 检查容器状态
docker ps -a

# 查看容器日志
docker logs veri-text

# 重启容器
docker restart veri-text

# 清理无用镜像
docker system prune -f
```

#### 端口冲突
```bash
# 检查端口占用
netstat -ano | findstr :8000    # Windows
lsof -i :8000                   # Unix/Linux

# 使用其他端口
docker run -p 8001:8000 lihongjie0209/veri-text:latest
```

#### 配置问题
```bash
# 验证配置文件
python -c "import yaml; yaml.safe_load(open('config/sensitive_words.yaml'))"

# 重载配置
curl -X POST http://localhost:8000/api/v1/reload/rules
```

#### 性能调优
```bash
# 增加工作进程
docker run -e GUNICORN_WORKERS=8 lihongjie0209/veri-text:latest

# 调整内存限制
docker run --memory=2g lihongjie0209/veri-text:latest
```

## 🤝 贡献指南

### 开发环境设置
```bash
# 克隆项目
git clone https://github.com/lihongjie0209/veri-text.git
cd veri-text

# 安装开发依赖
pip install -r requirements-dev.txt

# 设置pre-commit hooks
pre-commit install

# 运行测试
pytest tests/ -v
```

### 提交规范
```bash
# 功能开发
git commit -m "feat: 添加新的检测算法"

# 问题修复  
git commit -m "fix: 修复配置文件加载问题"

# 文档更新
git commit -m "docs: 更新API使用说明"

# 性能优化
git commit -m "perf: 优化检测算法性能"
```

### 发布流程
1. 创建feature分支开发
2. 提交PR并通过CI检查
3. 合并到main分支
4. 创建版本标签触发发布

## 📄 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE) 文件。

## 🔗 相关链接

- [GitHub Repository](https://github.com/lihongjie0209/veri-text)
- [Docker Hub](https://hub.docker.com/r/lihongjie0209/veri-text)
- [API文档](http://localhost:8000/docs)
- [问题反馈](https://github.com/lihongjie0209/veri-text/issues)

## 📈 版本历史

### v1.0.3 (最新)
- 🔧 修复GitHub Actions健康检查路径问题
- 🐛 解决FastAPI重定向导致的307状态码问题
- 📚 更新文档和使用说明

### v1.0.2  
- 🚀 完善CI/CD流水线
- 🐳 优化Docker镜像构建
- 📊 增强健康检查功能

### v1.0.1
- 🧠 实现贪心仲裁算法
- 🔧 支持YAML动态配置
- ⚡ 性能优化和稳定性提升

### v1.0.0
- 🎉 首个稳定版本发布
- 🚀 基础敏感词检测功能
- 🌐 Web界面和API文档

---

> 💡 **提示**: 如果您在使用过程中遇到问题，请查看 [故障排除](#-故障排除) 部分或提交 [Issue](https://github.com/lihongjie0209/veri-text/issues)。
