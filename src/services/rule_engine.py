"""
检测规则引擎 - 每个规则有自己的预处理机制
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Set
import ahocorasick
import jieba
import re
from dataclasses import dataclass

from ..models.detection import DetectionResultItem, DetectionConfig
from ..models.common import MatchType, DetectionMethod, Position
from ..core import get_logger

logger = get_logger()


@dataclass
class RuleConfig:
    """规则配置"""
    name: str
    rule_type: str
    enabled: bool = True
    priority: int = 0
    wordlist_ids: List[int] = None
    config: Dict[str, Any] = None


class BaseDetectionRule(ABC):
    """检测规则基类"""
    
    def __init__(self, rule_config: RuleConfig):
        self.rule_config = rule_config
        self.name = rule_config.name
        self.enabled = rule_config.enabled
        self.priority = rule_config.priority
        self.config = rule_config.config or {}
    
    @abstractmethod
    def preprocess_text(self, text: str) -> str:
        """预处理文本 - 每个规则有自己的预处理逻辑"""
        pass
    
    @abstractmethod
    def load_wordlist(self, words_by_category: Dict[str, List[str]]):
        """加载词库"""
        pass
    
    @abstractmethod
    def detect(self, text: str, config: DetectionConfig) -> List[DetectionResultItem]:
        """执行检测"""
        pass
    
    def is_valid_match(self, text: str, start: int, end: int) -> bool:
        """边界检查 - 可以被子类重写"""
        return True


class ExactMatchRule(BaseDetectionRule):
    """精确匹配规则 - 基于AC自动机"""
    
    def __init__(self, rule_config: RuleConfig):
        super().__init__(rule_config)
        self.automatons: Dict[str, ahocorasick.Automaton] = {}
        
        # 规则特定配置
        self.remove_spaces = self.config.get('remove_spaces', True)
        self.case_sensitive = self.config.get('case_sensitive', False)
        self.check_boundaries = self.config.get('check_boundaries', True)
    
    def preprocess_text(self, text: str) -> str:
        """精确匹配的预处理"""
        processed = text
        
        # 大小写处理
        if not self.case_sensitive:
            processed = processed.lower()
        
        # 移除空格和特殊字符
        if self.remove_spaces:
            # 移除常见的干扰字符
            noise_chars = r'[\s\.\*_\-\+\|\\\/\[\]{}()（）【】《》""'']'
            processed = re.sub(noise_chars, '', processed)
        
        return processed
    
    def load_wordlist(self, words_by_category: Dict[str, List[str]]):
        """加载词库到AC自动机"""
        self.automatons.clear()
        
        for category, words in words_by_category.items():
            if not words:
                continue
                
            automaton = ahocorasick.Automaton()
            
            for word in words:
                if not word.strip():
                    continue
                
                # 预处理敏感词
                processed_word = self.preprocess_text(word.strip())
                if processed_word:
                    automaton.add_word(processed_word, (word, category))
            
            # 构建自动机
            automaton.make_automaton()
            self.automatons[category] = automaton
            
        logger.info(f"ExactMatchRule 加载了 {len(self.automatons)} 个分类的词库")
    
    def detect(self, text: str, config: DetectionConfig) -> List[DetectionResultItem]:
        """执行精确匹配检测"""
        if not text.strip():
            return []
        
        # 预处理文本
        processed_text = self.preprocess_text(text)
        results = []
        
        # 确定要检测的分类
        categories_to_check = config.categories or list(self.automatons.keys())
        
        for category in categories_to_check:
            if category not in self.automatons:
                continue
            
            automaton = self.automatons[category]
            
            # 执行匹配
            for end_index, (original_word, word_category) in automaton.iter(processed_text):
                start_index = end_index - len(original_word) + 1
                
                # 边界检查
                if self.check_boundaries and not self.is_valid_match(processed_text, start_index, end_index):
                    continue
                
                # 创建检测结果
                result_item = DetectionResultItem(
                    matched_word=original_word,
                    category=word_category,
                    match_type=MatchType.EXACT,
                    confidence=1.0,
                    positions=[Position(start=start_index, end=end_index + 1)] if config.return_positions else [],
                    detection_method=DetectionMethod.RULE,
                    suggestion="***" if config.return_suggestions else None
                )
                results.append(result_item)
        
        return results
    
    def is_valid_match(self, text: str, start: int, end: int) -> bool:
        """检查边界"""
        # 检查前边界
        if start > 0:
            prev_char = text[start - 1]
            if prev_char.isalnum() or '\u4e00' <= prev_char <= '\u9fff':
                return False
        
        # 检查后边界
        if end < len(text) - 1:
            next_char = text[end + 1]
            if next_char.isalnum() or '\u4e00' <= next_char <= '\u9fff':
                return False
        
        return True


class JiebaRule(BaseDetectionRule):
    """基于jieba分词的检测规则"""
    
    def __init__(self, rule_config: RuleConfig):
        super().__init__(rule_config)
        self.word_sets: Dict[str, Set[str]] = {}
        
        # 规则特定配置
        self.use_hmm = self.config.get('use_hmm', True)
        self.cut_all = self.config.get('cut_all', False)
        self.case_sensitive = self.config.get('case_sensitive', False)
        
        # 初始化jieba
        jieba.initialize()
    
    def preprocess_text(self, text: str) -> str:
        """jieba规则的预处理"""
        processed = text
        
        # 大小写处理
        if not self.case_sensitive:
            processed = processed.lower()
        
        # 保留标点符号和空格，因为jieba需要这些来正确分词
        return processed
    
    def load_wordlist(self, words_by_category: Dict[str, List[str]]):
        """加载词库到集合中"""
        self.word_sets.clear()
        
        for category, words in words_by_category.items():
            word_set = set()
            for word in words:
                if not word.strip():
                    continue
                
                # 预处理敏感词
                processed_word = self.preprocess_text(word.strip())
                if processed_word:
                    word_set.add(processed_word)
                    # 同时添加原词到jieba词典
                    jieba.add_word(processed_word)
            
            self.word_sets[category] = word_set
        
        logger.info(f"JiebaRule 加载了 {len(self.word_sets)} 个分类的词库")
    
    def detect(self, text: str, config: DetectionConfig) -> List[DetectionResultItem]:
        """执行基于分词的检测"""
        if not text.strip():
            return []
        
        # 预处理文本
        processed_text = self.preprocess_text(text)
        
        # 使用jieba分词
        if self.cut_all:
            words = jieba.cut(processed_text, cut_all=True, HMM=self.use_hmm)
        else:
            words = jieba.cut(processed_text, HMM=self.use_hmm)
        
        word_list = list(words)
        results = []
        
        # 确定要检测的分类
        categories_to_check = config.categories or list(self.word_sets.keys())
        
        # 检查每个分词结果
        current_pos = 0
        for word in word_list:
            if not word.strip():
                current_pos += len(word)
                continue
            
            # 在词库中查找
            for category in categories_to_check:
                if category not in self.word_sets:
                    continue
                
                if word in self.word_sets[category]:
                    # 找到在原文本中的位置
                    start_pos = processed_text.find(word, current_pos)
                    if start_pos != -1:
                        end_pos = start_pos + len(word) - 1
                        
                        result_item = DetectionResultItem(
                            matched_word=word,
                            category=category,
                            match_type=MatchType.EXACT,
                            confidence=0.9,  # jieba分词的置信度稍低
                            positions=[Position(start=start_pos, end=end_pos + 1)] if config.return_positions else [],
                            detection_method=DetectionMethod.RULE,
                            suggestion="***" if config.return_suggestions else None
                        )
                        results.append(result_item)
            
            current_pos += len(word)
        
        return results


class RegexRule(BaseDetectionRule):
    """正则表达式匹配规则"""
    
    def __init__(self, rule_config: RuleConfig):
        super().__init__(rule_config)
        self.patterns: Dict[str, List[re.Pattern]] = {}
        
        # 规则特定配置
        self.case_sensitive = self.config.get('case_sensitive', False)
        self.multiline = self.config.get('multiline', False)
        self.dotall = self.config.get('dotall', False)
    
    def preprocess_text(self, text: str) -> str:
        """正则规则的预处理"""
        processed = text
        
        # 大小写处理
        if not self.case_sensitive:
            processed = processed.lower()
        
        return processed
    
    def load_wordlist(self, words_by_category: Dict[str, List[str]]):
        """加载词库为正则表达式"""
        self.patterns.clear()
        
        # 正则标志
        flags = 0
        if not self.case_sensitive:
            flags |= re.IGNORECASE
        if self.multiline:
            flags |= re.MULTILINE
        if self.dotall:
            flags |= re.DOTALL
        
        for category, words in words_by_category.items():
            pattern_list = []
            for word in words:
                if not word.strip():
                    continue
                
                try:
                    # 将敏感词转换为正则表达式
                    pattern_str = re.escape(word.strip())
                    pattern = re.compile(pattern_str, flags)
                    pattern_list.append(pattern)
                except re.error as e:
                    logger.warning(f"无效的正则表达式: {word} - {e}")
                    continue
            
            self.patterns[category] = pattern_list
        
        logger.info(f"RegexRule 加载了 {len(self.patterns)} 个分类的词库")
    
    def detect(self, text: str, config: DetectionConfig) -> List[DetectionResultItem]:
        """执行正则匹配检测"""
        if not text.strip():
            return []
        
        # 预处理文本
        processed_text = self.preprocess_text(text)
        results = []
        
        # 确定要检测的分类
        categories_to_check = config.categories or list(self.patterns.keys())
        
        for category in categories_to_check:
            if category not in self.patterns:
                continue
            
            for pattern in self.patterns[category]:
                for match in pattern.finditer(processed_text):
                    result_item = DetectionResultItem(
                        matched_word=match.group(),
                        category=category,
                        match_type=MatchType.REGEX,
                        confidence=0.95,
                        positions=[Position(start=match.start(), end=match.end())] if config.return_positions else [],
                        detection_method=DetectionMethod.RULE,
                        suggestion="***" if config.return_suggestions else None
                    )
                    results.append(result_item)
        
        return results
