# 敏感词检测服务 - 技术设计文档 (TDD)

## 1. 系统架构设计

### 1.1 总体架构
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client App    │───▶│  FastAPI Gateway │───▶│ Detection Engine │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                        │
                              ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │ Request/Response │    │   Word Lists    │
                       │   Validation     │    │   Repository    │
                       └─────────────────┘    └─────────────────┘
```

### 1.2 核心模块划分
- **API Gateway Layer**: FastAPI路由、请求验证、响应序列化
- **Service Layer**: 业务逻辑处理、检测策略协调
- **Detection Engine**: 规则匹配 + ML语义检测引擎
- **Repository Layer**: 敏感词库管理、配置存储

## 2. FastAPI接口设计

### 2.1 核心检测接口
```python
# Endpoint定义
@router.post("/api/v1/detect")
async def detect_sensitive_content(request: DetectionRequest) -> DetectionResponse

@router.get("/api/v1/health")
async def health_check() -> HealthResponse
```

### 2.2 管理接口（扩展功能）
```python
@router.get("/api/v1/wordlists")
async def list_wordlists() -> WordListsResponse

@router.post("/api/v1/wordlists")
async def create_wordlist(wordlist: WordListCreate) -> WordListResponse

@router.put("/api/v1/wordlists/{wordlist_id}")
async def update_wordlist(wordlist_id: int, wordlist: WordListUpdate) -> WordListResponse
```

## 3. Pydantic数据模型设计

### 3.1 检测相关模型
```python
# 检测配置模型
class DetectionConfig(BaseModel):
    detection_mode: DetectionMode = DetectionMode.HYBRID
    strictness_level: StrictnessLevel = StrictnessLevel.STANDARD
    categories: List[SensitiveCategory] = []
    return_positions: bool = True
    return_suggestions: bool = False
    custom_threshold: float = Field(default=0.8, ge=0.0, le=1.0)

# 检测请求模型
class DetectionRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000)
    config: DetectionConfig = DetectionConfig()

# 检测结果项模型
class DetectionResultItem(BaseModel):
    matched_word: str
    category: SensitiveCategory
    match_type: MatchType
    confidence: float = Field(..., ge=0.0, le=1.0)
    positions: List[Position]
    detection_method: DetectionMethod
    suggestion: Optional[str] = None

# 检测响应模型
class DetectionResponse(BaseModel):
    is_sensitive: bool
    risk_level: RiskLevel
    overall_score: float = Field(..., ge=0.0, le=1.0)
    detection_time_ms: int
    detection_mode_used: DetectionMode
    results: List[DetectionResultItem]
    summary: DetectionSummary
```

### 3.2 枚举类型定义
```python
class DetectionMode(str, Enum):
    RULE = "rule"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"

class StrictnessLevel(str, Enum):
    LOOSE = "loose"
    STANDARD = "standard"
    STRICT = "strict"
    CUSTOM = "custom"

class SensitiveCategory(str, Enum):
    POLITICAL = "political"
    PORNOGRAPHIC = "pornographic"
    VIOLENT = "violent"
    SPAM = "spam"
    PRIVACY = "privacy"

class MatchType(str, Enum):
    EXACT = "exact"
    FUZZY = "fuzzy"
    SEMANTIC = "semantic"

class DetectionMethod(str, Enum):
    RULE = "rule"
    SEMANTIC = "semantic"

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
```

## 4. 核心服务类接口设计

### 4.1 检测服务接口
```python
class SensitiveWordDetectionService:
    """敏感词检测服务主入口"""
    
    async def detect(self, request: DetectionRequest) -> DetectionResponse:
        """执行敏感词检测"""
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """服务健康检查"""
        pass

class RuleBasedDetector:
    """基于规则的检测器"""
    
    async def detect(self, text: str, config: DetectionConfig) -> List[DetectionResultItem]:
        """规则匹配检测"""
        pass
    
    def load_wordlists(self) -> None:
        """加载敏感词库"""
        pass

class SemanticDetector:
    """基于ML语义的检测器"""
    
    async def detect(self, text: str, config: DetectionConfig) -> List[DetectionResultItem]:
        """语义检测"""
        pass
    
    def load_model(self) -> None:
        """加载ML模型"""
        pass
