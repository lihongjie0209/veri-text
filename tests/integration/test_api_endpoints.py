"""
集成测试 - API接口测试
"""
import pytest
import asyncio
from httpx import AsyncClient
import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.main import app


class TestAPIEndpoints:
    """API接口集成测试"""
    
    @pytest.mark.asyncio
    async def test_root_endpoint(self):
        """测试根路径接口"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/")
            
            assert response.status_code == 200
            data = response.json()
            assert "service" in data
            assert "version" in data
            assert data["status"] == "running"
    
    @pytest.mark.asyncio
    async def test_health_check_endpoint(self):
        """测试健康检查接口"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/health/")
            
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "version" in data
    
    @pytest.mark.asyncio
    async def test_detection_endpoint_valid_request(self):
        """测试检测接口 - 有效请求"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            payload = {
                "text": "这是一段测试文本",
                "config": {
                    "detection_mode": "rule",
                    "strictness_level": "standard"
                }
            }
            
            response = await client.post("/api/v1/detect/", json=payload)
            
            assert response.status_code == 200
            data = response.json()
            assert "is_sensitive" in data
            assert "results" in data
            assert "summary" in data
    
    @pytest.mark.asyncio
    async def test_detection_endpoint_invalid_request(self):
        """测试检测接口 - 无效请求"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            payload = {
                "text": "",  # 空文本应该导致验证错误
            }
            
            response = await client.post("/api/v1/detect/", json=payload)
            
            assert response.status_code == 422  # 验证错误
    
    @pytest.mark.asyncio
    async def test_detection_endpoint_with_sensitive_content(self):
        """测试检测接口 - 包含敏感内容"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            payload = {
                "text": "这里包含政治敏感词1的内容",
                "config": {
                    "detection_mode": "rule",
                    "return_positions": True
                }
            }
            
            response = await client.post("/api/v1/detect/", json=payload)
            
            assert response.status_code == 200
            data = response.json()
            # 由于我们有测试词库，这里可能检测到敏感内容
            assert "is_sensitive" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
