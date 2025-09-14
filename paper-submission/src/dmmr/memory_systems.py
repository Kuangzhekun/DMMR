# -*- coding: utf-8 -*-
"""
多重记忆系统 - 实现情景、语义、程序记忆的管理
支持向量数据库和图数据库的真实/模拟后端
"""
import math
from typing import List, Dict, Any, Optional, Tuple
from .data_models import MemoryChunk, Node, Relationship
from .config import get_config

# 可选依赖
try:
    import faiss
    import numpy as np
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

try:
    from neo4j import GraphDatabase, Driver
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False


class VectorDatabase:
    """向量数据库接口 - 支持FAISS和内存实现"""
    
    def __init__(self, collection_name: str, use_real_backend: bool = False):
        self.collection_name = collection_name
        self.use_real_backend = use_real_backend
        self.config = get_config().database
        
        if use_real_backend and FAISS_AVAILABLE:
            self._init_faiss()
        else:
            self._init_memory_backend()
    
    def _init_faiss(self):
        """初始化FAISS后端"""
        self.dim = self.config.vector_dim
        self.index = faiss.IndexFlatIP(self.dim)  # 内积索引
        self.id_to_chunk = {}
        self.chunk_ids = []
        print(f"📊 FAISS向量数据库初始化完成 (维度: {self.dim})")
    
    def _init_memory_backend(self):
        """初始化内存后端"""
        self.memory_store = {}
        self.dim = get_config().database.vector_dim
        print(f"💾 内存向量数据库初始化完成 (集合: {self.collection_name})")
    
    def add(self, chunk: MemoryChunk):
        """添加记忆块"""
        # 确保有向量表示
        if chunk.embedding is None:
            chunk.embedding = self._generate_embedding(chunk.content)
        
        if hasattr(self, 'index'):  # FAISS后端
            self._add_to_faiss(chunk)
        else:  # 内存后端
            self._add_to_memory(chunk)
    
    def search(self, query_vector: List[float], n_results: int = 5) -> List[MemoryChunk]:
        """向量搜索"""
        if hasattr(self, 'index'):
            return self._search_faiss(query_vector, n_results)
        else:
            return self._search_memory(query_vector, n_results)
    
    def _add_to_faiss(self, chunk: MemoryChunk):
        """添加到FAISS索引"""
        vector = np.array(chunk.embedding, dtype='float32').reshape(1, -1)
        self.index.add(vector)
        
        chunk_id = chunk.id or f"chunk_{len(self.chunk_ids)}"
        self.chunk_ids.append(chunk_id)
        self.id_to_chunk[chunk_id] = chunk
    
    def _add_to_memory(self, chunk: MemoryChunk):
        """添加到内存存储"""
        chunk_id = chunk.id or f"chunk_{len(self.memory_store)}"
        self.memory_store[chunk_id] = chunk
    
    def _search_faiss(self, query_vector: List[float], n_results: int) -> List[MemoryChunk]:
        """FAISS搜索"""
        if self.index.ntotal == 0:
            return []
        
        query = np.array(query_vector, dtype='float32').reshape(1, -1)
        scores, indices = self.index.search(query, min(n_results, self.index.ntotal))
        
        results = []
        for idx in indices[0]:
            if 0 <= idx < len(self.chunk_ids):
                chunk_id = self.chunk_ids[idx]
                chunk = self.id_to_chunk.get(chunk_id)
                if chunk:
                    results.append(chunk)
        
        return results
    
    def _search_memory(self, query_vector: List[float], n_results: int) -> List[MemoryChunk]:
        """内存搜索"""
        scored_chunks = []
        
        for chunk in self.memory_store.values():
            if chunk.embedding:
                similarity = self._cosine_similarity(query_vector, chunk.embedding)
                scored_chunks.append((similarity, chunk))
        
        # 按相似度排序
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        return [chunk for _, chunk in scored_chunks[:n_results]]
    
    def _generate_embedding(self, text: str) -> List[float]:
        """生成简单的基于哈希的嵌入"""
        import hashlib
        
        # 使用文本哈希生成确定性向量
        hash_val = int(hashlib.md5(text.encode('utf-8')).hexdigest(), 16)
        
        # 生成固定维度的向量
        vector = []
        for i in range(self.dim):
            vector.append(math.sin(hash_val * (i + 1)) * 0.5 + 0.5)
        
        # L2归一化
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / norm for v in vector]
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        if not vec1 or not vec2:
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(a * a for a in vec2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)


