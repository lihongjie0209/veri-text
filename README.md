# 敏感词检测服务

一个高性能的敏感词检测API服务，支持规则匹配和语义检测两种模式。

## 快速启动

### 1. 环境准备

```bash
# 创建虚拟环境
uv venv

# 激活虚拟环境 (Windows)
.venv\Scripts\activate

# 激活虚拟环境 (Unix/Linux/macOS)
source .venv/bin/activate

# 安装依赖
uv pip install -r requirements.txt
```

### 2. 启动服务

#### 使用默认配置
```bash
python start_server.py
```
默认运行在 http://127.0.0.1:18085

#### 使用自定义端口
```bash
python start_server.py --port 8888
```

#### 启用调试模式
```bash
python start_server.py --port 8888 --debug --log-level DEBUG
```

#### 生产环境配置
```bash
python start_server.py --port 80 --host 0.0.0.0 --workers 4
```

#### 启用语义检测
```bash
python start_server.py --semantic-detection --model-path ./models/bert
```

### 3. 使用便捷脚本

#### Windows
```cmd
# 默认模式
start.bat

# 开发模式 (端口8080, 调试开启)
start.bat dev

# 生产模式 (端口80, 多进程)
start.bat prod

# 测试模式 (端口9000, 语义检测)
start.bat test

# 查看帮助
start.bat help
```

#### Unix/Linux/macOS
```bash
# 默认模式
./start.sh

# 开发模式
./start.sh dev

# 生产模式
./start.sh prod

# 测试模式
./start.sh test

# 查看帮助
./start.sh help
```

## 配置选项

### 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--host` | 监听地址 | 127.0.0.1 |
| `--port` | 监听端口 | 18085 |
| `--workers` | 工作进程数 | 1 |
| `--debug` | 启用调试模式 | False |
| `--api-prefix` | API前缀 | /api/v1 |
| `--docs-url` | 文档URL | /docs |
| `--max-text-length` | 文本最大长度 | 10000 |
| `--detection-mode` | 默认检测模式 | hybrid |
| `--strictness-level` | 默认严格程度 | standard |
| `--semantic-detection` | 启用语义检测 | False |
| `--model-path` | ML模型路径 | "" |
| `--semantic-threshold` | 语义检测阈值 | 0.8 |
| `--data-dir` | 数据目录 | src/data |
| `--wordlist-dir` | 词库目录 | src/data/wordlists |
| `--model-dir` | 模型目录 | src/data/models |
| `--log-level` | 日志级别 | INFO |
| `--log-file` | 日志文件路径 | "" |
| `--max-concurrent-requests` | 最大并发请求数 | 100 |
| `--request-timeout` | 请求超时时间（秒） | 30 |

### 环境变量

所有配置项都支持环境变量，格式为 `VERI_TEXT_` + 配置名（大写，下划线分隔）：

```bash
export VERI_TEXT_PORT=8080
export VERI_TEXT_DEBUG=true
export VERI_TEXT_SEMANTIC_DETECTION_ENABLED=true
```

### .env 文件

在项目根目录创建 `.env` 文件：

```env
VERI_TEXT_PORT=8080
VERI_TEXT_DEBUG=true
VERI_TEXT_HOST=0.0.0.0
VERI_TEXT_SEMANTIC_DETECTION_ENABLED=true
VERI_TEXT_LOG_LEVEL=DEBUG
```

## API使用

### Web界面
访问 http://127.0.0.1:端口号 使用Web界面进行检测

### API文档
访问 http://127.0.0.1:端口号/docs 查看交互式API文档

### API示例

#### 基本检测
```bash
curl -X POST "http://127.0.0.1:8888/api/v1/detect/" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "这是一个测试文本",
    "config": {
      "detection_mode": "rule_based",
      "categories": ["political", "pornographic"],
      "return_positions": true
    }
  }'
```

#### 健康检查
```bash
curl "http://127.0.0.1:8888/api/v1/health/"
```

## 检测模式

1. **rule_based**: 仅使用规则匹配
2. **semantic**: 仅使用语义检测（需要模型）
3. **hybrid**: 规则匹配 + 语义检测（推荐）

## 支持的敏感词类别

- `political`: 政治敏感
- `pornographic`: 色情内容
- `violent`: 暴力内容
- `spam`: 广告垃圾
- `privacy`: 隐私信息

## 日志和监控

### 日志级别
- `DEBUG`: 详细调试信息
- `INFO`: 一般信息（默认）
- `WARNING`: 警告信息
- `ERROR`: 错误信息

### 日志格式
支持JSON格式日志，便于日志收集和分析。

## 性能调优

### 生产环境建议
```bash
python start_server.py \
  --port 80 \
  --host 0.0.0.0 \
  --workers 4 \
  --max-concurrent-requests 200 \
  --request-timeout 60
```

### 开发环境建议
```bash
python start_server.py \
  --port 8888 \
  --debug \
  --log-level DEBUG
```

## 故障排除

### 端口被占用
```bash
# 尝试其他端口
python start_server.py --port 8889
```

### 权限问题（低端口）
```bash
# 使用高端口号 (>1024)
python start_server.py --port 8080
```

### 查看详细日志
```bash
python start_server.py --debug --log-level DEBUG
```

## 开发和扩展

### 添加自定义词库
在 `src/data/wordlists/` 目录下添加对应类别的文本文件。

### 启用语义检测
1. 下载预训练模型到 `src/data/models/` 目录
2. 使用 `--semantic-detection --model-path` 参数启动

### 自定义配置
修改 `src/core/config.py` 文件添加新的配置项。
