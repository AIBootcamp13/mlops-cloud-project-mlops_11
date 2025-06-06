@echo off
setlocal enabledelayedexpansion

echo.
echo ====================================================================
echo Movie MLOps Feature Store Prerequisites Setup
echo ====================================================================
echo.

REM 1. Check current directory
echo 1. Checking project directory...
if not exist "docker-compose.yml" (
    echo ERROR: docker-compose.yml not found. Please run from project root.
    echo Current location: %CD%
    pause
    exit /b 1
)
echo SUCCESS: Project directory confirmed: %CD%

REM 2. Check Docker environment
echo.
echo 2. Checking Docker environment...
docker --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: Docker not installed or not running.
    echo Please install Docker Desktop and start it.
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: Docker Compose not installed.
    pause
    exit /b 1
)

echo SUCCESS: Docker environment confirmed
docker --version
docker-compose --version

REM 3. Prepare environment files
echo.
echo 3. Preparing environment configuration...
if not exist ".env" (
    if exist ".env.template" (
        copy ".env.template" ".env" >nul
        echo SUCCESS: .env file created from template.
        echo WARNING: Please review .env file if needed.
    ) else (
        echo ERROR: .env.template file not found.
        pause
        exit /b 1
    )
) else (
    echo SUCCESS: .env file already exists.
)

REM 4. Create required directories
echo.
echo 4. Creating required directories...
if not exist "data" mkdir data
if not exist "data\feature_store" mkdir data\feature_store
if not exist "data\test" mkdir data\test
if not exist "logs" mkdir logs
if not exist "reports" mkdir reports
echo SUCCESS: Required directories created

REM 5. Clean existing environment (optional)
echo.
echo 5. Cleaning existing environment...
set /p cleanup="Clean existing Docker environment? Data may be lost. (y/N): "
if /i "!cleanup!"=="y" (
    echo Cleaning existing environment...
    docker-compose down -v 2>nul
    docker system prune -f >nul 2>&1
    echo SUCCESS: Existing environment cleaned
) else (
    echo SKIPPED: Existing environment cleanup
)

REM 6. Build Docker images
echo.
echo 6. Building Docker images...
echo This may take several minutes...
docker-compose build dev
if %ERRORLEVEL% neq 0 (
    echo ERROR: Docker image build failed
    echo.
    echo Solutions:
    echo 1. Check internet connection
    echo 2. Restart Docker Desktop
    echo 3. Check firewall/security software
    echo 4. Try: docker-compose build --no-cache dev
    pause
    exit /b 1
)
echo SUCCESS: Docker image build completed

REM 7. Start services
echo.
echo 7. Starting basic services...

echo Starting PostgreSQL...
docker-compose up -d postgres
timeout /t 10 /nobreak >nul

echo Starting Redis...
docker-compose up -d redis
timeout /t 5 /nobreak >nul

echo Starting development environment...
docker-compose up -d dev
timeout /t 10 /nobreak >nul

REM 8. Check service status
echo.
echo 8. Checking service status...
docker-compose ps

REM 9. Health checks
echo.
echo 9. Performing basic health checks...

echo Testing PostgreSQL connection...
docker-compose exec -T postgres pg_isready -U mlops_user -d mlops >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo SUCCESS: PostgreSQL is healthy
) else (
    echo ERROR: PostgreSQL connection failed
    set HEALTH_ISSUES=1
)

echo Testing Redis connection...
docker-compose exec -T redis redis-cli ping >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo SUCCESS: Redis is healthy
) else (
    echo ERROR: Redis connection failed
    set HEALTH_ISSUES=1
)

echo Testing Python environment...
docker-compose exec -T dev python --version >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo SUCCESS: Python environment is healthy
) else (
    echo ERROR: Python environment issue
    set HEALTH_ISSUES=1
)

REM 10. Comprehensive validation
echo.
echo 10. Comprehensive prerequisite validation...
docker-compose exec -T dev python -c "
import sys
from pathlib import Path

print('Comprehensive Prerequisites Validation')
print('=' * 50)

checks = {}
failed = False

# PostgreSQL test
try:
    import psycopg2
    conn = psycopg2.connect(host='postgres', database='mlops', user='mlops_user', password='mlops_password')
    conn.close()
    print('SUCCESS: PostgreSQL connection')
    checks['PostgreSQL'] = True
except Exception as e:
    print(f'ERROR: PostgreSQL connection failed ({e})')
    checks['PostgreSQL'] = False
    failed = True

# Redis test
try:
    import redis
    r = redis.Redis(host='redis', port=6379)
    r.ping()
    print('SUCCESS: Redis connection')
    checks['Redis'] = True
except Exception as e:
    print(f'ERROR: Redis connection failed ({e})')
    checks['Redis'] = False
    failed = True

# Python environment test
if sys.version_info >= (3, 8):
    print(f'SUCCESS: Python environment {sys.version.split()[0]}')
    checks['Python'] = True
else:
    print(f'ERROR: Python version insufficient ({sys.version.split()[0]})')
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
    print('SUCCESS: All essential packages installed')
    checks['Packages'] = True
else:
    print(f'ERROR: Missing packages {missing}')
    checks['Packages'] = False
    failed = True

# Data directory test
try:
    test_file = Path('/app/data/test_setup.tmp')
    test_file.write_text('test')
    test_file.unlink()
    print('SUCCESS: Data directory read/write permissions')
    checks['DataDir'] = True
except Exception as e:
    print(f'ERROR: Data directory permission issue ({e})')
    checks['DataDir'] = False
    failed = True

print('=' * 50)

passed = sum(checks.values())
total = len(checks)
success_rate = passed / total * 100

print(f'Prerequisites Result: {passed}/{total} passed ({success_rate:.1f}%%)')

if success_rate == 100:
    print('SUCCESS: All prerequisites completed!')
    sys.exit(0)
else:
    print('ERROR: Some issues found in prerequisites.')
    sys.exit(1)
"

if %ERRORLEVEL% equ 0 (
    echo.
    echo ====================================================================
    echo SUCCESS: Prerequisites Setup Complete!
    echo ====================================================================
    echo.
    echo All prerequisites have been successfully completed.
    echo.
    echo Next Steps:
    echo    1. Follow 2.1-environment-setup-testing.md for detailed testing
    echo    2. Enter container: docker-compose exec dev bash
    echo    3. Run test commands from the guide
    echo.
    echo Useful Commands:
    echo    - Check service status: docker-compose ps
    echo    - View logs: docker-compose logs -f dev
    echo    - Stop services: docker-compose down
    echo.
) else (
    echo.
    echo ====================================================================
    echo ERROR: Prerequisites Setup Issues Found
    echo ====================================================================
    echo.
    echo Troubleshooting:
    echo 1. Check logs: docker-compose logs dev
    echo 2. Restart services: docker-compose restart
    echo 3. Full restart: docker-compose down ^&^& docker-compose up -d dev redis postgres
    echo 4. Rebuild images: docker-compose build --no-cache dev
    echo.
    echo For persistent issues:
    echo - Restart Docker Desktop
    echo - Restart system
    echo - Check firewall/security software
    echo.
)

echo Press any key to continue...
pause >nul
