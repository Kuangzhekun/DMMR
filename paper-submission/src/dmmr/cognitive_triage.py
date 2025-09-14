# -*- coding: utf-8 -*-
"""
认知分类器 - 基于双重加工理论的任务类型识别
实现系统1(直觉)和系统2(分析)的认知切换机制
"""
from typing import Dict, List, Optional
from .data_models import TaskType
from .api_wrapper import APIWrapper
from .config import get_config


class CognitiveTriage:
    """认知分类器，判断用户交互的意图类型"""
    
    def __init__(self, api_wrapper: APIWrapper = None):
        self.api_wrapper = api_wrapper
        self.config = get_config().triage
        
        # 关键词规则库
        self.keywords = {
            TaskType.TECHNICAL_CODING: [
                '代码', 'bug', '错误', 'python', '函数', 'class', '类', '算法',
                '报错', '调试', '性能', 'API', 'git', 'powershell', '库', '框架',
                'def', 'return', 'import', 'from', 'typing', 'List', 'str', 'int',
                'float', 'bool', 'Dict', 'Optional', '->', 'if', 'for', 'while',
                'docker', 'javascript', 'nodejs', 'react', 'vue', 'angular'
            ],
            TaskType.EMOTIONAL_COUNSELING: [
                '感觉', '难过', '冲突', '朋友', '家人', '同事', '经理', '伤心',
                '焦虑', '沮丧', '开心', '关系', '感情', '情绪', '觉得', '心理',
                '压力', '烦恼', '困扰', '担心', '害怕', '愤怒', '失落'
            ],
            TaskType.CREATIVE_WRITING: [
                '写作', '创作', '故事', '小说', '诗歌', '文章', '剧本', '创意',
                '灵感', '情节', '人物', '对话', '描述', '修辞', '风格'
            ],
            TaskType.EDUCATIONAL: [
                '学习', '教学', '课程', '知识', '概念', '理论', '原理', '解释',
                '定义', '例子', '练习', '作业', '考试', '复习', '总结'
            ]
        }
        
        # LLM分类缓存
        self.llm_cache = {}
        self.llm_fallback_count = 0
        
        # LLM分类提示模板
        self.llm_prompt_template = """
请将以下用户输入分类到以下任务类型之一：

1. TECHNICAL_CODING - 编程、调试、代码相关问题
2. EMOTIONAL_COUNSELING - 个人情感、人际关系、心理支持
3. CREATIVE_WRITING - 创意写作、故事创作、文学创作
4. EDUCATIONAL - 学习、教学、知识解释
5. GENERAL_QA - 一般性问题、信息查询

用户输入："{text}"

请只回答任务类型名称（如："TECHNICAL_CODING"），不需要解释。
""".strip()
        
        mode_desc = "关键词规则"
        if self.config.use_llm_fallback and self.api_wrapper:
            mode_desc += " + LLM回退"
        
        print(f"🧠 认知分类器初始化完成 ({mode_desc})")
    
    def classify(self, text: str) -> TaskType:
        """
        分类用户输入的任务类型
        
        Args:
            text: 用户输入文本
            
        Returns:
            识别的任务类型
        """
        text_lower = text.lower()
        
        # 1. 关键词规则分类
        scores = self._calculate_keyword_scores(text_lower)
        
        # 2. 计算置信度
        max_score = max(scores.values()) if scores.values() else 0
        tied_types = [task_type for task_type, score in scores.items() if score == max_score]
        confidence = self._calculate_confidence(max_score, text_lower)
        
        # 3. 判断是否需要LLM回退
        if self._should_use_llm_fallback(max_score, len(tied_types), confidence, len(text)):
            llm_result = self._llm_classify(text)
            if llm_result:
                print(f"  [认知分类] 关键词分类置信度低，LLM判别: {llm_result.value}")
                return llm_result
        
        # 4. 返回关键词分类结果
        best_task_type = tied_types[0] if tied_types and max_score > 0 else TaskType.GENERAL_QA
        print(f"  [认知分类] {best_task_type.value} (分数: {max_score}, 置信度: {confidence:.2f})")
        return best_task_type
    
    def _calculate_keyword_scores(self, text_lower: str) -> Dict[TaskType, int]:
        """计算关键词匹配分数"""
        scores = {task_type: 0 for task_type in self.keywords}
        
        for task_type, keywords in self.keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    scores[task_type] += 1
        
        return scores
    
    def _calculate_confidence(self, max_score: int, text_lower: str) -> float:
        """计算分类置信度"""
        total_words = len(text_lower.split())
        if total_words == 0:
            return 0.0
        
        # 基础置信度：匹配关键词数与总词数的比例
        base_confidence = max_score / max(total_words, 1)
        
        # 调整因子
        adjustment = 0.0
        
        # 文本长度调整
        if total_words > 20:  # 长文本
            adjustment += 0.1
        elif total_words < 5:  # 短文本
            adjustment -= 0.1
        
        # 特定模式调整
        if any(pattern in text_lower for pattern in ['如何', '怎么', '为什么']):
            adjustment += 0.1
        
        return min(base_confidence + adjustment, 1.0)
    
    def _should_use_llm_fallback(self, max_score: int, tied_count: int, confidence: float, text_length: int) -> bool:
        """判断是否需要LLM回退"""
        if not self.config.use_llm_fallback or not self.api_wrapper:
            return False
        
        # LLM回退触发条件
        conditions = [
            max_score == 0,  # 无关键词匹配
            tied_count > 1 and max_score > 0,  # 多类型打平
            confidence < self.config.confidence_threshold,  # 置信度过低
            text_length > 100 and max_score < 3  # 长文本但匹配少
        ]
        
        return any(conditions)
    
    def _llm_classify(self, text: str) -> Optional[TaskType]:
        """使用LLM进行分类"""
        # 检查缓存
        cache_key = text[:200]
        if cache_key in self.llm_cache:
            return self.llm_cache[cache_key]
        
        try:
            # 调用LLM
            prompt = self.llm_prompt_template.format(text=text[:500])
            response = self.api_wrapper.generate_text(
                prompt,
                temperature=0.0,
                max_tokens=50
            )
            
            # 解析响应
            result = self._parse_llm_response(response)
            
            if result:
                # 更新缓存
                self._update_llm_cache(cache_key, result)
                self.llm_fallback_count += 1
                return result
                
        except Exception as e:
            print(f"  [认知分类] LLM分类失败: {e}")
        
        return None
    
    def _parse_llm_response(self, response: str) -> Optional[TaskType]:
        """解析LLM响应"""
        response_clean = response.strip().upper()
        
        # 任务类型映射
        type_mapping = {
            'TECHNICAL_CODING': TaskType.TECHNICAL_CODING,
            'EMOTIONAL_COUNSELING': TaskType.EMOTIONAL_COUNSELING,  
            'CREATIVE_WRITING': TaskType.CREATIVE_WRITING,
            'EDUCATIONAL': TaskType.EDUCATIONAL,
            'GENERAL_QA': TaskType.GENERAL_QA
        }
        
        # 精确匹配
        for type_name, task_type in type_mapping.items():
            if type_name in response_clean:
                return task_type
        
        # 模糊匹配
        if any(word in response_clean for word in ['TECHNICAL', 'CODING', 'PROGRAMMING']):
            return TaskType.TECHNICAL_CODING
        elif any(word in response_clean for word in ['EMOTIONAL', 'COUNSELING', 'FEELING']):
            return TaskType.EMOTIONAL_COUNSELING
        elif any(word in response_clean for word in ['CREATIVE', 'WRITING', 'STORY']):
            return TaskType.CREATIVE_WRITING
        elif any(word in response_clean for word in ['EDUCATIONAL', 'LEARNING', 'TEACHING']):
            return TaskType.EDUCATIONAL
        
        return TaskType.GENERAL_QA
    
    def _update_llm_cache(self, key: str, value: TaskType):
        """更新LLM缓存"""
        # 简单的LRU缓存
        max_cache_size = getattr(self.config, 'cache_max_size', 100)
        
        if len(self.llm_cache) >= max_cache_size:
            # 删除最旧的条目
            oldest_key = next(iter(self.llm_cache))
            del self.llm_cache[oldest_key]
        
        self.llm_cache[key] = value
    
    def get_classification_stats(self) -> Dict:
        """获取分类器统计信息"""
        return {
            'use_llm_fallback': self.config.use_llm_fallback,
            'api_available': self.api_wrapper is not None,
            'llm_fallback_count': self.llm_fallback_count,
            'cache_size': len(self.llm_cache),
            'confidence_threshold': self.config.confidence_threshold
        }