class GraphDatabase:
    """图数据库接口 - 支持Neo4j和内存实现"""
    
    def __init__(self, graph_name: str, use_real_backend: bool = False):
        self.graph_name = graph_name
        self.use_real_backend = use_real_backend
        self.config = get_config().database
        
        if use_real_backend and NEO4J_AVAILABLE:
            self._init_neo4j()
        else:
            self._init_memory_backend()
    
    def _init_neo4j(self):
        """初始化Neo4j后端"""
        try:
            self.driver = GraphDatabase.driver(
                self.config.graph_uri,
                auth=(self.config.graph_user, self.config.graph_password)
            )
            self.driver.verify_connectivity()
            print(f"🔗 Neo4j图数据库连接成功 ({self.graph_name})")
        except Exception as e:
            print(f"⚠️ Neo4j连接失败，使用内存后端: {e}")
            self._init_memory_backend()
    
    def _init_memory_backend(self):
        """初始化内存后端"""
        self.nodes = {}
        self.edges = []
        self.driver = None
        print(f"🧠 内存图数据库初始化完成 ({self.graph_name})")
    
    def add_node(self, node: Node):
        """添加节点"""
        if self.driver:
            self._add_node_neo4j(node)
        else:
            self.nodes[node.id] = node
    
    def add_relationship(self, rel: Relationship):
        """添加关系"""
        if self.driver:
            self._add_relationship_neo4j(rel)
        else:
            self.edges.append(rel)
    
    def get_node(self, node_id: str) -> Optional[Node]:
        """获取节点"""
        if self.driver:
            return self._get_node_neo4j(node_id)
        else:
            return self.nodes.get(node_id)
    
    def get_neighbors(self, node_id: str) -> List[Node]:
        """获取邻居节点"""
        if self.driver:
            return self._get_neighbors_neo4j(node_id)
        else:
            return self._get_neighbors_memory(node_id)
    
    def get_weighted_neighbors(self, node_id: str) -> List[Tuple[Node, float]]:
        """获取带权重的邻居节点"""
        if self.driver:
            return self._get_weighted_neighbors_neo4j(node_id)
        else:
            return self._get_weighted_neighbors_memory(node_id)
    
    # Neo4j实现
    def _add_node_neo4j(self, node: Node):
        """Neo4j添加节点"""
        query = (
            f"MERGE (n:{node.label} {{id: $id}}) "
            "SET n += $properties, n.embedding = $embedding"
        )
        with self.driver.session() as session:
            session.run(query, {
                "id": node.id,
                "properties": node.properties,
                "embedding": node.embedding or []
            })
    
    def _add_relationship_neo4j(self, rel: Relationship):
        """Neo4j添加关系"""
        query = (
            "MATCH (s {id: $source_id}), (t {id: $target_id}) "
            f"MERGE (s)-[r:{rel.label}]->(t) "
            "SET r += $properties, r.weight = $weight"
        )
        with self.driver.session() as session:
            session.run(query, {
                "source_id": rel.source_id,
                "target_id": rel.target_id,
                "properties": rel.properties,
                "weight": rel.weight
            })
    
    def _get_node_neo4j(self, node_id: str) -> Optional[Node]:
        """Neo4j获取节点"""
        query = "MATCH (n {id: $node_id}) RETURN n"
        with self.driver.session() as session:
            result = session.run(query, {"node_id": node_id})
            record = result.single()
            if record:
                n = record["n"]
                return Node(
                    id=n["id"],
                    label=list(n.labels)[0],
                    properties=dict(n),
                    embedding=n.get("embedding")
                )
        return None
    
    def _get_neighbors_neo4j(self, node_id: str) -> List[Node]:
        """Neo4j获取邻居"""
        query = "MATCH (n {id: $node_id})-[]-(neighbor) RETURN neighbor"
        neighbors = []
        with self.driver.session() as session:
            result = session.run(query, {"node_id": node_id})
            for record in result:
                n = record["neighbor"]
                neighbors.append(Node(
                    id=n["id"],
                    label=list(n.labels)[0],
                    properties=dict(n),
                    embedding=n.get("embedding")
                ))
        return neighbors
    
    def _get_weighted_neighbors_neo4j(self, node_id: str) -> List[Tuple[Node, float]]:
        """Neo4j获取带权重邻居"""
        query = "MATCH (n {id: $node_id})-[r]-(neighbor) RETURN neighbor, r.weight as weight"
        neighbors = []
        with self.driver.session() as session:
            result = session.run(query, {"node_id": node_id})
            for record in result:
                n = record["neighbor"]
                weight = record["weight"] or 1.0
                node = Node(
                    id=n["id"],
                    label=list(n.labels)[0],
                    properties=dict(n),
                    embedding=n.get("embedding")
                )
                neighbors.append((node, weight))
        return neighbors
    
    # 内存实现
    def _get_neighbors_memory(self, node_id: str) -> List[Node]:
        """内存获取邻居"""
        neighbors = []
        for edge in self.edges:
            if edge.source_id == node_id and edge.target_id in self.nodes:
                neighbors.append(self.nodes[edge.target_id])
            elif edge.target_id == node_id and edge.source_id in self.nodes:
                neighbors.append(self.nodes[edge.source_id])
        return neighbors
    
    def _get_weighted_neighbors_memory(self, node_id: str) -> List[Tuple[Node, float]]:
        """内存获取带权重邻居"""
        neighbors = []
        for edge in self.edges:
            if edge.source_id == node_id and edge.target_id in self.nodes:
                neighbors.append((self.nodes[edge.target_id], edge.weight))
            elif edge.target_id == node_id and edge.source_id in self.nodes:
                neighbors.append((self.nodes[edge.source_id], edge.weight))
        return neighbors


