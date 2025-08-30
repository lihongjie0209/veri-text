"""
应用配置管理
"""
import os
import argparse
from typing import List, Dict, Any, Optional
from pydantic import Field
from pydantic_settings import BaseSettings


def parse_args() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="敏感词检测服务",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python -m src.main --port 8080 --host 0.0.0.0 --debug
  python -m src.main --port 9000 --workers 4 --log-level DEBUG
        """
    )
    
    # 服务配置
    parser.add_argument("--host", type=str, help="监听地址 (默认: 127.0.0.1)")
    parser.add_argument("--port", type=int, help="监听端口 (默认: 18085)")
    parser.add_argument("--workers", type=int, help="工作进程数 (默认: 1)")
    parser.add_argument("--debug", action="store_true", help="启用调试模式")
    
    # API配置
    parser.add_argument("--api-prefix", type=str, help="API前缀 (默认: /api/v1)")
    parser.add_argument("--docs-url", type=str, help="文档URL (默认: /docs)")
    
    # 检测配置
    parser.add_argument("--max-text-length", type=int, help="文本最大长度 (默认: 10000)")
    parser.add_argument("--detection-mode", choices=["rule_based", "hybrid"], 
                       help="默认检测模式")
    parser.add_argument("--strictness-level", choices=["loose", "standard", "strict"], 
                       help="默认严格程度")
    
    # 数据路径配置
    parser.add_argument("--data-dir", type=str, help="数据目录")
    parser.add_argument("--wordlist-dir", type=str, help="词库目录")
    
    # 日志配置
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], 
                       help="日志级别")
    parser.add_argument("--log-file", type=str, help="日志文件路径")
    
    # 性能配置
    parser.add_argument("--max-concurrent-requests", type=int, help="最大并发请求数")
    parser.add_argument("--request-timeout", type=int, help="请求超时时间（秒）")
    
    return parser.parse_args()


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用基本信息
    app_name: str = Field(default="敏感词检测服务", description="应用名称")
    app_version: str = Field(default="1.0.0", description="应用版本")
    debug: bool = Field(default=False, description="调试模式")
    
    # 服务配置
    host: str = Field(default="127.0.0.1", description="监听地址")
    port: int = Field(default=18085, description="监听端口")
    workers: int = Field(default=1, description="工作进程数")
    
    # API配置
    api_prefix: str = Field(default="/api/v1", description="API前缀")
    docs_url: str = Field(default="/docs", description="文档URL")
    openapi_url: str = Field(default="/openapi.json", description="OpenAPI URL")
    
    # 检测配置
    max_text_length: int = Field(default=10000, description="文本最大长度")
    default_detection_mode: str = Field(default="hybrid", description="默认检测模式")
    default_strictness_level: str = Field(default="standard", description="默认严格程度")
    
    # 规则检测配置
    rule_detection_enabled: bool = Field(default=True, description="启用规则检测")
    wordlist_reload_interval: int = Field(default=3600, description="词库重载间隔（秒）")
    
    # 性能配置
    max_concurrent_requests: int = Field(default=100, description="最大并发请求数")
    request_timeout: int = Field(default=30, description="请求超时时间（秒）")
    
    # 数据路径配置
    data_dir: str = Field(default="data", description="数据目录")
    wordlist_config_file: str = Field(default="config/sensitive_words.yaml", description="敏感词库YAML配置文件路径")
    config_dir: str = Field(default="config", description="配置目录")
    
    # 日志配置
    log_level: str = Field(default="INFO", description="日志级别")
    log_format: str = Field(default="json", description="日志格式")
    log_file: str = Field(default="", description="日志文件路径")
    
    def __init__(self, **kwargs):
        # 检查是否在生产环境（Gunicorn环境）
        import sys
        is_gunicorn = 'gunicorn' in sys.modules or os.getenv('PRODUCTION', 'false').lower() == 'true'
        
        if is_gunicorn:
            # 生产环境：只使用环境变量，跳过命令行解析
            cli_config = {}
        else:
            # 开发环境：从命令行参数中获取值
            args = parse_args()
            
            # 将命令行参数转换为配置项
            cli_config = {}
            for key, value in vars(args).items():
                if value is not None:
                    # 转换命令行参数名为配置字段名
                    config_key = key.replace('-', '_')
                    cli_config[config_key] = value
        
        # 合并配置：命令行参数 > 环境变量 > 默认值
        merged_config = {**kwargs, **cli_config}
        super().__init__(**merged_config)
    
    class Config:
        env_prefix = "VERI_TEXT_"
        env_file = ".env"
        case_sensitive = False


# 全局配置实例（延迟初始化）
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """获取应用配置（单例模式）"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def create_settings(**kwargs) -> Settings:
    """创建新的配置实例（用于测试）"""
    return Settings(**kwargs)