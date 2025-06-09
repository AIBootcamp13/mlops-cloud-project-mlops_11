#!/bin/bash

# ==============================================================================
# Movie MLOps API 로컬 실행 스크립트
# Docker 없이 로컬에서 FastAPI 실행
# ==============================================================================

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 Movie MLOps API 로컬 실행...${NC}"

# 1. Python 가상환경 확인
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Python 가상환경 생성 중...${NC}"
    python3 -m venv venv
fi

echo -e "${YELLOW}Python 가상환경 활성화...${NC}"
source venv/bin/activate

# 2. 의존성 설치
echo -e "${YELLOW}Python 의존성 설치...${NC}"
pip install --upgrade pip
pip install -r requirements/base.txt
pip install -r requirements/api.txt

# 3. 환경 변수 설정
export PYTHONPATH=$(pwd)
export ENVIRONMENT=development
export DEBUG=true
export SECRET_KEY=your-super-secret-key-change-this-in-production-please
export ALGORITHM=HS256
export ACCESS_TOKEN_EXPIRE_MINUTES=30

# PostgreSQL/Redis가 Docker에서 실행 중이므로 localhost로 연결
export DATABASE_URL=postgresql://postgres:postgres123@localhost:5432/postgres
export REDIS_URL=redis://localhost:6379/0

export TMDB_API_KEY=88a297cdbe780782194a5cc6a9d86ec1
export TMDB_BASE_URL=https://api.themoviedb.org/3

export LOG_LEVEL=INFO
export LOG_FORMAT=json

# 4. API 서버 시작
echo -e "${GREEN}✅ FastAPI 서버 시작...${NC}"
echo -e "${BLUE}접속 URL: http://localhost:8000${NC}"
echo -e "${BLUE}API 문서: http://localhost:8000/docs${NC}"
echo -e "${YELLOW}Ctrl+C로 종료${NC}"

cd src
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
