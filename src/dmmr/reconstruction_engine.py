# -*- coding: utf-8 -*-
"""
Reconstruction Engine - Reconstructs AI answers based on activated memories.
Implements memory integration and context-aware answer generation.
"""
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
from .api_wrapper import APIWrapper


class ReconstructionEngine:
    """Reconstruction Engine - Integrates activated memory fragments into a coherent answer."""
    
    def __init__(self, api_wrapper: APIWrapper):
        self.api_wrapper = api_wrapper
        
        # Statistics
        self.reconstruction_count = 0
        self.total_memories_used = 0
        
        print("🔧 Reconstruction Engine initialized.")
    
    def reconstruct_answer(self, 
                          query: str,
                          retrieved_memories: List[Dict[str, Any]],
                          strategy_prompt: str = "",
                          code_only: bool = False,
                          generation_kwargs: Dict[str, Any] = None) -> Tuple[str, List[str], Dict[str, Any]]:
        """
        Reconstructs an answer based on retrieved memories.
        
        Args:
            query: The user's query.
            retrieved_memories: A list of retrieved memories.
            strategy_prompt: A prompt for the cognitive strategy.
            code_only: Whether to generate only code.
            generation_kwargs: Generation parameters.
            
        Returns:
            (Answer text, list of used memory IDs, reconstruction statistics)
        """
        print(f"🔧 Starting answer reconstruction...")
        print(f"   Query: {query[:50]}{'...' if len(query) > 50 else ''}")
        print(f"   Number of memories: {len(retrieved_memories)}")
        print(f"   Strategy: {strategy_prompt[:30]}{'...' if len(strategy_prompt) > 30 else ''}")
        
        # Parameter handling
        generation_kwargs = generation_kwargs or {}
        max_context_items = generation_kwargs.get('max_context_items', 5)
        max_context_chars = generation_kwargs.get('max_context_chars', 200)
        
        # Memory context processing
        processed_memories = self._process_memories(
            retrieved_memories, 
            max_context_items, 
            max_context_chars
        )
        
        memory_context = self._prepare_memory_context(processed_memories)
        used_memory_ids = [mem['id'] for mem in processed_memories if 'id' in mem]
        
        # Build reconstruction prompt
        full_prompt = self._build_reconstruction_prompt(
            query=query,
            memory_context=memory_context,
            strategy_prompt=strategy_prompt,
            code_only=code_only
        )
        
        # Generate answer
        try:
            answer = self.api_wrapper.generate_text(
                full_prompt, 
                **generation_kwargs
            )
        except Exception as e:
            print(f"❌ Generation failed: {e}")
            # Fallback: use a simpler prompt
            fallback_prompt = f"User question: {query}\n\nPlease provide a brief answer:"
            answer = self.api_wrapper.generate_text(fallback_prompt, max_tokens=500)
        
        # Post-processing
        if code_only:
            answer = self._clean_code_response(answer)
        else:
            answer = self._enhance_response(answer, strategy_prompt)
        
        # Statistics
        stats = self._calculate_reconstruction_stats(
            processed_memories, full_prompt, answer
        )
        
        # Update internal statistics
        self.reconstruction_count += 1
        self.total_memories_used += len(processed_memories)
        
        print(f"✅ Reconstruction complete (Memories used: {len(processed_memories)}, Answer length: {len(answer)})")
        
        return answer, used_memory_ids, stats
    
    def _process_memories(self, memories: List[Dict[str, Any]], 
                         max_items: int, max_chars: int) -> List[Dict[str, Any]]:
        """Processes and filters memories."""
        # Sort by significance
        sorted_memories = sorted(
            memories,
            key=lambda m: m.get('significance_score', 0.0),
            reverse=True
        )
        
        # Limit the number
        limited_memories = sorted_memories[:max_items]
        
        # Truncate content
        processed = []
        for memory in limited_memories:
            processed_memory = dict(memory)
            content = processed_memory.get('content', '')
            
            if len(content) > max_chars:
                processed_memory['content'] = content[:max_chars] + '...'
            
            processed.append(processed_memory)
        
        return processed
    
    def _prepare_memory_context(self, memories: List[Dict[str, Any]]) -> str:
        """Prepares the memory context string."""
        if not memories:
            return "(No relevant historical memories)"
        
        context_parts = []
        
        for i, memory in enumerate(memories, 1):
            content = memory.get('content', 'Unknown content')
            score = memory.get('significance_score', 0.0)
            source = memory.get('source', 'Memory')
            
            # Format timestamp information
            timestamp = memory.get('timestamp')
            time_str = self._format_timestamp(timestamp)
            
            # Build memory entry
            context_part = (
                f"{source}{i} ({time_str}, Significance:{score:.2f}): {content}"
            )
            context_parts.append(context_part)
        
        return "\n".join(context_parts)
    
    def _format_timestamp(self, timestamp: Any) -> str:
        """Formats the timestamp."""
        if not timestamp:
            return "Recently"
        
        try:
            if isinstance(timestamp, str):
                # Try to parse ISO format
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            elif isinstance(timestamp, datetime):
                dt = timestamp
            else:
                return "Recently"
            
            return dt.strftime('%m-%d %H:%M')
        except:
            return "Recently"
    
    def _build_reconstruction_prompt(self, query: str, memory_context: str,
                                   strategy_prompt: str, code_only: bool) -> str:
        """Builds the reconstruction prompt."""
        if code_only:
            return self._build_code_generation_prompt(query, memory_context)
        else:
            return self._build_conversational_prompt(query, memory_context, strategy_prompt)
    
    def _build_code_generation_prompt(self, query: str, memory_context: str) -> str:
        """Builds the code generation prompt."""
        return f"""
Based on the following technical information from historical memories, generate Python code to solve the user's problem.

=== Technical Memory Reference ===
{memory_context}

=== User Request ===
{query}

=== Code Implementation ===
Please provide complete, executable Python code with appropriate type hints and error handling:

```python
"""
    
    def _build_conversational_prompt(self, query: str, memory_context: str, strategy_prompt: str) -> str:
        """Builds the conversational answer prompt."""
        base_instruction = (
            "Please generate a helpful and accurate answer based on the historical memories and the user's current question."
            "Naturally integrate relevant historical information to maintain a coherent and personalized response."
        )
        
        if strategy_prompt:
            instruction = f"{strategy_prompt}\n\n{base_instruction}"
        else:
            instruction = base_instruction
        
        return f"""
{instruction}

=== Relevant Historical Memories ===
{memory_context}

=== User's Current Question ===
{query}

=== Your Answer ===
"""
    
    def _clean_code_response(self, response: str) -> str:
        """Cleans up the code response."""
        # Remove markdown code block markers
        if "```python" in response:
            start = response.find("```python") + 9
            end = response.find("```", start)
            if end != -1:
                response = response[start:end].strip()
        elif "```" in response:
            # Handle other code blocks
            start = response.find("```") + 3
            end = response.find("```", start)
            if end != -1:
                response = response[start:end].strip()
        
        return response
    
    def _enhance_response(self, response: str, strategy_prompt: str) -> str:
        """Enhances the response."""
        # Post-processing based on the strategy prompt
        if "empathy" in strategy_prompt or "emotional" in strategy_prompt.lower():
            response = self._add_empathy(response)
        elif "technical" in strategy_prompt or "technical" in strategy_prompt.lower():
            response = self._add_technical_formatting(response)
        
        return response
    
    def _add_empathy(self, response: str) -> str:
        """Adds empathetic elements."""
        # Simple empathy enhancement
        empathy_starters = [
            "I understand how you feel,",
            "That can certainly be frustrating,",
            "I can see how that would be difficult,"
        ]
        
        # Check if empathy is already expressed
        if not any(starter in response for starter in empathy_starters):
            # Add a simple empathetic prefix
            if len(response) > 0:
                response = f"I understand your situation. {response}"
        
        return response
    
    def _add_technical_formatting(self, response: str) -> str:
        """Adds technical formatting."""
        # Simple technical answer formatting
        if any(keyword in response for keyword in ['code', 'def', 'class', 'import']):
            if not response.startswith("Technical Answer:"):
                response = f"Technical Answer:\n\n{response}"
            
            if not response.endswith("If you have any other technical questions, feel free to ask."):
                response = f"{response}\n\nIf you have any other technical questions, feel free to ask."
        
        return response
    
    def _calculate_reconstruction_stats(self, memories: List[Dict], prompt: str, answer: str) -> Dict[str, Any]:
        """Calculates reconstruction statistics."""
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
        """Gets a summary of the reconstruction engine's activity."""
        return {
            'total_reconstructions': self.reconstruction_count,
            'total_memories_used': self.total_memories_used,
            'avg_memories_per_reconstruction': (
                self.total_memories_used / max(self.reconstruction_count, 1)
            )
        }



