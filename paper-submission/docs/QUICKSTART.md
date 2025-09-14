# DMMR 快速开始指南

本指南将帮助您在5分钟内启动并运行DMMR系统。

## 🚀 一键启动

### 方法1: Docker (推荐)

```bash
# 1. 克隆项目
git clone <repository_url>
cd DMMR-OpenSource

# 2. 配置API密钥
echo "ARK_API_KEY=your_api_key_here" > .env

# 3. 启动服务
docker-compose up -d

# 4. 验证服务
curl http://localhost:8000/health
```

### 方法2: 本地安装

```bash
# 1. 克隆项目
git clone <repository_url>
cd DMMR-OpenSource

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境
cp .env.example .env
# 编辑.env文件，设置ARK_API_KEY

# 4. 启动API服务
python api/server.py
```

## 💬 第一次对话

### 通过API

```bash
curl -X POST http://localhost:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "message": "你好！我想学习Python编程。"
  }'
```

### 通过Python客户端

```python
import requests

response = requests.post('http://localhost:8000/v1/chat', json={
    'user_id': 'test_user', 
    'message': '你好！我想学习Python编程。'
})

print(response.json()['ai_response'])
```

### 通过演示脚本

```bash
# 运行基本使用示例
python examples/basic_usage.py

# 运行API客户端演示
python examples/api_client_demo.py

# 运行记忆系统演示
python examples/memory_system_demo.py
```

## 🧪 测试功能

### 运行基准测试

```bash
python experiments/run_benchmark.py
```

### 测试不同任务类型

```python
# 技术编程
curl -X POST http://localhost:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "如何修复Python的ImportError？"}'

# 情感咨询
curl -X POST http://localhost:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "我最近工作压力很大，感觉很焦虑。"}'

# 创意写作
curl -X POST http://localhost:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "帮我写一个科幻故事的开头。"}'
```

## 🔧 基本配置

### 环境变量配置

创建 `.env` 文件：

```bash
# 必需配置
ARK_API_KEY=your_doubao_api_key

# 可选配置
DMMR_MODEL_NAME=doubao-seed-1-6-flash-250715
DMMR_USE_REAL_VECTOR=0  # 0=内存DB, 1=真实DB
DMMR_USE_REAL_GRAPH=0   # 0=内存DB, 1=Neo4j
DMMR_DECAY_FACTOR=0.5   # 激活衰减因子
DMMR_ACTIVATION_THRESHOLD=0.1  # 激活阈值
```

### 服务端口配置

默认端口：
- API服务: http://localhost:8000
- Neo4j Web界面: http://localhost:7474
- Neo4j Bolt: bolt://localhost:7687

## 📊 监控服务

### 健康检查

```bash
# 检查API健康状态
curl http://localhost:8000/health

# 获取系统配置
curl http://localhost:8000/v1/config

# 查看用户状态
curl http://localhost:8000/v1/status/test_user
```

### 查看日志

```bash
# Docker方式
docker-compose logs -f dmmr-api

# 本地方式
# 日志会输出到控制台
```

## 🛠️ 常见问题

### Q: API密钥错误怎么办？

A: 检查 `.env` 文件中的 `ARK_API_KEY` 是否正确设置。

### Q: 服务启动失败？

A: 
1. 检查端口8000是否被占用
2. 确认Python版本 >= 3.9
3. 验证所有依赖是否正确安装

### Q: Neo4j连接失败？

A: 
1. 使用Docker Compose自动启动Neo4j
2. 或手动安装Neo4j并配置连接信息

### Q: 响应速度慢？

A: 
1. 使用更小的上下文预算：`DMMR_BUDGET_ITEMS=3`
2. 提高激活阈值：`DMMR_ACTIVATION_THRESHOLD=0.2`
3. 确保网络连接稳定

## 🎯 下一步

完成快速开始后，您可以：

1. **深入了解功能**: 阅读 [README.md](../README.md)
2. **部署到生产**: 参考 [DEPLOYMENT.md](DEPLOYMENT.md)
3. **自定义配置**: 查看 [配置选项](CONFIGURATION.md)
4. **开发扩展**: 参考 [开发指南](DEVELOPMENT.md)

## 📚 示例代码

### Python集成示例

```python
from src.dmmr import DMMRAgent

# 创建智能体
agent = DMMRAgent(
    user_id="your_user_id",
    use_real_backends=False  # 开发环境使用内存数据库
)

# 进行对话
response, metrics = agent.process_input("你好，我想学习机器学习")

print(f"AI回答: {response}")
print(f"响应延迟: {metrics.latency_sec:.2f}秒")
print(f"记忆命中: {metrics.memory_hits}个")
```

### 持续对话示例

```python
# 多轮对话，测试记忆功能
conversations = [
    "我是一名Python初学者",
    "我想学习数据科学",
    "你还记得我是初学者吗？",  # 测试记忆回忆
]

for msg in conversations:
    response, _ = agent.process_input(msg)
    print(f"用户: {msg}")
    print(f"AI: {response}\n")
```

## 🔗 相关链接

- [项目主页](../README.md)
- [API文档](API.md)
- [架构设计](ARCHITECTURE.md)
- [问题反馈](https://github.com/your-org/DMMR/issues)

---

🎉 恭喜！您已经成功启动了DMMR系统。开始探索智能记忆的强大功能吧！

