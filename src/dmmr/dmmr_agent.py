# -*- coding: utf-8 -*-
"""
DMMR智能体 - 系统核心，整合所有认知模块
基于认知科学理论实现的长期记忆增强智能体
"""
import asyncio
import os
from typing import Dict, Any, Tuple, List, Optional
from datetime import datetime

from .config import get_config, validate_config
from .data_models import TaskType, MemoryChunk, Node, Relationship, ResponseMetrics
from .api_wrapper import APIWrapper
from .memory_systems import MultipleMemorySystems
from .cognitive_triage import CognitiveTriage
from .information_extractor import InformationExtractor
from .activation_engine import ActivationEngine
from .reconstruction_engine import ReconstructionEngine
from .score_calculator import ScoreCalculator


class DMMRAgent:
    """
    DMMR智能体 - 动态多模态记忆检索系统
    
    整合多重记忆系统、激活引擎、认知分类等核心模块
    实现基于认知科学理论的智能对话系统
    """
    
    def __init__(self, user_id: str = "default_user", 
                 use_real_backends: bool = False,
                 config_override: Optional[Dict[str, Any]] = None):
        """
        初始化DMMR智能体
        
        Args:
            user_id: 用户唯一标识
            use_real_backends: 是否使用真实数据库后端
            config_override: 配置覆盖参数
        """
        print("🚀 DMMR智能体初始化开始...")
        print(f"   用户ID: {user_id}")
        print(f"   真实后端: {use_real_backends}")
        
        # 验证配置
        if not validate_config():
            raise RuntimeError("配置验证失败，无法启动智能体")
        
        self.user_id = user_id
        self.use_real_backends = use_real_backends
        self.config = get_config()
        
        # 应用配置覆盖
        if config_override:
            self._apply_config_override(config_override)
            print(f"   应用配置覆盖: {config_override}")
        
        # 初始化核心组件
        self._init_components()
        
        # 会话状态管理
        self.conversation_context = []
        self.environment_profile = {}
        
        # 性能指标跟踪
        self.session_stats = {
            'total_queries': 0,
            'total_memories_created': 0,
            'total_memories_retrieved': 0,
            'avg_response_time': 0.0,
            'activation_events': 0
        }
        
        # 启动认知预热
        if self.config.activation.cache_size > 0:
            asyncio.create_task(self._cognitive_warmup())
        
        print("✅ DMMR智能体初始化完成")
    
    def _init_components(self):
        """初始化所有核心组件"""
        print("📦 初始化核心组件...")
        
        # 基础服务
        self.api_wrapper = APIWrapper()
        self.score_calculator = ScoreCalculator()
        
        # 认知模块
        self.triage = CognitiveTriage(api_wrapper=self.api_wrapper)
        self.memory_systems = MultipleMemorySystems(
            user_id=self.user_id,
            use_real_backends=self.use_real_backends
        )
        self.information_extractor = InformationExtractor(api_wrapper=self.api_wrapper)
        self.activation_engine = ActivationEngine(memory=self.memory_systems)
        self.reconstruction_engine = ReconstructionEngine(api_wrapper=self.api_wrapper)
        
        print("✅ 所有组件初始化完成")
    
    def _apply_config_override(self, overrides: Dict[str, Any]):
        """应用配置覆盖"""
        for key, value in overrides.items():
            if hasattr(self.config.activation, key):
                setattr(self.config.activation, key, value)
            elif hasattr(self.config.api, key):
                setattr(self.config.api, key, value)
    
    async def _cognitive_warmup(self):
        """认知预热 - 预加载常用记忆"""
        try:
            await self.activation_engine.cognitive_priming(
                user_id=self.user_id,
                context_hints=['技术', '编程', '问题解决']
            )
        except Exception as e:
            print(f"⚠️ 认知预热失败: {e}")
    
    def process_input(self, user_input: str, 
                     metadata: Optional[Dict[str, Any]] = None) -> Tuple[str, ResponseMetrics]:
        """
        处理用户输入的主要接口
        
        Args:
            user_input: 用户输入文本
            metadata: 可选的元数据信息
            
        Returns:
            (AI回答, 响应指标)
        """
        start_time = datetime.now()
        metadata = metadata or {}
        
        print(f"\n🎯 处理用户输入: {user_input[:50]}{'...' if len(user_input) > 50 else ''}")
        
        try:
            # 1. 认知分类
            task_type = self.triage.classify(user_input)
            metadata['task_type'] = task_type.value
            print(f"📋 任务类型: {task_type.value}")
            
            # 2. 信息抽取和记忆存储
            self._process_and_store_memory(user_input, task_type, metadata)
            
            # 3. 激活相关记忆
            activated_memories = self._activate_relevant_memories(user_input, task_type)
            
            # 4. 重构生成回答
            answer, response_metrics = self._generate_response(
                user_input, task_type, activated_memories, metadata
            )
            
            # 5. 更新统计信息
            self._update_session_stats(start_time, len(activated_memories))
            
            return answer, response_metrics
            
        except Exception as e:
            print(f"❌ 处理失败: {e}")
            
            # 降级处理
            fallback_answer = self._generate_fallback_response(user_input)
            fallback_metrics = ResponseMetrics(
                latency_sec=(datetime.now() - start_time).total_seconds(),
                token_usage={'total_tokens': 100},  # 估计值
                memory_hits=0,
                activation_nodes=0
            )
            
            return fallback_answer, fallback_metrics
    
    def _process_and_store_memory(self, user_input: str, task_type: TaskType, metadata: Dict):
        """处理输入并存储到记忆系统"""
        print("💾 存储记忆...")
        
        # 创建记忆块
        chunk = self.api_wrapper.process_input_to_chunk(user_input, metadata)
        chunk.task_type = task_type
        chunk.significance_score = self.score_calculator.calculate_initial_score(chunk)
        chunk.embedding = self.information_extractor.generate_embedding(chunk.content)
        
        # 存储到情景记忆
        self.memory_systems.add_to_episodic(chunk)
        
        # 提取结构化信息并存储到图记忆
        extracted_info = self.information_extractor.extract_entities_and_relations(
            user_input, task_type
        )
        
        # 存储节点和关系
        for node_data in extracted_info.get("nodes", []):
            node = Node(**node_data)
            node.embedding = self.information_extractor.generate_embedding(
                f"{node.id} {node.label}"
            )
            
            if task_type == TaskType.TECHNICAL_CODING:
                self.memory_systems.add_procedural_node(node)
            else:
                self.memory_systems.add_semantic_node(node)
        
        for rel_data in extracted_info.get("relationships", []):
            relationship = Relationship(**rel_data)
            
            if task_type == TaskType.TECHNICAL_CODING:
                self.memory_systems.add_procedural_relationship(relationship)
            else:
                self.memory_systems.add_semantic_relationship(relationship)
        
        # 更新环境画像
        self._update_environment_profile(user_input)
        
        self.session_stats['total_memories_created'] += 1
        print(f"   记忆存储完成 (节点: {len(extracted_info.get('nodes', []))}, 关系: {len(extracted_info.get('relationships', []))})")
    
    def _activate_relevant_memories(self, user_input: str, task_type: TaskType) -> List[Dict[str, Any]]:
        """激活相关记忆"""
        print("⚡ 激活相关记忆...")
        
        # 提取激活线索
        entities = self.information_extractor.extract_entities(user_input)
        cues = [(entity.id, entity.confidence) for entity in entities]
        
        # 如果没有实体，使用文本片段作为线索
        if not cues:
            text_words = user_input.strip().split()[:3]  # 使用前3个词
            cues = [(word, 0.7) for word in text_words]
        
        # 扩散激活
        activated_nodes = self.activation_engine.spreading_activation(
            cues=cues,
            task_type=task_type,
            max_depth=self.config.activation.max_depth
        )
        
        # 转换为记忆格式
        activated_memories = []
        for node in activated_nodes:
            activation_energy = node.properties.get('activation', 0.0)
            activated_memories.append({
                'id': node.id,
                'content': f"激活节点: {node.id} ({node.label})",
                'source': 'activated_node',
                'significance_score': activation_energy,
                'activation_energy': activation_energy
            })
        
        # 同时检索情景记忆
        if hasattr(user_input, '__len__') and len(user_input) > 0:
            query_embedding = self.information_extractor.generate_embedding(user_input)
            episodic_memories = self.memory_systems.search_episodic_by_vector(
                query_embedding, n_results=3
            )
            
            for chunk in episodic_memories:
                activated_memories.append({
                    'id': chunk.id or 'episodic_memory',
                    'content': chunk.content,
                    'source': 'episodic_memory',
                    'significance_score': chunk.significance_score,
                    'timestamp': chunk.timestamp.isoformat() if chunk.timestamp else None
                })
        
        self.session_stats['total_memories_retrieved'] += len(activated_memories)
        self.session_stats['activation_events'] += 1
        
        print(f"   激活记忆: {len(activated_memories)} 个")
        return activated_memories
    
    def _generate_response(self, user_input: str, task_type: TaskType, 
                          memories: List[Dict], metadata: Dict) -> Tuple[str, ResponseMetrics]:
        """生成回答和指标"""
        print("🤖 生成回答...")
        
        # 构建策略提示
        strategy_prompt = self._build_strategy_prompt(task_type)
        
        # 生成参数
        generation_kwargs = {
            'max_context_items': self.config.experiment.context_budget_items,
            'max_context_chars': self.config.experiment.context_budget_chars,
            'temperature': self.config.api.default_temperature,
            'max_tokens': self.config.api.default_max_tokens
        }
        
        # 检查是否需要纯代码模式
        code_only = (task_type == TaskType.TECHNICAL_CODING and 
                    'humaneval' in metadata.get('source', ''))
        
        # 重构回答
        answer, used_memory_ids, reconstruction_stats = self.reconstruction_engine.reconstruct_answer(
            query=user_input,
            retrieved_memories=memories,
            strategy_prompt=strategy_prompt,
            code_only=code_only,
            generation_kwargs=generation_kwargs
        )
        
        # 记录有用的预取
        self.activation_engine.mark_useful_prefetch(used_memory_ids)
        
        # 构建响应指标
        metrics = ResponseMetrics(
            latency_sec=reconstruction_stats.get('processing_time', 0.0),
            token_usage=self.api_wrapper.get_last_usage() or {},
            memory_hits=len(used_memory_ids),
            activation_nodes=len([m for m in memories if m.get('source') == 'activated_node'])
        )
        
        print(f"✅ 回答生成完成 (长度: {len(answer)}, 使用记忆: {len(used_memory_ids)})")
        return answer, metrics
    
    def _build_strategy_prompt(self, task_type: TaskType) -> str:
        """构建认知策略提示"""
        strategy_prompts = {
            TaskType.TECHNICAL_CODING: (
                "技术模式：提供准确、可执行的技术解决方案。"
                "优先给出具体代码示例和操作步骤。"
            ),
            TaskType.EMOTIONAL_COUNSELING: (
                "共情模式：以理解和支持为主。"
                "先表达共情，再提供1-3条具体可行的建议。"
            ),
            TaskType.CREATIVE_WRITING: (
                "创意模式：发挥想象力，提供富有创意的回答。"
                "注重语言的表现力和艺术性。"
            ),
            TaskType.EDUCATIONAL: (
                "教学模式：清晰解释概念，提供具体例子。"
                "循序渐进，确保易于理解。"
            ),
            TaskType.GENERAL_QA: (
                "平衡模式：准确、简洁、有用。"
                "根据问题性质灵活调整回答风格。"
            )
        }
        
        return strategy_prompts.get(task_type, strategy_prompts[TaskType.GENERAL_QA])
    
    def _update_environment_profile(self, user_input: str):
        """更新环境画像"""
        text_lower = user_input.lower()
        
        # OS检测
        if any(keyword in text_lower for keyword in ['windows', 'win10', 'win11', 'powershell']):
            self.environment_profile['os'] = 'windows'
        elif any(keyword in text_lower for keyword in ['linux', 'ubuntu', 'debian']):
            self.environment_profile['os'] = 'linux'
        elif any(keyword in text_lower for keyword in ['macos', 'mac', 'osx']):
            self.environment_profile['os'] = 'macos'
        
        # 技术栈检测
        tech_stack = []
        if 'python' in text_lower:
            tech_stack.append('python')
        if 'javascript' in text_lower or 'js' in text_lower:
            tech_stack.append('javascript')
        if 'docker' in text_lower:
            tech_stack.append('docker')
        
        if tech_stack:
            self.environment_profile['tech_stack'] = list(set(
                self.environment_profile.get('tech_stack', []) + tech_stack
            ))
    
    def _generate_fallback_response(self, user_input: str) -> str:
        """生成降级回答"""
        try:
            return self.api_wrapper.generate_text(
                f"请简要回答以下问题：{user_input}",
                max_tokens=200,
                temperature=0.7
            )
        except Exception:
            return "抱歉，我暂时无法处理您的请求。请稍后再试。"
    
    def _update_session_stats(self, start_time: datetime, memory_count: int):
        """更新会话统计"""
        response_time = (datetime.now() - start_time).total_seconds()
        
        self.session_stats['total_queries'] += 1
        
        # 更新平均响应时间
        total_queries = self.session_stats['total_queries']
        current_avg = self.session_stats['avg_response_time']
        self.session_stats['avg_response_time'] = (
            (current_avg * (total_queries - 1) + response_time) / total_queries
        )
    
    def reset_session(self):
        """重置会话状态"""
        print("🔄 重置会话状态")
        
        # 清除对话上下文
        self.conversation_context.clear()
        
        # 重置API对话历史
        self.api_wrapper.clear_history()
        
        # 可选：清除激活状态
        self.activation_engine.active_nodes.clear()
        
        print("✅ 会话状态已重置")
    
    def get_agent_status(self) -> Dict[str, Any]:
        """获取智能体状态信息"""
        return {
            'user_id': self.user_id,
            'use_real_backends': self.use_real_backends,
            'session_stats': dict(self.session_stats),
            'environment_profile': dict(self.environment_profile),
            'component_status': {
                'api_wrapper': self.api_wrapper.get_api_status(),
                'triage': self.triage.get_classification_stats(),
                'activation_engine': self.activation_engine.get_activation_summary(),
                'reconstruction_engine': self.reconstruction_engine.get_reconstruction_summary()
            },
            'config_summary': {
                'activation_threshold': self.config.activation.activation_threshold,
                'decay_factor': self.config.activation.decay_factor,
                'context_budget_items': self.config.experiment.context_budget_items,
                'model_name': self.config.api.model_name
            }
        }
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """获取记忆系统统计"""
        return {
            'total_memories_created': self.session_stats['total_memories_created'],
            'total_memories_retrieved': self.session_stats['total_memories_retrieved'],
            'activation_events': self.session_stats['activation_events'],
            'prefetch_stats': self.activation_engine.get_prefetch_stats()
        }



