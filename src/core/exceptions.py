"""
自定义异常类
"""
from typing import Optional, Any, Dict


class VeriTextBaseException(Exception):
    """基础异常类"""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ConfigurationError(VeriTextBaseException):
    """配置错误"""
    pass


class WordListError(VeriTextBaseException):
    """词库相关错误"""
    pass


class DetectionError(VeriTextBaseException):
    """检测过程错误"""
    pass


class ValidationError(VeriTextBaseException):
    """数据验证错误"""
    pass


class ResourceNotFoundError(VeriTextBaseException):
    """资源未找到错误"""
    pass


class ServiceUnavailableError(VeriTextBaseException):
    """服务不可用错误"""
    pass


class RateLimitError(VeriTextBaseException):
    """请求频率限制错误"""
    pass
