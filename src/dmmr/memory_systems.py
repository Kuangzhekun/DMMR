# -*- coding: utf-8 -*-
"""
Multiple Memory Systems - Manages episodic, semantic, and procedural memories.
Supports both real and simulated backends for vector and graph databases.
"""
import math
from typing import List, Dict, Any, Optional, Tuple
from .data_models import MemoryChunk, Node, Relationship
from .config import get_config

# Optional dependencies
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
    """Vector Database Interface - supports FAISS and in-memory implementations."""
    
    def __init__(self, collection_name: str, use_real_backend: bool = False):
        self.collection_name = collection_name
        self.use_real_backend = use_real_backend
        self.config = get_config().database
        
        if use_real_backend and FAISS_AVAILABLE:
            self._init_faiss()
        else:
            self._init_memory_backend()
    
    def _init_faiss(self):
        """Initializes the FAISS backend."""
        self.dim = self.config.vector_dim
        self.index = faiss.IndexFlatIP(self.dim)  # Inner product index
        self.id_to_chunk = {}
        self.chunk_ids = []
        print(f"📊 FAISS vector database initialized (dimension: {self.dim})")
    
    def _init_memory_backend(self):
        """Initializes the in-memory backend."""
        self.memory_store = {}
        self.dim = get_config().database.vector_dim
        print(f"💾 In-memory vector database initialized (collection: {self.collection_name})")
    
    def add(self, chunk: MemoryChunk):
        """Adds a memory chunk."""
        # Ensure there is a vector representation
        if chunk.embedding is None:
            chunk.embedding = self._generate_embedding(chunk.content)
        
        if hasattr(self, 'index'):  # FAISS backend
            self._add_to_faiss(chunk)
        else:  # In-memory backend
            self._add_to_memory(chunk)
    
    def search(self, query_vector: List[float], n_results: int = 5) -> List[MemoryChunk]:
        """Performs a vector search."""
        if hasattr(self, 'index'):
            return self._search_faiss(query_vector, n_results)
        else:
            return self._search_memory(query_vector, n_results)
    
    def _add_to_faiss(self, chunk: MemoryChunk):
        """Adds to the FAISS index."""
        vector = np.array(chunk.embedding, dtype='float32').reshape(1, -1)
        self.index.add(vector)
        
        chunk_id = chunk.id or f"chunk_{len(self.chunk_ids)}"
        self.chunk_ids.append(chunk_id)
        self.id_to_chunk[chunk_id] = chunk
    
    def _add_to_memory(self, chunk: MemoryChunk):
        """Adds to the in-memory store."""
        chunk_id = chunk.id or f"chunk_{len(self.memory_store)}"
        self.memory_store[chunk_id] = chunk
    
    def _search_faiss(self, query_vector: List[float], n_results: int) -> List[MemoryChunk]:
        """Searches using FAISS."""
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
        """Searches in-memory."""
        scored_chunks = []
        
        for chunk in self.memory_store.values():
            if chunk.embedding:
                similarity = self._cosine_similarity(query_vector, chunk.embedding)
                scored_chunks.append((similarity, chunk))
        
        # Sort by similarity
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        return [chunk for _, chunk in scored_chunks[:n_results]]
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generates a simple hash-based embedding."""
        import hashlib
        
        # Use text hash to generate a deterministic vector
        hash_val = int(hashlib.md5(text.encode('utf-8')).hexdigest(), 16)
        
        # Generate a fixed-dimensional vector
        vector = []
        for i in range(self.dim):
            vector.append(math.sin(hash_val * (i + 1)) * 0.5 + 0.5)
        
        # L2 normalization
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / norm for v in vector]
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculates cosine similarity."""
        if not vec1 or not vec2:
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(a * a for a in vec2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)


