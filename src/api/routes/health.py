"""
健康检查API路由
"""
from fastapi import APIRouter, Depends
from typing import Dict, Any

from ...models import HealthResponse
from ...services import SensitiveWordDetectionService
from ...core import get_logger
from ..dependencies import get_detection_service, get_app_settings

logger = get_logger()
router = APIRouter(prefix="/health", tags=["健康检查"])


@router.get(
    "/",
    response_model=HealthResponse,
    summary="健康检查",
    description="检查服务运行状态和各组件健康状况"
)
async def health_check(
    service: SensitiveWordDetectionService = Depends(get_detection_service),
    settings = Depends(get_app_settings)
) -> HealthResponse:
    """
    健康检查接口
    
    Args:
        service: 检测服务
        settings: 应用配置
        
    Returns:
        健康状态信息
    """
    try:
        # 获取服务健康状态
        health_data = await service.health_check()
        
        response = HealthResponse(
            status=health_data["status"],
            version=health_data["version"],
            uptime_seconds=health_data["uptime_seconds"],
            components=health_data["components"],
            message="服务运行正常"
        )
        
        return response
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        
        # 返回错误状态但不抛出异常
        return HealthResponse(
            status="unhealthy",
            version=settings.app_version,
            uptime_seconds=0,
            components={},
            success=False,
            message=f"健康检查失败: {str(e)}"
        )


@router.get(
    "/ready",
    summary="就绪检查", 
    description="检查服务是否已准备好接收请求"
)
async def readiness_check(
    service: SensitiveWordDetectionService = Depends(get_detection_service)
) -> Dict[str, Any]:
    """
    就绪检查接口（用于k8s readiness probe）
    
    Args:
        service: 检测服务
        
    Returns:
        就绪状态
    """
    try:
        health_data = await service.health_check()
        components = health_data.get("components", {})
        
        # 检查关键组件是否就绪
        rule_detector_ready = components.get("rule_detector", {}).get("loaded", False)
        
        if rule_detector_ready:
            return {"status": "ready"}
        else:
            return {"status": "not_ready", "reason": "components_not_loaded"}
            
    except Exception as e:
        logger.error(f"就绪检查失败: {e}")
        return {"status": "not_ready", "reason": str(e)}


@router.get(
    "/live",
    summary="存活检查",
    description="检查服务进程是否存活"
)
async def liveness_check() -> Dict[str, str]:
    """
    存活检查接口（用于k8s liveness probe）
    
    Returns:
        存活状态
    """
    return {"status": "alive"}
