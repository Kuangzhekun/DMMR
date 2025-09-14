# DMMR 一键安装脚本 (Windows PowerShell)
# 适用于 Windows 系统

param(
    [switch]$Docker,
    [switch]$Local,
    [switch]$Help
)

# 显示帮助信息
if ($Help) {
    Write-Host "DMMR Windows 安装脚本" -ForegroundColor Green
    Write-Host "用法: .\setup.ps1 [选项]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "选项:"
    Write-Host "  -Local   使用本地Python环境安装"
    Write-Host "  -Docker  使用Docker容器安装"
    Write-Host "  -Help    显示此帮助信息"
    Write-Host ""
    Write-Host "示例:"
    Write-Host "  .\setup.ps1 -Local   # 本地安装"
    Write-Host "  .\setup.ps1 -Docker  # Docker安装"
    exit 0
}

Write-Host "🚀 DMMR Windows 系统安装脚本" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green

# 检查执行策略
function Test-ExecutionPolicy {
    Write-Host "🔐 检查PowerShell执行策略..." -ForegroundColor Yellow
    
    $currentPolicy = Get-ExecutionPolicy -Scope CurrentUser
    
    if ($currentPolicy -eq "Restricted") {
        Write-Host "⚠️  当前执行策略受限，正在设置..." -ForegroundColor Yellow
        try {
            Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
            Write-Host "✅ 执行策略已设置为 RemoteSigned" -ForegroundColor Green
        }
        catch {
            Write-Host "❌ 无法设置执行策略，请以管理员身份运行:" -ForegroundColor Red
            Write-Host "   Set-ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Red
            exit 1
        }
    }
    else {
        Write-Host "✅ 执行策略: $currentPolicy" -ForegroundColor Green
    }
}

# 检查Python环境
function Test-Python {
    Write-Host "🐍 检查Python环境..." -ForegroundColor Yellow
    
    try {
        $pythonVersion = & python --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ $pythonVersion" -ForegroundColor Green
        }
        else {
            throw "Python未找到"
        }
        
        # 检查版本
        $version = (& python -c "import sys; print('.'.join(map(str, sys.version_info[:2])))" 2>&1)
        $requiredVersion = [Version]"3.9"
        $currentVersion = [Version]$version
        
        if ($currentVersion -lt $requiredVersion) {
            Write-Host "❌ Python版本过低: $version，需要3.9+" -ForegroundColor Red
            exit 1
        }
    }
    catch {
        Write-Host "❌ 未找到Python，请先安装Python 3.9+" -ForegroundColor Red
        Write-Host "   下载地址: https://www.python.org/downloads/" -ForegroundColor Yellow
        exit 1
    }
}

# 检查Docker环境
function Test-Docker {
    Write-Host "🐳 检查Docker环境..." -ForegroundColor Yellow
    
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
        Write-Host "⚠️  Docker未安装" -ForegroundColor Yellow
    }
    
    try {
        $composeVersion = & docker-compose --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ $composeVersion" -ForegroundColor Green
            $script:ComposeAvailable = $true
        }
    }
    catch {
        Write-Host "⚠️  Docker Compose未安装" -ForegroundColor Yellow
    }
}

# 创建Python虚拟环境
function New-VirtualEnv {
    Write-Host "📦 创建Python虚拟环境..." -ForegroundColor Yellow
    
    if (Test-Path "venv") {
        Write-Host "✅ 虚拟环境已存在" -ForegroundColor Green
    }
    else {
        & python -m venv venv
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ 虚拟环境创建完成" -ForegroundColor Green
        }
        else {
            Write-Host "❌ 虚拟环境创建失败" -ForegroundColor Red
            exit 1
        }
    }
    
    # 激活虚拟环境
    & .\venv\Scripts\Activate.ps1
    
    # 升级pip
    Write-Host "📦 升级pip..." -ForegroundColor Yellow
    & python -m pip install --upgrade pip
    Write-Host "✅ pip已升级" -ForegroundColor Green
}

# 安装Python依赖
function Install-Dependencies {
    Write-Host "📚 安装Python依赖..." -ForegroundColor Yellow
    
    & pip install -r requirements.txt
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ 依赖安装完成" -ForegroundColor Green
    }
    else {
        Write-Host "❌ 依赖安装失败" -ForegroundColor Red
        exit 1
    }
}

# 配置环境变量
function Set-Environment {
    Write-Host "⚙️ 配置环境变量..." -ForegroundColor Yellow
    
    if (-not (Test-Path ".env")) {
        Copy-Item ".env.example" ".env"
        Write-Host "✅ 环境配置文件已创建" -ForegroundColor Green
        Write-Host ""
        Write-Host "⚠️  重要：请编辑 .env 文件设置您的API密钥：" -ForegroundColor Yellow
        Write-Host "   ARK_API_KEY=your_actual_api_key_here" -ForegroundColor Yellow
        Write-Host ""
    }
    else {
        Write-Host "✅ 环境配置文件已存在" -ForegroundColor Green
    }
}

# 创建必要目录
function New-Directories {
    Write-Host "📁 创建必要目录..." -ForegroundColor Yellow
    
    $directories = @("cache", "results", "logs")
    foreach ($dir in $directories) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir | Out-Null
        }
    }
    Write-Host "✅ 目录创建完成" -ForegroundColor Green
}

