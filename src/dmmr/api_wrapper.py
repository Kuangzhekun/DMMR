# -*- coding: utf-8 -*-
"""
API包装器 - 封装LLM服务交互
支持多种API提供商（OpenAI兼容接口）
"""
import os
import uuid
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from openai import OpenAI

from .data_models import MemoryChunk, TaskType
from .config import get_config


class APIWrapper:
    """通用API包装器，支持OpenAI兼容接口"""
    
    def __init__(self):
        """初始化API包装器"""
        self.config = get_config().api
        
        # 验证API配置
        if not self.config.api_key:
            raise ValueError("API密钥未设置，请配置ARK_API_KEY或OPENAI_API_KEY环境变量")
        
        # 初始化客户端
        self.client = OpenAI(
            base_url=self.config.base_url,
            api_key=self.config.api_key,
            timeout=self.config.timeout
        )
        
        # 对话管理
        self.conversation_history = {}
        self.current_conversation_id = "dmmr_session"
        
        # Token统计
        self._usage_cumulative = {}
        self._usage_last = None
        
        print(f"APIWrapper 初始化完成 (模型: {self.config.model_name})")
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """
        生成文本响应
        
        Args:
            prompt: 输入提示
            **kwargs: 其他参数
            
        Returns:
            生成的文本
        """
        # 参数配置
        max_tokens = kwargs.get('max_tokens', self.config.default_max_tokens)
        temperature = kwargs.get('temperature', self.config.default_temperature)
        conversation_id = kwargs.get('conversation_id', self.current_conversation_id)
        system_prompt = kwargs.get('system_prompt', 
            "你是一个智能AI助手，可以回答各种问题，帮助用户解决问题。请用中文回复。")
        
        # 模型选择
        role = kwargs.get('role')
        model_name = self._get_model_for_role(role)
        
        # 管理对话历史
        self._init_conversation(conversation_id, system_prompt)
        
        # 添加用户消息
        self.conversation_history[conversation_id].append({
            "role": "user", 
            "content": prompt
        })
        
        # 管理对话长度
        self._manage_conversation_length(conversation_id)
        
        try:
            # API调用
            response = self.client.chat.completions.create(
                model=model_name,
                messages=self.conversation_history[conversation_id],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            ai_response = response.choices[0].message.content
            
            # 记录token使用量
            self._record_usage(response.usage)
            
            # 保存AI回复
            self.conversation_history[conversation_id].append({
                "role": "assistant", 
                "content": ai_response
            })
            
            return ai_response
            
        except Exception as e:
            error_msg = f"API调用失败: {str(e)}"
            print(f"❌ {error_msg}")
            raise RuntimeError(error_msg)
    
    def _get_model_for_role(self, role: Optional[str]) -> str:
        """根据角色获取对应模型"""
        if not role:
            return self.config.model_name
            
        role_models = {
            'agent': self.config.model_agent,
            'user_sim': self.config.model_user_sim,
            'critic': self.config.model_critic
        }
        
        return role_models.get(role) or self.config.model_name
    
    def _init_conversation(self, conversation_id: str, system_prompt: str):
        """初始化对话"""
        if conversation_id not in self.conversation_history:
            self.conversation_history[conversation_id] = [
                {"role": "system", "content": system_prompt}
            ]
    
    def _manage_conversation_length(self, conversation_id: str):
        """管理对话长度，防止token超限"""
        messages = self.conversation_history[conversation_id]
        
        # 保留系统消息和最近的对话
        if len(messages) > 20:
            system_message = messages[0]
            recent_messages = messages[-15:]  # 保留最近15条
            self.conversation_history[conversation_id] = [system_message] + recent_messages
    
    def _record_usage(self, usage):
        """记录token使用量"""
        if not usage:
            return
            
        usage_dict = {
            'prompt_tokens': getattr(usage, 'prompt_tokens', 0),
            'completion_tokens': getattr(usage, 'completion_tokens', 0),
            'total_tokens': getattr(usage, 'total_tokens', 0)
        }
        
        self._usage_last = usage_dict
        
        # 累计统计
        conv_id = self.current_conversation_id
        if conv_id not in self._usage_cumulative:
            self._usage_cumulative[conv_id] = {
                'prompt_tokens': 0,
                'completion_tokens': 0, 
                'total_tokens': 0
            }
        
        for key, value in usage_dict.items():
            if isinstance(value, int):
                self._usage_cumulative[conv_id][key] += value
    
    def process_input_to_chunk(self, user_input: str, metadata: Dict[str, Any] = None) -> MemoryChunk:
        """将用户输入处理为记忆块"""
        metadata = metadata or {}
        
        # 提取任务类型
        task_type = metadata.get('task_type', TaskType.GENERAL_QA)
        if isinstance(task_type, str):
            try:
                task_type = TaskType(task_type)
            except ValueError:
                task_type = TaskType.GENERAL_QA
        
        chunk = MemoryChunk(
            id=str(uuid.uuid4()),
            content=user_input,
            task_type=task_type,
            metadata=metadata,
            user_id=metadata.get('user_id', 'default')
        )
        
        return chunk
    
    def extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        keywords = []
        
        # 简单的关键词匹配
        keyword_patterns = {
            "技术": ["代码", "编程", "算法", "数据库", "Python", "API", "框架", "架构", "bug", "错误"],
            "情感": ["感觉", "焦虑", "担心", "压力", "困难", "帮助", "支持", "朋友"],
            "项目": ["项目", "计划", "规划", "设计", "需求", "方案", "任务"]
        }
        
        text_lower = text.lower()
        for category, patterns in keyword_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    keywords.append(pattern)
        
        return list(set(keywords))  # 去重
    
    def new_conversation(self, conversation_id: str = None, system_prompt: str = None):
        """开始新对话"""
        if conversation_id is None:
            conversation_id = f"dmmr_chat_{int(time.time())}"
        
        self.current_conversation_id = conversation_id
        
        # 清除旧的对话历史
        if conversation_id in self.conversation_history:
            del self.conversation_history[conversation_id]
        
        print(f"🔄 开始新对话: {conversation_id}")
        return conversation_id
    
    def clear_history(self, conversation_id: str = None):
        """清除对话历史"""
        if conversation_id is None:
            conversation_id = self.current_conversation_id
        
        if conversation_id in self.conversation_history:
            del self.conversation_history[conversation_id]
        
        if conversation_id in self._usage_cumulative:
            del self._usage_cumulative[conversation_id]
        
        self._usage_last = None
        print(f"🗑️ 已清除对话历史: {conversation_id}")
    
    def get_api_status(self) -> Dict[str, Any]:
        """获取API状态"""
        return {
            "api_available": self.client is not None,
            "model": self.config.model_name,
            "base_url": self.config.base_url,
            "conversations_count": len(self.conversation_history),
            "current_conversation": self.current_conversation_id,
            "api_key_configured": bool(self.config.api_key)
        }
    
    def get_last_usage(self) -> Optional[Dict[str, int]]:
        """获取最后一次API调用的token使用量"""
        return self._usage_last
    
    def get_cumulative_usage(self, conversation_id: str = None) -> Optional[Dict[str, int]]:
        """获取累计token使用量"""
        conv_id = conversation_id or self.current_conversation_id
        return self._usage_cumulative.get(conv_id)
    
    def get_and_reset_last_usage(self) -> Optional[Dict[str, int]]:
        """获取并重置最后一次使用量"""
        usage = self._usage_last
        self._usage_last = None
        return usage


