#!/bin/bash

# ==============================================================================
# Movie MLOps API 간단 실행 (Python 직접 실행)
# ==============================================================================

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 Movie MLOps API 간단 실행...${NC}"

# 1. Python 설치 확인
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    echo -e "${RED}❌ Python이 설치되지 않았습니다.${NC}"
    echo "다음 명령어로 Python을 설치하세요:"
    echo "sudo apt update && sudo apt install python3 python3-pip python3-venv"
    exit 1
fi

echo -e "${GREEN}✅ Python 발견: $(which $PYTHON_CMD)${NC}"

# 2. 필수 패키지 설치 (시스템 레벨)
echo -e "${YELLOW}필수 패키지 설치...${NC}"
$PYTHON_CMD -m pip install --user --upgrade pip
$PYTHON_CMD -m pip install --user fastapi uvicorn requests numpy pandas

# 3. 환경 변수 설정
export PYTHONPATH=$(pwd)
export ENVIRONMENT=development
export DEBUG=true
export SECRET_KEY=your-super-secret-key-change-this-in-production-please

# PostgreSQL/Redis 연결 설정 (Docker 서비스용)
export DATABASE_URL=postgresql://postgres:postgres123@localhost:5432/postgres
export REDIS_URL=redis://localhost:6379/0

export TMDB_API_KEY=88a297cdbe780782194a5cc6a9d86ec1
export TMDB_BASE_URL=https://api.themoviedb.org/3

# 4. PostgreSQL과 Redis 시작 (필요한 경우)
echo -e "${YELLOW}인프라 서비스 확인...${NC}"
if ! docker ps | grep -q movie-mlops-postgres; then
    echo "PostgreSQL 시작..."
    docker compose -f docker/docker-compose.postgres.yml up -d
fi

if ! docker ps | grep -q movie-mlops-redis; then
    echo "Redis 시작..."
    docker compose -f docker/docker-compose.redis.yml up -d
fi

echo "서비스 안정화 대기 (10초)..."
sleep 10

# 5. API 서버 시작
echo -e "${GREEN}✅ FastAPI 서버 시작...${NC}"
echo -e "${BLUE}접속 URL: http://localhost:8000${NC}"
echo -e "${BLUE}API 문서: http://localhost:8000/docs${NC}"
echo -e "${YELLOW}Ctrl+C로 종료${NC}"

cd src
$PYTHON_CMD -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
