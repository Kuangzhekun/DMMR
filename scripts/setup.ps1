# DMMR One-Click Installer (Windows PowerShell)
# For Windows systems

param(
    [switch]$Docker,
    [switch]$Local,
    [switch]$Help
)

# Display help information
if ($Help) {
    Write-Host "DMMR Windows Installation Script" -ForegroundColor Green
    Write-Host "Usage: .\setup.ps1 [Options]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Local   Install using a local Python environment"
    Write-Host "  -Docker  Install using Docker containers"
    Write-Host "  -Help    Display this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\setup.ps1 -Local   # Local installation"
    Write-Host "  .\setup.ps1 -Docker  # Docker installation"
    exit 0
}

Write-Host "🚀 DMMR Windows System Installation Script" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

# Check execution policy
function Test-ExecutionPolicy {
    Write-Host "🔐 Checking PowerShell execution policy..." -ForegroundColor Yellow
    
    $currentPolicy = Get-ExecutionPolicy -Scope CurrentUser
    
    if ($currentPolicy -eq "Restricted") {
        Write-Host "⚠️  Current execution policy is restricted, attempting to set it..." -ForegroundColor Yellow
        try {
            Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
            Write-Host "✅ Execution policy has been set to RemoteSigned" -ForegroundColor Green
        }
        catch {
            Write-Host "❌ Failed to set execution policy. Please run as an administrator:" -ForegroundColor Red
            Write-Host "   Set-ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Red
            exit 1
        }
    }
    else {
        Write-Host "✅ Execution policy: $currentPolicy" -ForegroundColor Green
    }
}

# Check Python environment
function Test-Python {
    Write-Host "🐍 Checking Python environment..." -ForegroundColor Yellow
    
    try {
        $pythonVersion = & python --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ $pythonVersion" -ForegroundColor Green
        }
        else {
            throw "Python not found"
        }
        
        # Check version
        $version = (& python -c "import sys; print('.'.join(map(str, sys.version_info[:2])))" 2>&1)
        $requiredVersion = [Version]"3.9"
        $currentVersion = [Version]$version
        
        if ($currentVersion -lt $requiredVersion) {
            Write-Host "❌ Python version is too old: $version, Python 3.9+ is required" -ForegroundColor Red
            exit 1
        }
    }
    catch {
        Write-Host "❌ Python not found. Please install Python 3.9+ first." -ForegroundColor Red
        Write-Host "   Download from: https://www.python.org/downloads/" -ForegroundColor Yellow
        exit 1
    }
}

# Check Docker environment
function Test-Docker {
    Write-Host "🐳 Checking Docker environment..." -ForegroundColor Yellow
    
    $script:DockerAvailable = $false
    $script:ComposeAvailable = $false
    
    try {
        $dockerVersion = & docker --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ $dockerVersion" -ForegroundColor Green
            $script:DockerAvailable = $true
        }
    }
    catch {
        Write-Host "⚠️  Docker not found" -ForegroundColor Yellow
    }
    
    try {
        $composeVersion = & docker-compose --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ $composeVersion" -ForegroundColor Green
            $script:ComposeAvailable = $true
        }
    }
    catch {
        Write-Host "⚠️  Docker Compose not found" -ForegroundColor Yellow
    }
}

# Create Python virtual environment
function New-VirtualEnv {
    Write-Host "📦 Creating Python virtual environment..." -ForegroundColor Yellow
    
    if (Test-Path "venv") {
        Write-Host "✅ Virtual environment already exists" -ForegroundColor Green
    }
    else {
        & python -m venv venv
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Virtual environment created successfully" -ForegroundColor Green
        }
        else {
            Write-Host "❌ Failed to create virtual environment" -ForegroundColor Red
            exit 1
        }
    }
    
    # Activate virtual environment
    & .\venv\Scripts\Activate.ps1
    
    # Upgrade pip
    Write-Host "📦 Upgrading pip..." -ForegroundColor Yellow
    & python -m pip install --upgrade pip
    Write-Host "✅ pip has been upgraded" -ForegroundColor Green
}

# Install Python dependencies
function Install-Dependencies {
    Write-Host "📚 Installing Python dependencies..." -ForegroundColor Yellow
    
    & pip install -r requirements.txt
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Dependencies installed successfully" -ForegroundColor Green
    }
    else {
        Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
        exit 1
    }
}

# Configure environment variables
function Set-Environment {
    Write-Host "⚙️ Configuring environment variables..." -ForegroundColor Yellow
    
    if (-not (Test-Path ".env")) {
        Copy-Item ".env.example" ".env"
        Write-Host "✅ Environment configuration file created" -ForegroundColor Green
        Write-Host ""
        Write-Host "⚠️  IMPORTANT: Please edit the .env file to set your API key:" -ForegroundColor Yellow
        Write-Host "   ARK_API_KEY=your_actual_api_key_here" -ForegroundColor Yellow
        Write-Host ""
    }
    else {
        Write-Host "✅ Environment configuration file already exists" -ForegroundColor Green
    }
}

# Create necessary directories
function New-Directories {
    Write-Host "📁 Creating necessary directories..." -ForegroundColor Yellow
    
    $directories = @("cache", "results", "logs")
    foreach ($dir in $directories) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir | Out-Null
        }
    }
    Write-Host "✅ Directories created successfully" -ForegroundColor Green
}

