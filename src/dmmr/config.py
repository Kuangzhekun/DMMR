# -*- coding: utf-8 -*-
"""
DMMR 配置管理
集中管理系统配置和环境变量
"""
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DatabaseConfig:
    """数据库配置"""
    # 向量数据库
    use_real_vector_db: bool = False
    vector_backend: str = "faiss"  # faiss, milvus, chroma
    vector_dim: int = 256
    vector_uri: Optional[str] = None
    
    # 图数据库
    use_real_graph_db: bool = False
    graph_backend: str = "neo4j"  # neo4j, memgraph
    graph_uri: Optional[str] = None
    graph_user: Optional[str] = None
    graph_password: Optional[str] = None
    
    # 本地缓存
    cache_dir: str = "cache"


@dataclass
class APIConfig:
    """API配置"""
    api_key: Optional[str] = None
    base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    model_name: str = "doubao-seed-1-6-flash-250715"
    
    # 模型路由 
    model_agent: Optional[str] = None
    model_user_sim: Optional[str] = None  
    model_critic: Optional[str] = None
    
    # 生成参数
    default_temperature: float = 0.7
    default_max_tokens: int = 2000
    timeout: int = 30


@dataclass
class ActivationConfig:
    """激活引擎配置"""
    decay_factor: float = 0.5
    activation_threshold: float = 0.1
    fan_out_factor: float = 1.0
    max_depth: int = 3
    cache_size: int = 100


@dataclass  
class TriageConfig:
    """认知分类配置"""
    confidence_threshold: float = 0.7
    use_llm_fallback: bool = True


@dataclass
class ExperimentConfig:
    """实验配置"""
    output_dir: str = "results"
    context_budget_items: int = 5
    context_budget_chars: int = 200
    random_seed: Optional[int] = 42


@dataclass
class DMMRConfig:
    """DMMR主配置"""
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    api: APIConfig = field(default_factory=APIConfig)  
    activation: ActivationConfig = field(default_factory=ActivationConfig)
    triage: TriageConfig = field(default_factory=TriageConfig)
    experiment: ExperimentConfig = field(default_factory=ExperimentConfig)


