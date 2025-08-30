#!/bin/bash
# VeriText 版本发布工具启动脚本

echo "🚀 VeriText 版本发布工具"
echo "=========================="

# 检查Python版本
python_version=$(python3 --version 2>&1)
echo "Python版本: $python_version"

# 检查依赖
if ! python3 -c "import click, inquirer, rich, packaging, requests" 2>/dev/null; then
    echo "❌ 缺少依赖，正在安装..."
    pip3 install -r requirements-release.txt
    if [ $? -ne 0 ]; then
        echo "❌ 依赖安装失败，请手动安装: pip3 install -r requirements-release.txt"
        exit 1
    fi
fi

# 检查API密钥
if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "⚠️  警告: 未设置OPENROUTER_API_KEY环境变量"
    echo "   AI功能将不可用，将使用备用提交信息生成"
    echo "   获取API密钥: https://openrouter.ai/"
    echo ""
fi

# 检查Git状态
if ! git status >/dev/null 2>&1; then
    echo "❌ 当前目录不是Git仓库"
    exit 1
fi

# 运行发布脚本
echo "启动发布工具..."
echo ""
python3 scripts/release.py "$@"
