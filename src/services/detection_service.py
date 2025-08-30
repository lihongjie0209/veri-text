"""
敏感词检测服务主入口
"""
import time
import asyncio
from typing import List, Dict, Any
from datetime import datetime

from ..models import (
    DetectionRequest, DetectionResponse, DetectionResultItem, 
    DetectionSummary, DetectionMode, RiskLevel
)
from ..core import get_logger, get_settings, DetectionError
from .rule_detector import RuleBasedDetector

logger = get_logger()


class SensitiveWordDetectionService:
    """敏感词检测服务主入口"""
    
    def __init__(self):
        """初始化检测服务"""
        self.settings = get_settings()
        
        # 初始化规则检测器 - 使用YAML配置
        self.rule_detector = RuleBasedDetector("config/sensitive_words.yaml")
        
        # 服务状态
        self.start_time = time.time()
        self.request_count = 0
        
        logger.info("敏感词检测服务初始化完成 - 使用YAML配置")
    
    async def detect(self, request: DetectionRequest) -> DetectionResponse:
        """
        执行敏感词检测
        
        Args:
            request: 检测请求
            
        Returns:
            检测响应
        """
        start_time = time.time()
        self.request_count += 1
        
        try:
            logger.debug(f"开始检测，文本长度: {len(request.text)}, 模式: {request.config.detection_mode}")
            
            # 验证文本长度
            if len(request.text) > self.settings.max_text_length:
                raise DetectionError(f"文本长度超过限制: {len(request.text)} > {self.settings.max_text_length}")
            
            # 根据检测模式执行相应的检测
            results = await self._execute_detection(request)
            
            # 生成检测响应
            response = await self._build_response(
                results, 
                request.config.detection_mode,
                start_time
            )
            
            detection_time = (time.time() - start_time) * 1000
            logger.info(f"检测完成，耗时 {detection_time:.2f}ms，发现敏感内容: {response.is_sensitive}")
            
            return response
            
        except Exception as e:
            logger.error(f"检测过程出错: {e}")
            raise DetectionError(f"检测失败: {e}")
    
    async def _execute_detection(self, request: DetectionRequest) -> List[DetectionResultItem]:
        """
        执行具体的检测逻辑
        
        Args:
            request: 检测请求
            
        Returns:
            检测结果列表
        """
        text = request.text
        config = request.config
        mode = config.detection_mode
        
        all_results = []
        
        if mode == DetectionMode.RULE:
            # 仅规则检测
            rule_results = await self.rule_detector.detect(text, config)
            all_results.extend(rule_results)
            
        elif mode == DetectionMode.SEMANTIC:
            # 语义检测已被移除，返回空结果
            logger.warning("语义检测已不支持，返回空结果")
            
        elif mode == DetectionMode.HYBRID:
            # 仅执行规则检测（语义检测已移除）
            rule_results = await self.rule_detector.detect(text, config)
            all_results.extend(rule_results)
        
        # 去重和合并结果
        merged_results = self._merge_and_deduplicate_results(all_results)
        
        return merged_results
    
    def _merge_and_deduplicate_results(
        self, 
        results: List[DetectionResultItem]
    ) -> List[DetectionResultItem]:
        """
        合并和去重检测结果
        
        Args:
            results: 原始结果列表
            
        Returns:
            去重后的结果列表
        """
        if not results:
            return []
        
        # 简单去重：基于匹配词和分类
        seen = set()
        unique_results = []
        
        for result in results:
            key = (result.matched_word, result.category)
            if key not in seen:
                seen.add(key)
                unique_results.append(result)
            else:
                # 如果重复，保留置信度更高的
                for i, existing in enumerate(unique_results):
                    if (existing.matched_word, existing.category) == key:
                        if result.confidence > existing.confidence:
                            unique_results[i] = result
                        break
        
        # 按置信度排序
        unique_results.sort(key=lambda x: x.confidence, reverse=True)
        
        return unique_results
    
    async def _build_response(
        self, 
        results: List[DetectionResultItem],
        detection_mode: DetectionMode,
        start_time: float
    ) -> DetectionResponse:
        """
        构建检测响应
        
        Args:
            results: 检测结果
            detection_mode: 检测模式
            start_time: 开始时间
            
        Returns:
            检测响应
        """
        # 计算检测时间
        detection_time_ms = int((time.time() - start_time) * 1000)
        
        # 是否包含敏感内容
        is_sensitive = len(results) > 0
        
        # 计算整体风险评分
        overall_score = 0.0
        if results:
            overall_score = max(result.confidence for result in results)
        
        # 确定风险等级
        risk_level = self._calculate_risk_level(overall_score, results)
        
        # 构建汇总信息
        categories_found = list(set(result.category for result in results))
        highest_risk_category = None
        if results:
            highest_risk_category = max(results, key=lambda x: x.confidence).category
        
        summary = DetectionSummary(
            total_matches=len(results),
            categories_found=categories_found,
            highest_risk_category=highest_risk_category
        )
        
        return DetectionResponse(
            is_sensitive=is_sensitive,
            risk_level=risk_level,
            overall_score=overall_score,
            detection_time_ms=detection_time_ms,
            detection_mode_used=detection_mode,
            results=results,
            summary=summary,
            message="检测完成"
        )
    
    def _calculate_risk_level(
        self, 
        overall_score: float, 
        results: List[DetectionResultItem]
    ) -> RiskLevel:
        """
        计算风险等级
        
        Args:
            overall_score: 整体评分
            results: 检测结果
            
        Returns:
            风险等级
        """
        if not results:
            return RiskLevel.LOW
        
        # 基于评分和敏感词数量确定风险等级
        if overall_score >= 0.9 or len(results) >= 5:
            return RiskLevel.CRITICAL
        elif overall_score >= 0.7 or len(results) >= 3:
            return RiskLevel.HIGH
        elif overall_score >= 0.5 or len(results) >= 1:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    async def health_check(self) -> Dict[str, Any]:
        """
        服务健康检查
        
        Returns:
            健康状态信息
        """
        uptime_seconds = int(time.time() - self.start_time)
        
        # 检查各组件状态
        components = {
            "rule_detector": self.rule_detector.get_status()
        }
        
        return {
            "status": "healthy",
            "version": self.settings.app_version,
            "uptime_seconds": uptime_seconds,
            "request_count": self.request_count,
            "components": components,
            "settings": {
                "max_text_length": self.settings.max_text_length,
                "rule_detection_enabled": self.settings.rule_detection_enabled
            }
        }
