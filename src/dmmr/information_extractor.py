# -*- coding: utf-8 -*-
"""
信息抽取器 - 从文本中提取实体、关系并生成嵌入
"""
import hashlib
import math
from typing import List, Dict, Any, Optional
from .data_models import Node, Relationship, Entity, TaskType
from .api_wrapper import APIWrapper


class InformationExtractor:
    """信息抽取器，负责从文本中抽取结构化信息"""
    
    def __init__(self, api_wrapper: APIWrapper):
        self.api_wrapper = api_wrapper
        
        # 实体识别规则库
        self.entity_rules = {
            # 技术实体
            "python": Entity(id="Python", label="Technology", properties={"type": "language"}),
            "powershell": Entity(id="PowerShell", label="Technology", properties={"type": "shell"}),
            "javascript": Entity(id="JavaScript", label="Technology", properties={"type": "language"}),
            "docker": Entity(id="Docker", label="Technology", properties={"type": "container"}),
            "api": Entity(id="API", label="Technology", properties={"type": "interface"}),
            
            # 问题类实体
            "bug": Entity(id="Bug", label="Problem", properties={"severity": "medium"}),
            "错误": Entity(id="Error", label="Problem", properties={"severity": "medium"}),
            "异常": Entity(id="Exception", label="Problem", properties={"severity": "high"}),
            
            # 人物关系实体
            "朋友": Entity(id="Friend", label="Person", properties={"relation": "social"}),
            "同事": Entity(id="Colleague", label="Person", properties={"relation": "work"}),
            "家人": Entity(id="Family", label="Person", properties={"relation": "family"}),
            
            # 目标活动实体
            "减肥": Entity(id="WeightLoss", label="Goal", properties={"category": "health"}),
            "运动": Entity(id="Exercise", label="Activity", properties={"category": "health"}),
            "学习": Entity(id="Learning", label="Activity", properties={"category": "education"}),
            
            # 概念实体
            "executionpolicy": Entity(id="ExecutionPolicy", label="Concept", properties={"domain": "security"}),
            "权限": Entity(id="Permission", label="Concept", properties={"domain": "security"}),
        }
        
        print("🔍 信息抽取器初始化完成")
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        生成文本嵌入向量
        使用确定性哈希方法生成轻量级嵌入
        """
        from .config import get_config
        dim = get_config().database.vector_dim
        
        # 使用MD5哈希确保相同文本产生相同向量
        hash_val = int(hashlib.md5(text.encode('utf-8')).hexdigest(), 16)
        
        # 生成向量
        vector = []
        for i in range(dim):
            # 使用不同的种子产生向量的每个维度
            seed = (hash_val * (i + 1)) % (2**32)
            value = math.sin(seed * 0.00001) * 0.5 + 0.5  # 映射到[0, 1]
            vector.append(value)
        
        # L2归一化
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / norm for v in vector]
    
    def extract_entities(self, text: str) -> List[Entity]:
        """从文本中抽取实体"""
        entities = {}
        text_lower = text.lower()
        
        # 基于规则的实体抽取
        for keyword, entity_template in self.entity_rules.items():
            if keyword in text_lower:
                # 创建实体副本避免修改模板
                entity = Entity(
                    id=entity_template.id,
                    label=entity_template.label,
                    properties=entity_template.properties.copy(),
                    confidence=self._calculate_entity_confidence(keyword, text)
                )
                entities[entity.id] = entity
        
        return list(entities.values())
    
    def extract_relationships(self, text: str, entities: List[Entity], task_type: TaskType) -> List[Relationship]:
        """从文本和实体中抽取关系"""
        relationships = []
        entity_ids = {e.id for e in entities}
        text_lower = text.lower()
        
        # 预定义关系规则
        relationship_rules = [
            # 技术关系
            ({"Python", "Bug"}, "RELATED_TO", 0.8),
            ({"JavaScript", "Bug"}, "RELATED_TO", 0.8),
            ({"PowerShell", "ExecutionPolicy"}, "CONFIGURED_BY", 0.9),
            ({"Docker", "API"}, "USES", 0.7),
            
            # 健康关系
            ({"Exercise", "WeightLoss"}, "SUPPORTS", 0.9),
            ({"Learning", "Exercise"}, "INCLUDES", 0.6),
            
            # 社交关系
            ({"Friend", "Exercise"}, "SUPPORTS", 0.5),
            ({"Colleague", "Learning"}, "SUPPORTS", 0.6),
            
            # 问题关系
            ({"Permission", "ExecutionPolicy"}, "CONTROLLED_BY", 0.8),
            ({"Error", "Bug"}, "IS_TYPE_OF", 0.7),
        ]
        
        # 应用关系规则
        for rule_entities, relation_type, base_weight in relationship_rules:
            if rule_entities.issubset(entity_ids):
                # 创建关系（选择任意两个实体作为源和目标）
                entity_list = list(rule_entities)
                if len(entity_list) >= 2:
                    relationships.append(Relationship(
                        source_id=entity_list[0],
                        target_id=entity_list[1], 
                        label=relation_type,
                        weight=base_weight * self._calculate_relation_confidence(text, relation_type),
                        properties={"task_type": task_type.value, "auto_extracted": True}
                    ))
        
        # 基于文本上下文的动态关系抽取
        relationships.extend(self._extract_contextual_relationships(text, entity_ids, task_type))
        
        return relationships
    
    def extract_entities_and_relations(self, text: str, task_type: TaskType) -> Dict[str, Any]:
        """综合抽取实体和关系"""
        # 抽取实体
        entities = self.extract_entities(text)
        
        # 抽取关系
        relationships = self.extract_relationships(text, entities, task_type)
        
        # 转换为序列化格式
        return {
            "nodes": [self._entity_to_node_dict(e) for e in entities],
            "relationships": [self._relationship_to_dict(r) for r in relationships]
        }
    
    def _calculate_entity_confidence(self, keyword: str, text: str) -> float:
        """计算实体置信度"""
        text_lower = text.lower()
        
        # 基础置信度
        base_confidence = 0.7
        
        # 根据关键词出现次数调整
        keyword_count = text_lower.count(keyword)
        frequency_bonus = min(keyword_count * 0.1, 0.2)
        
        # 根据上下文调整
        context_bonus = 0.0
        if any(ctx in text_lower for ctx in ["问题", "帮助", "如何"]):
            context_bonus += 0.1
        
        return min(base_confidence + frequency_bonus + context_bonus, 1.0)
    
    def _calculate_relation_confidence(self, text: str, relation_type: str) -> float:
        """计算关系置信度"""
        text_lower = text.lower()
        
        # 关系类型权重映射
        relation_weights = {
            "RELATED_TO": 0.8,
            "SUPPORTS": 0.9,
            "CONFIGURED_BY": 0.9,
            "USES": 0.7,
            "INCLUDES": 0.6,
            "CONTROLLED_BY": 0.8,
            "IS_TYPE_OF": 0.7
        }
        
        base_weight = relation_weights.get(relation_type, 0.5)
        
        # 根据上下文调整
        if any(word in text_lower for word in ["因为", "所以", "导致", "引起"]):
            base_weight += 0.1
        
        return min(base_weight, 1.0)
    
    def _extract_contextual_relationships(self, text: str, entity_ids: set, task_type: TaskType) -> List[Relationship]:
        """基于上下文抽取动态关系"""
        relationships = []
        text_lower = text.lower()
        
        # 因果关系检测
        causation_patterns = ["因为", "所以", "导致", "引起", "造成"]
        if any(pattern in text_lower for pattern in causation_patterns):
            # 简化实现：如果有多个实体，创建因果关系
            entity_list = list(entity_ids)
            if len(entity_list) >= 2:
                relationships.append(Relationship(
                    source_id=entity_list[0],
                    target_id=entity_list[1],
                    label="CAUSES",
                    weight=0.7,
                    properties={"type": "contextual", "task_type": task_type.value}
                ))
        
        # 依赖关系检测
        dependency_patterns = ["需要", "依赖", "基于", "使用"]
        if any(pattern in text_lower for pattern in dependency_patterns):
            entity_list = list(entity_ids)
            if len(entity_list) >= 2:
                relationships.append(Relationship(
                    source_id=entity_list[0],
                    target_id=entity_list[1],
                    label="DEPENDS_ON",
                    weight=0.6,
                    properties={"type": "contextual", "task_type": task_type.value}
                ))
        
        return relationships
    
    def _entity_to_node_dict(self, entity: Entity) -> Dict[str, Any]:
        """将实体转换为节点字典"""
        return {
            "id": entity.id,
            "label": entity.label,
            "properties": {**entity.properties, "confidence": entity.confidence}
        }
    
    def _relationship_to_dict(self, relationship: Relationship) -> Dict[str, Any]:
        """将关系转换为字典"""
        return {
            "source_id": relationship.source_id,
            "target_id": relationship.target_id,
            "label": relationship.label,
            "weight": relationship.weight,
            "properties": relationship.properties
        }



