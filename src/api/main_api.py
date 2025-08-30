"""
更新后的主API路由
集成新的检测服务和词库管理
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from ..models.detection import DetectionRequest, DetectionResponse
from ..services.enhanced_detection_service import EnhancedDetectionService
from ..core import get_logger

logger = get_logger()
router = APIRouter(prefix="/api", tags=["检测服务"])

# 检测服务实例（单例）
detection_service = None

def get_detection_service():
    """获取检测服务实例"""
    global detection_service
    if detection_service is None:
        detection_service = EnhancedDetectionService()
    return detection_service


@router.post("/detect", response_model=DetectionResponse)
async def detect_sensitive_content(request: DetectionRequest):
    """
    检测敏感内容
    
    这是主要的检测接口，支持多种检测模式和配置选项。
    """
    try:
        service = get_detection_service()
        return await service.detect(request)
    except Exception as e:
        logger.error(f"检测失败: {e}")
        raise HTTPException(status_code=500, detail=f"检测失败: {str(e)}")


@router.get("/health")
async def health_check():
    """
    健康检查
    
    返回服务状态和统计信息。
    """
    try:
        service = get_detection_service()
        return await service.health_check()
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(status_code=500, detail="服务不可用")


@router.post("/reload/rules")
async def reload_rules():
    """
    重新加载检测规则
    
    用于在运行时更新检测规则配置。
    """
    try:
        service = get_detection_service()
        service.reload_rules()
        return {"success": True, "message": "检测规则重新加载成功"}
    except Exception as e:
        logger.error(f"重新加载规则失败: {e}")
        raise HTTPException(status_code=500, detail=f"重新加载失败: {str(e)}")


@router.post("/reload/wordlists")
async def reload_wordlists():
    """
    重新加载词库
    
    用于在运行时更新词库内容。
    """
    try:
        service = get_detection_service()
        service.reload_wordlists()
        return {"success": True, "message": "词库重新加载成功"}
    except Exception as e:
        logger.error(f"重新加载词库失败: {e}")
        raise HTTPException(status_code=500, detail=f"重新加载失败: {str(e)}")


@router.get("/config/categories")
async def get_categories():
    """
    获取所有可用的敏感词分类
    
    从YAML配置文件中读取分类信息，用于前端动态渲染分类选择器。
    """
    try:
        service = get_detection_service()
        # 从配置读取器获取分类信息
        config_reader = service.config_reader
        wordlists = config_reader.get_all_wordlists()
        
        # 提取分类信息
        categories = []
        for wordlist in wordlists:
            if wordlist.enabled:
                categories.append({
                    "name": wordlist.name,
                    "description": wordlist.description,
                    "word_count": len(config_reader.load_words(wordlist.name))
                })
        
        return {
            "success": True,
            "categories": categories,
            "total_categories": len(categories)
        }
    except Exception as e:
        logger.error(f"获取分类失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取分类失败: {str(e)}")


@router.get("/config/wordlists")
async def get_wordlists_config():
    """
    获取词库配置信息
    
    返回完整的词库配置，包括启用状态、文件路径等。
    """
    try:
        service = get_detection_service()
        config_reader = service.config_reader
        wordlists = config_reader.get_all_wordlists()
        
        wordlists_info = []
        for wordlist in wordlists:
            try:
                words = config_reader.load_words(wordlist.name)
                wordlists_info.append({
                    "name": wordlist.name,
                    "description": wordlist.description,
                    "file": wordlist.file,
                    "enabled": wordlist.enabled,
                    "word_count": len(words)
                })
            except Exception as e:
                logger.warning(f"无法加载词库 {wordlist.name}: {e}")
                wordlists_info.append({
                    "name": wordlist.name,
                    "description": wordlist.description,
                    "file": wordlist.file,
                    "enabled": wordlist.enabled,
                    "word_count": 0,
                    "error": str(e)
                })
        
        return {
            "success": True,
            "wordlists": wordlists_info,
            "total_wordlists": len(wordlists_info)
        }
    except Exception as e:
        logger.error(f"获取词库配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取词库配置失败: {str(e)}")


# 管理界面路由
@router.get("/", response_class=HTMLResponse)
async def admin_interface():
    """管理界面首页"""
    with open("src/templates/wordlist_manager.html", "r", encoding="utf-8") as f:
        return f.read()
