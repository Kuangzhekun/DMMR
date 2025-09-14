# -*- coding: utf-8 -*-
"""
激活引擎 - 实现认知启动和扩散激活
基于ACT-R理论的联想记忆激活机制
"""
import asyncio
import math
from typing import List, Dict, Any, Tuple, Optional, Set
from .data_models import Node, TaskType
from .memory_systems import MultipleMemorySystems
from .config import get_config


class ActivationCache:
    """高速激活缓存，模拟认知就绪状态"""
    
    def __init__(self, max_size: int = 100):
        self.cache: Dict[str, Any] = {}
        self.max_size = max_size
        print(f"⚡ 激活缓存初始化 (容量: {max_size})")
    
    async def get(self, key: str) -> Optional[Any]:
        """异步获取缓存项"""
        return self.cache.get(key)
    
    async def set(self, key: str, value: Any):
        """异步设置缓存项"""
        if len(self.cache) >= self.max_size:
            await self.evict()
        self.cache[key] = value
    
    async def evict(self):
        """缓存淘汰策略"""
        # 简单实现：删除前20%的项目
        evict_count = int(self.max_size * 0.2)
        keys_to_remove = list(self.cache.keys())[:evict_count]
        
        for key in keys_to_remove:
            del self.cache[key]
        
        print(f"  [缓存清理] 淘汰了 {evict_count} 个缓存项")


