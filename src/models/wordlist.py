"""
词库相关数据模型
"""
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from datetime import datetime

from .common import BaseResponse


class WordListCreate(BaseModel):
    """创建词库请求模型"""
    name: str = Field(..., min_length=1, max_length=100, description="词库名称")
    category: str = Field(..., description="词库分类")
    words: List[str] = Field(..., min_items=1, description="敏感词列表")
    description: Optional[str] = Field(default=None, max_length=500, description="词库描述")


class WordListUpdate(BaseModel):
    """更新词库请求模型"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100, description="词库名称")
    words: Optional[List[str]] = Field(default=None, min_items=1, description="敏感词列表")
    description: Optional[str] = Field(default=None, max_length=500, description="词库描述")
    enabled: Optional[bool] = Field(default=None, description="是否启用")


class WordList(BaseModel):
    """词库模型"""
    id: int = Field(..., description="词库ID")
    name: str = Field(..., description="词库名称")
    category: str = Field(..., description="词库分类")
    words: List[str] = Field(..., description="敏感词列表")
    description: Optional[str] = Field(default=None, description="词库描述")
    enabled: bool = Field(default=True, description="是否启用")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    word_count: int = Field(..., ge=0, description="词条数量")


class WordListsResponse(BaseResponse):
    """词库列表响应模型"""
    wordlists: List[WordList] = Field(default=[], description="词库列表")
    total: int = Field(..., ge=0, description="总数量")


class WordListResponse(BaseResponse):
    """单个词库响应模型"""
    wordlist: WordList = Field(..., description="词库详情")
