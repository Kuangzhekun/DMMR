# -*- coding: utf-8 -*-
"""
DMMR API服务器 - 提供RESTful接口
基于FastAPI实现的高性能API服务
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from src.dmmr import DMMRAgent, get_config, validate_config


# ==================== 请求/响应模型 ====================

class ChatRequest(BaseModel):
    """聊天请求模型"""
    user_id: Optional[str] = "default_user"
    message: str
    metadata: Optional[Dict[str, Any]] = None
    use_real_backends: Optional[bool] = False


class ChatResponse(BaseModel):
    """聊天响应模型"""
    user_id: str
    message: str
    ai_response: str
    task_type: str
    metrics: Dict[str, Any]
    timestamp: str


class ResetRequest(BaseModel):
    """重置请求模型"""
    user_id: Optional[str] = "default_user"
    clear_memories: bool = False


class StatusResponse(BaseModel):
    """状态响应模型"""
    status: str
    version: str
    config_valid: bool
    active_agents: int
    uptime_seconds: float


# ==================== FastAPI应用 ====================

app = FastAPI(
    title="DMMR API",
    description="Dynamic Multi-Modal Memory Retrieval System API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应限制域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 全局状态 ====================

# 智能体实例缓存（按用户ID）
agents_cache: Dict[str, DMMRAgent] = {}
server_start_time = datetime.now()


# ==================== 辅助函数 ====================

def get_or_create_agent(user_id: str, use_real_backends: bool = False) -> DMMRAgent:
    """获取或创建智能体实例"""
    agent_key = f"{user_id}_{use_real_backends}"
    
    if agent_key not in agents_cache:
        print(f"🔄 创建新的DMMR智能体实例 (用户: {user_id}, 真实后端: {use_real_backends})")
        agents_cache[agent_key] = DMMRAgent(
            user_id=user_id,
            use_real_backends=use_real_backends
        )
    
    return agents_cache[agent_key]


def clear_agent_cache(user_id: str = None):
    """清除智能体缓存"""
    if user_id:
        # 清除特定用户的智能体
        keys_to_remove = [key for key in agents_cache.keys() if key.startswith(f"{user_id}_")]
        for key in keys_to_remove:
            del agents_cache[key]
        print(f"🗑️ 已清除用户 {user_id} 的智能体缓存")
    else:
        # 清除所有智能体
        agents_cache.clear()
        print("🗑️ 已清除所有智能体缓存")


# ==================== API端点 ====================

@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    print("🚀 DMMR API服务器启动中...")
    
    # 验证配置
    if not validate_config():
        print("❌ 配置验证失败")
        raise RuntimeError("系统配置无效，服务器无法启动")
    
    config = get_config()
    print(f"✅ 配置验证通过")
    print(f"   模型: {config.api.model_name}")
    print(f"   向量DB: {'真实' if config.database.use_real_vector_db else '内存'}")
    print(f"   图DB: {'真实' if config.database.use_real_graph_db else '内存'}")
    
    print("✅ DMMR API服务器启动完成")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    print("🛑 DMMR API服务器关闭中...")
    clear_agent_cache()
    print("✅ DMMR API服务器已关闭")


@app.get("/health", response_model=StatusResponse)
async def health_check():
    """健康检查端点"""
    uptime = (datetime.now() - server_start_time).total_seconds()
    
    return StatusResponse(
        status="healthy",
        version="1.0.0",
        config_valid=validate_config(),
        active_agents=len(agents_cache),
        uptime_seconds=uptime
    )


@app.post("/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """聊天对话端点"""
    try:
        print(f"📨 收到聊天请求 (用户: {request.user_id}, 消息长度: {len(request.message)})")
        
        # 验证输入
        if not request.message.strip():
            raise HTTPException(status_code=400, detail="消息内容不能为空")
        
        # 获取智能体实例
        agent = get_or_create_agent(request.user_id, request.use_real_backends or False)
        
        # 处理用户输入
        ai_response, metrics = agent.process_input(
            user_input=request.message,
            metadata=request.metadata
        )
        
        # 构建响应
        response = ChatResponse(
            user_id=request.user_id,
            message=request.message,
            ai_response=ai_response,
            task_type=request.metadata.get('task_type', 'unknown') if request.metadata else 'unknown',
            metrics={
                'latency_sec': metrics.latency_sec,
                'token_usage': metrics.token_usage,
                'memory_hits': metrics.memory_hits,
                'activation_nodes': metrics.activation_nodes
            },
            timestamp=datetime.now().isoformat()
        )
        
        print(f"✅ 处理完成 (响应长度: {len(ai_response)}, 延迟: {metrics.latency_sec:.2f}s)")
        return response
        
    except Exception as e:
        print(f"❌ 聊天处理失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@app.post("/v1/reset")
async def reset_session(request: ResetRequest):
    """重置会话端点"""
    try:
        print(f"🔄 重置会话请求 (用户: {request.user_id}, 清除记忆: {request.clear_memories})")
        
        if request.clear_memories:
            # 清除智能体缓存
            clear_agent_cache(request.user_id)
            message = "会话和记忆已完全重置"
        else:
            # 仅重置会话状态
            agent_keys = [key for key in agents_cache.keys() if key.startswith(f"{request.user_id}_")]
            for key in agent_keys:
                agents_cache[key].reset_session()
            message = "会话状态已重置，记忆保留"
        
        return {
            "status": "success",
            "user_id": request.user_id,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ 重置会话失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"重置失败: {str(e)}")


@app.get("/v1/status/{user_id}")
async def get_user_status(user_id: str, use_real_backends: bool = False):
    """获取用户智能体状态"""
    try:
        agent_key = f"{user_id}_{use_real_backends}"
        
        if agent_key not in agents_cache:
            return {
                "user_id": user_id,
                "agent_exists": False,
                "message": "智能体实例不存在"
            }
        
        agent = agents_cache[agent_key]
        status = agent.get_agent_status()
        memory_stats = agent.get_memory_stats()
        
        return {
            "user_id": user_id,
            "agent_exists": True,
            "agent_status": status,
            "memory_stats": memory_stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ 获取状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")


@app.get("/v1/config")
async def get_system_config():
    """获取系统配置信息"""
    try:
        config = get_config()
        
        return {
            "api_config": {
                "model_name": config.api.model_name,
                "base_url": config.api.base_url,
                "has_api_key": bool(config.api.api_key),
                "temperature": config.api.default_temperature,
                "max_tokens": config.api.default_max_tokens
            },
            "database_config": {
                "use_real_vector_db": config.database.use_real_vector_db,
                "vector_backend": config.database.vector_backend,
                "use_real_graph_db": config.database.use_real_graph_db,
                "graph_backend": config.database.graph_backend
            },
            "activation_config": {
                "decay_factor": config.activation.decay_factor,
                "activation_threshold": config.activation.activation_threshold,
                "max_depth": config.activation.max_depth
            },
            "experiment_config": {
                "context_budget_items": config.experiment.context_budget_items,
                "context_budget_chars": config.experiment.context_budget_chars
            }
        }
        
    except Exception as e:
        print(f"❌ 获取配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")


@app.delete("/v1/cache")
async def clear_cache():
    """清除所有智能体缓存"""
    try:
        agent_count = len(agents_cache)
        clear_agent_cache()
        
        return {
            "status": "success",
            "message": f"已清除 {agent_count} 个智能体实例",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ 清除缓存失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"清除缓存失败: {str(e)}")


# ==================== 运行服务器 ====================

if __name__ == "__main__":
    print("🌐 启动DMMR API服务器...")
    
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # 开发模式
        log_level="info"
    )