```

### 4.2 词库管理服务接口
```python
class WordListRepository:
    """敏感词库仓储"""
    
    def get_all_wordlists(self) -> List[WordList]:
        """获取所有词库"""
        pass
    
    def get_wordlist_by_category(self, category: SensitiveCategory) -> WordList:
        """按分类获取词库"""
        pass
    
    def create_wordlist(self, wordlist: WordListCreate) -> WordList:
        """创建新词库"""
        pass
    
    def update_wordlist(self, wordlist_id: int, wordlist: WordListUpdate) -> WordList:
        """更新词库"""
        pass
```

## 5. 技术选型与架构决策

### 5.1 Web框架选择
- **FastAPI**: 异步支持、自动文档生成、Pydantic集成
- **Uvicorn**: 高性能ASGI服务器

### 5.2 检测算法选择
- **规则匹配**: pyahocorasick库（AC自动机）
- **ML模型**: transformers + torch（BERT系列模型）
- **文本预处理**: jieba分词、opencc繁简转换

### 5.3 数据存储选择
- **词库存储**: JSON文件 + 内存缓存（MVP阶段）
- **配置存储**: YAML配置文件
- **后续扩展**: Redis缓存 + PostgreSQL持久化

### 5.4 依赖管理
- **包管理**: uv
- **虚拟环境**: uv venv
- **依赖锁定**: requirements.txt → 后续迁移至pyproject.toml

## 6. 关键技术挑战与解决方案

### 6.1 性能优化
- **词库加载**: 应用启动时一次性加载到内存
- **模型推理**: 模型预加载，避免重复初始化
- **并发处理**: 异步处理，连接池管理

### 6.2 内存管理
- **词库压缩**: Trie树压缩存储
- **模型量化**: 使用量化模型减少内存占用
- **缓存策略**: LRU缓存热点检测结果

### 6.3 扩展性设计
- **插件化检测器**: 便于添加新的检测算法
- **配置热更新**: 支持词库和配置的热更新
- **水平扩展**: 无状态设计，支持多实例部署

## 7. 详细实现方案

### 7.1 规则匹配检测实现细节
```python
# AC自动机实现伪代码
class ACAutomaton:
    def __init__(self):
        self.automaton = ahocorasick.Automaton()
        
    def build_from_wordlist(self, words: List[str]):
        for word in words:
            # 预处理: 繁简转换 + 大小写标准化
            normalized_word = self._normalize_text(word)
            self.automaton.add_word(normalized_word, (word, category))
        self.automaton.make_automaton()
    
    def search(self, text: str) -> List[Match]:
        normalized_text = self._normalize_text(text)
        matches = []
        for end_index, (original_word, category) in self.automaton.iter(normalized_text):
            # 边界检查，避免误匹配
            if self._is_word_boundary(normalized_text, start_index, end_index):
                matches.append(Match(word=original_word, start=start_index, end=end_index))
        return matches
```

### 7.2 ML语义检测实现细节
```python
# BERT模型加载和推理伪代码
class BERTSensitiveDetector:
    def __init__(self, model_path: str):
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
        self.model.eval()
    
    async def predict(self, text: str) -> List[Prediction]:
        # 文本预处理和tokenization
        inputs = self.tokenizer(text, return_tensors="pt", max_length=512, truncation=True)
        
        # 模型推理
        with torch.no_grad():
            outputs = self.model(**inputs)
            probabilities = torch.softmax(outputs.logits, dim=-1)
        
        # 结果解析
        predictions = []
        for category_idx, prob in enumerate(probabilities[0]):
            if prob > self.threshold:
                category = self.idx_to_category[category_idx]
                predictions.append(Prediction(category=category, confidence=prob.item()))
        
        return predictions
```

### 7.3 混合检测策略实现
```python
# 混合检测协调器伪代码
class HybridDetector:
    def __init__(self, rule_detector: RuleBasedDetector, semantic_detector: SemanticDetector):
        self.rule_detector = rule_detector
        self.semantic_detector = semantic_detector
    
    async def detect(self, text: str, config: DetectionConfig) -> List[DetectionResultItem]:
        results = []
        
        # 1. 优先执行规则匹配（快速）
        rule_results = await self.rule_detector.detect(text, config)
        results.extend(rule_results)
        
        # 2. 根据严格程度决定是否执行语义检测
        if self._should_run_semantic_detection(config, rule_results):
            semantic_results = await self.semantic_detector.detect(text, config)
            results.extend(self._merge_results(rule_results, semantic_results))
        
        # 3. 结果去重和置信度融合
        return self._deduplicate_and_merge(results)
