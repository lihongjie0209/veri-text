"""
YAML配置文件读取器
用于从YAML文件中读取敏感词库配置
"""
import yaml
from pathlib import Path
from typing import List, Dict, Optional
from ..core import get_logger

logger = get_logger()


class WordlistConfig:
    """敏感词库配置类"""
    
    def __init__(self, name: str, description: str, file: str, enabled: bool = True, weight: int = 100):
        self.name = name
        self.description = description
        self.file = file
        self.enabled = enabled
        self.weight = weight  # 新增权重字段，默认100
        self._words: Optional[List[str]] = None
    
    def get_normalized_weight(self) -> float:
        """获取标准化的权重值（0-1之间）"""
        return self.weight / 100.0
    
    def load_words(self, base_path: Path) -> List[str]:
        """加载词库文件中的敏感词"""
        if self._words is not None:
            return self._words
            
        file_path = base_path / self.file
        if not file_path.exists():
            logger.warning(f"敏感词库文件不存在: {file_path}")
            return []
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                words = [line.strip() for line in f if line.strip()]
            
            self._words = words
            logger.info(f"成功加载敏感词库 '{self.name}': {len(words)} 个词汇")
            return words
            
        except Exception as e:
            logger.error(f"加载敏感词库文件失败 {file_path}: {e}")
            return []
    
    def reload_words(self, base_path: Path) -> List[str]:
        """重新加载词库文件"""
        self._words = None
        return self.load_words(base_path)


class YamlConfigReader:
    """YAML配置文件读取器"""
    
    def __init__(self, config_file: str = "config/sensitive_words.yaml"):
        self.config_file = Path(config_file)
        self.wordlists: List[WordlistConfig] = []
        self.global_settings: Dict = {}
        self._load_config()
    
    def _load_config(self):
        """加载YAML配置文件"""
        if not self.config_file.exists():
            logger.error(f"配置文件不存在: {self.config_file}")
            return
            
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 加载全局设置
            self.global_settings = config.get('global_settings', {})
            
            # 加载敏感词库配置
            wordlists_config = config.get('wordlists', [])
            self.wordlists = []
            
            for wl_config in wordlists_config:
                wordlist = WordlistConfig(
                    name=wl_config.get('name', ''),
                    description=wl_config.get('description', ''),
                    file=wl_config.get('file', ''),
                    enabled=wl_config.get('enabled', True),
                    weight=wl_config.get('weight', 100)  # 读取权重，默认100
                )
                self.wordlists.append(wordlist)
            
            logger.info(f"成功加载配置文件: {len(self.wordlists)} 个敏感词库配置")
            
        except Exception as e:
            logger.error(f"加载配置文件失败 {self.config_file}: {e}")
    
    def get_enabled_wordlists(self) -> List[WordlistConfig]:
        """获取启用的敏感词库"""
        return [wl for wl in self.wordlists if wl.enabled]
    
    def get_wordlist_by_name(self, name: str) -> Optional[WordlistConfig]:
        """根据名称获取敏感词库配置"""
        for wl in self.wordlists:
            if wl.name == name:
                return wl
        return None
    
    def reload_config(self):
        """重新加载配置文件"""
        self._load_config()
    
    def get_all_words(self, base_path: Optional[Path] = None) -> Dict[str, List[str]]:
        """获取所有启用词库的敏感词"""
        if base_path is None:
            base_path = self.config_file.parent.parent
            
        all_words = {}
        for wordlist in self.get_enabled_wordlists():
            words = wordlist.load_words(base_path)
            all_words[wordlist.name] = words
            
        return all_words
    
    def get_flattened_words(self, base_path: Optional[Path] = None) -> List[str]:
        """获取所有启用词库的敏感词（扁平化列表）"""
        if base_path is None:
            base_path = self.config_file.parent.parent
            
        all_words = []
        for wordlist in self.get_enabled_wordlists():
            words = wordlist.load_words(base_path)
            all_words.extend(words)
            
        # 去重并保持顺序
        return list(dict.fromkeys(all_words))
    
    def get_category_weights(self) -> Dict[str, float]:
        """获取所有词库的权重映射（分类名称到标准化权重）"""
        weights = {}
        for wordlist in self.wordlists:
            weights[wordlist.name] = wordlist.get_normalized_weight()
        return weights
