@echo off
rem VeriText 版本发布工具启动脚本 (Windows)

echo 🚀 VeriText 版本发布工具
echo ==========================

rem 检查Python版本
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python未安装或不在PATH中
    pause
    exit /b 1
)

echo Python版本: 
python --version

rem 检查依赖
python -c "import click, inquirer, rich, packaging, requests" >nul 2>&1
if errorlevel 1 (
    echo ❌ 缺少依赖，正在安装...
    pip install -r requirements-release.txt
    if errorlevel 1 (
        echo ❌ 依赖安装失败，请手动安装: pip install -r requirements-release.txt
        pause
        exit /b 1
    )
)

rem 检查API密钥
if "%OPENROUTER_API_KEY%"=="" (
    echo ⚠️  警告: 未设置OPENROUTER_API_KEY环境变量
    echo    AI功能将不可用，将使用备用提交信息生成
    echo    获取API密钥: https://openrouter.ai/
    echo.
)

rem 检查Git状态
git status >nul 2>&1
if errorlevel 1 (
    echo ❌ 当前目录不是Git仓库
    pause
    exit /b 1
)

rem 运行发布脚本
echo 启动发布工具...
echo.
python scripts\release.py %*

if errorlevel 1 (
    echo.
    echo 发布过程中出现错误
    pause
)
