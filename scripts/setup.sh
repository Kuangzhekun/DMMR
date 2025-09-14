#!/bin/bash
# DMMR 一键安装脚本
# 适用于 Linux/macOS 系统

set -e

echo "🚀 DMMR 系统安装脚本"
echo "=========================="

# 检查Python版本
check_python() {
    echo "🐍 检查Python环境..."
    
    if ! command -v python3 &> /dev/null; then
        echo "❌ 未找到Python3，请先安装Python 3.9+"
        exit 1
    fi
    
    python_version=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
    required_version="3.9"
    
    if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
        echo "❌ Python版本过低: $python_version，需要3.9+"
        exit 1
    fi
    
    echo "✅ Python版本: $python_version"
}

# 检查Docker
check_docker() {
    echo "🐳 检查Docker环境..."
    
    if command -v docker &> /dev/null; then
        echo "✅ Docker已安装: $(docker --version)"
        DOCKER_AVAILABLE=true
    else
        echo "⚠️  Docker未安装，将使用本地安装方式"
        DOCKER_AVAILABLE=false
    fi
    
    if command -v docker-compose &> /dev/null; then
        echo "✅ Docker Compose已安装: $(docker-compose --version)"
        COMPOSE_AVAILABLE=true
    else
        echo "⚠️  Docker Compose未安装"
        COMPOSE_AVAILABLE=false
    fi
}

# 创建虚拟环境
setup_venv() {
    echo "📦 创建Python虚拟环境..."
    
    if [ -d "venv" ]; then
        echo "✅ 虚拟环境已存在"
    else
        python3 -m venv venv
        echo "✅ 虚拟环境创建完成"
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 升级pip
    pip install --upgrade pip
    echo "✅ pip已升级"
}

# 安装Python依赖
install_dependencies() {
    echo "📚 安装Python依赖..."
    
    pip install -r requirements.txt
    echo "✅ 依赖安装完成"
}

# 配置环境变量
setup_env() {
    echo "⚙️ 配置环境变量..."
    
    if [ ! -f ".env" ]; then
        cp .env.example .env
        echo "✅ 环境配置文件已创建"
        echo ""
        echo "⚠️  重要：请编辑 .env 文件设置您的API密钥："
        echo "   ARK_API_KEY=your_actual_api_key_here"
        echo ""
    else
        echo "✅ 环境配置文件已存在"
    fi
}

# 创建必要目录
create_directories() {
    echo "📁 创建必要目录..."
    
    mkdir -p cache results logs
    echo "✅ 目录创建完成"
}

# 验证安装
verify_installation() {
    echo "🧪 验证安装..."
    
    # 检查配置
    if python -c "from src.dmmr import validate_config; exit(0 if validate_config() else 1)" 2>/dev/null; then
        echo "✅ 配置验证通过"
    else
        echo "⚠️  配置验证失败，请检查API密钥设置"
    fi
    
    # 运行基本测试
    echo "🔍 运行基本功能测试..."
    if python examples/basic_usage.py > /dev/null 2>&1; then
        echo "✅ 基本功能测试通过"
    else
        echo "⚠️  基本功能测试失败，请检查配置"
    fi
}

# 显示后续步骤
show_next_steps() {
    echo ""
    echo "🎉 DMMR安装完成！"
    echo "==================="
    echo ""
    echo "📋 后续步骤："
    echo ""
    echo "1. 激活虚拟环境："
    echo "   source venv/bin/activate"
    echo ""
    echo "2. 编辑环境配置："
    echo "   nano .env  # 设置ARK_API_KEY"
    echo ""
    echo "3. 启动API服务："
    echo "   python api/server.py"
    echo ""
    echo "4. 运行示例："
    echo "   python examples/basic_usage.py"
    echo ""
    echo "5. 运行基准测试："
    echo "   python experiments/run_benchmark.py"
    echo ""
    
    if [ "$DOCKER_AVAILABLE" = true ] && [ "$COMPOSE_AVAILABLE" = true ]; then
        echo "🐳 Docker选项："
        echo "   docker-compose up -d  # 启动完整服务栈"
        echo ""
    fi
    
    echo "📚 更多信息："
    echo "   - 快速开始: docs/QUICKSTART.md"
    echo "   - 部署指南: docs/DEPLOYMENT.md" 
    echo "   - API文档: http://localhost:8000/docs"
}

# 主安装流程
main() {
    echo "开始安装DMMR系统..."
    echo ""
    
    # 检查环境
    check_python
    check_docker
    
    # 询问安装方式
    echo ""
    echo "请选择安装方式："
    echo "1) 本地安装 (Python虚拟环境)"
    if [ "$DOCKER_AVAILABLE" = true ]; then
        echo "2) Docker安装"
    fi
    echo ""
    read -p "请输入选择 (1-2): " choice
    
    case $choice in
        1)
            echo "选择本地安装方式"
            setup_venv
            install_dependencies
            setup_env
            create_directories
            verify_installation
            show_next_steps
            ;;
        2)
            if [ "$DOCKER_AVAILABLE" = false ]; then
                echo "❌ Docker未安装，无法使用Docker方式"
                exit 1
            fi
            echo "选择Docker安装方式"
            setup_env
            create_directories
            echo "🐳 构建Docker镜像..."
            docker build -t dmmr:latest .
            echo "✅ Docker镜像构建完成"
            
            if [ "$COMPOSE_AVAILABLE" = true ]; then
                echo "🚀 启动服务..."
                docker-compose up -d
                echo "✅ 服务启动完成"
                echo ""
                echo "🌐 服务地址："
                echo "   - API服务: http://localhost:8000"
                echo "   - API文档: http://localhost:8000/docs"
                echo "   - Neo4j: http://localhost:7474"
            else
                echo "🚀 启动API服务..."
                docker run -d --name dmmr-api -p 8000:8000 --env-file .env dmmr:latest
                echo "✅ API服务启动完成: http://localhost:8000"
            fi
            ;;
        *)
            echo "❌ 无效选择"
            exit 1
            ;;
    esac
}

# 错误处理
trap 'echo "❌ 安装过程中出现错误"; exit 1' ERR

# 运行主函数
main "$@"


