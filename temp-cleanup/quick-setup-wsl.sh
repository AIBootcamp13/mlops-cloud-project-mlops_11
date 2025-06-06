#!/bin/bash

# Quick WSL Docker Compose v2 Setup for Movie MLOps
set -e

echo "🚀 Movie MLOps Quick Setup (Docker Compose v2)"
echo "=============================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

success() { echo -e "${GREEN}✅ $1${NC}"; }
error() { echo -e "${RED}❌ $1${NC}"; }
warning() { echo -e "${YELLOW}⚠️ $1${NC}"; }

# Check environment
echo "📋 Checking environment..."
if [ ! -f "docker-compose.yml" ]; then
    error "Run from project root directory"
    exit 1
fi

if ! docker info &> /dev/null; then
    error "Docker not accessible"
    exit 1
fi

if ! docker compose version &> /dev/null; then
    error "Docker Compose v2 not available"
    exit 1
fi

success "Environment check passed"

# Setup
echo ""
echo "🔧 Setting up environment..."

# Create .env if needed
if [ ! -f ".env" ]; then
    cp .env.template .env
    success ".env file created"
fi

# Create directories
mkdir -p data/{feature_store,test,raw,processed} logs reports
success "Directories created"

# Build image
echo ""
echo "🔨 Building Docker image..."
if docker compose build dev; then
    success "Image build completed"
else
    error "Image build failed"
    exit 1
fi

# Start services
echo ""
echo "🚀 Starting services..."
docker compose up -d postgres
echo "Waiting for PostgreSQL..."
sleep 15

docker compose up -d redis
echo "Waiting for Redis..."
sleep 5

docker compose up -d dev
echo "Waiting for dev environment..."
sleep 10

# Check status
echo ""
echo "📊 Service status:"
docker compose ps

# Test connections
echo ""
echo "🧪 Testing connections..."
if docker compose exec -T dev python -c "
import redis, psycopg2
try:
    r = redis.Redis(host='redis', port=6379)
    r.ping()
    print('✅ Redis: OK')
except Exception as e:
    print(f'❌ Redis: {e}')
    exit(1)

try:
    conn = psycopg2.connect(host='postgres', database='mlops', user='mlops_user', password='mlops_password')
    conn.close()
    print('✅ PostgreSQL: OK')
except Exception as e:
    print(f'❌ PostgreSQL: {e}')
    exit(1)

print('🎉 All tests passed!')
"; then
    echo ""
    success "🎉 Setup completed successfully!"
    echo ""
    echo "Next steps:"
    echo "  1. Enter container: docker compose exec dev bash"
    echo "  2. Follow 2.1-environment-setup-testing.md"
    echo ""
    echo "Useful commands:"
    echo "  - Status: docker compose ps"
    echo "  - Logs: docker compose logs -f dev"
    echo "  - Stop: docker compose down"
else
    error "Connection tests failed"
    echo "Check logs: docker compose logs dev"
    exit 1
fi
