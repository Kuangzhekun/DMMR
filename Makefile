# DMMR Makefile
# Provides common development and deployment commands

.PHONY: help install test run docker clean docs lint format

# Default target
help:
	@echo "DMMR Project Management Commands"
	@echo "================================"
	@echo ""
	@echo "Installation and Setup:"
	@echo "  install      Install project dependencies"
	@echo "  install-dev  Install development dependencies"
	@echo "  setup        Run the setup script"
	@echo ""
	@echo "Development and Testing:"
	@echo "  test         Run the test suite"
	@echo "  benchmark    Run benchmarks"
	@echo "  lint         Lint the code"
	@echo "  format       Format the code"
	@echo ""
	@echo "Running Services:"
	@echo "  run          Start the API server"
	@echo "  demo         Run the demo script"
	@echo ""
	@echo "Docker Operations:"
	@echo "  docker-build Build the Docker image"
	@echo "  docker-up    Start Docker services"
	@echo "  docker-down  Stop Docker services"
	@echo "  docker-logs  View Docker logs"
	@echo ""
	@echo "Documentation and Cleanup:"
	@echo "  docs         Generate documentation"
	@echo "  clean        Clean up temporary files"

# Install dependencies
install:
	@echo "📦 Installing project dependencies..."
	pip install -r requirements.txt
	@echo "✅ Dependencies installed successfully"

install-dev:
	@echo "📦 Installing development dependencies..."
	pip install -r requirements.txt
	pip install pytest pytest-asyncio black flake8 mypy
	@echo "✅ Development dependencies installed successfully"

# Run setup script
setup:
	@echo "🚀 Running setup script..."
	@if [ "$(shell uname)" = "Linux" ] || [ "$(shell uname)" = "Darwin" ]; then \
		chmod +x scripts/setup.sh && ./scripts/setup.sh; \
	else \
		echo "On Windows, please run: powershell scripts/setup.ps1"; \
	fi

# Testing
test:
	@echo "🧪 Running test suite..."
	python -m pytest tests/ -v
	@echo "✅ Tests completed"

benchmark:
	@echo "⚡ Running benchmarks..."
	python experiments/run_benchmark.py
	@echo "✅ Benchmarks completed"

# Code Quality
lint:
	@echo "🔍 Running code linting..."
	flake8 src/ --max-line-length=100
	mypy src/
	@echo "✅ Linting completed"

format:
	@echo "✨ Formatting code..."
	black src/ examples/ experiments/
	@echo "✅ Code formatting completed"

# Run services
run:
	@echo "🚀 Starting API server..."
	python api/server.py

demo:
	@echo "🎯 Running demo script..."
	python examples/basic_usage.py

# Docker Operations
docker-build:
	@echo "🐳 Building Docker image..."
	docker build -t dmmr:latest .
	@echo "✅ Docker image built successfully"

docker-up:
	@echo "🚀 Starting Docker services..."
	docker-compose up -d
	@echo "✅ Docker services started successfully"

docker-down:
	@echo "🛑 Stopping Docker services..."
	docker-compose down
	@echo "✅ Docker services stopped"

docker-logs:
	@echo "📋 Viewing Docker logs..."
	docker-compose logs -f dmmr-api

# Documentation
docs:
	@echo "📚 Generating documentation..."
	@echo "API documentation is available at http://localhost:8000/docs after starting the service."

# Cleanup
clean:
	@echo "🧹 Cleaning up temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache/ 2>/dev/null || true
	rm -rf dist/ build/ 2>/dev/null || true
	@echo "✅ Cleanup completed"

# Check environment
check-env:
	@echo "🔍 Checking environment configuration..."
	@python -c "from src.dmmr import validate_config; print('✅ Configuration is valid' if validate_config() else '❌ Configuration is invalid')"

# Health check
health:
	@echo "🏥 Checking service health status..."
	@curl -s http://localhost:8000/health | python -m json.tool || echo "❌ API service is not running"

# Quickstart (full process)
quickstart: install setup run

# Development environment setup
dev-setup: install-dev
	@echo "🔧 Creating development environment configuration..."
	@if [ ! -f ".env" ]; then cp .env.example .env; fi
	@echo "✅ Development environment setup completed"



