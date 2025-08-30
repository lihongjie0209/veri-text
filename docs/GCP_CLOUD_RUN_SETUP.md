# GCP Cloud Run 自动部署配置指南

本文档介绍如何配置GitHub Actions自动部署到GCP Cloud Run的完整流程。

## 🚀 概述

当新版本标签推送到GitHub时，CI/CD流水线将自动：
1. 构建并推送Docker镜像到Docker Hub
2. 部署最新镜像到GCP Cloud Run
3. 执行健康检查和功能测试
4. 提供部署后的服务URL和测试命令

## 📋 前置条件

- 已有GCP账户和项目
- 已启用Cloud Run API
- 已有GitHub仓库管理员权限

## 🔧 GCP设置

### 1. 创建服务账户

```bash
# 设置项目ID
export PROJECT_ID="your-project-id"
export SERVICE_ACCOUNT_NAME="github-actions-cloud-run"

# 创建服务账户
gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
  --display-name="GitHub Actions Cloud Run Deployer" \
  --description="Service account for GitHub Actions to deploy to Cloud Run"

# 获取服务账户邮箱
export SERVICE_ACCOUNT_EMAIL="$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com"
```

### 2. 分配必要权限

```bash
# Cloud Run开发者权限
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
  --role="roles/run.developer"

# Service Account用户权限
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
  --role="roles/iam.serviceAccountUser"

# 存储对象查看权限（用于拉取镜像）
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
  --role="roles/storage.objectViewer"
```

### 3. 创建密钥文件

```bash
# 创建并下载密钥文件
gcloud iam service-accounts keys create key.json \
  --iam-account=$SERVICE_ACCOUNT_EMAIL

# 查看密钥内容（用于配置GitHub Secrets）
cat key.json
```

### 4. 启用必要的API

```bash
# 启用Cloud Run API
gcloud services enable run.googleapis.com

# 启用Container Registry API（如果使用GCR）
gcloud services enable containerregistry.googleapis.com

# 启用Artifact Registry API（如果使用Artifact Registry）
gcloud services enable artifactregistry.googleapis.com
```

## 🔐 GitHub配置

### 1. 配置Secrets

在GitHub仓库的 `Settings` > `Secrets and variables` > `Actions` 中添加：

#### Secrets
| 名称 | 值 | 说明 |
|------|----|----|
| `GCP_SA_KEY` | `key.json的完整内容` | GCP服务账户密钥（JSON格式） |

### 2. 配置Variables

在GitHub仓库的 `Settings` > `Secrets and variables` > `Actions` 的 `Variables` 标签中添加：

#### Variables
| 名称 | 默认值 | 说明 |
|------|-------|------|
| `CLOUD_RUN_SERVICE_NAME` | `veri-text` | Cloud Run服务名称 |
| `GCP_REGION` | `us-central1` | GCP部署区域 |
| `CLOUD_RUN_MEMORY` | `1Gi` | 内存限制 |
| `CLOUD_RUN_CPU` | `1` | CPU限制 |
| `CLOUD_RUN_CONCURRENCY` | `80` | 并发请求数 |
| `CLOUD_RUN_MAX_INSTANCES` | `10` | 最大实例数 |
| `CLOUD_RUN_MIN_INSTANCES` | `0` | 最小实例数 |
| `CLOUD_RUN_TIMEOUT` | `300` | 超时时间（秒） |
| `GUNICORN_WORKERS` | `2` | Gunicorn工作进程数 |
| `GUNICORN_LOG_LEVEL` | `info` | 日志级别 |

## 🌍 推荐的区域配置

根据用户地理位置选择最近的区域：

| 地区 | 推荐区域 | 区域代码 |
|------|---------|---------|
| 亚洲 | Asia Pacific (Tokyo) | `asia-northeast1` |
| 中国用户 | Asia Pacific (Tokyo) | `asia-northeast1` |
| 美国 | US Central | `us-central1` |
| 欧洲 | Europe West | `europe-west1` |

## 📊 资源配置建议

### 开发环境
```
CLOUD_RUN_MEMORY=512Mi
CLOUD_RUN_CPU=1
CLOUD_RUN_MAX_INSTANCES=3
CLOUD_RUN_MIN_INSTANCES=0
GUNICORN_WORKERS=1
```

### 生产环境
```
CLOUD_RUN_MEMORY=2Gi
CLOUD_RUN_CPU=2
CLOUD_RUN_MAX_INSTANCES=20
CLOUD_RUN_MIN_INSTANCES=1
GUNICORN_WORKERS=4
```

### 高并发环境
```
CLOUD_RUN_MEMORY=4Gi
CLOUD_RUN_CPU=4
CLOUD_RUN_MAX_INSTANCES=50
CLOUD_RUN_MIN_INSTANCES=2
GUNICORN_WORKERS=8
```

## 🚀 部署流程

### 自动部署（推荐）

