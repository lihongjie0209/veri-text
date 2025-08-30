# GitHub Actions 部署指南

## 🚀 自动化部署流程

本项目使用GitHub Actions实现自动化构建和发布Docker镜像到DockerHub。

### 🏗️ 工作流程概述

#### 1. CI构建测试 (ci-build.yml)
- **触发条件**: 推送到 `main`, `develop`, `feature/**`, `hotfix/**` 分支或PR
- **功能**: 
  - 构建Docker镜像
  - 运行基础功能测试
  - 不推送到DockerHub

#### 2. 发布构建 (docker-build.yml)
- **触发条件**: 
  - 推送 `v*` 格式的标签 (如 `v1.0.0`)
  - 手动触发
- **功能**:
  - 多平台构建 (linux/amd64, linux/arm64)
  - 推送到DockerHub
  - 安全扫描
  - 镜像功能测试

## ⚙️ 配置要求

### GitHub Secrets 设置

在GitHub仓库设置中添加以下Secrets：

1. **DOCKERHUB_USERNAME**: DockerHub用户名 (`lihongjie0209`)
2. **DOCKERHUB_TOKEN**: DockerHub访问令牌

#### 创建DockerHub访问令牌：
1. 登录 [DockerHub](https://hub.docker.com/)
2. 点击头像 → Account Settings → Security
3. 点击 "New Access Token"
4. 输入描述，选择权限（Read, Write, Delete）
5. 复制生成的令牌

#### 在GitHub中设置Secrets：
1. 进入仓库 → Settings → Secrets and variables → Actions
2. 点击 "New repository secret"
3. 添加以上两个secrets

## 📦 镜像发布策略

### 标签策略

| 触发方式 | 示例标签 | 生成的镜像标签 |
|---------|---------|---------------|
| `v1.0.0` | git tag v1.0.0 | `1.0.0`, `1.0`, `1`, `latest` |
| `v1.2.3` | git tag v1.2.3 | `1.2.3`, `1.2`, `1`, `latest` |
| `main` 分支 | push to main | `main` |
| `develop` 分支 | push to develop | `develop` |
| 手动触发 | 自定义 | 用户指定 |

### 发布新版本

```bash
# 1. 创建并推送标签
git tag v1.0.0
git push origin v1.0.0

# 2. 或者使用GitHub CLI
gh release create v1.0.0 --title "Release v1.0.0" --notes "发布说明"
```

## 🐳 使用发布的镜像

### 拉取最新版本
```bash
docker pull lihongjie0209/veri-text:latest
```

### 拉取特定版本
```bash
docker pull lihongjie0209/veri-text:1.0.0
```

### 运行容器
```bash
# 基础运行
docker run -d -p 8888:8000 lihongjie0209/veri-text:latest

# 生产环境配置
docker run -d -p 8888:8000 \
  -e GUNICORN_WORKERS=4 \
  -e GUNICORN_TIMEOUT=30 \
  -e GUNICORN_MAX_REQUESTS=1000 \
  lihongjie0209/veri-text:latest

# 自定义配置
docker run -d -p 8888:8000 \
  -e GUNICORN_BIND=0.0.0.0:8000 \
  -e GUNICORN_WORKERS=8 \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/data:/app/data \
  lihongjie0209/veri-text:latest
```

## 🔧 手动触发部署

1. 进入GitHub仓库
2. 点击 Actions 标签
3. 选择 "Docker Build and Push" 工作流
4. 点击 "Run workflow"
5. 选择分支和配置选项
6. 点击 "Run workflow"

### 手动触发选项

- **push_to_dockerhub**: 是否推送到DockerHub
- **custom_tag**: 自定义镜像标签（可选）

## 📊 构建状态监控

### Badge 状态

在README中添加构建状态徽章：

```markdown
![Docker Build](https://github.com/lihongjie0209/veri-text/actions/workflows/docker-build.yml/badge.svg)
![CI Build](https://github.com/lihongjie0209/veri-text/actions/workflows/ci-build.yml/badge.svg)
```

### 查看构建日志

1. 进入GitHub仓库
2. 点击 Actions 标签
3. 选择相应的工作流运行
4. 查看详细日志

## 🔒 安全扫描

发布版本会自动进行安全扫描：
- 使用Docker Scout扫描已知漏洞
- 重点关注严重和高危漏洞
- 扫描结果不会阻止发布但会记录日志

## 🚨 故障排除

### 常见问题

1. **DockerHub推送失败**
   - 检查DOCKERHUB_USERNAME和DOCKERHUB_TOKEN是否正确
   - 确认DockerHub令牌有写入权限

2. **构建失败**
   - 检查Dockerfile语法
   - 确认依赖文件存在

3. **测试失败**
   - 检查应用启动日志
   - 确认健康检查端点正常

### 调试方法

```bash
# 本地测试构建
docker build -t veri-text:local .

# 本地测试运行
docker run -d -p 8080:8000 veri-text:local

# 查看日志
docker logs <container_id>
```

## 📋 环境变量

支持的环境变量详见：[环境变量配置文档](./docs/environment-variables.md)

## 🔄 版本管理

建议使用语义化版本号：
- `v1.0.0` - 主要版本
- `v1.1.0` - 次要版本  
- `v1.1.1` - 补丁版本
