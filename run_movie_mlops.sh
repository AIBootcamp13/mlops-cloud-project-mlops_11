#!/bin/bash
# ==============================================================================
# Movie MLOps 메인 실행 스크립트 (리팩토링 버전)
# WSL Docker 환경 - 기능별 스택 관리
# ==============================================================================

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 함수 정의
print_header() {
    echo -e "${CYAN}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "   🎬 Movie MLOps Development Environment"
    echo "   WSL Docker 기반 기능별 스택 관리"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${NC}"
}

print_menu() {
    echo ""
    echo -e "${BLUE}🛠️  환경 설정 및 관리${NC}"
    echo "1) 전체 환경 설정 (최초 1회)"
    echo "2) 모든 스택 시작 (인프라 + ML + 모니터링)"
    echo "3) 모든 스택 중지"
    echo ""
    echo -e "${BLUE}📦 기능별 스택 관리${NC}"
    echo "4) 인프라 스택 (PostgreSQL + Redis)"
    echo "5) API 스택 (FastAPI + Airflow)"  
    echo "6) ML 스택 (MLflow + Feast + PyTorch + Jupyter)"
    echo "7) 모니터링 스택 (Prometheus + Grafana + Kafka)"
    echo ""
    echo -e "${BLUE}🧪 테스트 및 검증${NC}"
    echo "8) 전체 시스템 테스트"
    echo "9) ML 스택 통합 테스트"
    echo "10) 모니터링 스택 테스트"
    echo ""
    echo -e "${BLUE}📊 상태 확인${NC}"
    echo "11) 서비스 상태 확인"
    echo "12) 로그 확인"
    echo "13) 리소스 사용량 확인"
    echo ""
    echo "0) 종료"
    echo ""
}

check_prerequisites() {
    # Docker 설치 확인
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker가 설치되지 않았습니다.${NC}"
        exit 1
    fi
    
    # Docker Compose 설치 확인
    if ! command -v docker &> /dev/null || ! docker compose version &> /dev/null; then
        echo -e "${RED}❌ Docker Compose V2가 설치되지 않았습니다.${NC}"
        exit 1
    fi
    
    # WSL 환경 확인
    if ! grep -q microsoft /proc/version 2>/dev/null; then
        echo -e "${YELLOW}⚠️  WSL 환경이 아닐 수 있습니다.${NC}"
    fi
    
    # .env 파일 확인
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}⚠️  .env 파일이 없습니다. .env.template에서 복사합니다.${NC}"
        cp .env.template .env
    fi
}

setup_environment() {
    echo -e "${GREEN}🚀 전체 환경 설정 시작...${NC}"
    
    # 네트워크 생성
    if ! docker network ls | grep -q "movie-mlops-network"; then
        echo "Docker 네트워크 생성 중..."
        docker network create movie-mlops-network
    fi
    
    # 필요한 디렉토리 생성
    echo "디렉토리 구조 생성 중..."
    mkdir -p {data,logs,models,notebooks}
    mkdir -p logs/{airflow,mlflow,api,feast,postgres,redis,kafka,prometheus,grafana}
    mkdir -p data/{raw,processed,external,mlflow/artifacts,feast}
    mkdir -p models/{trained,deployed,experiments}
    
    echo -e "${GREEN}✅ 환경 설정이 완료되었습니다.${NC}"
}

start_all_stacks() {
    echo -e "${GREEN}🚀 모든 스택 시작...${NC}"
    
    # 1. 인프라 스택
    echo "1️⃣ 인프라 스택 시작 중..."
    docker compose -f docker/docker-compose.postgres.yml up -d
    docker compose -f docker/docker-compose.redis.yml up -d
    
    # 잠시 대기
    echo "인프라 서비스 안정화 대기 중... (15초)"
    sleep 15
    
    # 2. ML 스택
    echo "2️⃣ ML 스택 시작 중..."
    docker compose -f docker/stacks/docker-compose.ml-stack.yml up -d
    
    # 3. 모니터링 스택
    echo "3️⃣ 모니터링 스택 시작 중..."
    docker compose -f docker/stacks/docker-compose.monitoring.yml up -d
    
    echo -e "${GREEN}✅ 모든 스택이 시작되었습니다!${NC}"
    show_service_urls
}

stop_all_stacks() {
    echo -e "${RED}🛑 모든 스택 중지...${NC}"
    
    # 역순으로 중지
    docker compose -f docker/stacks/docker-compose.monitoring.yml down
    docker compose -f docker/stacks/docker-compose.ml-stack.yml down
    docker compose -f docker/docker-compose.redis.yml down
    docker compose -f docker/docker-compose.postgres.yml down
    
    echo -e "${GREEN}✅ 모든 스택이 중지되었습니다.${NC}"
}