class ActivationEngine:
    """激活引擎 - DMMR的核心认知机制"""
    
    def __init__(self, memory: MultipleMemorySystems):
        self.memory = memory
        self.cache = ActivationCache()
        self.config = get_config().activation
        
        # 激活参数
        self.decay_factor = self.config.decay_factor
        self.activation_threshold = self.config.activation_threshold
        self.fan_out_factor = self.config.fan_out_factor
        self.max_depth = self.config.max_depth
        
        # 激活状态跟踪
        self.active_nodes: Dict[str, float] = {}
        
        # 预取统计
        self.prefetch_stats = {
            "total_prefetches": 0,
            "useful_prefetches": 0
        }
        self._last_prefetch_ids: Set[str] = set()
        self._last_turn_stats = {"total": 0, "useful": 0}
        
        print(f"⚡ 激活引擎初始化完成 (阈值: {self.activation_threshold}, 衰减: {self.decay_factor})")
    
    async def cognitive_priming(self, user_id: str, context_hints: List[str] = None):
        """
        认知启动 - 预加载相关记忆到认知就绪状态
        模拟记忆系统的预激活过程
        """
        print(f"🧠 开始认知启动 (用户: {user_id})")
        
        # 预取高频节点
        high_priority_nodes = ["Python", "Bug", "PowerShell", "API", "学习", "朋友"]
        
        prefetch_count = 0
        for node_id in high_priority_nodes:
            # 尝试从语义记忆获取节点
            node = self.memory.get_semantic_node(node_id)
            if node:
                await self.cache.set(f"node:{node_id}", node)
                self._last_prefetch_ids.add(node_id)
                prefetch_count += 1
                print(f"  → 预取节点: {node_id}")
            
            # 也从程序记忆尝试获取
            proc_node = self.memory.get_procedural_node(node_id)
            if proc_node:
                await self.cache.set(f"proc_node:{node_id}", proc_node)
                prefetch_count += 1
        
        # 更新统计
        self._last_turn_stats["total"] = prefetch_count
        self.prefetch_stats["total_prefetches"] += prefetch_count
        
        # 启动后台语义扩展
        asyncio.create_task(self._background_semantic_expansion(user_id))
        
        print(f"✅ 认知启动完成 (预取: {prefetch_count} 个节点)")
    
    async def _background_semantic_expansion(self, user_id: str):
        """后台语义扩展任务"""
        await asyncio.sleep(0.1)  # 模拟异步处理延迟
        
        print("  [后台] 语义扩展任务执行中...")
        
        # 模拟从记忆系统中发现更多相关节点
        expansion_nodes = ["Docker", "JavaScript", "Framework", "Exception"]
        
        for node_id in expansion_nodes:
            node = self.memory.get_semantic_node(node_id)
            if node:
                await self.cache.set(f"expanded:{node_id}", node)
        
        print("  [后台] 语义扩展完成")
    
    def spreading_activation(self, cues: List[Tuple[str, float]], 
                           task_type: TaskType, 
                           max_depth: Optional[int] = None) -> List[Node]:
        """
        扩散激活 - 核心联想记忆算法
        基于ACT-R理论实现激活能量在记忆网络中的传播
        
        Args:
            cues: 激活线索列表 [(节点ID, 初始能量)]
            task_type: 任务类型，影响注意力权重
            max_depth: 最大扩散深度
            
        Returns:
            激活的节点列表
        """
        max_depth = max_depth or self.max_depth
        print(f"🔥 开始扩散激活 (线索: {len(cues)}, 类型: {task_type.value}, 深度: {max_depth})")
        
        # 重置激活状态
        self.active_nodes.clear()
        
        # 获取任务相关的注意力权重
        attention_weights = self._get_attention_weights(task_type)
        
        # 初始化激活队列
        activation_queue = []
        for node_id, initial_energy in cues:
            self.active_nodes[node_id] = initial_energy
            activation_queue.append((node_id, 0))  # (节点ID, 深度)
        
        visited = set()
        
        # BFS扩散激活
        while activation_queue:
            current_id, depth = activation_queue.pop(0)
            
            if depth >= max_depth or current_id in visited:
                continue
            
            visited.add(current_id)
            current_activation = self.active_nodes.get(current_id, 0)
            
            # 检查激活阈值
            if current_activation < self.activation_threshold:
                continue
            
            print(f"  → 处理节点: {current_id} (激活: {current_activation:.3f}, 深度: {depth})")
            
            # 获取邻居节点
            neighbors = self._get_all_neighbors(current_id)
            
            # 传播激活能量
            for neighbor_node, edge_weight in neighbors:
                # 计算注意力权重
                attention_weight = attention_weights.get(neighbor_node.label, 1.0)
                
                # ACT-R激活传播公式：A_i = B_i + Σ(W_j * S_ji)
                # 这里简化为：received_energy = sender_activation * decay * edge_weight * attention_weight
                received_energy = (current_activation * 
                                 self.decay_factor * 
                                 edge_weight * 
                                 attention_weight)
                
                # 更新邻居节点激活值
                neighbor_id = neighbor_node.id
                self.active_nodes[neighbor_id] = (
                    self.active_nodes.get(neighbor_id, 0) + received_energy
                )
                
                # 添加到激活队列
                if neighbor_id not in visited:
                    activation_queue.append((neighbor_id, depth + 1))
            
            # 跨模态激活门控
            if current_activation > 0.8:  # 高激活阈值触发跨模态
                await self._cross_modal_activation(current_id)
        
        # 收集并返回激活节点
        activated_nodes = self._collect_activated_nodes()
        
        print(f"✅ 扩散激活完成 (激活节点: {len(activated_nodes)})")
        return activated_nodes
    
    def _get_attention_weights(self, task_type: TaskType) -> Dict[str, float]:
        """获取任务相关的注意力权重"""
        attention_maps = {
            TaskType.TECHNICAL_CODING: {
                "Technology": 1.5,
                "Concept": 1.2, 
                "Problem": 1.3,
                "default": 0.8
            },
            TaskType.EMOTIONAL_COUNSELING: {
                "Person": 1.5,
                "Goal": 1.3,
                "Activity": 1.2,
                "default": 0.7
            },
            TaskType.CREATIVE_WRITING: {
                "Concept": 1.4,
                "Activity": 1.2,
                "default": 1.0
            },
            TaskType.EDUCATIONAL: {
                "Concept": 1.5,
                "Technology": 1.2,
                "default": 1.0
            }
        }
        
        return attention_maps.get(task_type, {"default": 1.0})
    
    def _get_all_neighbors(self, node_id: str) -> List[Tuple[Node, float]]:
        """获取节点的所有邻居（语义+程序记忆）"""
        neighbors = []
        
        # 语义记忆邻居
        semantic_neighbors = self.memory.get_semantic_weighted_neighbors(node_id)
        neighbors.extend(semantic_neighbors)
        
        # 程序记忆邻居
        procedural_neighbors = self.memory.get_procedural_weighted_neighbors(node_id)
        neighbors.extend(procedural_neighbors)
        
        return neighbors
    
    async def _cross_modal_activation(self, node_id: str):
        """跨模态激活 - 从图记忆触发向量记忆检索"""
        print(f"  🔗 跨模态激活: {node_id}")
        
        # 获取节点
        node = (self.memory.get_semantic_node(node_id) or 
                self.memory.get_procedural_node(node_id))
        
        if node and node.embedding:
            # 在情景记忆中搜索相关事件
            episodic_memories = self.memory.search_episodic_by_vector(
                node.embedding, n_results=2
            )
            
            if episodic_memories:
                print(f"    → 发现相关情景记忆: {len(episodic_memories)} 个")
                
                # 可以进一步将情景记忆中的实体重新注入激活网络
                # 这里简化处理
    
    def _collect_activated_nodes(self) -> List[Node]:
        """收集所有激活节点"""
        activated_nodes = []
        
        for node_id, activation_energy in self.active_nodes.items():
            if activation_energy > self.activation_threshold:
                # 尝试从两个记忆系统获取节点
                node = (self.memory.get_semantic_node(node_id) or 
                       self.memory.get_procedural_node(node_id))
                
                if node:
                    # 将激活能量存储在节点属性中
                    node.properties["activation"] = activation_energy
                    activated_nodes.append(node)
        
        # 按激活能量排序
        activated_nodes.sort(
            key=lambda n: n.properties.get("activation", 0),
            reverse=True
        )
        
        return activated_nodes
    
    def mark_useful_prefetch(self, used_memory_ids: List[str]):
        """标记有用的预取项"""
        if not used_memory_ids:
            return
        
        used_set = set(used_memory_ids)
        hits = len(self._last_prefetch_ids.intersection(used_set))
        
        if hits > 0:
            self._last_turn_stats["useful"] += hits
            self.prefetch_stats["useful_prefetches"] += hits
            print(f"  📊 预取命中: {hits}/{len(self._last_prefetch_ids)}")
    
    def reward_activation_path(self, path_nodes: List[str], reward: float = 0.1):
        """奖励成功的激活路径（强化学习）"""
        print(f"  🎯 路径奖励: {len(path_nodes)} 个节点, 奖励: {reward}")
        
        # 在真实系统中，这里会更新图中边的权重
        # 简化实现：记录成功路径用于未来优化
        for i, node_id in enumerate(path_nodes):
            if node_id in self.active_nodes:
                # 略微增加该节点的基础激活水平
                self.active_nodes[node_id] += reward * (1.0 - i * 0.1)
    
    def get_prefetch_stats(self) -> Dict[str, int]:
        """获取预取统计信息"""
        return dict(self.prefetch_stats)
    
    def get_and_reset_prefetch_stats(self) -> Dict[str, int]:
        """获取并重置单轮统计"""
        stats = dict(self._last_turn_stats)
        
        # 重置单轮统计
        self._last_turn_stats = {"total": 0, "useful": 0}
        self._last_prefetch_ids.clear()
        
        return stats
    
    def get_activation_summary(self) -> Dict[str, Any]:
        """获取激活引擎运行摘要"""
        return {
            "active_nodes_count": len(self.active_nodes),
            "total_activation_energy": sum(self.active_nodes.values()),
            "avg_activation_energy": (
                sum(self.active_nodes.values()) / len(self.active_nodes)
                if self.active_nodes else 0
            ),
            "cache_size": len(self.cache.cache),
            "prefetch_hit_rate": (
                self.prefetch_stats["useful_prefetches"] / 
                max(self.prefetch_stats["total_prefetches"], 1)
            )
        }



