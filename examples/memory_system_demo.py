#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DMMR 记忆系统演示
展示情景记忆、语义记忆、程序记忆的工作原理
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.dmmr import (
    MultipleMemorySystems, InformationExtractor, ActivationEngine,
    APIWrapper, MemoryChunk, Node, Relationship, TaskType
)


def demo_episodic_memory():
    """演示情景记忆"""
    print("🧠 情景记忆演示")
    print("-" * 30)
    
    # 创建记忆系统
    memory_systems = MultipleMemorySystems("demo_user", use_real_backends=False)
    api_wrapper = APIWrapper()
    extractor = InformationExtractor(api_wrapper)
    
    # 创建一些情景记忆
    conversations = [
        "昨天我在学习Python时遇到了pandas导入错误",
        "今天解决了昨天的问题，原来是环境配置有误",
        "刚才写了一个数据处理脚本，运行很成功"
    ]
    
    chunks = []
    for i, content in enumerate(conversations):
        chunk = MemoryChunk(
            id=f"episode_{i}",
            content=content,
            task_type=TaskType.TECHNICAL_CODING,
            user_id="demo_user",
            significance_score=0.7 + i * 0.1
        )
        chunk.embedding = extractor.generate_embedding(content)
        memory_systems.add_to_episodic(chunk)
        chunks.append(chunk)
        print(f"   添加情景记忆 {i+1}: {content}")
    
    # 测试向量检索
    print("\n🔍 测试向量检索:")
    query = "Python编程问题"
    query_embedding = extractor.generate_embedding(query)
    
    results = memory_systems.search_episodic_by_vector(query_embedding, n_results=2)
    for i, result in enumerate(results):
        print(f"   检索结果 {i+1}: {result.content}")
    
    return memory_systems


def demo_semantic_memory(memory_systems):
    """演示语义记忆"""
    print("\n🌐 语义记忆演示")
    print("-" * 30)
    
    # 添加语义节点
    nodes = [
        Node(id="Python", label="Technology", properties={"type": "programming_language", "popularity": "high"}),
        Node(id="Pandas", label="Technology", properties={"type": "library", "domain": "data_science"}),
        Node(id="DataProcessing", label="Concept", properties={"complexity": "medium"}),
        Node(id="Environment", label="Concept", properties={"type": "development_setup"})
    ]
    
    for node in nodes:
        memory_systems.add_semantic_node(node)
        print(f"   添加语义节点: {node.id} ({node.label})")
    
    # 添加语义关系
    relationships = [
        Relationship(source_id="Pandas", target_id="Python", label="DEPENDS_ON", weight=0.9),
        Relationship(source_id="DataProcessing", target_id="Pandas", label="USES", weight=0.8),
        Relationship(source_id="Python", target_id="Environment", label="REQUIRES", weight=0.7)
    ]
    
    for rel in relationships:
        memory_systems.add_semantic_relationship(rel)
        print(f"   添加语义关系: {rel.source_id} -[{rel.label}]-> {rel.target_id}")
    
    # 测试图遍历
    print("\n🕸️ 测试图遍历 (Python的邻居):")
    neighbors = memory_systems.get_semantic_neighbors("Python")
    for neighbor in neighbors:
        print(f"   邻居节点: {neighbor.id} ({neighbor.label})")
    
    return memory_systems


def demo_procedural_memory(memory_systems):
    """演示程序记忆"""
    print("\n⚙️ 程序记忆演示")
    print("-" * 30)
    
    # 添加程序节点（技能和流程）
    procedure_nodes = [
        Node(id="DebuggingSkill", label="Skill", properties={"proficiency": "intermediate", "domain": "programming"}),
        Node(id="ImportError", label="Problem", properties={"category": "syntax", "frequency": "common"}),
        Node(id="EnvironmentCheck", label="Procedure", properties={"steps": 3, "difficulty": "easy"}),
        Node(id="LibraryInstallation", label="Procedure", properties={"steps": 2, "difficulty": "easy"})
    ]
    
    for node in procedure_nodes:
        memory_systems.add_procedural_node(node)
        print(f"   添加程序节点: {node.id} ({node.label})")
    
    # 添加程序关系
    procedure_relationships = [
        Relationship(source_id="DebuggingSkill", target_id="ImportError", label="CAN_SOLVE", weight=0.8),
        Relationship(source_id="EnvironmentCheck", target_id="ImportError", label="DIAGNOSES", weight=0.9),
        Relationship(source_id="LibraryInstallation", target_id="ImportError", label="FIXES", weight=0.7)
    ]
    
    for rel in procedure_relationships:
        memory_systems.add_procedural_relationship(rel)
        print(f"   添加程序关系: {rel.source_id} -[{rel.label}]-> {rel.target_id}")
    
    # 测试程序记忆检索
    print("\n🔧 测试程序记忆检索 (ImportError的解决方案):")
    neighbors = memory_systems.get_procedural_weighted_neighbors("ImportError")
    for neighbor, weight in neighbors:
        print(f"   解决方案: {neighbor.id} (权重: {weight:.2f})")
    
    return memory_systems


