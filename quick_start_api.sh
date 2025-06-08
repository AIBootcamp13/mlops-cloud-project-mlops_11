#!/bin/bash

# ==============================================================================
# Movie MLOps API 빠른 시작 스크립트
# ==============================================================================

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 Movie MLOps API 빠른 시작...${NC}"

# 1. Docker 네트워크 생성
echo -e "${YELLOW}1. Docker 네트워크 생성...${NC}"
if ! docker network ls | grep -q "movie-mlops-network"; then
    docker network create movie-mlops-network
    echo -e "${GREEN}✅ 네트워크 생성 완료${NC}"
else
    echo -e "${GREEN}✅ 네트워크 이미 존재${NC}"
fi

# 2. PostgreSQL 시작
echo -e "${YELLOW}2. PostgreSQL 시작...${NC}"
docker compose -f docker/docker-compose.postgres.yml up -d
echo -e "${GREEN}✅ PostgreSQL 시작됨${NC}"

# 3. Redis 시작
echo -e "${YELLOW}3. Redis 시작...${NC}"
docker compose -f docker/docker-compose.redis.yml up -d
echo -e "${GREEN}✅ Redis 시작됨${NC}"

# 4. 서비스 안정화 대기
echo -e "${YELLOW}4. 서비스 안정화 대기 (15초)...${NC}"
sleep 15

# 5. 서비스 상태 확인
echo -e "${YELLOW}5. 인프라 서비스 상태 확인...${NC}"
if docker ps --filter "name=movie-mlops-postgres" --filter "status=running" | grep -q postgres; then
    echo -e "${GREEN}✅ PostgreSQL 실행 중${NC}"
else
    echo -e "${RED}❌ PostgreSQL 실행 실패${NC}"
    exit 1
fi

if docker ps --filter "name=movie-mlops-redis" --filter "status=running" | grep -q redis; then
    echo -e "${GREEN}✅ Redis 실행 중${NC}"
else
    echo -e "${RED}❌ Redis 실행 실패${NC}"
    exit 1
fi

# 6. API 서비스 시작
echo -e "${YELLOW}6. API 서비스 시작...${NC}"
docker compose -f docker/docker-compose.api.yml up -d
echo -e "${GREEN}✅ API 서비스 시작됨${NC}"

# 7. API 서비스 대기
echo -e "${YELLOW}7. API 서비스 안정화 대기 (30초)...${NC}"
sleep 30

# 8. 최종 상태 확인
echo -e "${YELLOW}8. 서비스 상태 최종 확인...${NC}"
docker ps --filter "name=movie-mlops" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 9. 헬스체크
echo -e "\n${YELLOW}9. API 헬스체크...${NC}"
if curl -f -s http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}✅ API 서비스 정상 작동${NC}"
else
    echo -e "${RED}❌ API 서비스 응답 없음${NC}"
    echo -e "${YELLOW}로그 확인:${NC}"
    docker logs movie-mlops-api --tail=20
fi

echo -e "\n${GREEN}🎉 Movie MLOps API 시작 완료!${NC}"
echo -e "\n${BLUE}📊 접속 정보:${NC}"
echo "🔹 API 문서: http://localhost:8000/docs"
echo "🔹 API 헬스체크: http://localhost:8000/health"
echo "🔹 PostgreSQL: localhost:5432"
echo "🔹 Redis: localhost:6379"
echo "🔹 PgAdmin: http://localhost:5050"
echo "🔹 Redis Commander: http://localhost:8081"

echo -e "\n${BLUE}🧪 테스트 실행:${NC}"
echo "chmod +x ./scripts/test/test_api_integration.sh"
echo "./scripts/test/test_api_integration.sh"
