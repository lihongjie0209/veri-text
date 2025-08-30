"""
增强的敏感词检测服务管理器
集成多规则检测、结果仲裁和YAML配置系统
"""
import time
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..models.detection import (
    DetectionRequest, DetectionResponse, DetectionResultItem, 
    DetectionSummary, DetectionConfig
)
from ..models.common import RiskLevel, DetectionMode
from ..services.rule_engine import (
    BaseDetectionRule, ExactMatchRule, JiebaRule, RegexRule, 
    RuleConfig
)
from ..services.result_arbitrator import DetectionResultArbitrator, ArbitrationConfig
from ..services.yaml_config_reader import YamlConfigReader
from ..core import get_logger, get_settings, DetectionError

logger = get_logger()


class EnhancedDetectionService:
    """增强的敏感词检测服务"""
    
    def __init__(self, config_file: str = "config/sensitive_words.yaml"):
        """初始化检测服务"""
        self.settings = get_settings()
        
        # 初始化YAML配置读取器
        self.config_reader = YamlConfigReader(config_file)
        
        # 初始化组件
        self.arbitrator = DetectionResultArbitrator(yaml_config_reader=self.config_reader)
        
        # 检测规则
        self.rules: Dict[str, BaseDetectionRule] = {}
        
        # 服务状态
        self.start_time = time.time()
        self.request_count = 0
        
        # 加载检测规则
        self._load_detection_rules()
        
        logger.info("增强敏感词检测服务初始化完成 - 使用YAML配置")
    
    def _load_detection_rules(self):
        """从YAML配置加载检测规则"""
        try:
            # 重新加载配置
            self.config_reader.reload_config()
            
            # 创建多种检测规则
            self._create_default_rules()
            
            # 为规则加载词库
            self._load_wordlists_for_rules()
                
        except Exception as e:
            logger.error(f"加载检测规则失败: {e}")
            # 创建默认规则
            self._create_default_rules()
    
    def _create_rule_instance(self, rule_config: RuleConfig) -> Optional[BaseDetectionRule]:
        """创建规则实例"""
        rule_type = rule_config.rule_type
        
        if rule_type == 'exact':
            return ExactMatchRule(rule_config)
        elif rule_type == 'jieba':
            return JiebaRule(rule_config)
        elif rule_type == 'regex':
            return RegexRule(rule_config)
        else:
            logger.warning(f"未知的规则类型: {rule_type}")
            return None
    
    def _create_default_rules(self):
        """创建默认检测规则"""
        # 精确匹配规则
        exact_config = RuleConfig(
            name="default_exact",
            rule_type="exact",
            enabled=True,
            priority=100,
            config={
                "remove_spaces": True,
                "case_sensitive": False,
                "check_boundaries": True
            }
        )
        self.rules["default_exact"] = ExactMatchRule(exact_config)
        
        # jieba分词规则
        jieba_config = RuleConfig(
            name="default_jieba",
            rule_type="jieba",
            enabled=True,
            priority=90,
            config={
                "use_hmm": True,
                "cut_all": False,
                "case_sensitive": False
            }
        )
        self.rules["default_jieba"] = JiebaRule(jieba_config)
        
        logger.info("创建了默认检测规则")
    
    def _load_wordlists_for_rules(self):
        """为规则加载词库"""
        for rule_name, rule in self.rules.items():
            try:
                # 获取所有启用的词库
                enabled_wordlists = self.config_reader.get_enabled_wordlists()
                
                # 按分类组织词汇
                words_by_category = {}
                base_path = self.config_reader.config_file.parent.parent
                
                for wordlist_config in enabled_wordlists:
                    category = wordlist_config.name  # 使用name作为分类
                    words = wordlist_config.load_words(base_path)
                    
                    if category not in words_by_category:
                        words_by_category[category] = []
                    words_by_category[category].extend(words)
                
                # 加载到规则
                rule.load_wordlist(words_by_category)
                
                logger.debug(f"规则 {rule_name} 加载了 {len(words_by_category)} 个分类的词库")
                
            except Exception as e:
                logger.error(f"为规则 {rule_name} 加载词库失败: {e}")
    
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
            
            # 执行多规则检测
            results_by_rule = await self._execute_multi_rule_detection(request)
            
            # 结果仲裁
            final_results, summary = self.arbitrator.arbitrate(results_by_rule)
            
            # 计算风险等级
            risk_level = self.arbitrator.calculate_overall_risk_level(final_results)
            
            # 计算整体评分
            overall_score = 0.0
            if final_results:
                overall_score = max(result.confidence for result in final_results)
            
            # 构建响应
            response = DetectionResponse(
                is_sensitive=len(final_results) > 0,
                risk_level=risk_level,
                overall_score=overall_score,
                detection_time_ms=int((time.time() - start_time) * 1000),
                detection_mode_used=request.config.detection_mode,
                results=final_results,
                summary=summary,
                message="检测完成"
            )
            
            # 记录检测历史
            await self._record_detection_history(request, response, results_by_rule)
            
            detection_time = (time.time() - start_time) * 1000
            logger.info(f"检测完成，耗时 {detection_time:.2f}ms，发现敏感内容: {response.is_sensitive}")
            
            return response
            
        except Exception as e:
            logger.error(f"检测过程出错: {e}")
            raise DetectionError(f"检测失败: {e}")
    
    async def _execute_multi_rule_detection(
        self, 
        request: DetectionRequest
    ) -> Dict[str, List[DetectionResultItem]]:
        """执行多规则检测"""
        text = request.text
        config = request.config
        
        results_by_rule = {}
        
        # 根据检测模式确定使用的规则
        rules_to_use = self._get_rules_for_mode(config.detection_mode)
        
        for rule_name, rule in rules_to_use.items():
            try:
                if not rule.enabled:
                    continue
                
                # 执行检测
                results = rule.detect(text, config)
                results_by_rule[rule_name] = results
                
                logger.debug(f"规则 {rule_name} 检测到 {len(results)} 个匹配")
                
            except Exception as e:
                logger.error(f"规则 {rule_name} 检测失败: {e}")
                results_by_rule[rule_name] = []
        
        return results_by_rule
    
    def _get_rules_for_mode(self, detection_mode: DetectionMode) -> Dict[str, BaseDetectionRule]:
        """根据检测模式获取规则"""
        if detection_mode == DetectionMode.RULE:
            # 仅规则检测，排除语义规则
            return {
                name: rule for name, rule in self.rules.items()
                if rule.rule_config.rule_type != 'semantic'
            }
        elif detection_mode == DetectionMode.SEMANTIC:
            # 仅语义检测
            return {
                name: rule for name, rule in self.rules.items()
                if rule.rule_config.rule_type == 'semantic'
            }
        else:  # HYBRID
            # 所有规则
            return self.rules
    
    async def _record_detection_history(
        self, 
        request: DetectionRequest, 
        response: DetectionResponse,
        results_by_rule: Dict[str, List[DetectionResultItem]]
    ):
        """记录检测历史到日志"""
        try:
            # 计算文本哈希
            text_hash = hashlib.sha256(request.text.encode('utf-8')).hexdigest()
            
            # 文本预览
            text_preview = request.text[:200]
            
            # 使用的规则ID
            rule_ids = list(results_by_rule.keys())
            
            # 记录检测结果到日志
            logger.info(f"检测历史记录: hash={text_hash[:8]}, "
                       f"preview='{text_preview}', "
                       f"sensitive={response.is_sensitive}, "
                       f"risk={response.risk_level.value}, "
                       f"score={response.overall_score:.2f}, "
                       f"time={response.detection_time_ms}ms, "
                       f"rules={rule_ids}, "
                       f"matches={len(response.results)}")
                
        except Exception as e:
            logger.error(f"记录检测历史失败: {e}")
    
    def reload_rules(self):
        """重新加载检测规则"""
        logger.info("重新加载检测规则")
        self.rules.clear()
        self._load_detection_rules()
    
    def reload_wordlists(self):
        """重新加载词库"""
        logger.info("重新加载词库")
        self.config_reader.reload_config()
        self._load_wordlists_for_rules()
    
    def reload_config(self):
        """重新加载整个配置"""
        logger.info("重新加载YAML配置")
        self.config_reader.reload_config()
        self.rules.clear()
        self._load_detection_rules()
    
    async def health_check(self) -> Dict[str, Any]:
        """服务健康检查"""
        uptime_seconds = int(time.time() - self.start_time)
        
        # 词库统计信息
        enabled_wordlists = self.config_reader.get_enabled_wordlists()
        total_words = 0
        wordlist_stats = {
            "total_wordlists": len(enabled_wordlists),
            "enabled_wordlists": len(enabled_wordlists),
            "wordlist_details": []
        }
        
        base_path = self.config_reader.config_file.parent.parent
        for wordlist_config in enabled_wordlists:
            words = wordlist_config.load_words(base_path)
            word_count = len(words)
            total_words += word_count
            
            wordlist_stats["wordlist_details"].append({
                "name": wordlist_config.name,
                "description": wordlist_config.description,
                "file": wordlist_config.file,
                "word_count": word_count,
                "enabled": wordlist_config.enabled
            })
        
        wordlist_stats["total_words"] = total_words
        
        # 规则状态
        rule_status = {}
        for rule_name, rule in self.rules.items():
            rule_status[rule_name] = {
                "enabled": rule.enabled,
                "priority": rule.priority,
                "type": rule.rule_config.rule_type
            }
        
        return {
            "status": "healthy",
            "version": self.settings.app_version,
            "uptime_seconds": uptime_seconds,
            "request_count": self.request_count,
            "wordlist_stats": wordlist_stats,
            "rules": rule_status,
            "settings": {
                "max_text_length": self.settings.max_text_length,
            }
        }
