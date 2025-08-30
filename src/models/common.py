"""
通用数据模型
"""
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class DetectionMode(str, Enum):
    """检测模式"""
    RULE = "rule"
    HYBRID = "hybrid"


class StrictnessLevel(str, Enum):
    """检测严格程度"""
    LOOSE = "loose"
    STANDARD = "standard"
    STRICT = "strict"
    CUSTOM = "custom"


class MatchType(str, Enum):
    """匹配类型"""
    EXACT = "exact"
    FUZZY = "fuzzy"


class DetectionMethod(str, Enum):
    """检测方法"""
    RULE = "rule"


class RiskLevel(str, Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Position(BaseModel):
    """位置信息"""
    start: int = Field(..., ge=0, description="起始位置")
    end: int = Field(..., ge=0, description="结束位置")
    
    def model_post_init(self, __context):
        """Pydantic v2 的后初始化方法"""
        if self.start >= self.end:
            raise ValueError("start position must be less than end position")


class BaseResponse(BaseModel):
    """基础响应模型"""
    success: bool = True
    message: str = "操作成功"
    timestamp: Optional[str] = None