1. **创建版本标签**：
```bash
git tag v1.0.5
git push origin v1.0.5
```

2. **GitHub Actions自动执行**：
   - 构建Docker镜像
   - 推送到Docker Hub
   - 部署到Cloud Run
   - 执行测试验证

### 手动部署

```bash
# 设置变量
export PROJECT_ID="your-project-id"
export SERVICE_NAME="veri-text"
export REGION="asia-northeast1"
export IMAGE="lihongjie0209/veri-text:latest"

# 部署到Cloud Run
gcloud run deploy $SERVICE_NAME \
  --image=$IMAGE \
  --platform=managed \
  --region=$REGION \
  --allow-unauthenticated \
  --port=8000 \
  --memory=1Gi \
  --cpu=1 \
  --concurrency=80 \
  --max-instances=10 \
  --min-instances=0 \
  --timeout=300 \
  --set-env-vars="GUNICORN_WORKERS=2,GUNICORN_LOG_LEVEL=info"
```

## 🔍 验证部署

### 1. 检查服务状态

```bash
# 查看服务信息
gcloud run services describe $SERVICE_NAME --region=$REGION

# 获取服务URL
gcloud run services describe $SERVICE_NAME \
  --region=$REGION \
  --format='value(status.url)'
```

### 2. 健康检查

```bash
# 替换为实际的服务URL
SERVICE_URL="https://your-service-url"

# 健康检查
curl "$SERVICE_URL/api/v1/health/"

# 功能测试
curl -X POST "$SERVICE_URL/api/v1/detect/" \
  -H "Content-Type: application/json" \
  -d '{"text":"测试文本","config":{"detection_mode":"rule"}}'
```

## 📊 监控和日志

### 查看日志

```bash
# 查看实时日志
gcloud run logs tail $SERVICE_NAME --region=$REGION

# 查看特定时间段的日志
gcloud run logs read $SERVICE_NAME --region=$REGION --limit=50
```

### 监控指标

在GCP Console中查看：
- **Cloud Run** > **your-service** > **Metrics**
- 请求数量、延迟、错误率
- CPU和内存使用情况
- 实例数量变化

## 🛠️ 故障排除

### 常见问题

#### 1. 部署权限错误
```
Error: (gcloud.run.deploy) User does not have permission to access...
```
**解决方案**：检查服务账户权限，确保有 `roles/run.developer` 角色。

#### 2. 镜像拉取失败
```
Error: Failed to pull image
```
**解决方案**：
- 确保Docker Hub镜像存在且公开
- 检查镜像标签是否正确

#### 3. 服务启动超时
```
Error: Container failed to start
```
**解决方案**：
- 检查容器健康检查配置
- 增加启动超时时间
- 查看Cloud Run日志排查问题

#### 4. GitHub Actions部署失败
```
Error: could not parse application default credentials
```
**解决方案**：
- 检查 `GCP_SA_KEY` secret是否正确设置
- 确保JSON密钥格式完整

### 调试命令

```bash
# 检查服务账户权限
gcloud iam service-accounts get-iam-policy $SERVICE_ACCOUNT_EMAIL

# 测试服务账户权限
gcloud auth activate-service-account --key-file=key.json
gcloud run services list --region=$REGION

# 检查API是否启用
gcloud services list --enabled --filter="name:run.googleapis.com"
```

## 🔄 回滚部署

如果新版本有问题，可以快速回滚：

```bash
# 查看历史版本
gcloud run revisions list --service=$SERVICE_NAME --region=$REGION

# 回滚到指定版本
gcloud run services update-traffic $SERVICE_NAME \
  --to-revisions=your-revision-name=100 \
  --region=$REGION
```

## 💰 成本优化

### 配置建议
- 设置合适的 `min-instances` 避免冷启动，但控制成本
- 使用 `concurrency` 控制单个实例的并发数
- 监控实际使用情况，调整资源配置

### 成本监控
- 在GCP Console的Billing中查看Cloud Run费用
- 设置预算提醒避免超支
- 定期检查资源使用情况和配置

## 📚 参考资源

- [Cloud Run官方文档](https://cloud.google.com/run/docs)
- [GitHub Actions for GCP](https://github.com/google-github-actions)
- [gcloud CLI参考](https://cloud.google.com/sdk/gcloud/reference/run)
- [Cloud Run定价](https://cloud.google.com/run/pricing)

---

## ✅ 配置检查清单

在开始部署前，请确认以下配置：

- [ ] GCP项目已创建且启用了Cloud Run API
- [ ] 服务账户已创建并分配了正确的权限
- [ ] GitHub Secrets中已添加 `GCP_SA_KEY`
- [ ] GitHub Variables中已配置服务名称和区域
- [ ] Docker Hub镜像构建和推送正常工作
- [ ] 本地测试了手动部署流程

完成以上配置后，每次推送版本标签都会自动触发完整的CI/CD流程，实现从代码到生产环境的自动化部署！
