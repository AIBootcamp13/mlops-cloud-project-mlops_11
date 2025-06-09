#!/bin/bash
# ==============================================================================
# Feast + FastAPI 통합 실행 스크립트
# Docker Compose 기반으로 선택적 서비스 실행
# ==============================================================================

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

print_header() {
    echo -e "${CYAN}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "   🎬 Movie MLOps - Feast + FastAPI 실행기"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${NC}"
}

check_prerequisites() {
    # Docker 확인
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker가 설치되지 않았습니다.${NC}"
        exit 1
    fi
    
    # .env 파일 확인
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}⚠️  .env 파일이 없습니다. .env.template에서 복사합니다.${NC}"
        cp .env.template .env
    fi
}

setup_network() {
    echo -e "${BLUE}🌐 네트워크 설정 중...${NC}"
    
    if ! docker network inspect movie-mlops-network >/dev/null 2>&1; then
        echo "Docker 네트워크 생성 중..."
        docker network create movie-mlops-network
        echo "✅ 네트워크 생성 완료"
    else
        echo "✅ 네트워크 이미 존재함"
    fi
}

cleanup_containers() {
    echo -e "${YELLOW}🧹 기존 컨테이너 정리 중...${NC}"
    
    # 관련 컨테이너 중지 및 제거
    containers_to_clean=("movie-mlops-feast" "movie-mlops-api" "movie-mlops-feast-new" "movie-mlops-api-new")
    
    for container in "${containers_to_clean[@]}"; do
        if docker ps -a --format "{{.Names}}" | grep -q "^${container}$"; then
            echo "정리 중: ${container}"
            docker stop "${container}" 2>/dev/null || true
            docker rm "${container}" 2>/dev/null || true
        fi
    done
    
    echo "✅ 컨테이너 정리 완료"
}

start_infrastructure() {
    echo -e "${BLUE}🏗️ 인프라 서비스 확인 중...${NC}"
    
    # PostgreSQL 확인
    if ! docker ps --filter "name=movie-mlops-postgres" --filter "status=running" | grep -q movie-mlops-postgres; then
        echo "PostgreSQL 시작 중..."
        docker compose -f docker/docker-compose.postgres.yml up -d
        sleep 5
    else
        echo "✅ PostgreSQL 이미 실행 중"
    fi
    
    # Redis 확인
    if ! docker ps --filter "name=movie-mlops-redis" --filter "status=running" | grep -q movie-mlops-redis; then
        echo "Redis 시작 중..."
        docker compose -f docker/docker-compose.redis.yml up -d
        sleep 3
    else
        echo "✅ Redis 이미 실행 중"
    fi
}

start_feast_fastapi() {
    echo -e "${GREEN}🚀 Feast + FastAPI 시작 중...${NC}"
    
    # Docker Compose로 선택적 서비스 실행
    if [ -f "docker/stacks/docker-compose.ml-stack-fixed.yml" ]; then
        echo "수정된 ML 스택 파일 사용 중..."
        docker compose -f docker/stacks/docker-compose.ml-stack-fixed.yml \
            --project-directory . \
            up -d feast api
    else
        echo "기본 ML 스택 파일 사용 중..."
        docker compose -f docker/stacks/docker-compose.ml-stack.yml \
            --project-directory . \
            up -d feast api
    fi
    
    echo -e "${GREEN}✅ Feast + FastAPI 시작 완료!${NC}"
}

show_status() {
    echo -e "${BLUE}📊 서비스 상태 확인...${NC}"
    echo ""
    
    # 실행 중인 컨테이너 확인
    running_containers=$(docker ps --filter "name=movie-mlops" --format "{{.Names}}" | wc -l)
    
    if [ "$running_containers" -gt 0 ]; then
        echo "실행 중인 서비스:"
        docker ps --filter "name=movie-mlops" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        echo ""
        
        echo "📊 서비스 접속 정보:"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "🔹 Feast UI: http://localhost:6567/docs"
        echo "🔹 FastAPI: http://localhost:8000/docs"
        echo "🔹 PostgreSQL: localhost:5432"
        echo "🔹 Redis: localhost:6379"
        echo ""
        
        # 헬스체크
        echo "🏥 헬스체크..."
        sleep 3
        
        # Feast 확인
        if curl -s -f http://localhost:6567/docs >/dev/null 2>&1; then
            echo "✅ Feast 서비스 정상"
        else
            echo "❌ Feast 서비스 연결 실패"
        fi
        
        # FastAPI 확인
        if curl -s -f http://localhost:8000/docs >/dev/null 2>&1; then
            echo "✅ FastAPI 서비스 정상"
        else
            echo "❌ FastAPI 서비스 연결 실패"
        fi
        
    else
        echo "실행 중인 Movie MLOps 서비스가 없습니다."
    fi
}

view_logs() {
    echo -e "${BLUE}📝 서비스 로그 확인...${NC}"
    echo ""
    echo "Feast 로그:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    docker logs --tail=20 movie-mlops-feast 2>/dev/null || echo "Feast 로그를 가져올 수 없습니다."
    
    echo ""
    echo "FastAPI 로그:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    docker logs --tail=20 movie-mlops-api 2>/dev/null || echo "FastAPI 로그를 가져올 수 없습니다."
}

stop_services() {
    echo -e "${RED}🛑 서비스 중지 중...${NC}"
    
    # Docker Compose로 중지
    if [ -f "docker/stacks/docker-compose.ml-stack-fixed.yml" ]; then
        docker compose -f docker/stacks/docker-compose.ml-stack-fixed.yml \
            --project-directory . \
            stop feast api
    else
        docker compose -f docker/stacks/docker-compose.ml-stack.yml \
            --project-directory . \
            stop feast api
    fi
    
    echo -e "${GREEN}✅ 서비스 중지 완료${NC}"
}

print_menu() {
    echo ""
    echo -e "${BLUE}🛠️  메뉴${NC}"
    echo "1) Feast + FastAPI 시작"
    echo "2) 서비스 상태 확인"
    echo "3) 로그 확인"
    echo "4) 서비스 중지"
    echo "5) 컨테이너 정리"
    echo "0) 종료"
    echo ""
}

# 메인 실행부
main() {
    print_header
    check_prerequisites
    setup_network
    
    while true; do
        print_menu
        read -p "선택해주세요 (0-5): " choice
        
        case $choice in
            1)
                cleanup_containers
                start_infrastructure
                start_feast_fastapi
                show_status
                ;;
            2)
                show_status
                ;;
            3)
                view_logs
                ;;
            4)
                stop_services
                ;;
            5)
                cleanup_containers
                ;;
            0)
                echo -e "${GREEN}👋 Feast + FastAPI 실행기를 종료합니다.${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}❌ 잘못된 선택입니다. 다시 선택해주세요.${NC}"
                ;;
        esac
        
        echo ""
        read -p "계속하려면 Enter를 누르세요..."
    done
}

# 스크립트가 직접 실행될 때만 main 함수 호출
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
