# Movie MLOps Feature Store Prerequisites Setup - PowerShell Version
param(
    [switch]$Force,
    [switch]$Verbose
)

Write-Host ""
Write-Host "====================================================================" -ForegroundColor Yellow
Write-Host "🚀 Movie MLOps Feature Store Prerequisites Setup" -ForegroundColor Yellow
Write-Host "====================================================================" -ForegroundColor Yellow
Write-Host ""

# Helper function for colored output
function Write-Status {
    param([string]$Message, [string]$Type = "Info")
    switch ($Type) {
        "Success" { Write-Host "✅ $Message" -ForegroundColor Green }
        "Error" { Write-Host "❌ $Message" -ForegroundColor Red }
        "Warning" { Write-Host "⚠️ $Message" -ForegroundColor Yellow }
        "Info" { Write-Host "ℹ️ $Message" -ForegroundColor Cyan }
        default { Write-Host $Message }
    }
}

# 1. Check current directory
Write-Host "📁 1. Checking project directory..." -ForegroundColor Blue
if (-not (Test-Path "docker-compose.yml")) {
    Write-Status "docker-compose.yml not found. Please run from project root." "Error"
    Write-Host "Current location: $(Get-Location)" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Status "Project directory confirmed: $(Get-Location)" "Success"

# 2. Check Docker environment
Write-Host ""
Write-Host "🐳 2. Checking Docker environment..." -ForegroundColor Blue
try {
    $dockerVersion = docker --version 2>$null
    if ($LASTEXITCODE -ne 0) { throw "Docker command failed" }
    
    $composeVersion = docker-compose --version 2>$null
    if ($LASTEXITCODE -ne 0) { throw "Docker Compose command failed" }
    
    Write-Status "Docker environment confirmed" "Success"
    Write-Host "   $dockerVersion" -ForegroundColor Gray
    Write-Host "   $composeVersion" -ForegroundColor Gray
}
catch {
    Write-Status "Docker not installed or not running." "Error"
    Write-Status "Please install Docker Desktop and start it." "Error"
    Read-Host "Press Enter to exit"
    exit 1
}

# 3. Prepare environment files
Write-Host ""
Write-Host "🔧 3. Preparing environment configuration..." -ForegroundColor Blue
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.template") {
        Copy-Item ".env.template" ".env"
        Write-Status ".env file created from template." "Success"
        Write-Status "Please review .env file if needed." "Warning"
    } else {
        Write-Status ".env.template file not found." "Error"
        Read-Host "Press Enter to exit"
        exit 1
    }
} else {
    Write-Status ".env file already exists." "Success"
}

# 4. Create required directories
Write-Host ""
Write-Host "📁 4. Creating required directories..." -ForegroundColor Blue
$directories = @("data", "data\feature_store", "data\test", "logs", "reports")
foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}
Write-Status "Required directories created" "Success"

# 5. Clean existing environment (optional)
Write-Host ""
Write-Host "🧹 5. Cleaning existing environment..." -ForegroundColor Blue
if ($Force) {
    $cleanup = "y"
} else {
    $cleanup = Read-Host "Clean existing Docker environment? Data may be lost. (y/N)"
}

if ($cleanup -eq "y" -or $cleanup -eq "Y") {
    Write-Host "Cleaning existing environment..."
    docker-compose down -v 2>$null | Out-Null
    docker system prune -f 2>$null | Out-Null
    Write-Status "Existing environment cleaned" "Success"
} else {
    Write-Status "Existing environment cleanup skipped" "Info"
}

# 6. Build Docker images
Write-Host ""
Write-Host "🔨 6. Building Docker images..." -ForegroundColor Blue
Write-Host "This may take several minutes..." -ForegroundColor Yellow

try {
    if ($Verbose) {
        docker-compose build dev
    } else {
        docker-compose build dev | Out-Null
    }
    
    if ($LASTEXITCODE -ne 0) { throw "Docker build failed" }
    Write-Status "Docker image build completed" "Success"
}
catch {
    Write-Status "Docker image build failed" "Error"
    Write-Host ""
    Write-Host "Solutions:" -ForegroundColor Yellow
    Write-Host "1. Check internet connection"
    Write-Host "2. Restart Docker Desktop"
    Write-Host "3. Check firewall/security software"
    Write-Host "4. Try: docker-compose build --no-cache dev"
    Read-Host "Press Enter to exit"
    exit 1
}

# 7. Start services
Write-Host ""
Write-Host "🚀 7. Starting basic services..." -ForegroundColor Blue

Write-Host "Starting PostgreSQL..."
docker-compose up -d postgres | Out-Null
Start-Sleep -Seconds 10

Write-Host "Starting Redis..."
docker-compose up -d redis | Out-Null
Start-Sleep -Seconds 5

Write-Host "Starting development environment..."
docker-compose up -d dev | Out-Null
Start-Sleep -Seconds 10

# 8. Check service status
Write-Host ""
Write-Host "📊 8. Checking service status..." -ForegroundColor Blue
docker-compose ps

# 9. Health checks
Write-Host ""
Write-Host "🔍 9. Performing basic health checks..." -ForegroundColor Blue

