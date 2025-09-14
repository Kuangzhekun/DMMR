# -*- coding: utf-8 -*-
"""
DMMR: Dynamic Multi-Modal Memory Retrieval System

基于认知科学理论的长期记忆系统，用于增强大语言模型的多轮交互能力。

核心模块:
- DMMRAgent: 主智能体
- MultipleMemorySystems: 多重记忆系统
- ActivationEngine: 激活引擎
- CognitiveTriage: 认知分类
"""

from .config import get_config, validate_config, config_manager
from .data_models import (
    TaskType, MemoryChunk, Node, Relationship, Entity,
    ActivationResult, RetrievalResult, ResponseMetrics,
    ExperimentConfig, BenchmarkResult
)
from .dmmr_agent import DMMRAgent
from .api_wrapper import APIWrapper
from .memory_systems import MultipleMemorySystems
from .cognitive_triage import CognitiveTriage
from .information_extractor import InformationExtractor
from .activation_engine import ActivationEngine
from .reconstruction_engine import ReconstructionEngine
from .score_calculator import ScoreCalculator

__version__ = "1.0.0"
__author__ = "DMMR Team"
__description__ = "Dynamic Multi-Modal Memory Retrieval System"

__all__ = [
    # Core Agent
    "DMMRAgent",
    
    # Configuration
    "get_config",
    "validate_config", 
    "config_manager",
    
    # Core Components  
    "APIWrapper",
    "MultipleMemorySystems",
    "CognitiveTriage",
    "InformationExtractor", 
    "ActivationEngine",
    "ReconstructionEngine",
    "ScoreCalculator",
    
    # Data Models
    "TaskType",
    "MemoryChunk",
    "Node", 
    "Relationship",
    "Entity",
    "ActivationResult",
    "RetrievalResult",
    "ResponseMetrics",
    "ExperimentConfig", 
    "BenchmarkResult"
]