start_infrastructure() {
    echo -e "${GREEN}🏗️ 인프라 스택 시작...${NC}"
    docker compose -f docker/docker-compose.postgres.yml up -d
    docker compose -f docker/docker-compose.redis.yml up -d
    echo -e "${GREEN}✅ 인프라 스택이 시작되었습니다.${NC}"
    echo "🔹 PostgreSQL: localhost:5432"
    echo "🔹 Redis: localhost:6379"
}

start_api_stack() {
    echo -e "${GREEN}💻 API 스택 시작...${NC}"
    docker compose -f docker/docker-compose.api.yml up -d
    docker compose -f docker/docker-compose.airflow.yml up -d
    echo -e "${GREEN}✅ API 스택이 시작되었습니다.${NC}"
    echo "🔹 FastAPI: http://localhost:8000/docs"
    echo "🔹 Airflow: http://localhost:8080 (admin/admin)"
}

start_ml_stack() {
    echo -e "${GREEN}🤖 ML 스택 시작...${NC}"
    docker compose -f docker/stacks/docker-compose.ml-stack.yml up -d
    echo -e "${GREEN}✅ ML 스택이 시작되었습니다.${NC}"
    echo "🔹 MLflow: http://localhost:5000"
    echo "🔹 Feast: http://localhost:6566"
    echo "🔹 Jupyter: http://localhost:8888"
    echo "🔹 FastAPI: http://localhost:8000/docs"
    echo "🔹 Airflow: http://localhost:8080"
}

start_monitoring_stack() {
    echo -e "${GREEN}📊 모니터링 스택 시작...${NC}"
    docker compose -f docker/stacks/docker-compose.monitoring.yml up -d
    echo -e "${GREEN}✅ 모니터링 스택이 시작되었습니다.${NC}"
    echo "🔹 Prometheus: http://localhost:9090"
    echo "🔹 Grafana: http://localhost:3000 (admin/admin123)"
    echo "🔹 Kafka UI: http://localhost:8082"
    echo "🔹 AlertManager: http://localhost:9093"
}

test_full_system() {
    echo -e "${GREEN}🧪 전체 시스템 테스트 실행...${NC}"
    
    # 통합 테스트 순서대로 실행
    echo "1. API 기본 테스트..."
    if [ -f "scripts/test/test_api.sh" ]; then
        ./scripts/test/test_api.sh
    fi
    
    echo "2. ML 스택 테스트..."
    if [ -f "scripts/ml/test_ml_stack.sh" ]; then
        chmod +x scripts/ml/test_ml_stack.sh
        ./scripts/ml/test_ml_stack.sh
    fi
    
    echo "3. 모니터링 스택 테스트..."
    if [ -f "scripts/monitoring/test_monitoring_stack.sh" ]; then
        chmod +x scripts/monitoring/test_monitoring_stack.sh
        ./scripts/monitoring/test_monitoring_stack.sh
    fi
    
    echo -e "${GREEN}✅ 전체 시스템 테스트 완료!${NC}"
}

test_ml_stack() {
    echo -e "${GREEN}🧪 ML 스택 통합 테스트 실행...${NC}"
    if [ -f "scripts/ml/test_ml_stack.sh" ]; then
        chmod +x scripts/ml/test_ml_stack.sh
        ./scripts/ml/test_ml_stack.sh
    else
        echo -e "${RED}❌ ML 테스트 스크립트를 찾을 수 없습니다.${NC}"
    fi
}

test_monitoring_stack() {
    echo -e "${GREEN}🧪 모니터링 스택 테스트 실행...${NC}"
    if [ -f "scripts/monitoring/test_monitoring_stack.sh" ]; then
        chmod +x scripts/monitoring/test_monitoring_stack.sh
        ./scripts/monitoring/test_monitoring_stack.sh
    else
        echo -e "${RED}❌ 모니터링 테스트 스크립트를 찾을 수 없습니다.${NC}"
    fi
}

check_status() {
    echo -e "${BLUE}📊 서비스 상태 확인...${NC}"
    echo ""
    
    # 실행 중인 컨테이너 확인
    running_containers=$(docker ps --filter "name=movie-mlops" --format "{{.Names}}" | wc -l)
    
    if [ "$running_containers" -gt 0 ]; then
        echo "실행 중인 서비스 ($running_containers 개):"
        docker ps --filter "name=movie-mlops" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        echo ""
        show_service_urls
    else
        echo "실행 중인 Movie MLOps 서비스가 없습니다."
        echo ""
        echo "서비스 시작 방법:"
        echo "  - 전체 스택: 메뉴에서 2번 선택"
        echo "  - ML 스택: 메뉴에서 6번 선택"
        echo "  - 모니터링 스택: 메뉴에서 7번 선택"
    fi
}

