"""
检测相关API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any

from ...models import DetectionRequest, DetectionResponse
from ...services import SensitiveWordDetectionService
from ...core import get_logger, DetectionError, ValidationError
from ..dependencies import get_detection_service

logger = get_logger()
router = APIRouter(prefix="/detect", tags=["检测"])


@router.post(
    "/",
    response_model=DetectionResponse,
    summary="敏感词检测",
    description="对输入文本进行敏感词检测，支持规则匹配和语义检测"
)
async def detect_sensitive_content(
    request: DetectionRequest,
    service: SensitiveWordDetectionService = Depends(get_detection_service)
) -> DetectionResponse:
    """
    敏感词检测接口
    
    Args:
        request: 检测请求
        service: 检测服务
        
    Returns:
        检测结果
        
    Raises:
        HTTPException: 当检测失败时
    """
    try:
        logger.info(f"收到检测请求，文本长度: {len(request.text)}")
        
        # 执行检测
        response = await service.detect(request)
        
        return response
        
    except ValidationError as e:
        logger.warning(f"请求参数验证失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"请求参数无效: {e.message}"
        )
    except DetectionError as e:
        logger.error(f"检测过程出错: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"检测失败: {e.message}"
        )
    except Exception as e:
        logger.error(f"未知错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务内部错误"
        )
