# DMMR Makefile
# 提供常用的开发和部署命令

.PHONY: help install test run docker clean docs lint format

# 默认目标
help:
	@echo "DMMR 项目管理命令"
	@echo "=================="
	@echo ""
	@echo "安装和设置:"
	@echo "  install      安装项目依赖"
	@echo "  install-dev  安装开发依赖"
	@echo "  setup        运行设置脚本"
	@echo ""
	@echo "开发和测试:"
	@echo "  test         运行测试套件"
	@echo "  benchmark    运行基准测试"
	@echo "  lint         代码检查"
	@echo "  format       代码格式化"
	@echo ""
	@echo "运行服务:"
	@echo "  run          启动API服务器"
	@echo "  demo         运行演示脚本"
	@echo ""
	@echo "Docker操作:"
	@echo "  docker-build 构建Docker镜像"
	@echo "  docker-up    启动Docker服务"
	@echo "  docker-down  停止Docker服务"
	@echo ""
	@echo "文档和清理:"
	@echo "  docs         生成文档"
	@echo "  clean        清理临时文件"

# 安装依赖
install:
	@echo "📦 安装项目依赖..."
	pip install -r requirements.txt
	@echo "✅ 依赖安装完成"

install-dev:
	@echo "📦 安装开发依赖..."
	pip install -r requirements.txt
	pip install pytest pytest-asyncio black flake8 mypy
	@echo "✅ 开发依赖安装完成"

# 运行设置脚本
setup:
	@echo "🚀 运行设置脚本..."
	@if [ "$(shell uname)" = "Linux" ] || [ "$(shell uname)" = "Darwin" ]; then \
		chmod +x scripts/setup.sh && ./scripts/setup.sh; \
	else \
		echo "请在Windows上运行: powershell scripts/setup.ps1"; \
	fi

# 测试
test:
	@echo "🧪 运行测试套件..."
	python -m pytest tests/ -v
	@echo "✅ 测试完成"

benchmark:
	@echo "⚡ 运行基准测试..."
	python experiments/run_benchmark.py
	@echo "✅ 基准测试完成"

# 代码质量
lint:
	@echo "🔍 运行代码检查..."
	flake8 src/ --max-line-length=100
	mypy src/
	@echo "✅ 代码检查完成"

format:
	@echo "✨ 格式化代码..."
	black src/ examples/ experiments/
	@echo "✅ 代码格式化完成"

# 运行服务
run:
	@echo "🚀 启动API服务器..."
	python api/server.py

demo:
	@echo "🎯 运行演示脚本..."
	python examples/basic_usage.py

# Docker操作
docker-build:
	@echo "🐳 构建Docker镜像..."
	docker build -t dmmr:latest .
	@echo "✅ Docker镜像构建完成"

docker-up:
	@echo "🚀 启动Docker服务..."
	docker-compose up -d
	@echo "✅ Docker服务启动完成"

docker-down:
	@echo "🛑 停止Docker服务..."
	docker-compose down
	@echo "✅ Docker服务已停止"

docker-logs:
	@echo "📋 查看Docker日志..."
	docker-compose logs -f dmmr-api

# 文档
docs:
	@echo "📚 生成文档..."
	@echo "API文档可在启动服务后访问: http://localhost:8000/docs"

# 清理
clean:
	@echo "🧹 清理临时文件..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache/ 2>/dev/null || true
	rm -rf dist/ build/ 2>/dev/null || true
	@echo "✅ 清理完成"

# 检查环境
check-env:
	@echo "🔍 检查环境配置..."
	@python -c "from src.dmmr import validate_config; print('✅ 配置有效' if validate_config() else '❌ 配置无效')"

# 健康检查
health:
	@echo "🏥 检查服务健康状态..."
	@curl -s http://localhost:8000/health | python -m json.tool || echo "❌ API服务未启动"

# 快速启动（完整流程）
quickstart: install setup run

# 开发环境设置
dev-setup: install-dev
	@echo "🔧 创建开发环境配置..."
	@if [ ! -f ".env" ]; then cp .env.example .env; fi
	@echo "✅ 开发环境设置完成"