```

### 7.4 文本预处理管道
```python
# 文本预处理流水线
class TextPreprocessor:
    def __init__(self):
        self.converter = opencc.OpenCC('t2s')  # 繁简转换
        
    def normalize(self, text: str) -> str:
        # 1. 繁体转简体
        text = self.converter.convert(text)
        
        # 2. 统一大小写
        text = text.lower()
        
        # 3. 移除多余空白
        text = re.sub(r'\s+', ' ', text).strip()
        
        # 4. 处理特殊字符插入（可选）
        if self.remove_noise:
            text = re.sub(r'[^\w\s\u4e00-\u9fff]', '', text)
        
        return text
    
    def extract_positions_mapping(self, original: str, normalized: str) -> List[Tuple[int, int]]:
        """维护原文和标准化文本的位置映射"""
        # 实现位置映射逻辑，用于将检测结果映射回原文位置
        pass
```

## 8. 项目目录结构设计
```
src/
├── api/                    # FastAPI 路由层
│   ├── __init__.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── detection.py    # 检测相关路由
│   │   ├── health.py       # 健康检查路由
│   │   └── wordlists.py    # 词库管理路由（扩展）
│   └── dependencies.py     # FastAPI 依赖注入
├── core/                   # 核心业务逻辑
│   ├── __init__.py
│   ├── config.py          # 配置管理
│   ├── exceptions.py      # 自定义异常
│   └── logging.py         # 日志配置
├── models/                 # Pydantic 数据模型
│   ├── __init__.py
│   ├── detection.py       # 检测相关模型
│   ├── wordlist.py        # 词库相关模型
│   └── common.py          # 通用模型
├── services/               # 业务服务层
│   ├── __init__.py
│   ├── detection_service.py  # 检测服务主入口
│   ├── rule_detector.py     # 规则检测器
│   ├── semantic_detector.py # 语义检测器
│   └── text_processor.py    # 文本预处理
├── repository/             # 数据仓储层
│   ├── __init__.py
│   ├── wordlist_repo.py   # 词库仓储
│   └── config_repo.py     # 配置仓储
├── utils/                  # 工具类
│   ├── __init__.py
│   ├── text_utils.py      # 文本处理工具
│   └── ml_utils.py        # ML相关工具
├── data/                   # 数据文件
│   ├── wordlists/         # 敏感词库
│   │   ├── political.txt
│   │   ├── pornographic.txt
│   │   └── violent.txt
│   └── models/            # ML模型文件
├── main.py                 # FastAPI 应用入口
└── __init__.py

tests/                      # 测试代码
├── __init__.py
├── unit/                   # 单元测试
│   ├── test_detection_service.py
│   ├── test_rule_detector.py
│   └── test_semantic_detector.py
├── integration/            # 集成测试
│   ├── test_api_endpoints.py
│   └── test_full_pipeline.py
└── fixtures/               # 测试数据
    ├── sample_texts.py
    └── expected_results.py

docs/                       # 文档
├── sensitive-word-detection/
│   ├── sensitive-word-detection_PRD.md
│   └── sensitive-word-detection_TDD.md
└── api/                    # API文档
    └── openapi.json

config/                     # 配置文件
├── settings.yaml          # 应用配置
├── wordlist_config.yaml   # 词库配置
└── model_config.yaml      # 模型配置

.github/                    # CI/CD配置
└── workflows/
    └── ci.yml

requirements.txt            # 依赖列表
pyproject.toml             # 项目配置（后续迁移）
README.md                  # 项目说明
.gitignore                 # Git忽略文件
```

## 9. 部署和运维考虑

### 9.1 容器化部署
- **Docker镜像**: 基于Python 3.11-slim镜像
- **多阶段构建**: 分离构建环境和运行环境
- **健康检查**: 容器级别的健康检查端点

### 9.2 性能监控
- **指标收集**: 响应时间、QPS、错误率、内存使用
- **日志记录**: 结构化日志，包含请求ID追踪
- **告警机制**: 基于阈值的自动告警

### 9.3 配置管理
- **环境分离**: dev/test/prod环境配置分离
- **敏感信息**: 使用环境变量管理API密钥等
- **热更新**: 支持词库和模型的热更新机制
