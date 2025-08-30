# 版本发布工具配置指南

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r scripts/requirements-release.txt
```

### 2. 配置API密钥

#### Windows (PowerShell):
```powershell
# 临时设置（当前会话有效）
$env:OPENROUTER_API_KEY = "your-api-key-here"

# 永久设置（添加到系统环境变量）
[Environment]::SetEnvironmentVariable("OPENROUTER_API_KEY", "your-api-key-here", "User")
```

#### Linux/Mac (Bash):
```bash
# 临时设置
export OPENROUTER_API_KEY="your-api-key-here"

# 永久设置（添加到 ~/.bashrc 或 ~/.zshrc）
echo 'export OPENROUTER_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

### 3. 获取OpenRouter API密钥

1. 访问 [OpenRouter](https://openrouter.ai/)
2. 注册并登录账户
3. 在 API Keys 页面创建新的API密钥
4. 复制密钥并设置到环境变量

### 4. 运行发布工具

```bash
# 预览模式（不执行实际操作）
python scripts/release.py --dry-run

# 正式发布
python scripts/release.py
```

## 🛠️ 使用流程

1. **确保代码已修改**: 必须有未提交的更改
2. **选择版本类型**: patch/minor/major
3. **确认版本信息**: 检查新版本号
4. **预览文件更改**: 查看将要提交的文件
5. **生成提交信息**: AI自动生成或手动编辑
6. **执行发布**: 自动提交、标签、推送

## 🔧 故障排除

### 问题1: 缺少依赖
```
❌ 缺少依赖库: No module named 'click'
```
**解决**: 重新安装依赖
```bash
pip install -r scripts/requirements-release.txt
```

### 问题2: API密钥未设置
```
❌ 请设置OPENROUTER_API_KEY环境变量
```
**解决**: 按照上述步骤设置API密钥

### 问题3: 没有未提交更改
```
❌ 没有发现未提交的更改
```
**解决**: 确保有文件修改但未提交

### 问题4: Git推送失败
```
❌ 推送失败
```
**解决**: 检查网络连接和Git配置

## 📋 功能特性

- ✅ 自动版本号升级（语义化版本）
- ✅ AI智能生成提交信息
- ✅ 交互式版本选择界面
- ✅ 美观的命令行界面
- ✅ 自动Git标签和推送
- ✅ 支持预览模式
- ✅ 详细的操作反馈

## 🎯 版本类型说明

- **patch**: 修复bug，第三位数字+1 (1.0.0 → 1.0.1)
- **minor**: 新功能，第二位数字+1 (1.0.1 → 1.1.0)  
- **major**: 重大更新，第一位数字+1 (1.1.0 → 2.0.0)

## 🔑 安全提醒

- 请妥善保管API密钥，不要提交到代码库
- 建议使用环境变量而非硬编码密钥
- 定期轮换API密钥以确保安全