# Verify installation
function Test-Installation {
    Write-Host "🧪 Verifying installation..." -ForegroundColor Yellow
    
    # Check configuration
    try {
        & python -c "from src.dmmr import validate_config; exit(0 if validate_config() else 1)" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Configuration validation passed" -ForegroundColor Green
        }
        else {
            Write-Host "⚠️  Configuration validation failed. Please check your API key settings." -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "⚠️  Configuration validation failed. Please check your API key settings." -ForegroundColor Yellow
    }
    
    # Run basic test
    Write-Host "🔍 Running basic functionality test..." -ForegroundColor Yellow
    try {
        & python examples/basic_usage.py >$null 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Basic functionality test passed" -ForegroundColor Green
        }
        else {
            Write-Host "⚠️  Basic functionality test failed. Please check your configuration." -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "⚠️  Basic functionality test failed. Please check your configuration." -ForegroundColor Yellow
    }
}

# Display next steps
function Show-NextSteps {
    Write-Host ""
    Write-Host "🎉 DMMR installation complete!" -ForegroundColor Green
    Write-Host "=============================" -ForegroundColor Green
    Write-Host ""
    Write-Host "📋 Next Steps:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "1. Activate the virtual environment:" -ForegroundColor White
    Write-Host "   .\venv\Scripts\Activate.ps1" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "2. Edit the environment configuration:" -ForegroundColor White
    Write-Host "   notepad .env  # Set ARK_API_KEY" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "3. Start the API service:" -ForegroundColor White
    Write-Host "   python api/server.py" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "4. Run an example:" -ForegroundColor White
    Write-Host "   python examples/basic_usage.py" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "5. Run benchmarks:" -ForegroundColor White
    Write-Host "   python experiments/run_benchmark.py" -ForegroundColor Cyan
    Write-Host ""
    
    if ($script:DockerAvailable -and $script:ComposeAvailable) {
        Write-Host "🐳 Docker Options:" -ForegroundColor Blue
        Write-Host "   docker-compose up -d  # Start the complete service stack" -ForegroundColor Cyan
        Write-Host ""
    }
    
    Write-Host "📚 More Information:" -ForegroundColor Yellow
    Write-Host "   - Quickstart Guide: docs/QUICKSTART.md" -ForegroundColor White
    Write-Host "   - Deployment Guide: docs/DEPLOYMENT.md" -ForegroundColor White
    Write-Host "   - API Documentation: http://localhost:8000/docs" -ForegroundColor White
}

# Local installation process
function Install-Local {
    Write-Host "Starting local installation..." -ForegroundColor Green
    
    Test-ExecutionPolicy
    Test-Python
    New-VirtualEnv
    Install-Dependencies
    Set-Environment
    New-Directories
    Test-Installation
    Show-NextSteps
}

# Docker installation process
function Install-Docker {
    if (-not $script:DockerAvailable) {
        Write-Host "❌ Docker is not installed. Cannot proceed with Docker installation." -ForegroundColor Red
        Write-Host "   Please install Docker Desktop first: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
        exit 1
    }
    
    Write-Host "Starting Docker installation..." -ForegroundColor Green
    
    Set-Environment
    New-Directories
    
    Write-Host "🐳 Building Docker image..." -ForegroundColor Yellow
    & docker build -t dmmr:latest .
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Docker image built successfully" -ForegroundColor Green
    }
    else {
        Write-Host "❌ Failed to build Docker image" -ForegroundColor Red
        exit 1
    }
    
    if ($script:ComposeAvailable) {
        Write-Host "🚀 Starting services..." -ForegroundColor Yellow
        & docker-compose up -d
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Services started successfully" -ForegroundColor Green
            Write-Host ""
            Write-Host "🌐 Service Endpoints:" -ForegroundColor Yellow
            Write-Host "   - API Service: http://localhost:8000" -ForegroundColor White
            Write-Host "   - API Docs: http://localhost:8000/docs" -ForegroundColor White
            Write-Host "   - Neo4j Browser: http://localhost:7474" -ForegroundColor White
        }
        else {
            Write-Host "❌ Failed to start services" -ForegroundColor Red
            exit 1
        }
    }
    else {
        Write-Host "🚀 Starting API service..." -ForegroundColor Yellow
        & docker run -d --name dmmr-api -p 8000:8000 --env-file .env dmmr:latest
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ API service started successfully: http://localhost:8000" -ForegroundColor Green
        }
        else {
            Write-Host "❌ Failed to start API service" -ForegroundColor Red
            exit 1
        }
    }
}

# Main installation process
function Start-Installation {
    Write-Host "Starting DMMR system installation..." -ForegroundColor Green
    Write-Host ""
    
    # Check environment
    Test-Docker
    
    # Select installation method based on parameters
    if ($Local) {
        Install-Local
    }
    elseif ($Docker) {
        Install-Docker
    }
    else {
        # Interactive selection
        Write-Host "Please select an installation method:" -ForegroundColor Yellow
        Write-Host "1) Local installation (Python virtual environment)" -ForegroundColor White
        if ($script:DockerAvailable) {
            Write-Host "2) Docker installation" -ForegroundColor White
        }
        Write-Host ""
        
        do {
            $choice = Read-Host "Enter your choice (1-2)"
        } while ($choice -notmatch "^[12]$")
        
        switch ($choice) {
            "1" { Install-Local }
            "2" { 
                if ($script:DockerAvailable) {
                    Install-Docker
                }
                else {
                    Write-Host "❌ Docker is not installed. Cannot proceed with Docker installation." -ForegroundColor Red
                    exit 1
                }
            }
        }
    }
}

# Error handling
trap {
    Write-Host "❌ An error occurred during installation: $_" -ForegroundColor Red
    exit 1
}

# Run the main function
Start-Installation



