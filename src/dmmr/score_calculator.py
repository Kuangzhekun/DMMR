# -*- coding: utf-8 -*-
"""
Score Calculator - Calculates memory significance and relevance scores.
Evaluates the value of memories based on multiple heuristics.
"""
import math
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from .data_models import MemoryChunk, TaskType


class ScoreCalculator:
    """Calculates memory significance scores."""
    
    def __init__(self):
        # Scoring weight configuration
        self.weights = {
            'recency': 0.3,      # Temporal recency
            'frequency': 0.25,   # Access frequency
            'relevance': 0.2,    # Content relevance
            'task_match': 0.15,  # Task type match
            'user_feedback': 0.1 # User feedback
        }
        
        # Task type weights
        self.task_type_weights = {
            TaskType.TECHNICAL_CODING: 1.2,
            TaskType.EMOTIONAL_COUNSELING: 1.1,
            TaskType.CREATIVE_WRITING: 1.0,
            TaskType.EDUCATIONAL: 1.1,
            TaskType.GENERAL_QA: 1.0
        }
        
        print("📊 Score Calculator initialized.")
    
    def calculate_initial_score(self, chunk: MemoryChunk) -> float:
        """
        Calculates the initial significance score for a memory chunk.
        
        Args:
            chunk: The memory chunk.
            
        Returns:
            Significance score (0.0 - 1.0).
        """
        scores = {
            'recency': self._calculate_recency_score(chunk),
            'content_quality': self._calculate_content_quality_score(chunk),
            'task_importance': self._calculate_task_importance_score(chunk),
            'metadata_richness': self._calculate_metadata_score(chunk)
        }
        
        # Weighted average
        total_score = (
            scores['recency'] * 0.3 +
            scores['content_quality'] * 0.4 +
            scores['task_importance'] * 0.2 +
            scores['metadata_richness'] * 0.1
        )
        
        # Ensure the score is within a valid range
        final_score = max(0.0, min(1.0, total_score))
        
        return final_score
    
    def calculate_relevance_score(self, chunk: MemoryChunk, 
                                query: str, 
                                task_type: TaskType) -> float:
        """
        Calculates the relevance score of a memory to the current query.
        
        Args:
            chunk: The memory chunk.
            query: The query text.
            task_type: The task type.
            
        Returns:
            Relevance score (0.0 - 1.0).
        """
        scores = {
            'text_similarity': self._calculate_text_similarity(chunk.content, query),
            'task_match': self._calculate_task_match_score(chunk.task_type, task_type),
            'keyword_overlap': self._calculate_keyword_overlap(chunk, query),
            'context_relevance': self._calculate_context_relevance(chunk, query)
        }
        
        # Weighted calculation of the total score
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
        Updates the memory score based on user feedback.
        
        Args:
            chunk: The memory chunk.
            feedback_type: The type of feedback ('useful', 'not_useful', 'accurate', 'inaccurate').
            feedback_value: The feedback value (-1.0 to 1.0).
            
        Returns:
            The updated score.
        """
        current_score = chunk.significance_score
        
        # Feedback impact weights
        feedback_weights = {
            'useful': 0.2,
            'not_useful': -0.2,
            'accurate': 0.15,
            'inaccurate': -0.25
        }
        
        feedback_impact = feedback_weights.get(feedback_type, 0.0) * abs(feedback_value)
        new_score = current_score + feedback_impact
        
        # Clamp the score to the valid range
        new_score = max(0.0, min(1.0, new_score))
        
        return new_score
    
    def _calculate_recency_score(self, chunk: MemoryChunk) -> float:
        """Calculates the recency score."""
        try:
            if isinstance(chunk.timestamp, str):
                timestamp = datetime.fromisoformat(chunk.timestamp.replace('Z', '+00:00'))
            else:
                timestamp = chunk.timestamp
            
            # Calculate the time difference in hours
            time_diff = (datetime.now() - timestamp.replace(tzinfo=None)).total_seconds() / 3600
            
            # Use an exponential decay function
            # Score is 1.0 within 24 hours, then decays exponentially
            decay_rate = 0.1  # Decay rate
            recency_score = math.exp(-decay_rate * time_diff / 24)
            
            return max(0.0, min(1.0, recency_score))
            
        except Exception:
            # Return a medium score if parsing fails
            return 0.5
    
    def _calculate_content_quality_score(self, chunk: MemoryChunk) -> float:
        """Calculates the content quality score."""
        content = chunk.content
        if not content:
            return 0.0
        
        quality_indicators = {
            'length': min(len(content) / 100, 1.0),  # Content length
            'structure': self._assess_content_structure(content),
            'informativeness': self._assess_informativeness(content),
            'clarity': self._assess_clarity(content)
        }
        
        # Weighted average
        quality_score = (
            quality_indicators['length'] * 0.2 +
            quality_indicators['structure'] * 0.3 +
            quality_indicators['informativeness'] * 0.3 +
            quality_indicators['clarity'] * 0.2
        )
        
        return quality_score
    
    def _calculate_task_importance_score(self, chunk: MemoryChunk) -> float:
        """Calculates the task importance score."""
        task_type = chunk.task_type
        base_weight = self.task_type_weights.get(task_type, 1.0)
        
        # Adjust based on task-specific features
        content_lower = chunk.content.lower()
        
        if task_type == TaskType.TECHNICAL_CODING:
            # Importance indicators for technical content
            tech_indicators = ['bug', 'error', 'exception', 'issue', 'solution']
            importance_boost = sum(1 for indicator in tech_indicators if indicator in content_lower) * 0.1
        elif task_type == TaskType.EMOTIONAL_COUNSELING:
            # Importance indicators for emotional content
            emotion_indicators = ['feel', 'emotion', 'stress', 'anxiety', 'difficult', 'support']
            importance_boost = sum(1 for indicator in emotion_indicators if indicator in content_lower) * 0.1
        else:
            importance_boost = 0.0
        
        return min(1.0, base_weight * 0.5 + importance_boost)
    
    def _calculate_metadata_score(self, chunk: MemoryChunk) -> float:
        """Calculates the metadata richness score."""
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
        """Calculates text similarity (simplified implementation)."""
        if not text1 or not text2:
            return 0.0
        
        # Tokenize
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        # Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_task_match_score(self, chunk_task: TaskType, query_task: TaskType) -> float:
        """Calculates the task type match score."""
        if chunk_task == query_task:
            return 1.0
        
        # Task type similarity matrix
        similarity_matrix = {
            (TaskType.TECHNICAL_CODING, TaskType.EDUCATIONAL): 0.6,
            (TaskType.EMOTIONAL_COUNSELING, TaskType.GENERAL_QA): 0.4,
            (TaskType.CREATIVE_WRITING, TaskType.EDUCATIONAL): 0.3,
        }
        
        # Symmetry
        pair = (chunk_task, query_task)
        reverse_pair = (query_task, chunk_task)
        
        return similarity_matrix.get(pair, similarity_matrix.get(reverse_pair, 0.2))
    
    def _calculate_keyword_overlap(self, chunk: MemoryChunk, query: str) -> float:
        """Calculates keyword overlap."""
        # Get keywords from metadata
        chunk_keywords = set()
        if 'keywords' in chunk.metadata:
            chunk_keywords.update(chunk.metadata['keywords'])
        
        # Extract keywords from content
        content_words = set(chunk.content.lower().split())
        chunk_keywords.update(content_words)
        
        # Query keywords
        query_words = set(query.lower().split())
        
        if not chunk_keywords or not query_words:
            return 0.0
        
        # Calculate overlap
        overlap = len(chunk_keywords.intersection(query_words))
        total = len(chunk_keywords.union(query_words))
        
        return overlap / total if total > 0 else 0.0
    
    def _calculate_context_relevance(self, chunk: MemoryChunk, query: str) -> float:
        """Calculates context relevance."""
        # Simplified implementation: based on content length and query match
        content_length = len(chunk.content)
        query_length = len(query)
        
        # Length similarity
        length_similarity = 1.0 - abs(content_length - query_length) / max(content_length, query_length, 1)
        
        # Content containment
        query_lower = query.lower()
        content_lower = chunk.content.lower()
        containment = 1.0 if query_lower in content_lower or content_lower in query_lower else 0.5
        
        return (length_similarity * 0.3 + containment * 0.7)
    
    def _assess_content_structure(self, content: str) -> float:
        """Assesses the quality of the content structure."""
        if not content:
            return 0.0
        
        # Simple structural indicators
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
        """Assesses informativeness."""
        if not content:
            return 0.0
        
        # Informativeness indicators
        word_count = len(content.split())
        unique_words = len(set(content.lower().split()))
        
        # Lexical diversity
        lexical_diversity = unique_words / max(word_count, 1)
        
        # Indicator words for specific information
        info_indicators = ['specific', 'detailed', 'example', 'such as', 'steps', 'method', 'reason', 'result']
        info_richness = sum(1 for indicator in info_indicators if indicator in content) / len(info_indicators)
        
        return (lexical_diversity * 0.6 + info_richness * 0.4)
    
    def _assess_clarity(self, content: str) -> float:
        """Assesses content clarity."""
        if not content:
            return 0.0
        
        # Clarity indicators
        sentences = content.split('.')
        avg_sentence_length = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
        
        # Ideal sentence length is between 10-20 words
        sentence_length_score = 1.0 - abs(avg_sentence_length - 15) / 15
        sentence_length_score = max(0.0, min(1.0, sentence_length_score))
        
        # Avoid excessive repetition of words
        words = content.lower().split()
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        max_freq = max(word_freq.values()) if word_freq else 1
        repetition_penalty = min(max_freq / len(words), 0.3)
        
        clarity_score = sentence_length_score * (1.0 - repetition_penalty)
        
        return max(0.0, min(1.0, clarity_score))
    
    def get_scoring_stats(self) -> Dict[str, Any]:
        """Gets scoring statistics."""
        return {
            'weights': dict(self.weights),
            'task_type_weights': {k.value: v for k, v in self.task_type_weights.items()},
            'scoring_components': [
                'recency', 'content_quality', 'task_importance', 'metadata_richness'
            ]
        }