class MultipleMemorySystems:
    """多重记忆系统管理器"""
    
    def __init__(self, user_id: str, use_real_backends: bool = False):
        self.user_id = user_id
        self.use_real_backends = use_real_backends
        
        print(f"🧠 初始化多重记忆系统 (用户: {user_id}, 真实后端: {use_real_backends})")
        
        # 情景记忆 - 向量数据库
        self.episodic = VectorDatabase(
            collection_name=f"{user_id}_episodic",
            use_real_backend=use_real_backends
        )
        
        # 语义记忆 - 图数据库
        self.semantic = GraphDatabase(
            graph_name=f"{user_id}_semantic",
            use_real_backend=use_real_backends
        )
        
        # 程序记忆 - 图数据库
        self.procedural = GraphDatabase(
            graph_name=f"{user_id}_procedural",
            use_real_backend=use_real_backends
        )
        
        print("✅ 多重记忆系统初始化完成")
    
    # 情景记忆接口
    def add_to_episodic(self, chunk: MemoryChunk):
        """添加到情景记忆"""
        self.episodic.add(chunk)
    
    def search_episodic_by_vector(self, query_vector: List[float], n_results: int = 3) -> List[MemoryChunk]:
        """向量搜索情景记忆"""
        return self.episodic.search(query_vector, n_results)
    
    # 语义记忆接口
    def add_semantic_node(self, node: Node):
        """添加语义节点"""
        self.semantic.add_node(node)
    
    def add_semantic_relationship(self, rel: Relationship):
        """添加语义关系"""
        self.semantic.add_relationship(rel)
    
    def get_semantic_node(self, node_id: str) -> Optional[Node]:
        """获取语义节点"""
        return self.semantic.get_node(node_id)
    
    def get_semantic_neighbors(self, node_id: str) -> List[Node]:
        """获取语义邻居"""
        return self.semantic.get_neighbors(node_id)
    
    def get_semantic_weighted_neighbors(self, node_id: str) -> List[Tuple[Node, float]]:
        """获取语义带权邻居"""
        return self.semantic.get_weighted_neighbors(node_id)
    
    # 程序记忆接口
    def add_procedural_node(self, node: Node):
        """添加程序节点"""
        self.procedural.add_node(node)
    
    def add_procedural_relationship(self, rel: Relationship):
        """添加程序关系"""
        self.procedural.add_relationship(rel)
    
    def get_procedural_node(self, node_id: str) -> Optional[Node]:
        """获取程序节点"""
        return self.procedural.get_node(node_id)
    
    def get_procedural_neighbors(self, node_id: str) -> List[Node]:
        """获取程序邻居"""
        return self.procedural.get_neighbors(node_id)
    
    def get_procedural_weighted_neighbors(self, node_id: str) -> List[Tuple[Node, float]]:
        """获取程序带权邻居"""
        return self.procedural.get_weighted_neighbors(node_id)

