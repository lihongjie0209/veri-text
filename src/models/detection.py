"""
检测相关数据模型
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from .common import (
    DetectionMode, StrictnessLevel, 
    MatchType, DetectionMethod, RiskLevel, Position, BaseResponse
)


class DetectionConfig(BaseModel):
    """检测配置模型"""
    detection_mode: DetectionMode = Field(default=DetectionMode.HYBRID, description="检测模式")
    strictness_level: StrictnessLevel = Field(default=StrictnessLevel.STANDARD, description="严格程度")
    categories: List[str] = Field(default=[], description="检测的敏感词分类，空列表表示全部")
    return_positions: bool = Field(default=True, description="是否返回敏感词位置")
    return_suggestions: bool = Field(default=False, description="是否返回替换建议")
    custom_threshold: float = Field(default=0.8, ge=0.0, le=1.0, description="自定义检测阈值")


class DetectionRequest(BaseModel):
    """检测请求模型"""
    text: str = Field(..., min_length=1, max_length=10000, description="待检测的文本内容")
    config: DetectionConfig = Field(default_factory=DetectionConfig, description="检测配置")


class DetectionResultItem(BaseModel):
    """检测结果项模型"""
    matched_word: str = Field(..., description="匹配到的敏感词")
    category: str = Field(..., description="敏感词分类")
    match_type: MatchType = Field(..., description="匹配类型")
    confidence: float = Field(..., ge=0.0, le=1.0, description="检测置信度")
    positions: List[Position] = Field(default=[], description="在原文中的位置")
    detection_method: DetectionMethod = Field(..., description="检测方法")
    suggestion: Optional[str] = Field(default=None, description="替换建议")


class DetectionSummary(BaseModel):
    """检测结果汇总"""
    total_matches: int = Field(..., ge=0, description="总匹配数")
    categories_found: List[str] = Field(default=[], description="发现的敏感词分类")
    highest_risk_category: Optional[str] = Field(default=None, description="最高风险分类")


class DetectionResponse(BaseResponse):
    """检测响应模型"""
    is_sensitive: bool = Field(..., description="是否包含敏感内容")
    risk_level: RiskLevel = Field(..., description="风险等级")
    overall_score: float = Field(..., ge=0.0, le=1.0, description="整体敏感度评分")
    detection_time_ms: int = Field(..., ge=0, description="检测耗时（毫秒）")
    detection_mode_used: DetectionMode = Field(..., description="实际使用的检测模式")
    results: List[DetectionResultItem] = Field(default=[], description="检测结果详情")
    summary: DetectionSummary = Field(..., description="检测结果汇总")


class HealthResponse(BaseResponse):
    """健康检查响应模型"""
    status: str = Field(..., description="服务状态")
    version: str = Field(..., description="服务版本")
    uptime_seconds: int = Field(..., ge=0, description="运行时长（秒）")
    components: Dict[str, Any] = Field(default={}, description="各组件状态")
