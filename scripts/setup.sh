#!/bin/bash
# DMMR One-Click Installer
# For Linux/macOS systems

set -e

echo "🚀 DMMR System Installation Script"
echo "================================="

# Check Python version
check_python() {
    echo "🐍 Checking Python environment..."
    
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python3 not found. Please install Python 3.9+ first."
        exit 1
    fi
    
    python_version=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:2])))")
    required_version="3.9"
    
    if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
        echo "❌ Python version is too old: $python_version. Python 3.9+ is required."
        exit 1
    fi
    
    echo "✅ Python version: $python_version"
}

# Check Docker
check_docker() {
    echo "🐳 Checking Docker environment..."
    
    if command -v docker &> /dev/null; then
        echo "✅ Docker is installed: $(docker --version)"
        DOCKER_AVAILABLE=true
    else
        echo "⚠️  Docker not found. Will proceed with local installation."
        DOCKER_AVAILABLE=false
    fi
    
    if command -v docker-compose &> /dev/null; then
        echo "✅ Docker Compose is installed: $(docker-compose --version)"
        COMPOSE_AVAILABLE=true
    else
        echo "⚠️  Docker Compose not found."
        COMPOSE_AVAILABLE=false
    fi
}

# Setup virtual environment
setup_venv() {
    echo "📦 Creating Python virtual environment..."
    
    if [ -d "venv" ]; then
        echo "✅ Virtual environment already exists."
    else
        python3 -m venv venv
        echo "✅ Virtual environment created successfully."
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    echo "✅ pip has been upgraded."
}

# Install Python dependencies
install_dependencies() {
    echo "📚 Installing Python dependencies..."
    
    pip install -r requirements.txt
    echo "✅ Dependencies installed successfully."
}

# Setup environment variables
setup_env() {
    echo "⚙️ Configuring environment variables..."
    
    if [ ! -f ".env" ]; then
        cp .env.example .env
        echo "✅ Environment configuration file created."
        echo ""
        echo "⚠️  IMPORTANT: Please edit the .env file to set your API key:"
        echo "   ARK_API_KEY=your_actual_api_key_here"
        echo ""
    else
        echo "✅ Environment configuration file already exists."
    fi
}

# Create necessary directories
create_directories() {
    echo "📁 Creating necessary directories..."
    
    mkdir -p cache results logs
    echo "✅ Directories created successfully."
}

# Verify installation
verify_installation() {
    echo "🧪 Verifying installation..."
    
    # Check configuration
    if python -c "from src.dmmr import validate_config; exit(0 if validate_config() else 1)" 2>/dev/null; then
        echo "✅ Configuration validation passed."
    else
        echo "⚠️  Configuration validation failed. Please check your API key settings."
    fi
    
    # Run basic test
    echo "🔍 Running basic functionality test..."
    if python examples/basic_usage.py > /dev/null 2>&1; then
        echo "✅ Basic functionality test passed."
    else
        echo "⚠️  Basic functionality test failed. Please check your configuration."
    fi
}

# Show next steps
show_next_steps() {
    echo ""
    echo "🎉 DMMR installation complete!"
    echo "============================="
    echo ""
    echo "📋 Next Steps:"
    echo ""
    echo "1. Activate the virtual environment:"
    echo "   source venv/bin/activate"
    echo ""
    echo "2. Edit the environment configuration:"
    echo "   nano .env  # Set ARK_API_KEY"
    echo ""
    echo "3. Start the API service:"
    echo "   python api/server.py"
    echo ""
    echo "4. Run an example:"
    echo "   python examples/basic_usage.py"
    echo ""
    echo "5. Run benchmarks:"
    echo "   python experiments/run_benchmark.py"
    echo ""
    
    if [ "$DOCKER_AVAILABLE" = true ] && [ "$COMPOSE_AVAILABLE" = true ]; then
        echo "🐳 Docker Options:"
        echo "   docker-compose up -d  # Start the complete service stack"
        echo ""
    fi
    
    echo "📚 More Information:"
    echo "   - Quickstart Guide: docs/QUICKSTART.md"
    echo "   - Deployment Guide: docs/DEPLOYMENT.md" 
    echo "   - API Documentation: http://localhost:8000/docs"
}

# Main installation process
main() {
    echo "Starting DMMR system installation..."
    echo ""
    
    # Check environment
    check_python
    check_docker
    
    # Ask for installation method
    echo ""
    echo "Please select an installation method:"
    echo "1) Local installation (Python virtual environment)"
    if [ "$DOCKER_AVAILABLE" = true ]; then
        echo "2) Docker installation"
    fi
    echo ""
    read -p "Enter your choice (1-2): " choice
    
    case $choice in
        1)
            echo "Starting local installation..."
            setup_venv
            install_dependencies
            setup_env
            create_directories
            verify_installation
            show_next_steps
            ;;
        2)
            if [ "$DOCKER_AVAILABLE" = false ]; then
                echo "❌ Docker is not installed. Cannot proceed with Docker installation."
                exit 1
            fi
            echo "Starting Docker installation..."
            setup_env
            create_directories
            echo "🐳 Building Docker image..."
            docker build -t dmmr:latest .
            echo "✅ Docker image built successfully."
            
            if [ "$COMPOSE_AVAILABLE" = true ]; then
                echo "🚀 Starting services..."
                docker-compose up -d
                echo "✅ Services started successfully."
                echo ""
                echo "🌐 Service Endpoints:"
                echo "   - API Service: http://localhost:8000"
                echo "   - API Docs: http://localhost:8000/docs"
                echo "   - Neo4j Browser: http://localhost:7474"
            else
                echo "🚀 Starting API service..."
                docker run -d --name dmmr-api -p 8000:8000 --env-file .env dmmr:latest
                echo "✅ API service started successfully: http://localhost:8000"
            fi
            ;;
        *)
            echo "❌ Invalid choice."
            exit 1
            ;;
    esac
}

# Error handling
trap 'echo "❌ An error occurred during installation"; exit 1' ERR

# Run the main function
main "$@"



