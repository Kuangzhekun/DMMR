# -*- coding: utf-8 -*-
"""
DMMR: Dynamic Multi-Modal Memory Retrieval System

A long-term memory system based on cognitive science theories, designed to enhance
the multi-turn interaction capabilities of large language models.

Core Modules:
- DMMRAgent: The main agent.
- MultipleMemorySystems: The multi-memory system.
- ActivationEngine: The activation engine.
- CognitiveTriage: The cognitive triage module.
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