# 验证安装
function Test-Installation {
    Write-Host "🧪 验证安装..." -ForegroundColor Yellow
    
    # 检查配置
    try {
        & python -c "from src.dmmr import validate_config; exit(0 if validate_config() else 1)" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ 配置验证通过" -ForegroundColor Green
        }
        else {
            Write-Host "⚠️  配置验证失败，请检查API密钥设置" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "⚠️  配置验证失败，请检查API密钥设置" -ForegroundColor Yellow
    }
    
    # 运行基本测试
    Write-Host "🔍 运行基本功能测试..." -ForegroundColor Yellow
    try {
        & python examples/basic_usage.py >$null 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ 基本功能测试通过" -ForegroundColor Green
        }
        else {
            Write-Host "⚠️  基本功能测试失败，请检查配置" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "⚠️  基本功能测试失败，请检查配置" -ForegroundColor Yellow
    }
}

# 显示后续步骤
function Show-NextSteps {
    Write-Host ""
    Write-Host "🎉 DMMR安装完成！" -ForegroundColor Green
    Write-Host "===================" -ForegroundColor Green
    Write-Host ""
    Write-Host "📋 后续步骤：" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "1. 激活虚拟环境：" -ForegroundColor White
    Write-Host "   .\venv\Scripts\Activate.ps1" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "2. 编辑环境配置：" -ForegroundColor White
    Write-Host "   notepad .env  # 设置ARK_API_KEY" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "3. 启动API服务：" -ForegroundColor White
    Write-Host "   python api/server.py" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "4. 运行示例：" -ForegroundColor White
    Write-Host "   python examples/basic_usage.py" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "5. 运行基准测试：" -ForegroundColor White
    Write-Host "   python experiments/run_benchmark.py" -ForegroundColor Cyan
    Write-Host ""
    
    if ($script:DockerAvailable -and $script:ComposeAvailable) {
        Write-Host "🐳 Docker选项：" -ForegroundColor Blue
        Write-Host "   docker-compose up -d  # 启动完整服务栈" -ForegroundColor Cyan
        Write-Host ""
    }
    
    Write-Host "📚 更多信息：" -ForegroundColor Yellow
    Write-Host "   - 快速开始: docs/QUICKSTART.md" -ForegroundColor White
    Write-Host "   - 部署指南: docs/DEPLOYMENT.md" -ForegroundColor White
    Write-Host "   - API文档: http://localhost:8000/docs" -ForegroundColor White
}

# 本地安装流程
function Install-Local {
    Write-Host "选择本地安装方式" -ForegroundColor Green
    
    Test-ExecutionPolicy
    Test-Python
    New-VirtualEnv
    Install-Dependencies
    Set-Environment
    New-Directories
    Test-Installation
    Show-NextSteps
}

# Docker安装流程
function Install-Docker {
    if (-not $script:DockerAvailable) {
        Write-Host "❌ Docker未安装，无法使用Docker方式" -ForegroundColor Red
        Write-Host "   请先安装Docker Desktop: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
        exit 1
    }
    
    Write-Host "选择Docker安装方式" -ForegroundColor Green
    
    Set-Environment
    New-Directories
    
    Write-Host "🐳 构建Docker镜像..." -ForegroundColor Yellow
    & docker build -t dmmr:latest .
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Docker镜像构建完成" -ForegroundColor Green
    }
    else {
        Write-Host "❌ Docker镜像构建失败" -ForegroundColor Red
        exit 1
    }
    
    if ($script:ComposeAvailable) {
        Write-Host "🚀 启动服务..." -ForegroundColor Yellow
        & docker-compose up -d
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ 服务启动完成" -ForegroundColor Green
            Write-Host ""
            Write-Host "🌐 服务地址：" -ForegroundColor Yellow
            Write-Host "   - API服务: http://localhost:8000" -ForegroundColor White
            Write-Host "   - API文档: http://localhost:8000/docs" -ForegroundColor White
            Write-Host "   - Neo4j: http://localhost:7474" -ForegroundColor White
        }
        else {
            Write-Host "❌ 服务启动失败" -ForegroundColor Red
            exit 1
        }
    }
    else {
        Write-Host "🚀 启动API服务..." -ForegroundColor Yellow
        & docker run -d --name dmmr-api -p 8000:8000 --env-file .env dmmr:latest
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ API服务启动完成: http://localhost:8000" -ForegroundColor Green
        }
        else {
            Write-Host "❌ API服务启动失败" -ForegroundColor Red
            exit 1
        }
    }
}

# 主安装流程
function Start-Installation {
    Write-Host "开始安装DMMR系统..." -ForegroundColor Green
    Write-Host ""
    
    # 检查环境
    Test-Docker
    
    # 根据参数选择安装方式
    if ($Local) {
        Install-Local
    }
    elseif ($Docker) {
        Install-Docker
    }
    else {
        # 交互式选择
        Write-Host "请选择安装方式：" -ForegroundColor Yellow
        Write-Host "1) 本地安装 (Python虚拟环境)" -ForegroundColor White
        if ($script:DockerAvailable) {
            Write-Host "2) Docker安装" -ForegroundColor White
        }
        Write-Host ""
        
        do {
            $choice = Read-Host "请输入选择 (1-2)"
        } while ($choice -notmatch "^[12]$")
        
        switch ($choice) {
            "1" { Install-Local }
            "2" { 
                if ($script:DockerAvailable) {
                    Install-Docker
                }
                else {
                    Write-Host "❌ Docker未安装，无法使用Docker方式" -ForegroundColor Red
                    exit 1
                }
            }
        }
    }
}

# 错误处理
trap {
    Write-Host "❌ 安装过程中出现错误: $_" -ForegroundColor Red
    exit 1
}

# 运行主函数
Start-Installation


