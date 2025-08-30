"""
API包导出
"""
from .dependencies import get_detection_service, get_app_settings
from .routes import detection_router, health_router

__all__ = [
    "get_detection_service", "get_app_settings",
    "detection_router", "health_router"
]