def demo_activation_engine(memory_systems):
    """演示激活引擎"""
    print("\n⚡ 激活引擎演示")
    print("-" * 30)
    
    # 创建激活引擎
    activation_engine = ActivationEngine(memory_systems)
    
    # 测试扩散激活
    print("🔥 测试扩散激活 (从Python开始):")
    cues = [("Python", 1.0)]
    
    activated_nodes = activation_engine.spreading_activation(
        cues=cues,
        task_type=TaskType.TECHNICAL_CODING,
        max_depth=2
    )
    
    print("   激活的节点:")
    for node in activated_nodes:
        activation = node.properties.get('activation', 0.0)
        print(f"   - {node.id} ({node.label}): 激活度 {activation:.3f}")
    
    # 模拟路径奖励
    print("\n🎯 模拟路径奖励:")
    successful_path = ["Python", "Pandas", "DataProcessing"]
    activation_engine.reward_activation_path(successful_path, reward=0.1)
    
    return activation_engine


def demo_cross_modal_integration(memory_systems, activation_engine):
    """演示跨模态记忆整合"""
    print("\n🔗 跨模态记忆整合演示")
    print("-" * 30)
    
    # 模拟查询
    query = "pandas import error解决方案"
    extractor = InformationExtractor(APIWrapper())
    
    # 1. 从查询中提取实体作为激活线索
    entities = extractor.extract_entities(query)
    cues = [(entity.id, entity.confidence) for entity in entities]
    print(f"   从查询提取的线索: {[(c[0], f'{c[1]:.2f}') for c in cues]}")
    
    # 2. 激活图记忆
    activated_nodes = activation_engine.spreading_activation(
        cues=cues,
        task_type=TaskType.TECHNICAL_CODING,
        max_depth=2
    )
    print(f"   激活的图节点数: {len(activated_nodes)}")
    
    # 3. 使用激活节点的嵌入检索情景记忆
    print("   跨模态检索结果:")
    for node in activated_nodes[:2]:  # 只展示前2个
        if hasattr(node, 'embedding') and node.embedding:
            episodic_results = memory_systems.search_episodic_by_vector(
                node.embedding, n_results=1
            )
            for episode in episodic_results:
                print(f"   - 节点 {node.id} 激活了情景记忆: {episode.content[:50]}...")
    
    return activated_nodes


def main():
    """主演示函数"""
    print("🚀 DMMR 记忆系统完整演示")
    print("=" * 50)
    
    try:
        # 1. 情景记忆演示
        memory_systems = demo_episodic_memory()
        
        # 2. 语义记忆演示  
        memory_systems = demo_semantic_memory(memory_systems)
        
        # 3. 程序记忆演示
        memory_systems = demo_procedural_memory(memory_systems)
        
        # 4. 激活引擎演示
        activation_engine = demo_activation_engine(memory_systems)
        
        # 5. 跨模态整合演示
        demo_cross_modal_integration(memory_systems, activation_engine)
        
        print("\n✅ 记忆系统演示完成!")
        print("\n📊 演示总结:")
        print("   - 情景记忆: 存储具体的交互历史")
        print("   - 语义记忆: 存储概念和知识关系")
        print("   - 程序记忆: 存储技能和解决方案")
        print("   - 激活引擎: 实现联想和跨模态检索")
        
    except Exception as e:
        print(f"❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()