Write-Host "Testing PostgreSQL connection..."
$pgResult = docker-compose exec -T postgres pg_isready -U mlops_user -d mlops 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Status "PostgreSQL is healthy" "Success"
} else {
    Write-Status "PostgreSQL connection failed" "Error"
    $healthIssues = $true
}

Write-Host "Testing Redis connection..."
$redisResult = docker-compose exec -T redis redis-cli ping 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Status "Redis is healthy" "Success"
} else {
    Write-Status "Redis connection failed" "Error"
    $healthIssues = $true
}

Write-Host "Testing Python environment..."
$pythonResult = docker-compose exec -T dev python --version 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Status "Python environment is healthy" "Success"
} else {
    Write-Status "Python environment issue" "Error"
    $healthIssues = $true
}

# 10. Comprehensive validation
Write-Host ""
Write-Host "🧪 10. Comprehensive prerequisite validation..." -ForegroundColor Blue

$validationScript = @"
import sys
from pathlib import Path

print('🎯 Comprehensive Prerequisites Validation')
print('=' * 50)

checks = {}
failed = False

# PostgreSQL test
try:
    import psycopg2
    conn = psycopg2.connect(host='postgres', database='mlops', user='mlops_user', password='mlops_password')
    conn.close()
    print('✅ PostgreSQL connection: SUCCESS')
    checks['PostgreSQL'] = True
except Exception as e:
    print(f'❌ PostgreSQL connection: FAILED ({e})')
    checks['PostgreSQL'] = False
    failed = True

# Redis test
try:
    import redis
    r = redis.Redis(host='redis', port=6379)
    r.ping()
    print('✅ Redis connection: SUCCESS')
    checks['Redis'] = True
except Exception as e:
    print(f'❌ Redis connection: FAILED ({e})')
    checks['Redis'] = False
    failed = True

# Python environment test
if sys.version_info >= (3, 8):
    print(f'✅ Python environment: SUCCESS ({sys.version.split()[0]})')
    checks['Python'] = True
else:
    print(f'❌ Python environment: VERSION TOO OLD ({sys.version.split()[0]})')
    checks['Python'] = False
    failed = True

# Essential packages test
essential_packages = ['redis', 'psycopg2', 'pandas', 'numpy', 'fastapi']
missing = []
for pkg in essential_packages:
    try:
        __import__(pkg)
    except ImportError:
        missing.append(pkg)

if not missing:
    print('✅ Essential packages: ALL INSTALLED')
    checks['Packages'] = True
else:
    print(f'❌ Essential packages: MISSING {missing}')
    checks['Packages'] = False
    failed = True

# Data directory test
try:
    test_file = Path('/app/data/test_setup.tmp')
    test_file.write_text('test')
    test_file.unlink()
    print('✅ Data directory: READ/WRITE OK')
    checks['DataDir'] = True
except Exception as e:
    print(f'❌ Data directory: PERMISSION ISSUE ({e})')
    checks['DataDir'] = False
    failed = True

print('=' * 50)

passed = sum(checks.values())
total = len(checks)
success_rate = passed / total * 100

print(f'📊 Prerequisites Result: {passed}/{total} passed ({success_rate:.1f}%)')

if success_rate == 100:
    print('🎉 SUCCESS: All prerequisites completed!')
    sys.exit(0)
else:
    print('❌ ERROR: Some issues found in prerequisites.')
    sys.exit(1)
"@

try {
    docker-compose exec -T dev python -c $validationScript
    $validationSuccess = ($LASTEXITCODE -eq 0)
}
catch {
    $validationSuccess = $false
}

# Final results
Write-Host ""
if ($validationSuccess) {
    Write-Host "====================================================================" -ForegroundColor Green
    Write-Host "🎉 SUCCESS: Prerequisites Setup Complete!" -ForegroundColor Green
    Write-Host "====================================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "✅ All prerequisites have been successfully completed." -ForegroundColor Green
    Write-Host ""
    Write-Host "📋 Next Steps:" -ForegroundColor Cyan
    Write-Host "   1. Follow 2.1-environment-setup-testing.md for detailed testing"
    Write-Host "   2. Enter container: docker-compose exec dev bash"
    Write-Host "   3. Run test commands from the guide"
    Write-Host ""
    Write-Host "🔗 Useful Commands:" -ForegroundColor Cyan
    Write-Host "   - Check service status: docker-compose ps"
    Write-Host "   - View logs: docker-compose logs -f dev"
    Write-Host "   - Stop services: docker-compose down"
} else {
    Write-Host "====================================================================" -ForegroundColor Red
    Write-Host "❌ ERROR: Prerequisites Setup Issues Found" -ForegroundColor Red
    Write-Host "====================================================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "🔧 Troubleshooting:" -ForegroundColor Yellow
    Write-Host "1. Check logs: docker-compose logs dev"
    Write-Host "2. Restart services: docker-compose restart"
    Write-Host "3. Full restart: docker-compose down; docker-compose up -d dev redis postgres"
    Write-Host "4. Rebuild images: docker-compose build --no-cache dev"
    Write-Host ""
    Write-Host "For persistent issues:" -ForegroundColor Yellow
    Write-Host "- Restart Docker Desktop"
    Write-Host "- Restart system"
    Write-Host "- Check firewall/security software"
}

Write-Host ""
Read-Host "Press Enter to continue"