show_service_urls() {
    echo "📊 서비스 접속 정보:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "🔹 개발 환경:"
    echo "   Jupyter Lab: http://localhost:8888"
    echo "   API 문서: http://localhost:8000/docs"
    echo ""
    echo "🔹 ML 도구:"
    echo "   MLflow UI: http://localhost:5000"
    echo "   Feast UI: http://localhost:6566"
    echo ""
    echo "🔹 워크플로우:"
    echo "   Airflow UI: http://localhost:8080 (admin/admin)"
    echo ""
    echo "🔹 모니터링:"
    echo "   Grafana: http://localhost:3000 (admin/admin123)"
    echo "   Prometheus: http://localhost:9090"
    echo "   Kafka UI: http://localhost:8082"
    echo ""
    echo "🔹 데이터베이스:"
    echo "   PostgreSQL: localhost:5432"
    echo "   Redis: localhost:6379"
}

view_logs() {
    echo -e "${BLUE}📝 어떤 서비스의 로그를 확인하시겠습니까?${NC}"
    echo "1) API"
    echo "2) MLflow"
    echo "3) Feast"
    echo "4) Airflow"
    echo "5) Prometheus"
    echo "6) Grafana"
    echo "7) Kafka"
    echo "8) PostgreSQL"
    echo "9) Redis"
    echo "10) 전체 (최근 50줄)"
    read -p "선택 (1-10): " log_choice
    
    case $log_choice in
        1) docker compose -f docker/docker-compose.api.yml logs -f ;;
        2) docker logs -f movie-mlops-mlflow ;;
        3) docker logs -f movie-mlops-feast ;;
        4) docker compose -f docker/docker-compose.airflow.yml logs -f ;;
        5) docker logs -f movie-mlops-prometheus ;;
        6) docker logs -f movie-mlops-grafana ;;
        7) docker logs -f movie-mlops-kafka ;;
        8) docker compose -f docker/docker-compose.postgres.yml logs -f ;;
        9) docker compose -f docker/docker-compose.redis.yml logs -f ;;
        10) docker logs --tail=50 $(docker ps --filter "name=movie-mlops" -q) ;;
        *) echo "잘못된 선택입니다." ;;
    esac
}

check_resources() {
    echo -e "${BLUE}📊 시스템 리소스 사용량 확인...${NC}"
    echo ""
    
    # Docker 컨테이너 리소스 사용량
    echo "=== Docker 컨테이너 리소스 사용량 ==="
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" $(docker ps --filter "name=movie-mlops" -q) 2>/dev/null || echo "리소스 정보를 가져올 수 없습니다."
    
    echo ""
    echo "=== 시스템 전체 정보 ==="
    
    # 시스템 리소스 (사용 가능한 경우)
    if command -v free &> /dev/null; then
        echo "메모리 사용량:"
        free -h
    fi
    
    echo ""
    if command -v df &> /dev/null; then
        echo "디스크 사용량:"
        df -h / 2>/dev/null || echo "디스크 정보를 가져올 수 없습니다."
    fi
    
    echo ""
    echo "Docker 시스템 사용량:"
    docker system df 2>/dev/null || echo "Docker 시스템 정보를 가져올 수 없습니다."
}

# 메인 실행부
main() {
    print_header
    check_prerequisites
    
    while true; do
        print_menu
        read -p "선택해주세요 (0-13): " choice
        
        case $choice in
            1) setup_environment ;;
            2) start_all_stacks ;;
            3) stop_all_stacks ;;
            4) start_infrastructure ;;
            5) start_api_stack ;;
            6) start_ml_stack ;;
            7) start_monitoring_stack ;;
            8) test_full_system ;;
            9) test_ml_stack ;;
            10) test_monitoring_stack ;;
            11) check_status ;;
            12) view_logs ;;
            13) check_resources ;;
            0) echo -e "${GREEN}👋 Movie MLOps 개발 환경을 종료합니다.${NC}"; exit 0 ;;
            *) echo -e "${RED}❌ 잘못된 선택입니다. 다시 선택해주세요.${NC}" ;;
        esac
        
        echo ""
        read -p "계속하려면 Enter를 누르세요..."
    done
}

# 스크립트가 직접 실행될 때만 main 함수 호출
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