class GraphDatabase:
    """Graph Database Interface - supports Neo4j and in-memory implementations."""
    
    def __init__(self, graph_name: str, use_real_backend: bool = False):
        self.graph_name = graph_name
        self.use_real_backend = use_real_backend
        self.config = get_config().database
        
        if use_real_backend and NEO4J_AVAILABLE:
            self._init_neo4j()
        else:
            self._init_memory_backend()
    
    def _init_neo4j(self):
        """Initializes the Neo4j backend."""
        try:
            self.driver = GraphDatabase.driver(
                self.config.graph_uri,
                auth=(self.config.graph_user, self.config.graph_password)
            )
            self.driver.verify_connectivity()
            print(f"🔗 Neo4j graph database connected successfully ({self.graph_name})")
        except Exception as e:
            print(f"⚠️ Neo4j connection failed, falling back to in-memory backend: {e}")
            self._init_memory_backend()
    
    def _init_memory_backend(self):
        """Initializes the in-memory backend."""
        self.nodes = {}
        self.edges = []
        self.driver = None
        print(f"🧠 In-memory graph database initialized ({self.graph_name})")
    
    def add_node(self, node: Node):
        """Adds a node."""
        if self.driver:
            self._add_node_neo4j(node)
        else:
            self.nodes[node.id] = node
    
    def add_relationship(self, rel: Relationship):
        """Adds a relationship."""
        if self.driver:
            self._add_relationship_neo4j(rel)
        else:
            self.edges.append(rel)
    
    def get_node(self, node_id: str) -> Optional[Node]:
        """Gets a node."""
        if self.driver:
            return self._get_node_neo4j(node_id)
        else:
            return self.nodes.get(node_id)
    
    def get_neighbors(self, node_id: str) -> List[Node]:
        """Gets neighbor nodes."""
        if self.driver:
            return self._get_neighbors_neo4j(node_id)
        else:
            return self._get_neighbors_memory(node_id)
    
    def get_weighted_neighbors(self, node_id: str) -> List[Tuple[Node, float]]:
        """Gets neighbor nodes with weights."""
        if self.driver:
            return self._get_weighted_neighbors_neo4j(node_id)
        else:
            return self._get_weighted_neighbors_memory(node_id)
    
    # Neo4j implementations
    def _add_node_neo4j(self, node: Node):
        """Adds a node to Neo4j."""
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
        """Adds a relationship to Neo4j."""
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
        """Gets a node from Neo4j."""
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
        """Gets neighbors from Neo4j."""
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
        """Gets weighted neighbors from Neo4j."""
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
    
    # In-memory implementations
    def _get_neighbors_memory(self, node_id: str) -> List[Node]:
        """Gets neighbors from in-memory store."""
        neighbors = []
        for edge in self.edges:
            if edge.source_id == node_id and edge.target_id in self.nodes:
                neighbors.append(self.nodes[edge.target_id])
            elif edge.target_id == node_id and edge.source_id in self.nodes:
                neighbors.append(self.nodes[edge.source_id])
        return neighbors
    
    def _get_weighted_neighbors_memory(self, node_id: str) -> List[Tuple[Node, float]]:
        """Gets weighted neighbors from in-memory store."""
        neighbors = []
        for edge in self.edges:
            if edge.source_id == node_id and edge.target_id in self.nodes:
                neighbors.append((self.nodes[edge.target_id], edge.weight))
            elif edge.target_id == node_id and edge.source_id in self.nodes:
                neighbors.append((self.nodes[edge.source_id], edge.weight))
        return neighbors


class MultipleMemorySystems:
    """Manager for the multiple memory systems."""
    
    def __init__(self, user_id: str, use_real_backends: bool = False):
        self.user_id = user_id
        self.use_real_backends = use_real_backends
        
        print(f"🧠 Initializing multiple memory systems (User: {user_id}, Real Backends: {use_real_backends})")
        
        # Episodic Memory - Vector Database
        self.episodic = VectorDatabase(
            collection_name=f"{user_id}_episodic",
            use_real_backend=use_real_backends
        )
        
        # Semantic Memory - Graph Database
        self.semantic = GraphDatabase(
            graph_name=f"{user_id}_semantic",
            use_real_backend=use_real_backends
        )
        
        # Procedural Memory - Graph Database
        self.procedural = GraphDatabase(
            graph_name=f"{user_id}_procedural",
            use_real_backend=use_real_backends
        )
        
        print("✅ Multiple memory systems initialized successfully.")
    
    # Episodic Memory Interface
    def add_to_episodic(self, chunk: MemoryChunk):
        """Adds a chunk to episodic memory."""
        self.episodic.add(chunk)
    
    def search_episodic_by_vector(self, query_vector: List[float], n_results: int = 3) -> List[MemoryChunk]:
        """Searches episodic memory by vector."""
        return self.episodic.search(query_vector, n_results)
    
    # Semantic Memory Interface
    def add_semantic_node(self, node: Node):
        """Adds a semantic node."""
        self.semantic.add_node(node)
    
    def add_semantic_relationship(self, rel: Relationship):
        """Adds a semantic relationship."""
        self.semantic.add_relationship(rel)
    
    def get_semantic_node(self, node_id: str) -> Optional[Node]:
        """Gets a semantic node."""
        return self.semantic.get_node(node_id)
    
    def get_semantic_neighbors(self, node_id: str) -> List[Node]:
        """Gets semantic neighbors."""
        return self.semantic.get_neighbors(node_id)
    
    def get_semantic_weighted_neighbors(self, node_id: str) -> List[Tuple[Node, float]]:
        """Gets weighted semantic neighbors."""
        return self.semantic.get_weighted_neighbors(node_id)
    
    # Procedural Memory Interface
    def add_procedural_node(self, node: Node):
        """Adds a procedural node."""
        self.procedural.add_node(node)
    
    def add_procedural_relationship(self, rel: Relationship):
        """Adds a procedural relationship."""
        self.procedural.add_relationship(rel)
    
    def get_procedural_node(self, node_id: str) -> Optional[Node]:
        """Gets a procedural node."""
        return self.procedural.get_node(node_id)
    
    def get_procedural_neighbors(self, node_id: str) -> List[Node]:
        """Gets procedural neighbors."""
        return self.procedural.get_neighbors(node_id)
    
    def get_procedural_weighted_neighbors(self, node_id: str) -> List[Tuple[Node, float]]:
        """Gets weighted procedural neighbors."""
        return self.procedural.get_weighted_neighbors(node_id)