class ConfigManager:
    """配置管理器"""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            self._config = self._load_config()
    
    def _load_config(self) -> DMMRConfig:
        """从环境变量加载配置"""
        config = DMMRConfig()
        
        # 数据库配置
        config.database.use_real_vector_db = os.getenv("DMMR_USE_REAL_VECTOR", "0") == "1"
        config.database.vector_backend = os.getenv("DMMR_VECTOR_BACKEND", config.database.vector_backend)
        config.database.vector_dim = int(os.getenv("DMMR_VECTOR_DIM", str(config.database.vector_dim)))
        config.database.vector_uri = os.getenv("DMMR_VECTOR_URI", config.database.vector_uri)
        
        config.database.use_real_graph_db = os.getenv("DMMR_USE_REAL_GRAPH", "0") == "1"
        config.database.graph_backend = os.getenv("DMMR_GRAPH_BACKEND", config.database.graph_backend)
        config.database.graph_uri = os.getenv("DMMR_GRAPH_URI", config.database.graph_uri)
        config.database.graph_user = os.getenv("DMMR_GRAPH_USER", config.database.graph_user)
        config.database.graph_password = os.getenv("DMMR_GRAPH_PASSWORD", config.database.graph_password)
        
        config.database.cache_dir = os.getenv("DMMR_CACHE_DIR", config.database.cache_dir)
        
        # API配置
        config.api.api_key = os.getenv("ARK_API_KEY") or os.getenv("OPENAI_API_KEY")
        config.api.base_url = os.getenv("DMMR_API_BASE_URL", config.api.base_url)
        config.api.model_name = os.getenv("DMMR_MODEL_NAME", config.api.model_name)
        config.api.model_agent = os.getenv("DMMR_MODEL_AGENT")
        config.api.model_user_sim = os.getenv("DMMR_MODEL_USER_SIM")
        config.api.model_critic = os.getenv("DMMR_MODEL_CRITIC")
        config.api.default_temperature = float(os.getenv("DMMR_TEMPERATURE", str(config.api.default_temperature)))
        config.api.default_max_tokens = int(os.getenv("DMMR_MAX_TOKENS", str(config.api.default_max_tokens)))
        config.api.timeout = int(os.getenv("DMMR_TIMEOUT", str(config.api.timeout)))
        
        # 激活配置
        config.activation.decay_factor = float(os.getenv("DMMR_DECAY_FACTOR", str(config.activation.decay_factor)))
        config.activation.activation_threshold = float(os.getenv("DMMR_ACTIVATION_THRESHOLD", str(config.activation.activation_threshold)))
        config.activation.fan_out_factor = float(os.getenv("DMMR_FAN_OUT_FACTOR", str(config.activation.fan_out_factor)))
        config.activation.max_depth = int(os.getenv("DMMR_MAX_DEPTH", str(config.activation.max_depth)))
        config.activation.cache_size = int(os.getenv("DMMR_CACHE_SIZE", str(config.activation.cache_size)))
        
        # 分类配置
        config.triage.confidence_threshold = float(os.getenv("DMMR_TRIAGE_THRESHOLD", str(config.triage.confidence_threshold)))
        config.triage.use_llm_fallback = os.getenv("DMMR_TRIAGE_LLM", "1") == "1"
        
        # 实验配置
        config.experiment.output_dir = os.getenv("DMMR_OUTPUT_DIR", config.experiment.output_dir)
        config.experiment.context_budget_items = int(os.getenv("DMMR_BUDGET_ITEMS", str(config.experiment.context_budget_items)))
        config.experiment.context_budget_chars = int(os.getenv("DMMR_BUDGET_CHARS", str(config.experiment.context_budget_chars)))
        if os.getenv("DMMR_RANDOM_SEED"):
            config.experiment.random_seed = int(os.getenv("DMMR_RANDOM_SEED"))
            
        return config
    
    @property
    def config(self) -> DMMRConfig:
        """获取配置对象"""
        return self._config
    
    def validate_config(self) -> list[str]:
        """验证配置"""
        warnings = []
        
        if not self.config.api.api_key:
            warnings.append("API密钥未设置，请设置ARK_API_KEY或OPENAI_API_KEY环境变量")
        
        # 确保输出目录存在
        Path(self.config.experiment.output_dir).mkdir(parents=True, exist_ok=True)
        
        # 确保缓存目录存在
        Path(self.config.database.cache_dir).mkdir(parents=True, exist_ok=True)
        
        return warnings
    
    def print_config(self):
        """打印配置摘要"""
        print("DMMR 系统配置")
        print("=" * 50)
        
        warnings = self.validate_config()
        if warnings:
            print("⚠️  配置警告:")
            for warning in warnings:
                print(f"   - {warning}")
            print()
        
        print("📊 核心配置:")
        print(f"   API Key: {'✓' if self.config.api.api_key else '✗'}")
        print(f"   模型: {self.config.api.model_name}")
        print(f"   真实向量DB: {'启用' if self.config.database.use_real_vector_db else '禁用'}")
        print(f"   真实图DB: {'启用' if self.config.database.use_real_graph_db else '禁用'}")
        print(f"   激活阈值: {self.config.activation.activation_threshold}")
        print(f"   衰减因子: {self.config.activation.decay_factor}")


# 全局配置管理器
config_manager = ConfigManager()


def get_config() -> DMMRConfig:
    """获取全局配置"""
    return config_manager.config


def validate_config() -> bool:
    """验证配置是否有效"""
    warnings = config_manager.validate_config()
    if warnings:
        print("配置验证失败:")
        for warning in warnings:
            print(f"  - {warning}")
        return False
    return True


if __name__ == "__main__":
    config_manager.print_config()



