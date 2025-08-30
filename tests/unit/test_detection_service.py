"""
单元测试 - 检测服务测试 - YAML配置版本
"""
import pytest
import asyncio
from unittest.mock import MagicMock, patch

import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.models import DetectionRequest, DetectionConfig, DetectionMode
from src.services import SensitiveWordDetectionService, TextPreprocessor


class TestTextPreprocessor:
    """文本预处理器测试"""
    
    def setup_method(self):
        """测试前置设置"""
        self.processor = TextPreprocessor()
    
    def test_normalize_basic(self):
        """测试基础文本标准化"""
        text = "Hello 世界！"
        result = self.processor.normalize(text)
        assert result == "hello 世界！"
    
    def test_normalize_with_noise(self):
        """测试包含噪音字符的文本标准化"""
        text = "测试*文*本"
        result = self.processor.normalize(text, remove_noise=True)
        assert "*" not in result
    
    def test_clean_for_matching(self):
        """测试匹配前的文本清理"""
        text = "敏.感.词"
        result = self.processor.clean_for_matching(text)
        assert result == "敏感词"


class TestDetectionService:
    """检测服务测试"""
    
    def setup_method(self):
        """测试前置设置"""
        # 使用模拟的设置
        with patch('src.core.get_settings') as mock_settings:
            mock_settings.return_value = MagicMock(
                wordlist_dir="src/data/wordlists",
                model_path="",
                semantic_detection_enabled=False,
                rule_detection_enabled=True,
                max_text_length=10000,
                app_version="1.0.0"
            )
            self.service = SensitiveWordDetectionService()
    
    @pytest.mark.asyncio
    async def test_detect_empty_text(self):
        """测试空文本检测"""
        request = DetectionRequest(text="")
        
        with pytest.raises(Exception):  # 应该抛出验证错误
            await self.service.detect(request)
    
    @pytest.mark.asyncio
    async def test_detect_normal_text(self):
        """测试正常文本检测"""
        request = DetectionRequest(
            text="这是一段正常的文本内容",
            config=DetectionConfig(detection_mode=DetectionMode.RULE)
        )
        
        # 模拟规则检测器
        with patch.object(self.service.rule_detector, 'detect', return_value=[]):
            response = await self.service.detect(request)
            
            assert response.is_sensitive is False
            assert response.overall_score == 0.0
            assert len(response.results) == 0
    
    @pytest.mark.asyncio 
    async def test_health_check(self):
        """测试健康检查"""
        health_data = await self.service.health_check()
        
        assert "status" in health_data
        assert "version" in health_data
        assert "uptime_seconds" in health_data
        assert "components" in health_data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
