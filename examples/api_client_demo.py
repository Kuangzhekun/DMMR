#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DMMR API客户端演示
演示如何通过HTTP API与DMMR服务交互
"""
import requests
import json
import time
from typing import Dict, Any


class DMMRAPIClient:
    """DMMR API客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def health_check(self) -> Dict[str, Any]:
        """检查服务健康状态"""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def chat(self, message: str, user_id: str = "demo_user", 
             metadata: Dict[str, Any] = None, use_real_backends: bool = False) -> Dict[str, Any]:
        """发送聊天消息"""
        payload = {
            "user_id": user_id,
            "message": message,
            "metadata": metadata or {},
            "use_real_backends": use_real_backends
        }
        
        response = self.session.post(f"{self.base_url}/v1/chat", json=payload)
        response.raise_for_status()
        return response.json()
    
    def reset_session(self, user_id: str = "demo_user", clear_memories: bool = False) -> Dict[str, Any]:
        """重置用户会话"""
        payload = {
            "user_id": user_id,
            "clear_memories": clear_memories
        }
        
        response = self.session.post(f"{self.base_url}/v1/reset", json=payload)
        response.raise_for_status()
        return response.json()
    
    def get_user_status(self, user_id: str = "demo_user", use_real_backends: bool = False) -> Dict[str, Any]:
        """获取用户智能体状态"""
        params = {"use_real_backends": use_real_backends}
        response = self.session.get(f"{self.base_url}/v1/status/{user_id}", params=params)
        response.raise_for_status()
        return response.json()
    
    def get_config(self) -> Dict[str, Any]:
        """获取系统配置"""
        response = self.session.get(f"{self.base_url}/v1/config")
        response.raise_for_status()
        return response.json()


def demo_conversation(client: DMMRAPIClient):
    """演示对话交互"""
    print("🎯 开始对话演示...")
    
    user_id = "api_demo_user"
    
    # 重置会话
    print("🔄 重置会话...")
    reset_result = client.reset_session(user_id, clear_memories=True)
    print(f"   状态: {reset_result['status']}")
    
    # 对话序列
    conversations = [
        "你好！我是一名Python开发者，想了解如何优化代码性能",
        "我的程序处理大量数据时很慢，有什么建议吗？",
        "pandas DataFrame操作有什么优化技巧？",
        "谢谢你的建议！现在我想转换话题，聊聊机器学习"
    ]
    
    for i, message in enumerate(conversations, 1):
        print(f"\n--- 对话轮次 {i} ---")
        print(f"👤 用户: {message}")
        
        try:
            # 发送消息
            start_time = time.time()
            response = client.chat(
                message=message,
                user_id=user_id,
                metadata={"demo": True, "round": i}
            )
            end_time = time.time()
            
            # 显示回复
            print(f"🤖 DMMR: {response['ai_response']}")
            print(f"📊 任务类型: {response['task_type']}")
            print(f"⏱️  API延迟: {end_time - start_time:.2f}s")
            print(f"📈 指标: {response['metrics']}")
            
        except requests.exceptions.RequestException as e:
            print(f"❌ API调用失败: {e}")
            continue
    
    # 查看用户状态
    print(f"\n📋 查看用户状态...")
    try:
        status = client.get_user_status(user_id)
        if status['agent_exists']:
            print(f"   总查询数: {status['agent_status']['session_stats']['total_queries']}")
            print(f"   创建记忆数: {status['memory_stats']['total_memories_created']}")
            print(f"   检索记忆数: {status['memory_stats']['total_memories_retrieved']}")
        else:
            print("   智能体不存在")
    except requests.exceptions.RequestException as e:
        print(f"❌ 获取状态失败: {e}")


def demo_system_info(client: DMMRAPIClient):
    """演示系统信息查询"""
    print("\n🔧 系统信息演示...")
    
    try:
        # 健康检查
        print("1. 健康检查:")
        health = client.health_check()
        print(f"   状态: {health['status']}")
        print(f"   版本: {health['version']}")
        print(f"   活跃智能体: {health['active_agents']}")
        print(f"   运行时间: {health['uptime_seconds']:.1f}秒")
        
        # 系统配置
        print("\n2. 系统配置:")
        config = client.get_config()
        print(f"   模型: {config['api_config']['model_name']}")
        print(f"   向量数据库: {config['database_config']['vector_backend']} ({'真实' if config['database_config']['use_real_vector_db'] else '内存'})")
        print(f"   图数据库: {config['database_config']['graph_backend']} ({'真实' if config['database_config']['use_real_graph_db'] else '内存'})")
        print(f"   激活阈值: {config['activation_config']['activation_threshold']}")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 系统信息获取失败: {e}")


def main():
    """主函数"""
    print("🌐 DMMR API客户端演示")
    print("=" * 50)
    
    # 创建API客户端
    client = DMMRAPIClient("http://localhost:8000")
    
    try:
        # 测试连接
        print("🔗 测试API连接...")
        health = client.health_check()
        print(f"✅ 连接成功! 服务状态: {health['status']}")
        
        # 演示系统信息
        demo_system_info(client)
        
        # 演示对话交互
        demo_conversation(client)
        
        print("\n✅ API演示完成!")
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到DMMR API服务")
        print("   请确保API服务器正在运行:")
        print("   python api/server.py")
        print("   或者:")
        print("   docker-compose up")
        
    except Exception as e:
        print(f"❌ 演示过程中发生错误: {e}")


if __name__ == "__main__":
    main()



