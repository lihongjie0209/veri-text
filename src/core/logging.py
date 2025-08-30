"""
日志配置
"""
import logging
import sys
from typing import Dict, Any
from datetime import datetime

from .config import get_settings


def setup_logging() -> logging.Logger:
    """设置日志配置"""
    settings = get_settings()
    
    # 创建logger
    logger = logging.getLogger("veri_text")
    logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # 避免重复添加handler
    if logger.handlers:
        return logger
    
    # 创建formatter
    if settings.log_format.lower() == "json":
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # 控制台handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件handler（如果配置了日志文件）
    if settings.log_file:
        file_handler = logging.FileHandler(settings.log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


class JsonFormatter(logging.Formatter):
    """JSON格式的日志格式化器"""
    
    def format(self, record: logging.LogRecord) -> str:
        import json
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # 添加额外的字段
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = record.request_id
        
        if hasattr(record, 'user_id'):
            log_entry["user_id"] = record.user_id
        
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False)


# 全局logger实例
logger = setup_logging()


def get_logger() -> logging.Logger:
    """获取全局logger"""
    return logger
