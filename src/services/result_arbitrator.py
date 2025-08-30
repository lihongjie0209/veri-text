"""
敏感词检测结果仲裁组件
基于贪心策略的最大匹配算法来合并和仲裁多个引擎的检测结果
"""
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict
from dataclasses import dataclass, field

from ..models.detection import DetectionResultItem, DetectionSummary
from ..models.common import RiskLevel, MatchType, Position
from ..core import get_logger
from .yaml_config_reader import YamlConfigReader

logger = get_logger()


@dataclass 
class Hit:
    """标准化的命中结果数据结构"""
    word: str           # 命中的敏感词
    start: int          # 在原始文本中的起始索引
    end: int            # 在原始文本中的结束索引 (不包含)
    category: str       # 敏感词分类
    source: str         # 来源引擎标识
    confidence: float   # 置信度
    match_type: MatchType  # 匹配类型
    detection_method: str  # 检测方法
    suggestion: Optional[str] = None  # 替换建议
    positions: Optional[List[Position]] = field(default=None)  # 位置列表
    
    def __post_init__(self):
        """初始化后处理"""
        if self.positions is None:
            self.positions = [Position(start=self.start, end=self.end)]


@dataclass
class ArbitrationConfig:
    """仲裁配置"""
    # 合并策略：基于最大匹配原则
    enable_max_matching: bool = True
    
    # 置信度处理
    confidence_threshold: float = 0.5
    confidence_boost_factor: float = 0.1  # 多引擎匹配的置信度提升
    
    # 分类权重
    category_weights: Dict[str, float] = None
    
    # 引擎权重
    engine_weights: Dict[str, float] = None


