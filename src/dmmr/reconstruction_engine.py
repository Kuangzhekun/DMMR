# -*- coding: utf-8 -*-
"""
重构引擎 - 基于激活记忆重构生成AI回答
实现记忆整合和上下文感知的回答生成
"""
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
from .api_wrapper import APIWrapper


class ReconstructionEngine:
    """重构引擎 - 将激活的记忆片段整合成连贯回答"""
    
    def __init__(self, api_wrapper: APIWrapper):
        self.api_wrapper = api_wrapper
        
        # 统计信息
        self.reconstruction_count = 0
        self.total_memories_used = 0
        
        print("🔧 重构引擎初始化完成")
    
    def reconstruct_answer(self, 
                          query: str,
                          retrieved_memories: List[Dict[str, Any]],
                          strategy_prompt: str = "",
                          code_only: bool = False,
                          generation_kwargs: Dict[str, Any] = None) -> Tuple[str, List[str], Dict[str, Any]]:
        """
        基于检索记忆重构答案
        
        Args:
            query: 用户查询
            retrieved_memories: 检索到的记忆列表
            strategy_prompt: 认知策略提示
            code_only: 是否仅生成代码
            generation_kwargs: 生成参数
            
        Returns:
            (回答文本, 使用的记忆ID列表, 重构统计)
        """
        print(f"🔧 开始重构回答...")
        print(f"   查询: {query[:50]}{'...' if len(query) > 50 else ''}")
        print(f"   记忆数量: {len(retrieved_memories)}")
        print(f"   策略: {strategy_prompt[:30]}{'...' if len(strategy_prompt) > 30 else ''}")
        
        # 参数处理
        generation_kwargs = generation_kwargs or {}
        max_context_items = generation_kwargs.get('max_context_items', 5)
        max_context_chars = generation_kwargs.get('max_context_chars', 200)
        
        # 记忆上下文处理
        processed_memories = self._process_memories(
            retrieved_memories, 
            max_context_items, 
            max_context_chars
        )
        
        memory_context = self._prepare_memory_context(processed_memories)
        used_memory_ids = [mem['id'] for mem in processed_memories if 'id' in mem]
        
        # 构建重构提示
        full_prompt = self._build_reconstruction_prompt(
            query=query,
            memory_context=memory_context,
            strategy_prompt=strategy_prompt,
            code_only=code_only
        )
        
        # 生成回答
        try:
            answer = self.api_wrapper.generate_text(
                full_prompt, 
                **generation_kwargs
            )
        except Exception as e:
            print(f"❌ 生成失败: {e}")
            # 降级处理：使用更简单的提示
            fallback_prompt = f"用户问题：{query}\n\n请简要回答："
            answer = self.api_wrapper.generate_text(fallback_prompt, max_tokens=500)
        
        # 后处理
        if code_only:
            answer = self._clean_code_response(answer)
        else:
            answer = self._enhance_response(answer, strategy_prompt)
        
        # 统计信息
        stats = self._calculate_reconstruction_stats(
            processed_memories, full_prompt, answer
        )
        
        # 更新内部统计
        self.reconstruction_count += 1
        self.total_memories_used += len(processed_memories)
        
        print(f"✅ 重构完成 (使用记忆: {len(processed_memories)}, 回答长度: {len(answer)})")
        
        return answer, used_memory_ids, stats
    
    def _process_memories(self, memories: List[Dict[str, Any]], 
                         max_items: int, max_chars: int) -> List[Dict[str, Any]]:
        """处理和过滤记忆"""
        # 按重要性排序
        sorted_memories = sorted(
            memories,
            key=lambda m: m.get('significance_score', 0.0),
            reverse=True
        )
        
        # 限制数量
        limited_memories = sorted_memories[:max_items]
        
        # 截断内容
        processed = []
        for memory in limited_memories:
            processed_memory = dict(memory)
            content = processed_memory.get('content', '')
            
            if len(content) > max_chars:
                processed_memory['content'] = content[:max_chars] + '...'
            
            processed.append(processed_memory)
        
        return processed
    
    def _prepare_memory_context(self, memories: List[Dict[str, Any]]) -> str:
        """准备记忆上下文字符串"""
        if not memories:
            return "（没有相关的历史记忆）"
        
        context_parts = []
        
        for i, memory in enumerate(memories, 1):
            content = memory.get('content', '未知内容')
            score = memory.get('significance_score', 0.0)
            source = memory.get('source', '记忆')
            
            # 格式化时间信息
            timestamp = memory.get('timestamp')
            time_str = self._format_timestamp(timestamp)
            
            # 构建记忆条目
            context_part = (
                f"{source}{i} ({time_str}, 重要性:{score:.2f}): {content}"
            )
            context_parts.append(context_part)
        
        return "\n".join(context_parts)
    
    def _format_timestamp(self, timestamp: Any) -> str:
        """格式化时间戳"""
        if not timestamp:
            return "最近"
        
        try:
            if isinstance(timestamp, str):
                # 尝试解析ISO格式
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            elif isinstance(timestamp, datetime):
                dt = timestamp
            else:
                return "最近"
            
            return dt.strftime('%m-%d %H:%M')
        except:
            return "最近"
    
    def _build_reconstruction_prompt(self, query: str, memory_context: str,
                                   strategy_prompt: str, code_only: bool) -> str:
        """构建重构提示"""
        if code_only:
            return self._build_code_generation_prompt(query, memory_context)
        else:
            return self._build_conversational_prompt(query, memory_context, strategy_prompt)
    
    def _build_code_generation_prompt(self, query: str, memory_context: str) -> str:
        """构建代码生成提示"""
        return f"""
基于以下历史记忆中的技术信息，生成解决用户问题的Python代码。

=== 技术记忆参考 ===
{memory_context}

=== 用户需求 ===
{query}

=== 代码实现 ===
请提供完整、可执行的Python代码，包含适当的类型注解和错误处理：

```python
"""
    
    def _build_conversational_prompt(self, query: str, memory_context: str, strategy_prompt: str) -> str:
        """构建对话式回答提示"""
        base_instruction = (
            "请基于以下历史记忆和用户当前的问题，生成一个有帮助、准确的回答。"
            "自然地融入相关的历史信息，保持回答的连贯性和个性化。"
        )
        
        if strategy_prompt:
            instruction = f"{strategy_prompt}\n\n{base_instruction}"
        else:
            instruction = base_instruction
        
        return f"""
{instruction}

=== 相关历史记忆 ===
{memory_context}

=== 用户当前问题 ===
{query}

=== 您的回答 ===
"""
    
    def _clean_code_response(self, response: str) -> str:
        """清理代码响应"""
        # 移除markdown代码块标记
        if "```python" in response:
            start = response.find("```python") + 9
            end = response.find("```", start)
            if end != -1:
                response = response[start:end].strip()
        elif "```" in response:
            # 处理其他代码块
            start = response.find("```") + 3
            end = response.find("```", start)
            if end != -1:
                response = response[start:end].strip()
        
        return response
    
    def _enhance_response(self, response: str, strategy_prompt: str) -> str:
        """增强回答"""
        # 基于策略提示进行后处理
        if "共情" in strategy_prompt or "emotional" in strategy_prompt.lower():
            response = self._add_empathy(response)
        elif "技术" in strategy_prompt or "technical" in strategy_prompt.lower():
            response = self._add_technical_formatting(response)
        
        return response
    
    def _add_empathy(self, response: str) -> str:
        """添加共情元素"""
        # 简单的共情增强
        empathy_starters = [
            "我理解您的感受，",
            "这确实可能让人感到困扰，",
            "我能体会到您的处境，"
        ]
        
        # 检查是否已经有共情表达
        if not any(starter in response for starter in empathy_starters):
            # 简单添加共情前缀
            if len(response) > 0:
                response = f"我理解您的情况。{response}"
        
        return response
    
    def _add_technical_formatting(self, response: str) -> str:
        """添加技术格式化"""
        # 简单的技术回答格式化
        if any(keyword in response for keyword in ['代码', 'def', 'class', 'import']):
            if not response.startswith("技术解答："):
                response = f"技术解答：\n\n{response}"
            
            if not response.endswith("如有其他技术问题，请随时询问。"):
                response = f"{response}\n\n如有其他技术问题，请随时询问。"
        
        return response
    
    def _calculate_reconstruction_stats(self, memories: List[Dict], prompt: str, answer: str) -> Dict[str, Any]:
        """计算重构统计信息"""
        return {
            'memories_used': len(memories),
            'prompt_length': len(prompt),
            'answer_length': len(answer),
            'avg_memory_score': (
                sum(m.get('significance_score', 0.0) for m in memories) / len(memories)
                if memories else 0.0
            ),
            'reconstruction_timestamp': datetime.now().isoformat()
        }
    
    def get_reconstruction_summary(self) -> Dict[str, Any]:
        """获取重构引擎运行摘要"""
        return {
            'total_reconstructions': self.reconstruction_count,
            'total_memories_used': self.total_memories_used,
            'avg_memories_per_reconstruction': (
                self.total_memories_used / max(self.reconstruction_count, 1)
            )
        }


