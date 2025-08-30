"""
FastAPI依赖注入
"""
from functools import lru_cache
from ..services import SensitiveWordDetectionService
from ..core import get_settings


# 全局服务实例缓存
@lru_cache()
def get_detection_service() -> SensitiveWordDetectionService:
    """获取检测服务实例（单例）"""
    return SensitiveWordDetectionService()


@lru_cache()
def get_app_settings():
    """获取应用配置（单例）"""
    return get_settings()
