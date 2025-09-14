# -*- coding: utf-8 -*-
"""
DMMR 数据模型定义
定义了系统中使用的核心数据结构
"""
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class TaskType(Enum):
    """任务类型枚举"""
    GENERAL_QA = "general_qa"
    TECHNICAL_CODING = "technical_coding"
    EMOTIONAL_COUNSELING = "emotional_counseling"
    CREATIVE_WRITING = "creative_writing"
    EDUCATIONAL = "educational"


class MemoryChunk(BaseModel):
    """情景记忆块，存储单次交互的完整上下文"""
    id: Optional[str] = Field(default=None, description="记忆块唯一标识")
    content: str = Field(description="记忆内容")
    summary: Optional[str] = Field(default=None, description="记忆摘要")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")
    user_id: str = Field(description="用户ID")
    task_type: TaskType = Field(default=TaskType.GENERAL_QA, description="任务类型")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    significance_score: float = Field(default=0.0, description="重要性评分")
    embedding: Optional[List[float]] = Field(default=None, description="向量嵌入")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Node(BaseModel):
    """图节点，表示语义或程序记忆中的实体"""
    id: str = Field(description="节点唯一标识")
    label: str = Field(description="节点标签/类型")
    properties: Dict[str, Any] = Field(default_factory=dict, description="节点属性")
    embedding: Optional[List[float]] = Field(default=None, description="节点嵌入")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        return isinstance(other, Node) and self.id == other.id


class Relationship(BaseModel):
    """图关系，表示节点间的连接"""
    source_id: str = Field(description="源节点ID")
    target_id: str = Field(description="目标节点ID")
    label: str = Field(description="关系标签/类型")
    weight: float = Field(default=1.0, description="关系权重")
    properties: Dict[str, Any] = Field(default_factory=dict, description="关系属性")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")

    def __hash__(self):
        return hash((self.source_id, self.target_id, self.label))
    
    def __eq__(self, other):
        return (isinstance(other, Relationship) and 
                self.source_id == other.source_id and 
                self.target_id == other.target_id and 
                self.label == other.label)


class Entity(BaseModel):
    """实体，用于信息抽取"""
    id: str = Field(description="实体ID")
    label: str = Field(description="实体类型")
    properties: Dict[str, Any] = Field(default_factory=dict, description="实体属性")
    confidence: float = Field(default=1.0, description="置信度")


class ActivationResult(BaseModel):
    """激活结果"""
    activated_nodes: List[Node] = Field(description="激活的节点")
    activation_path: List[str] = Field(description="激活路径")
    total_energy: float = Field(description="总激活能量")
    process_time: float = Field(description="处理时间")


class RetrievalResult(BaseModel):
    """检索结果"""
    memories: List[Dict[str, Any]] = Field(description="检索到的记忆")
    used_memory_ids: List[str] = Field(description="使用的记忆ID")
    retrieval_stats: Dict[str, Any] = Field(default_factory=dict, description="检索统计")


class ResponseMetrics(BaseModel):
    """响应指标"""
    latency_sec: float = Field(description="响应延迟(秒)")
    token_usage: Dict[str, int] = Field(default_factory=dict, description="Token使用量")
    memory_hits: int = Field(default=0, description="记忆命中数")
    activation_nodes: int = Field(default=0, description="激活节点数")


class ExperimentConfig(BaseModel):
    """实验配置"""
    experiment_id: str = Field(description="实验ID")
    user_id: str = Field(description="用户ID") 
    use_real_backends: bool = Field(default=False, description="是否使用真实后端")
    ablation_config: Dict[str, Any] = Field(default_factory=dict, description="消融配置")
    context_budget_items: int = Field(default=5, description="上下文预算项目数")
    context_budget_chars: int = Field(default=200, description="上下文预算字符数")


class BenchmarkResult(BaseModel):
    """基准测试结果"""
    experiment_id: str = Field(description="实验ID")
    scenario_id: str = Field(description="场景ID")
    session_id: str = Field(description="会话ID")
    user_input: str = Field(description="用户输入")
    ai_response: str = Field(description="AI响应")
    metrics: ResponseMetrics = Field(description="响应指标")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")