class DetectionResultArbitrator:
    """检测结果仲裁器 - 基于贪心策略的最大匹配算法"""
    
    def __init__(self, config: ArbitrationConfig = None, yaml_config_reader=None):
        self.config = config or ArbitrationConfig()
        self.yaml_config_reader = yaml_config_reader
        
        # 从YAML配置读取分类权重，如果有的话
        if self.yaml_config_reader and not self.config.category_weights:
            self.config.category_weights = self.yaml_config_reader.get_category_weights()
        
        # 如果仍然没有分类权重，使用默认权重值（所有分类都是1.0）
        if not self.config.category_weights:
            self.config.category_weights = {}
        
        # 默认引擎权重
        if not self.config.engine_weights:
            self.config.engine_weights = {
                'ExactMatchRule': 1.0,
                'JiebaRule': 0.9,
                'RegexRule': 0.85,
                'SemanticRule': 0.8,
                'ACAutomatonRule': 0.95
            }
    
    def arbitrate(
        self, 
        results_by_rule: Dict[str, List[DetectionResultItem]]
    ) -> Tuple[List[DetectionResultItem], DetectionSummary]:
        """
        仲裁多个引擎的检测结果，采用基于最大匹配原则的贪心算法
        
        Args:
            results_by_rule: 按规则分组的检测结果
            
        Returns:
            仲裁后的结果列表和汇总信息
        """
        logger.debug(f"开始仲裁 {len(results_by_rule)} 个引擎的检测结果")
        
        # 1. 将所有结果转换为标准化的Hit结构
        all_hits = self._convert_to_hits(results_by_rule)
        
        # 2. 应用基于最大匹配原则的贪心合并算法
        if self.config.enable_max_matching:
            merged_hits = self._merge_hits_greedy(all_hits)
        else:
            merged_hits = all_hits
        
        # 3. 增强多引擎匹配的置信度
        enhanced_hits = self._enhance_multi_engine_matches(merged_hits, results_by_rule)
        
        # 4. 过滤低置信度结果
        filtered_hits = self._filter_by_confidence(enhanced_hits)
        
        # 5. 应用分类权重
        weighted_hits = self._apply_category_weights(filtered_hits)
        
        # 6. 转换回DetectionResultItem格式并排序
        final_results = self._convert_to_detection_results(weighted_hits)
        final_results = self._sort_results(final_results)
        
        # 7. 生成汇总信息
        summary = self._generate_summary(final_results)
        
        logger.debug(f"仲裁完成，最终结果: {len(final_results)} 个匹配")
        
        return final_results, summary
    
    def _convert_to_hits(self, results_by_rule: Dict[str, List[DetectionResultItem]]) -> List[Hit]:
        """将检测结果转换为标准化的Hit结构"""
        all_hits = []
        
        for rule_name, results in results_by_rule.items():
            for result in results:
                # 应用引擎权重调整置信度
                engine_weight = self.config.engine_weights.get(rule_name, 1.0)
                adjusted_confidence = min(1.0, result.confidence * engine_weight)
                
                # 提取位置信息
                if result.positions:
                    for pos in result.positions:
                        hit = Hit(
                            word=result.matched_word,
                            start=pos.start,
                            end=pos.end,
                            category=result.category,
                            source=rule_name,
                            confidence=adjusted_confidence,
                            match_type=result.match_type,
                            detection_method=result.detection_method,
                            suggestion=result.suggestion
                        )
                        all_hits.append(hit)
                else:
                    # 如果没有位置信息，创建一个默认的Hit
                    hit = Hit(
                        word=result.matched_word,
                        start=0,
                        end=len(result.matched_word),
                        category=result.category,
                        source=rule_name,
                        confidence=adjusted_confidence,
                        match_type=result.match_type,
                        detection_method=result.detection_method,
                        suggestion=result.suggestion
                    )
                    all_hits.append(hit)
        
        return all_hits
    
    def _merge_hits_greedy(self, all_hits: List[Hit]) -> List[Hit]:
        """
        基于贪心策略的最大匹配算法合并命中结果
        
        核心思想：在所有可能的匹配结果中，总是选择最长、最具体的匹配项
        
        Args:
            all_hits: 所有引擎的命中结果
            
        Returns:
            合并后的无重叠、无冗余的命中结果
        """
        if not all_hits:
            return []
        
        # 步骤1：多级排序 - 这是算法的关键
        # 第一排序键：按start(起始索引)升序排列
        # 第二排序键：如果start相同，则按end(结束索引)降序排列
        # 这确保了在同一个起始位置，更长的词会排在前面
        sorted_hits = sorted(all_hits, key=lambda x: (x.start, -x.end))
        
        # 步骤2：遍历与过滤 - 贪心选择
        final_hits = []
        last_accepted_end = -1
        
        for hit in sorted_hits:
            # 检查重叠：判断当前hit的起始位置是否小于上一个被接受的hit的结束位置
            if hit.start >= last_accepted_end:
                # 没有重叠，这是一个全新的、有效的命中
                final_hits.append(hit)
                last_accepted_end = hit.end
                logger.debug(f"接受命中: '{hit.word}' at [{hit.start}:{hit.end}] from {hit.source}")
            else:
                # 有重叠，根据最大匹配原则忽略这个较短或重叠的匹配
                logger.debug(f"忽略重叠命中: '{hit.word}' at [{hit.start}:{hit.end}] from {hit.source}")
        
        logger.debug(f"贪心合并完成: {len(all_hits)} -> {len(final_hits)} 个命中")
        return final_hits
    
    def _enhance_multi_engine_matches(
        self, 
        hits: List[Hit],
        results_by_rule: Dict[str, List[DetectionResultItem]]
    ) -> List[Hit]:
        """增强多引擎匹配的置信度"""
        enhanced_hits = []
        
        for hit in hits:
            # 计算有多少个引擎匹配了这个词在相似位置
            match_count = 0
            for rule_results in results_by_rule.values():
                for rule_result in rule_results:
                    if (rule_result.matched_word == hit.word and 
                        rule_result.category == hit.category):
                        # 检查位置是否相近
                        if rule_result.positions:
                            for pos in rule_result.positions:
                                if abs(pos.start - hit.start) <= 2:  # 位置容忍度
                                    match_count += 1
                                    break
                        else:
                            match_count += 1
                        break
            
            # 如果多个引擎都匹配，提升置信度
            if match_count > 1:
                boost = self.config.confidence_boost_factor * (match_count - 1)
                enhanced_confidence = min(1.0, hit.confidence + boost)
                
                enhanced_hit = Hit(
                    word=hit.word,
                    start=hit.start,
                    end=hit.end,
                    category=hit.category,
                    source=hit.source,
                    confidence=enhanced_confidence,
                    match_type=hit.match_type,
                    detection_method=hit.detection_method,
                    suggestion=hit.suggestion
                )
                enhanced_hits.append(enhanced_hit)
            else:
                enhanced_hits.append(hit)
        
        return enhanced_hits
    
    def _filter_by_confidence(self, hits: List[Hit]) -> List[Hit]:
        """按置信度过滤"""
        return [hit for hit in hits if hit.confidence >= self.config.confidence_threshold]
    
    def _apply_category_weights(self, hits: List[Hit]) -> List[Hit]:
        """应用分类权重"""
        weighted_hits = []
        
        for hit in hits:
            weight = self.config.category_weights.get(hit.category, 1.0)
            weighted_confidence = min(1.0, hit.confidence * weight)
            
            weighted_hit = Hit(
                word=hit.word,
                start=hit.start,
                end=hit.end,
                category=hit.category,
                source=hit.source,
                confidence=weighted_confidence,
                match_type=hit.match_type,
                detection_method=hit.detection_method,
                suggestion=hit.suggestion
            )
            weighted_hits.append(weighted_hit)
        
        return weighted_hits
    
    def _convert_to_detection_results(self, hits: List[Hit]) -> List[DetectionResultItem]:
        """将Hit结构转换回DetectionResultItem格式"""
        results = []
        
        for hit in hits:
            result = DetectionResultItem(
                matched_word=hit.word,
                category=hit.category,
                match_type=hit.match_type,
                confidence=hit.confidence,
                positions=hit.positions,
                detection_method=hit.detection_method,
                suggestion=hit.suggestion
            )
            results.append(result)
        
        return results
    
    def _sort_results(self, results: List[DetectionResultItem]) -> List[DetectionResultItem]:
        """排序结果"""
        # 按置信度降序，然后按分类权重降序
        def sort_key(result):
            category_weight = self.config.category_weights.get(result.category, 1.0)
            return (-result.confidence, -category_weight)
        
        return sorted(results, key=sort_key)
    
    def _generate_summary(self, results: List[DetectionResultItem]) -> DetectionSummary:
        """生成检测汇总"""
        if not results:
            return DetectionSummary(
                total_matches=0,
                categories_found=[],
                highest_risk_category=None
            )
        
        # 统计分类
        categories_found = list(set(result.category for result in results))
        
        # 找出最高风险分类
        highest_risk_category = None
        if results:
            # 按置信度和分类权重排序后的第一个
            highest_confidence_result = results[0]
            highest_risk_category = highest_confidence_result.category
        
        return DetectionSummary(
            total_matches=len(results),
            categories_found=categories_found,
            highest_risk_category=highest_risk_category
        )
    
    def calculate_overall_risk_level(self, results: List[DetectionResultItem]) -> RiskLevel:
        """计算整体风险等级"""
        if not results:
            return RiskLevel.LOW
        
        # 基于最高置信度和匹配数量
        max_confidence = max(result.confidence for result in results)
        match_count = len(results)
        
        # 计算加权分数
        weighted_score = max_confidence
        
        # 高权重分类的额外权重（权重>=90的分类视为高风险）
        for result in results:
            category_weight = self.config.category_weights.get(result.category, 1.0)
            if category_weight >= 0.9:  # 高权重分类
                weighted_score += 0.1
        
        # 多匹配的额外权重
        if match_count >= 5:
            weighted_score += 0.2
        elif match_count >= 3:
            weighted_score += 0.1
        
        # 确定风险等级
        if weighted_score >= 0.9:
            return RiskLevel.CRITICAL
        elif weighted_score >= 0.7:
            return RiskLevel.HIGH
        elif weighted_score >= 0.5:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _filter_by_confidence(self, results: List[DetectionResultItem]) -> List[DetectionResultItem]:
        """按置信度过滤"""
        return [
            result for result in results 
            if result.confidence >= self.config.confidence_threshold
        ]
    
    def _sort_results(self, results: List[DetectionResultItem]) -> List[DetectionResultItem]:
        """排序结果"""
        # 按置信度降序，然后按分类权重降序
        def sort_key(result):
            category_weight = self.config.category_weights.get(result.category, 1.0)
            return (-result.confidence, -category_weight)
        
        return sorted(results, key=sort_key)
    
    def _generate_summary(self, results: List[DetectionResultItem]) -> DetectionSummary:
        """生成检测汇总"""
        if not results:
            return DetectionSummary(
                total_matches=0,
                categories_found=[],
                highest_risk_category=None
            )
        
        # 统计分类
        categories_found = list(set(result.category for result in results))
        
        # 找出最高风险分类
        highest_risk_category = None
        if results:
            # 按置信度和分类权重排序后的第一个
            highest_confidence_result = results[0]
            highest_risk_category = highest_confidence_result.category
        
        return DetectionSummary(
            total_matches=len(results),
            categories_found=categories_found,
            highest_risk_category=highest_risk_category
        )
    
    def calculate_overall_risk_level(self, results: List[DetectionResultItem]) -> RiskLevel:
        """计算整体风险等级"""
        if not results:
            return RiskLevel.LOW
        
        # 基于最高置信度和匹配数量
        max_confidence = max(result.confidence for result in results)
        match_count = len(results)
        
        # 计算加权分数
        weighted_score = max_confidence
        
        # 高权重分类的额外权重（权重>=90的分类视为高风险）
        for result in results:
            category_weight = self.config.category_weights.get(result.category, 1.0)
            if category_weight >= 0.9:  # 高权重分类
                weighted_score += 0.1
        
        # 多匹配的额外权重
        if match_count >= 5:
            weighted_score += 0.2
        elif match_count >= 3:
            weighted_score += 0.1
        
        # 确定风险等级
        if weighted_score >= 0.9:
            return RiskLevel.CRITICAL
        elif weighted_score >= 0.7:
            return RiskLevel.HIGH
        elif weighted_score >= 0.5:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
