#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DMMR 基本使用示例
演示如何创建和使用DMMR智能体进行对话
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.dmmr import DMMRAgent, get_config, validate_config


def main():
    """基本使用示例"""
    print("🚀 DMMR 基本使用示例")
    print("=" * 50)
    
    # 1. 验证配置
    print("1. 验证系统配置...")
    if not validate_config():
        print("❌ 配置验证失败！请检查环境变量设置。")
        print("   请参考 .env.example 文件配置环境变量")
        return
    
    config = get_config()
    print(f"✅ 配置验证成功")
    print(f"   模型: {config.api.model_name}")
    print(f"   API Key: {'已配置' if config.api.api_key else '未配置'}")
    
    # 2. 创建DMMR智能体
    print("\n2. 创建DMMR智能体...")
    try:
        agent = DMMRAgent(
            user_id="example_user",
            use_real_backends=False  # 使用内存后端进行演示
        )
        print("✅ 智能体创建成功")
    except Exception as e:
        print(f"❌ 智能体创建失败: {e}")
        return
    
    # 3. 演示对话交互
    print("\n3. 开始对话演示...")
    
    # 示例对话序列
    conversations = [
        "你好，我在学习Python编程，遇到了一个bug",
        "我的代码报错：NameError: name 'pd' is not defined",
        "好的，我已经导入了pandas，还有其他需要注意的吗？",
        "谢谢你的帮助！现在我想了解一些机器学习的基础概念"
    ]
    
    for i, user_input in enumerate(conversations, 1):
        print(f"\n--- 对话 {i} ---")
        print(f"用户: {user_input}")
        
        try:
            # 处理用户输入
            ai_response, metrics = agent.process_input(user_input)
            
            print(f"AI: {ai_response}")
            print(f"📊 指标: 延迟={metrics.latency_sec:.2f}s, 记忆命中={metrics.memory_hits}, Token使用={metrics.token_usage}")
            
        except Exception as e:
            print(f"❌ 处理失败: {e}")
            continue
    
    # 4. 显示智能体状态
    print("\n4. 智能体状态:")
    status = agent.get_agent_status()
    print(f"   总查询数: {status['session_stats']['total_queries']}")
    print(f"   创建记忆数: {status['session_stats']['total_memories_created']}")
    print(f"   检索记忆数: {status['session_stats']['total_memories_retrieved']}")
    print(f"   平均响应时间: {status['session_stats']['avg_response_time']:.2f}s")
    
    # 5. 记忆统计
    print("\n5. 记忆系统统计:")
    memory_stats = agent.get_memory_stats()
    print(f"   记忆创建总数: {memory_stats['total_memories_created']}")
    print(f"   记忆检索总数: {memory_stats['total_memories_retrieved']}")
    print(f"   激活事件数: {memory_stats['activation_events']}")
    
    print("\n✅ 基本使用示例完成!")


if __name__ == "__main__":
    main()

