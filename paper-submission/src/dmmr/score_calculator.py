# -*- coding: utf-8 -*-
"""
评分计算器 - 计算记忆重要性和相关性分数
基于多种启发式方法评估记忆的价值
"""
import math
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from .data_models import MemoryChunk, TaskType


class ScoreCalculator:
    """记忆重要性评分计算器"""
    
    def __init__(self):
        # 评分权重配置
        self.weights = {
            'recency': 0.3,      # 时间新近性
            'frequency': 0.25,   # 访问频率
            'relevance': 0.2,    # 内容相关性
            'task_match': 0.15,  # 任务类型匹配
            'user_feedback': 0.1 # 用户反馈
        }
        
        # 任务类型权重
        self.task_type_weights = {
            TaskType.TECHNICAL_CODING: 1.2,
            TaskType.EMOTIONAL_COUNSELING: 1.1,
            TaskType.CREATIVE_WRITING: 1.0,
            TaskType.EDUCATIONAL: 1.1,
            TaskType.GENERAL_QA: 1.0
        }
        
        print("📊 评分计算器初始化完成")
    
    def calculate_initial_score(self, chunk: MemoryChunk) -> float:
        """
        计算记忆块的初始重要性分数
        
        Args:
            chunk: 记忆块
            
        Returns:
            重要性分数 (0.0 - 1.0)
        """
        scores = {
            'recency': self._calculate_recency_score(chunk),
            'content_quality': self._calculate_content_quality_score(chunk),
            'task_importance': self._calculate_task_importance_score(chunk),
            'metadata_richness': self._calculate_metadata_score(chunk)
        }
        
        # 加权平均
        total_score = (
            scores['recency'] * 0.3 +
            scores['content_quality'] * 0.4 +
            scores['task_importance'] * 0.2 +
            scores['metadata_richness'] * 0.1
        )
        
        # 确保分数在有效范围内
        final_score = max(0.0, min(1.0, total_score))
        
        return final_score
    
    def calculate_relevance_score(self, chunk: MemoryChunk, 
                                query: str, 
                                task_type: TaskType) -> float:
        """
        计算记忆与当前查询的相关性分数
        
        Args:
            chunk: 记忆块
            query: 查询文本
            task_type: 任务类型
            
        Returns:
            相关性分数 (0.0 - 1.0)
        """
        scores = {
            'text_similarity': self._calculate_text_similarity(chunk.content, query),
            'task_match': self._calculate_task_match_score(chunk.task_type, task_type),
            'keyword_overlap': self._calculate_keyword_overlap(chunk, query),
            'context_relevance': self._calculate_context_relevance(chunk, query)
        }
        
        # 加权计算总分
        relevance_score = (
            scores['text_similarity'] * 0.4 +
            scores['task_match'] * 0.3 +
            scores['keyword_overlap'] * 0.2 +
            scores['context_relevance'] * 0.1
        )
        
        return max(0.0, min(1.0, relevance_score))
    
    def update_score_with_feedback(self, chunk: MemoryChunk, 
                                  feedback_type: str, 
                                  feedback_value: float) -> float:
        """
        基于用户反馈更新记忆分数
        
        Args:
            chunk: 记忆块
            feedback_type: 反馈类型 ('useful', 'not_useful', 'accurate', 'inaccurate')
            feedback_value: 反馈值 (-1.0 到 1.0)
            
        Returns:
            更新后的分数
        """
        current_score = chunk.significance_score
        
        # 反馈影响权重
        feedback_weights = {
            'useful': 0.2,
            'not_useful': -0.2,
            'accurate': 0.15,
            'inaccurate': -0.25
        }
        
        feedback_impact = feedback_weights.get(feedback_type, 0.0) * abs(feedback_value)
        new_score = current_score + feedback_impact
        
        # 限制分数范围
        new_score = max(0.0, min(1.0, new_score))
        
        return new_score
    
    def _calculate_recency_score(self, chunk: MemoryChunk) -> float:
        """计算时间新近性分数"""
        try:
            if isinstance(chunk.timestamp, str):
                timestamp = datetime.fromisoformat(chunk.timestamp.replace('Z', '+00:00'))
            else:
                timestamp = chunk.timestamp
            
            # 计算时间差（小时）
            time_diff = (datetime.now() - timestamp.replace(tzinfo=None)).total_seconds() / 3600
            
            # 使用指数衰减函数
            # 24小时内得分为1.0，之后指数衰减
            decay_rate = 0.1  # 衰减率
            recency_score = math.exp(-decay_rate * time_diff / 24)
            
            return max(0.0, min(1.0, recency_score))
            
        except Exception:
            # 解析失败时返回中等分数
            return 0.5
    
    def _calculate_content_quality_score(self, chunk: MemoryChunk) -> float:
        """计算内容质量分数"""
        content = chunk.content
        if not content:
            return 0.0
        
        quality_indicators = {
            'length': min(len(content) / 100, 1.0),  # 内容长度
            'structure': self._assess_content_structure(content),
            'informativeness': self._assess_informativeness(content),
            'clarity': self._assess_clarity(content)
        }
        
        # 加权平均
        quality_score = (
            quality_indicators['length'] * 0.2 +
            quality_indicators['structure'] * 0.3 +
            quality_indicators['informativeness'] * 0.3 +
            quality_indicators['clarity'] * 0.2
        )
        
        return quality_score
    
    def _calculate_task_importance_score(self, chunk: MemoryChunk) -> float:
        """计算任务重要性分数"""
        task_type = chunk.task_type
        base_weight = self.task_type_weights.get(task_type, 1.0)
        
        # 根据任务特定特征调整
        content_lower = chunk.content.lower()
        
        if task_type == TaskType.TECHNICAL_CODING:
            # 技术内容的重要性指标
            tech_indicators = ['bug', '错误', 'exception', '问题', '解决方案']
            importance_boost = sum(1 for indicator in tech_indicators if indicator in content_lower) * 0.1
        elif task_type == TaskType.EMOTIONAL_COUNSELING:
            # 情感内容的重要性指标
            emotion_indicators = ['感觉', '情绪', '压力', '焦虑', '困难', '支持']
            importance_boost = sum(1 for indicator in emotion_indicators if indicator in content_lower) * 0.1
        else:
            importance_boost = 0.0
        
        return min(1.0, base_weight * 0.5 + importance_boost)
    
    def _calculate_metadata_score(self, chunk: MemoryChunk) -> float:
        """计算元数据丰富度分数"""
        metadata = chunk.metadata
        if not metadata:
            return 0.3
        
        richness_indicators = [
            'user_id' in metadata,
            'task_type' in metadata,
            'keywords' in metadata,
            'context' in metadata,
            'importance' in metadata
        ]
        
        richness_score = sum(richness_indicators) / len(richness_indicators)
        return richness_score
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度（简化实现）"""
        if not text1 or not text2:
            return 0.0
        
        # 分词
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        # Jaccard相似度
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_task_match_score(self, chunk_task: TaskType, query_task: TaskType) -> float:
        """计算任务类型匹配分数"""
        if chunk_task == query_task:
            return 1.0
        
        # 任务类型相似性矩阵
        similarity_matrix = {
            (TaskType.TECHNICAL_CODING, TaskType.EDUCATIONAL): 0.6,
            (TaskType.EMOTIONAL_COUNSELING, TaskType.GENERAL_QA): 0.4,
            (TaskType.CREATIVE_WRITING, TaskType.EDUCATIONAL): 0.3,
        }
        
        # 对称性
        pair = (chunk_task, query_task)
        reverse_pair = (query_task, chunk_task)
        
        return similarity_matrix.get(pair, similarity_matrix.get(reverse_pair, 0.2))
    
    def _calculate_keyword_overlap(self, chunk: MemoryChunk, query: str) -> float:
        """计算关键词重叠度"""
        # 从元数据获取关键词
        chunk_keywords = set()
        if 'keywords' in chunk.metadata:
            chunk_keywords.update(chunk.metadata['keywords'])
        
        # 从内容提取关键词
        content_words = set(chunk.content.lower().split())
        chunk_keywords.update(content_words)
        
        # 查询关键词
        query_words = set(query.lower().split())
        
        if not chunk_keywords or not query_words:
            return 0.0
        
        # 计算重叠度
        overlap = len(chunk_keywords.intersection(query_words))
        total = len(chunk_keywords.union(query_words))
        
        return overlap / total if total > 0 else 0.0
    
    def _calculate_context_relevance(self, chunk: MemoryChunk, query: str) -> float:
        """计算上下文相关性"""
        # 简化实现：基于内容长度和查询匹配度
        content_length = len(chunk.content)
        query_length = len(query)
        
        # 长度相似性
        length_similarity = 1.0 - abs(content_length - query_length) / max(content_length, query_length, 1)
        
        # 内容包含性
        query_lower = query.lower()
        content_lower = chunk.content.lower()
        containment = 1.0 if query_lower in content_lower or content_lower in query_lower else 0.5
        
        return (length_similarity * 0.3 + containment * 0.7)
    
    def _assess_content_structure(self, content: str) -> float:
        """评估内容结构质量"""
        if not content:
            return 0.0
        
        # 简单的结构指标
        has_sentences = '.' in content or '?' in content or '!' in content
        has_paragraphs = '\n' in content
        reasonable_length = 10 <= len(content) <= 1000
        
        structure_score = (
            0.4 * has_sentences +
            0.3 * has_paragraphs + 
            0.3 * reasonable_length
        )
        
        return structure_score
    
    def _assess_informativeness(self, content: str) -> float:
        """评估信息丰富度"""
        if not content:
            return 0.0
        
        # 信息丰富度指标
        word_count = len(content.split())
        unique_words = len(set(content.lower().split()))
        
        # 词汇多样性
        lexical_diversity = unique_words / max(word_count, 1)
        
        # 包含具体信息的指标词
        info_indicators = ['具体', '详细', '例如', '比如', '步骤', '方法', '原因', '结果']
        info_richness = sum(1 for indicator in info_indicators if indicator in content) / len(info_indicators)
        
        return (lexical_diversity * 0.6 + info_richness * 0.4)
    
    def _assess_clarity(self, content: str) -> float:
        """评估内容清晰度"""
        if not content:
            return 0.0
        
        # 清晰度指标
        sentences = content.split('.')
        avg_sentence_length = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
        
        # 理想句长在10-20词之间
        sentence_length_score = 1.0 - abs(avg_sentence_length - 15) / 15
        sentence_length_score = max(0.0, min(1.0, sentence_length_score))
        
        # 避免过多重复词汇
        words = content.lower().split()
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        max_freq = max(word_freq.values()) if word_freq else 1
        repetition_penalty = min(max_freq / len(words), 0.3)
        
        clarity_score = sentence_length_score * (1.0 - repetition_penalty)
        
        return max(0.0, min(1.0, clarity_score))
    
    def get_scoring_stats(self) -> Dict[str, Any]:
        """获取评分统计信息"""
        return {
            'weights': dict(self.weights),
            'task_type_weights': {k.value: v for k, v in self.task_type_weights.items()},
            'scoring_components': [
                'recency', 'content_quality', 'task_importance', 'metadata_richness'
            ]
        }

