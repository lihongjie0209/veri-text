# VeriText 版本发布工具

## 功能特性

- 🎯 **智能版本管理**: 自动检测当前版本，支持patch/minor/major升级
- 🤖 **AI生成提交信息**: 使用OpenRouter AI分析代码更改生成专业提交信息  
- 🎨 **美观交互界面**: 基于rich和inquirer的现代化命令行界面
- 🔄 **完整发布流程**: 自动提交、标签、推送到远程仓库
- 🛡️ **安全可靠**: 支持预览模式，确认后执行

## 安装依赖

```bash
# 安装发布工具依赖
pip install -r requirements-release.txt
```

## 环境配置

设置OpenRouter API密钥（用于AI生成提交信息）：

```bash
# Windows
set OPENROUTER_API_KEY=your_api_key_here

# Linux/macOS  
export OPENROUTER_API_KEY=your_api_key_here
```

获取API密钥：访问 [OpenRouter](https://openrouter.ai/) 注册并获取API密钥

## 使用方法

### 基本用法

```bash
# 进入项目根目录
cd /path/to/veri-text

# 运行发布脚本
python scripts/release.py
```

### 预览模式

```bash
# 预览模式，查看将要执行的操作但不实际执行
python scripts/release.py --dry-run
```

## 使用流程

1. **检查状态**: 脚本检查Git状态，确保有未提交的更改
2. **选择版本类型**: 
   - `patch`: 修复bug (1.0.0 → 1.0.1)
   - `minor`: 新功能 (1.0.0 → 1.1.0)  
   - `major`: 重大变更 (1.0.0 → 2.0.0)
3. **确认发布**: 显示版本信息确认表
4. **预览更改**: 显示将要提交的文件更改
5. **生成提交信息**: AI分析更改并生成专业提交信息
6. **执行发布**: 自动提交、创建标签、推送到远程

## 版本检测

脚本会按以下优先级检测当前版本：

1. Git标签 (`git describe --tags --abbrev=0`)
2. `pyproject.toml` 文件
3. `setup.py` 文件  
4. `src/core/config.py` 文件
5. `__init__.py` 文件
6. 默认 `0.1.0`

## AI提交信息

脚本使用OpenRouter AI服务分析代码更改并生成高质量的提交信息：

- 遵循Conventional Commits规范
- 中文描述，专业格式
- 包含版本发布的重要信息
- 支持手动编辑生成的信息

## 自动化集成

发布完成后，GitHub Actions会自动：

- 运行CI/CD流水线
- 构建Docker镜像
- 发布到Docker Hub
- 更新项目文档

## 故障排除

### 常见问题

1. **缺少依赖**: 运行 `pip install -r requirements-release.txt`
2. **API密钥未设置**: 设置 `OPENROUTER_API_KEY` 环境变量
3. **Git权限问题**: 确保有推送权限到远程仓库
4. **网络问题**: 检查网络连接和API服务状态

### 错误处理

脚本包含完善的错误处理：

- 网络超时自动重试
- AI服务失败时使用备用提交信息
- Git操作失败时提供详细错误信息
- 支持Ctrl+C安全退出

## 示例输出

```
🚀 VeriText 自动化版本发布工具

当前版本: 1.0.3
项目路径: /path/to/veri-text  
AI服务: ✓ OpenRouter

✅ 发现 5 个未提交的更改

? 选择版本升级类型: patch (补丁版本): 1.0.3 → 1.0.4

📋 文件更改预览:
  📝 修改 src/templates/detector.html
  📝 修改 src/static/js/app.js
  📝 修改 README.md

🤖 AI正在生成提交信息...

📝 生成的提交信息:
┌─ 提交信息预览 ─┐
│ feat: 发布v1.0.4版本                     │
│                                          │  
│ - 移除UI中的SEMANTIC检测选项             │
│ - 简化检测模式选择                       │
│ - 修复API路径配置                        │
│ - 更新版本信息和文档                     │
└──────────────────────────────────────────┘

🚀 开始执行发布...
📝 提交代码更改...
🏷️ 创建版本标签...  
⬆️ 推送到远程仓库...

🎉 版本 v1.0.4 发布成功!

✅ 代码已提交
✅ 标签已创建: v1.0.4
✅ 已推送到远程仓库

🔗 GitHub Actions将自动构建和发布Docker镜像
```

## 最佳实践

1. **发布前准备**:
   - 确保所有功能已测试
   - 更新文档和配置
   - 检查依赖版本

2. **版本选择**:
   - Bug修复使用patch
   - 新功能使用minor  
   - 重大变更使用major

3. **提交信息**:
   - 让AI生成初始版本
   - 根据需要手动调整
   - 保持描述清晰准确

4. **发布后验证**:
   - 检查GitHub Actions状态
   - 验证Docker镜像构建
   - 测试新版本功能
