#!/bin/bash
# ==============================================================================
# Movie MLOps 메인 실행 스크립트
# WSL Docker 환경 - 개발용
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
    echo "   WSL Docker 기반 통합 개발 환경"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${NC}"
}

print_menu() {
    echo ""
    echo -e "${BLUE}🛠️  개발 환경 관리${NC}"
    echo "1) 전체 환경 설정 (최초 1회)"
    echo "2) 전체 서비스 시작"
    echo "3) 전체 서비스 중지"
    echo ""
    echo -e "${BLUE}🔧 개별 서비스 관리${NC}"
    echo "4) 기본 인프라 (PostgreSQL + Redis)"
    echo "5) 개발 환경 (Jupyter + API)"
    echo "6) MLOps 서비스 (MLflow + Airflow + Feast)"
    echo "7) 모니터링 (Prometheus + Grafana)"
    echo "8) 이벤트 스트리밍 (Kafka)"
    echo ""
    echo -e "${BLUE}📊 상태 확인${NC}"
    echo "9) 서비스 상태 확인"
    echo "10) 로그 확인"
    echo ""
    echo -e "${BLUE}🧪 테스트${NC}"
    echo "11) 전체 테스트 실행"
    echo "12) 개별 테스트 실행"
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
}

setup_environment() {
    echo -e "${GREEN}🚀 전체 환경 설정 시작...${NC}"
    ./scripts/setup/setup_wsl_docker.sh
}

start_all_services() {
    echo -e "${GREEN}🚀 전체 서비스 시작...${NC}"
    ./scripts/docker/start_all_services.sh
}

stop_all_services() {
    echo -e "${RED}🛑 전체 서비스 중지...${NC}"
    ./scripts/docker/stop_all_services.sh
}

start_infrastructure() {
    echo -e "${GREEN}🏗️ 기본 인프라 시작...${NC}"
    docker compose -f docker/docker-compose.postgres.yml up -d
    docker compose -f docker/docker-compose.redis.yml up -d
    echo -e "${GREEN}✅ 기본 인프라가 시작되었습니다.${NC}"
}

start_development() {
    echo -e "${GREEN}💻 개발 환경 시작...${NC}"
    docker compose -f docker/docker-compose.jupyter.yml up -d
    docker compose -f docker/docker-compose.api.yml up -d
    echo -e "${GREEN}✅ 개발 환경이 시작되었습니다.${NC}"
    echo "🔹 Jupyter: http://localhost:8888"
    echo "🔹 API 문서: http://localhost:8000/docs"
}

start_mlops() {
    echo -e "${GREEN}🤖 MLOps 서비스 시작...${NC}"
    docker compose -f docker/docker-compose.mlflow.yml up -d
    docker compose -f docker/docker-compose.airflow.yml up -d
    docker compose -f docker/docker-compose.feast.yml up -d
    echo -e "${GREEN}✅ MLOps 서비스가 시작되었습니다.${NC}"
    echo "🔹 MLflow: http://localhost:5000"
    echo "🔹 Airflow: http://localhost:8080"
}

start_monitoring() {
    echo -e "${GREEN}📊 모니터링 서비스 시작...${NC}"
    docker compose -f docker/docker-compose.monitoring.yml up -d
    echo -e "${GREEN}✅ 모니터링 서비스가 시작되었습니다.${NC}"
    echo "🔹 Grafana: http://localhost:3000"
    echo "🔹 Prometheus: http://localhost:9090"
}

start_kafka() {
    echo -e "${GREEN}📡 이벤트 스트리밍 시작...${NC}"
    docker compose -f docker/docker-compose.kafka.yml up -d
    echo -e "${GREEN}✅ Kafka가 시작되었습니다.${NC}"
    echo "🔹 Kafka UI: http://localhost:8082"
}

check_status() {
    echo -e "${BLUE}📊 서비스 상태 확인...${NC}"
    echo ""
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep movie-mlops || echo "실행 중인 서비스가 없습니다."
}

view_logs() {
    echo -e "${BLUE}📝 어떤 서비스의 로그를 확인하시겠습니까?${NC}"
    echo "1) API"
    echo "2) Jupyter"
    echo "3) MLflow"
    echo "4) Airflow"
    echo "5) PostgreSQL"
    echo "6) Redis"
    echo "7) 전체"
    read -p "선택 (1-7): " log_choice
    
    case $log_choice in
        1) docker compose -f docker/docker-compose.api.yml logs -f ;;
        2) docker compose -f docker/docker-compose.jupyter.yml logs -f ;;
        3) docker compose -f docker/docker-compose.mlflow.yml logs -f ;;
        4) docker compose -f docker/docker-compose.airflow.yml logs -f ;;
        5) docker compose -f docker/docker-compose.postgres.yml logs -f ;;
        6) docker compose -f docker/docker-compose.redis.yml logs -f ;;
        7) docker logs -f $(docker ps -q --filter "name=movie-mlops") ;;
        *) echo "잘못된 선택입니다." ;;
    esac
}

run_tests() {
    echo -e "${GREEN}🧪 전체 테스트 실행...${NC}"
    if [ -f "run_tests.sh" ]; then
        ./run_tests.sh
    else
        echo "테스트 스크립트를 찾을 수 없습니다."
    fi
}

# 메인 실행부
main() {
    print_header
    check_prerequisites
    
    while true; do
        print_menu
        read -p "선택해주세요 (0-12): " choice
        
        case $choice in
            1) setup_environment ;;
            2) start_all_services ;;
            3) stop_all_services ;;
            4) start_infrastructure ;;
            5) start_development ;;
            6) start_mlops ;;
            7) start_monitoring ;;
            8) start_kafka ;;
            9) check_status ;;
            10) view_logs ;;
            11) run_tests ;;
            12) echo "개별 테스트 기능은 추후 구현 예정입니다." ;;
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
