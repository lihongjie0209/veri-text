"""
文本预处理工具
"""
import re
import opencc
from typing import List, Tuple, Optional

from ..core import get_logger

logger = get_logger()


class TextPreprocessor:
    """文本预处理器"""
    
    def __init__(self):
        """初始化预处理器"""
        try:
            # 初始化繁简转换器
            self.converter = opencc.OpenCC('t2s')  # 繁体转简体
            logger.info("文本预处理器初始化成功")
        except Exception as e:
            logger.error(f"文本预处理器初始化失败: {e}")
            raise
    
    def normalize(self, text: str, remove_noise: bool = False) -> str:
        """
        标准化文本
        
        Args:
            text: 原始文本
            remove_noise: 是否移除噪音字符
            
        Returns:
            标准化后的文本
        """
        if not text:
            return ""
        
        try:
            # 1. 繁体转简体
            text = self.converter.convert(text)
            
            # 2. 统一大小写
            text = text.lower()
            
            # 3. 移除多余空白
            text = re.sub(r'\s+', ' ', text).strip()
            
            # 4. 处理特殊字符（可选）
            if remove_noise:
                # 保留中文、英文、数字和基本标点
                text = re.sub(r'[^\w\s\u4e00-\u9fff，。！？；：""''（）【】《》]', '', text)
            
            return text
            
        except Exception as e:
            logger.error(f"文本标准化失败: {e}")
            return text  # 返回原文本
    
    def extract_positions_mapping(
        self, 
        original: str, 
        normalized: str
    ) -> List[Tuple[int, int]]:
        """
        提取原文和标准化文本的位置映射
        
        Args:
            original: 原始文本
            normalized: 标准化文本
            
        Returns:
            位置映射列表 [(原始位置, 标准化位置), ...]
        """
        # 简单实现：假设位置基本对应
        # 实际项目中可能需要更复杂的映射算法
        mapping = []
        
        # 基础映射：按字符对应
        min_len = min(len(original), len(normalized))
        for i in range(min_len):
            mapping.append((i, i))
        
        return mapping
    
    def clean_for_matching(self, text: str) -> str:
        """
        为匹配过程清理文本（移除干扰字符）
        
        Args:
            text: 输入文本
            
        Returns:
            清理后的文本
        """
        if not text:
            return ""
        
        # 移除常见的干扰字符
        # 空格、点、星号、下划线等
        noise_chars = r'[\s\.\*_\-\+\|\\\/\[\]{}()（）【】《》""'']'
        cleaned = re.sub(noise_chars, '', text)
        
        return cleaned
    
    def split_text(self, text: str, max_length: int = 1000) -> List[str]:
        """
        分割长文本
        
        Args:
            text: 输入文本
            max_length: 最大长度
            
        Returns:
            分割后的文本片段列表
        """
        if len(text) <= max_length:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + max_length
            
            # 尝试在句号、问号、感叹号处分割
            if end < len(text):
                for i in range(end, start + max_length // 2, -1):
                    if text[i] in '。！？\n':
                        end = i + 1
                        break
            
            chunks.append(text[start:end])
            start = end
        
        return chunks
