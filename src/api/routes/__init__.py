"""
API路由包导出
"""
from .detection import router as detection_router
from .health import router as health_router

__all__ = ["detection_router", "health_router"]
