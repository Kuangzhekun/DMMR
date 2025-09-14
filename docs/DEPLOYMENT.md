# DMMR 部署指南

本文档提供了DMMR系统的详细部署说明，包括本地开发、Docker容器化部署和生产环境配置。

## 📋 部署选项

### 1. 本地开发部署

适用于开发、测试和快速验证。

#### 环境要求
- Python 3.9+
- pip 或 conda
- 可选：Neo4j (图数据库)
- 可选：向量数据库 (FAISS/Milvus)

#### 快速开始

```bash
# 1. 克隆项目
git clone <repository_url>
cd DMMR-OpenSource

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，至少设置 ARK_API_KEY

# 5. 运行基本示例
python examples/basic_usage.py

# 6. 启动API服务器
python api/server.py
```

#### 验证部署

```bash
# 测试API健康状态
curl http://localhost:8000/health

# 运行基准测试
python experiments/run_benchmark.py
```

### 2. Docker 容器化部署

适用于生产环境和简化的部署流程。

#### 单容器部署

```bash
# 构建镜像
docker build -t dmmr:latest .

# 运行容器
docker run -d \
  --name dmmr-api \
  -p 8000:8000 \
  -e ARK_API_KEY="your_api_key_here" \
  -v $(pwd)/results:/app/results \
  dmmr:latest
```

#### Docker Compose 部署

```bash
# 复制环境配置
cp .env.example .env
# 编辑 .env 文件设置必要的环境变量

# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f dmmr-api
```

Docker Compose 会启动：
- DMMR API服务 (端口 8000)
- Neo4j 图数据库 (端口 7474/7687)
- 可选的向量数据库服务

#### 容器健康检查

```bash
# 检查API服务
curl http://localhost:8000/health

# 检查Neo4j (用户名: neo4j, 密码: dmmr_password)
curl -u neo4j:dmmr_password http://localhost:7474/db/data/

# 查看容器状态
docker-compose ps
```

### 3. 生产环境部署

#### Kubernetes 部署

创建 Kubernetes 配置文件：

```yaml
# dmmr-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dmmr-api
spec:
  replicas: 2
  selector:
    matchLabels:
      app: dmmr-api
  template:
    metadata:
      labels:
        app: dmmr-api
    spec:
      containers:
      - name: dmmr-api
        image: dmmr:latest
        ports:
        - containerPort: 8000
        env:
        - name: ARK_API_KEY
          valueFrom:
            secretKeyRef:
              name: dmmr-secrets
              key: api-key
        - name: DMMR_USE_REAL_GRAPH
          value: "1"
        - name: DMMR_GRAPH_URI
          value: "bolt://neo4j-service:7687"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: dmmr-api-service
spec:
  selector:
    app: dmmr-api
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

部署到Kubernetes：

```bash
# 创建密钥
kubectl create secret generic dmmr-secrets \
  --from-literal=api-key="your_api_key_here"

# 部署应用
kubectl apply -f dmmr-deployment.yaml

# 查看状态
kubectl get pods -l app=dmmr-api
kubectl get services
```

## ⚙️ 配置说明

### 环境变量配置

| 变量名 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| `ARK_API_KEY` | ✅ | - | API密钥 |
| `DMMR_MODEL_NAME` | ❌ | doubao-seed-1-6-flash-250715 | 使用的模型名称 |
| `DMMR_USE_REAL_VECTOR` | ❌ | 0 | 是否使用真实向量数据库 |
| `DMMR_USE_REAL_GRAPH` | ❌ | 0 | 是否使用真实图数据库 |
| `DMMR_DECAY_FACTOR` | ❌ | 0.5 | 激活衰减因子 |
| `DMMR_ACTIVATION_THRESHOLD` | ❌ | 0.1 | 激活阈值 |

完整配置选项请参考 `.env.example` 文件。

### 数据库配置

#### 内存数据库 (默认)
- 适用于开发和测试
- 无需额外配置
- 数据不持久化

#### Neo4j 图数据库
```bash
# 环境变量
DMMR_USE_REAL_GRAPH=1
DMMR_GRAPH_URI=bolt://localhost:7687
DMMR_GRAPH_USER=neo4j
DMMR_GRAPH_PASSWORD=your_password
```

#### FAISS 向量数据库
```bash
# 环境变量
DMMR_USE_REAL_VECTOR=1
DMMR_VECTOR_BACKEND=faiss
DMMR_VECTOR_DIM=256
```

## 📊 监控和维护

### 健康检查端点

```bash
# API健康状态
GET /health

# 系统配置信息
GET /v1/config

# 用户状态
GET /v1/status/{user_id}
```

### 日志配置

```bash
# 设置日志级别
export DMMR_LOG_LEVEL=INFO

# Docker日志查看
docker-compose logs -f dmmr-api

# Kubernetes日志查看
kubectl logs -f deployment/dmmr-api
```

### 性能监控

```bash
# 运行基准测试
python experiments/run_benchmark.py

# 查看API指标
curl http://localhost:8000/v1/config
```

## 🔧 故障排除

### 常见问题

#### 1. API密钥错误
```
症状: "API密钥未配置" 错误
解决: 检查环境变量 ARK_API_KEY 是否正确设置
```

#### 2. 数据库连接失败
```
症状: Neo4j连接错误
解决: 
- 检查Neo4j服务是否运行
- 验证连接字符串和认证信息
- 检查网络连接和防火墙设置
```

#### 3. 内存不足
```
症状: 容器重启或API响应慢
解决: 
- 增加容器内存限制
- 优化上下文预算配置
- 启用数据库持久化
```

#### 4. API响应超时
```
症状: 请求超时
解决:
- 检查模型服务可用性
- 调整超时设置
- 优化查询复杂度
```

### 调试模式

```bash
# 启用调试模式
export DMMR_LOG_LEVEL=DEBUG

# 详细错误信息
python -u api/server.py

# Docker调试
docker run -it --entrypoint /bin/bash dmmr:latest
```

## 🚀 性能优化

### 配置优化

```bash
# 减少上下文预算以降低延迟
DMMR_BUDGET_ITEMS=3
DMMR_BUDGET_CHARS=150

# 调整激活参数以提高精确度
DMMR_ACTIVATION_THRESHOLD=0.2
DMMR_DECAY_FACTOR=0.6
```

### 缓存策略

```bash
# 启用更大的缓存
DMMR_CACHE_SIZE=200

# 使用真实数据库以持久化数据
DMMR_USE_REAL_VECTOR=1
DMMR_USE_REAL_GRAPH=1
```

### 扩展部署

```yaml
# docker-compose.override.yml
version: '3.8'
services:
  dmmr-api:
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
```

## 📚 进一步阅读

- [API文档](API.md) - REST API详细说明
- [配置指南](CONFIGURATION.md) - 详细配置选项
- [开发指南](DEVELOPMENT.md) - 开发环境设置
- [架构文档](ARCHITECTURE.md) - 系统架构说明



