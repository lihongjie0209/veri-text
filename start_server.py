#!/usr/bin/env python3
"""
敏感词检测服务启动脚本
支持命令行参数配置
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入并运行主程序
if __name__ == "__main__":
    from src.main import main
    main()
