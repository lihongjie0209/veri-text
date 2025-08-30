"""
基于规则的敏感词检测器 - 使用YAML配置
"""
import ahocorasick
import time
from typing import List, Dict, Set, Optional, Any
from pathlib import Path

from ..models import (
    DetectionConfig, DetectionResultItem,
    MatchType, DetectionMethod, Position
)
from ..core import get_logger, DetectionError
from .text_processor import TextPreprocessor
from .yaml_config_reader import YamlConfigReader

logger = get_logger()


class RuleBasedDetector:
    """基于规则的敏感词检测器 - 使用YAML配置"""
    
    def __init__(self, config_file: str = "config/sensitive_words.yaml"):
        """
        初始化检测器
        
        Args:
            config_file: YAML配置文件路径
        """
        self.config_reader = YamlConfigReader(config_file)
        self.text_processor = TextPreprocessor()
        
        # AC自动机，存储所有敏感词
        self.automaton: ahocorasick.Automaton = None
        
        # 词汇到分类的映射 (使用词库名称作为分类)
        self.word_to_category: Dict[str, str] = {}
        
        # 词库加载状态
        self.loaded = False
        self.last_load_time = 0
        
        logger.info(f"规则检测器初始化完成，配置文件: {config_file}")
    
    async def load_wordlists(self) -> None:
        """从YAML配置加载敏感词库"""
        try:
            start_time = time.time()
            
            # 重新加载配置
            self.config_reader.reload_config()
            
            # 创建新的AC自动机
            self.automaton = ahocorasick.Automaton()
            self.word_to_category.clear()
            
            # 从配置中获取所有启用的词库
            enabled_wordlists = self.config_reader.get_enabled_wordlists()
            
            total_words = 0
            
            for wordlist_config in enabled_wordlists:
                # 直接使用词库名称作为分类
                category = wordlist_config.name
                
                # 加载词汇
                base_path = self.config_reader.config_file.parent.parent
                words = wordlist_config.load_words(base_path)
                
                for word in words:
                    if word and not word.startswith('#'):  # 跳过空行和注释
                        # 标准化敏感词
                        normalized_word = self.text_processor.normalize(word)
                        if normalized_word:
                            self.automaton.add_word(normalized_word, (word, category))
                            self.word_to_category[normalized_word] = category
                            total_words += 1
                
                logger.info(f"加载词库 '{wordlist_config.name}' ({category}): {len(words)} 个词")
            
            # 构建自动机
            if total_words > 0:
                self.automaton.make_automaton()
            
            self.loaded = True
            self.last_load_time = time.time()
            load_duration = (self.last_load_time - start_time) * 1000
            
            logger.info(f"词库加载完成，总计 {total_words} 个敏感词，耗时 {load_duration:.2f}ms")
            
        except Exception as e:
            logger.error(f"词库加载失败: {e}")
            raise DetectionError(f"词库加载失败: {e}")
    
    async def detect(
        self, 
        text: str, 
        config: DetectionConfig
    ) -> List[DetectionResultItem]:
        """
        执行规则匹配检测
        
        Args:
            text: 待检测文本
            config: 检测配置
            
        Returns:
            检测结果列表
        """
        if not self.loaded:
            await self.load_wordlists()
        
        if not text.strip() or not self.automaton:
            return []
        
        try:
            start_time = time.time()
            
            # 文本预处理
            normalized_text = self.text_processor.normalize(text)
            cleaned_text = self.text_processor.clean_for_matching(normalized_text)
            
            results = []
            
            # 确定要检测的分类 (直接使用字符串比较)
            if config.categories:
                categories_to_check = set(config.categories)
            else:
                categories_to_check = None  # 检测所有分类
            
            # 执行匹配
            for end_index, (original_word, word_category) in self.automaton.iter(cleaned_text):
                # 检查分类是否在检测范围内
                if categories_to_check and word_category not in categories_to_check:
                    continue
                    
                start_index = end_index - len(original_word) + 1
                
                # 边界检查
                if self._is_valid_match(cleaned_text, start_index, end_index):
                    # 创建检测结果 (直接使用字符串分类)
                    result_item = DetectionResultItem(
                        matched_word=original_word,
                        category=word_category,  # 直接使用字符串分类
                        match_type=MatchType.EXACT,
                        confidence=1.0,  # 规则匹配置信度为1
                        positions=[Position(start=start_index, end=end_index + 1)] if config.return_positions else [],
                        detection_method=DetectionMethod.RULE,
                        suggestion="***" if config.return_suggestions else None
                    )
                    results.append(result_item)
            
            detection_time = (time.time() - start_time) * 1000
            logger.debug(f"规则检测完成，发现 {len(results)} 个匹配，耗时 {detection_time:.2f}ms")
            
            return results
            
        except Exception as e:
            logger.error(f"规则检测失败: {e}")
            raise DetectionError(f"规则检测失败: {e}")
    
    def _is_valid_match(self, text: str, start: int, end: int) -> bool:
        """
        验证匹配是否有效（边界检查）
        
        Args:
            text: 文本
            start: 起始位置
            end: 结束位置
            
        Returns:
            是否为有效匹配
        """
        # 简化边界检查，主要防止部分匹配
        # 比如"法轮功"不应该匹配"大法轮功夫"中的"法轮功"
        
        # 检查前边界 - 只检查中文字符
        if start > 0:
            prev_char = text[start - 1]
            # 如果前一个字符是中文字符，可能是部分匹配
            if '\u4e00' <= prev_char <= '\u9fff':
                # 可以考虑放宽条件，或者使用更智能的边界检查
                pass
        
        # 检查后边界 - 只检查中文字符  
        if end < len(text) - 1:
            next_char = text[end + 1]
            # 如果后一个字符是中文字符，可能是部分匹配
            if '\u4e00' <= next_char <= '\u9fff':
                # 可以考虑放宽条件，或者使用更智能的边界检查
                pass
        
        # 对于中文文本，暂时返回True，因为中文没有明显的单词边界
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """获取检测器状态"""
        enabled_wordlists = self.config_reader.get_enabled_wordlists() if self.config_reader else []
        
        return {
            "loaded": self.loaded,
            "last_load_time": self.last_load_time,
            "enabled_wordlists": len(enabled_wordlists),
            "total_words": len(self.word_to_category) if self.loaded else 0,
            "wordlists": [
                {
                    "name": wl.name,
                    "file": wl.file,
                    "description": wl.description
                }
                for wl in enabled_wordlists
            ]
        }
