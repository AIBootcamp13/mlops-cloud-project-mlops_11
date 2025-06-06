#!/bin/bash

# Movie MLOps Feature Store Prerequisites Setup - WSL/Linux Version
set -e

echo ""
echo "===================================================================="
echo "🚀 Movie MLOps Feature Store Prerequisites Setup (WSL/Linux)"
echo "===================================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Helper functions
success() {
    echo -e "${GREEN}✅ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

info() {
    echo -e "${CYAN}ℹ️ $1${NC}"
}

# 1. Check current directory
echo -e "${BLUE}📁 1. Checking project directory...${NC}"
if [ ! -f "docker-compose.yml" ]; then
    error "docker-compose.yml not found. Please run from project root."
    echo "Current location: $(pwd)"
    exit 1
fi
success "Project directory confirmed: $(pwd)"

# 2. Check Docker environment
echo ""
echo -e "${BLUE}🐳 2. Checking Docker environment...${NC}"
if ! command -v docker &> /dev/null; then
    error "Docker not installed or not in PATH."
    echo "Please install Docker and ensure it's running."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    error "Docker Compose not installed or not in PATH."
    echo "Please install Docker Compose."
    exit 1
fi

# Test Docker daemon
if ! docker info &> /dev/null; then
    error "Docker daemon not running or not accessible."
    echo "Please start Docker Desktop or ensure Docker daemon is running."
    exit 1
fi

success "Docker environment confirmed"
docker --version
docker-compose --version

# 3. Prepare environment files
echo ""
echo -e "${BLUE}🔧 3. Preparing environment configuration...${NC}"
if [ ! -f ".env" ]; then
    if [ -f ".env.template" ]; then
        cp ".env.template" ".env"
        success ".env file created from template."
        warning "Please review .env file if needed."
    else
        error ".env.template file not found."
        exit 1
    fi
else
    success ".env file already exists."
fi

# 4. Create required directories
echo ""
echo -e "${BLUE}📁 4. Creating required directories...${NC}"
mkdir -p data/{feature_store,test,raw,processed} logs reports
success "Required directories created"

# 5. Fix file permissions (important for WSL)
echo ""
echo -e "${BLUE}🔐 5. Fixing file permissions...${NC}"
chmod -R 755 data logs reports 2>/dev/null || true
success "File permissions fixed"

# 6. Clean existing environment (optional)
echo ""
echo -e "${BLUE}🧹 6. Cleaning existing environment...${NC}"
read -p "Clean existing Docker environment? Data may be lost. (y/N): " cleanup
if [[ $cleanup =~ ^[Yy]$ ]]; then
    echo "Cleaning existing environment..."
    docker-compose down -v 2>/dev/null || true
    docker system prune -f >/dev/null 2>&1 || true
    success "Existing environment cleaned"
else
    info "Existing environment cleanup skipped"
fi

# 7. Build Docker images
echo ""
echo -e "${BLUE}🔨 7. Building Docker images...${NC}"
echo "This may take several minutes..."

if docker-compose build dev; then
    success "Docker image build completed"
else
    error "Docker image build failed"
    echo ""
    echo "Solutions:"
    echo "1. Check internet connection"
    echo "2. Restart Docker Desktop"
    echo "3. Check firewall/security software"
    echo "4. Try: docker-compose build --no-cache dev"
    exit 1
fi

# 8. Start services
echo ""
echo -e "${BLUE}🚀 8. Starting basic services...${NC}"

echo "Starting PostgreSQL..."
docker-compose up -d postgres
sleep 10

echo "Starting Redis..."
docker-compose up -d redis
sleep 5

echo "Starting development environment..."
docker-compose up -d dev
sleep 10

# 9. Check service status
echo ""
echo -e "${BLUE}📊 9. Checking service status...${NC}"
docker-compose ps

# 10. Health checks
echo ""
echo -e "${BLUE}🔍 10. Performing basic health checks...${NC}"

echo "Testing PostgreSQL connection..."
if docker-compose exec -T postgres pg_isready -U mlops_user -d mlops >/dev/null 2>&1; then
    success "PostgreSQL is healthy"
else
    error "PostgreSQL connection failed"
    HEALTH_ISSUES=1
fi

echo "Testing Redis connection..."
if docker-compose exec -T redis redis-cli ping >/dev/null 2>&1; then
    success "Redis is healthy"
else
    error "Redis connection failed"
    HEALTH_ISSUES=1
fi

echo "Testing Python environment..."
if docker-compose exec -T dev python --version >/dev/null 2>&1; then
    success "Python environment is healthy"
else
    error "Python environment issue"
    HEALTH_ISSUES=1
fi

# 11. Comprehensive validation
echo ""
echo -e "${BLUE}🧪 11. Comprehensive prerequisite validation...${NC}"

validation_script='
import sys
from pathlib import Path

print("🎯 Comprehensive Prerequisites Validation")
print("=" * 50)

checks = {}
failed = False

# PostgreSQL test
try:
    import psycopg2
    conn = psycopg2.connect(host="postgres", database="mlops", user="mlops_user", password="mlops_password")
    conn.close()
    print("✅ PostgreSQL connection: SUCCESS")
    checks["PostgreSQL"] = True
except Exception as e:
    print(f"❌ PostgreSQL connection: FAILED ({e})")
    checks["PostgreSQL"] = False
    failed = True

# Redis test
try:
    import redis
    r = redis.Redis(host="redis", port=6379)
    r.ping()
    print("✅ Redis connection: SUCCESS")
    checks["Redis"] = True
except Exception as e:
    print(f"❌ Redis connection: FAILED ({e})")
    checks["Redis"] = False
    failed = True

# Python environment test
if sys.version_info >= (3, 8):
    print(f"✅ Python environment: SUCCESS ({sys.version.split()[0]})")
    checks["Python"] = True
else:
    print(f"❌ Python environment: VERSION TOO OLD ({sys.version.split()[0]})")
    checks["Python"] = False
    failed = True

# Essential packages test
essential_packages = ["redis", "psycopg2", "pandas", "numpy", "fastapi"]
missing = []
for pkg in essential_packages:
    try:
        __import__(pkg)
    except ImportError:
        missing.append(pkg)

if not missing:
    print("✅ Essential packages: ALL INSTALLED")
    checks["Packages"] = True
else:
    print(f"❌ Essential packages: MISSING {missing}")
    checks["Packages"] = False
    failed = True

# Data directory test
try:
    test_file = Path("/app/data/test_setup.tmp")
    test_file.write_text("test")
    test_file.unlink()
    print("✅ Data directory: READ/WRITE OK")
    checks["DataDir"] = True
except Exception as e:
    print(f"❌ Data directory: PERMISSION ISSUE ({e})")
    checks["DataDir"] = False
    failed = True

print("=" * 50)

passed = sum(checks.values())
total = len(checks)
success_rate = passed / total * 100

print(f"📊 Prerequisites Result: {passed}/{total} passed ({success_rate:.1f}%)")

if success_rate == 100:
    print("🎉 SUCCESS: All prerequisites completed!")
    sys.exit(0)
else:
    print("❌ ERROR: Some issues found in prerequisites.")
    sys.exit(1)
'

if docker-compose exec -T dev python -c "$validation_script"; then
    VALIDATION_SUCCESS=true
else
    VALIDATION_SUCCESS=false
fi

# Final results
echo ""
if [ "$VALIDATION_SUCCESS" = "true" ]; then
    echo -e "${GREEN}====================================================================${NC}"
    echo -e "${GREEN}🎉 SUCCESS: Prerequisites Setup Complete!${NC}"
    echo -e "${GREEN}====================================================================${NC}"
    echo ""
    echo -e "${GREEN}✅ All prerequisites have been successfully completed.${NC}"
    echo ""
    echo -e "${CYAN}📋 Next Steps:${NC}"
    echo "   1. Follow 2.1-environment-setup-testing.md for detailed testing"
    echo "   2. Enter container: docker-compose exec dev bash"
    echo "   3. Run test commands from the guide"
    echo ""
    echo -e "${CYAN}🔗 Useful Commands:${NC}"
    echo "   - Check service status: docker-compose ps"
    echo "   - View logs: docker-compose logs -f dev"
    echo "   - Stop services: docker-compose down"
else
    echo -e "${RED}====================================================================${NC}"
    echo -e "${RED}❌ ERROR: Prerequisites Setup Issues Found${NC}"
    echo -e "${RED}====================================================================${NC}"
    echo ""
    echo -e "${YELLOW}🔧 Troubleshooting:${NC}"
    echo "1. Check logs: docker-compose logs dev"
    echo "2. Restart services: docker-compose restart"
    echo "3. Full restart: docker-compose down && docker-compose up -d dev redis postgres"
    echo "4. Rebuild images: docker-compose build --no-cache dev"
    echo ""
    echo -e "${YELLOW}For persistent issues:${NC}"
    echo "- Restart Docker Desktop"
    echo "- Check Docker Desktop WSL2 integration"
    echo "- Restart WSL: wsl --shutdown && wsl"
    echo "- Check firewall/security software"
fi

echo ""
echo "Press Enter to continue..."
read
