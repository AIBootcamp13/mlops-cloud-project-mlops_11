#!/bin/bash
# ==============================================================================
# Movie MLOps 메인 실행 스크립트 (모듈화 버전)
# WSL Docker 환경 - 기능별 스택 관리
# 번호 2 (start_all_stacks) 기반으로 lib 구조 모듈화
# ==============================================================================

set -e

# 모듈 로드
source lib/ui/messages.sh
source lib/ui/menu.sh
source lib/core/config.sh
source lib/core/network.sh
source lib/core/docker.sh
source lib/services/database.sh
source lib/services/ml.sh
source lib/services/monitoring.sh

# ===== 번호 2 (start_all_stacks) 함수 - 4,5,6,7,8 순차 호출 버전 =====
start_all_stacks() {
    echo -e "${GREEN}🚀 모든 스택 시작...${NC}"
    
    # 기본 준비 작업 (기존 2번과 동일)
    ensure_movie_mlops_network
    cleanup_all_containers
    
    # 1단계: 인프라 스택 (4번)
    echo "🏗️ 4번: 인프라 스택 시작..."
    start_infrastructure_stack  # 직접 호출로 중복 방지
    show_infrastructure_urls
    
    # 2단계: API 스택 (5번) - 인프라 위에서 동작
    echo "💻 5번: API 스택 시작..."
    start_api_stack_all  # 직접 호출로 중복 방지
    show_api_urls
    
    # 3단계: ML 스택 (6번) - 인프라 위에서 동작
    echo "🤖 6번: ML 스택 시작..."
    start_ml_only_stack_all  # 직접 호출로 중복 방지
    show_ml_urls
    
    # 4단계: 워크플로우 스택 (7번) - 인프라 위에서 동작
    echo "🔄 7번: 워크플로우 스택 시작..."
    start_workflow_stack_all  # 직접 호출로 중복 방지
    show_workflow_urls
    
    # 5단계: 모니터링 스택 (8번) - 독립적 동작
    echo "📊 8번: 모니터링 스택 시작..."
    start_monitoring_stack_all  # 직접 호출로 중복 방지
    show_monitoring_urls
    
    # 최종 결과 출력 (기존 2번과 동일)
    echo -e "${GREEN}✅ 모든 스택이 시작되었습니다!${NC}"
    show_service_urls
}

# ===== 기존 함수들 (일부는 모듈 함수 호출로 변경) =====
stop_all_stacks() {
    echo -e "${RED}🛑 모든 스택 중지...${NC}"
    
    # 역순으로 중지
    stop_monitoring_stack
    
    # ML 스택 중지 (수정된 버전 우선 시도)
    if [ -f "docker/stacks/docker-compose.ml-stack-fixed.yml" ]; then
        docker compose -f docker/stacks/docker-compose.ml-stack-fixed.yml --project-directory . --profile development down 2>/dev/null || true
    fi
    docker compose -f docker/stacks/docker-compose.ml-stack.yml --project-directory . down 2>/dev/null || true
    
    stop_infrastructure_stack
    
    echo -e "${GREEN}✅ 모든 스택이 중지되었습니다.${NC}"
}

# ===== 새로운 분리된 스택 함수들 =====
start_infrastructure() {
    echo -e "${GREEN}🏗️ 인프라 스택 시작...${NC}"
    
    # 네트워크 확인
    ensure_movie_mlops_network
    
    # 기존 인프라 컨테이너만 제거
    cleanup_infrastructure_containers
    
    # 인프라 스택 시작
    start_infrastructure_stack
    
    # URL 출력
    show_infrastructure_urls
}

start_api_stack() {
    echo -e "${GREEN}💻 API 스택 시작...${NC}"
    
    # 네트워크 확인
    ensure_movie_mlops_network
    
    # 기존 API 컨테이너만 제거 (인프라는 유지)
    cleanup_api_containers
    
    # API 스택 시작
    start_api_stack_all
    
    # URL 출력
    show_api_urls
}

start_ml_stack() {
    echo -e "${GREEN}🤖 ML 스택 시작...${NC}"
    
    # 네트워크 확인
    ensure_movie_mlops_network
    
    # 기존 ML 컨테이너만 제거 (인프라는 유지)
    cleanup_ml_containers
    
    # ML 스택 시작
    start_ml_only_stack_all
    
    # URL 출력
    show_ml_urls
}

start_workflow_stack() {
    echo -e "${GREEN}🔄 워크플로우 스택 시작...${NC}"
    
    # 네트워크 확인
    ensure_movie_mlops_network
    
    # 기존 워크플로우 컨테이너만 제거 (인프라는 유지)
    cleanup_workflow_containers
    
    # 워크플로우 스택 시작
    start_workflow_stack_all
    
    # URL 출력
    show_workflow_urls
}

start_monitoring_stack() {
    echo -e "${GREEN}📊 모니터링 스택 시작...${NC}"
    
    # 네트워크 확인
    ensure_movie_mlops_network
    
    # 기존 모니터링 컨테이너만 제거
    cleanup_monitoring_containers
    
    # 모니터링 스택 시작
    start_monitoring_stack_all
    
    # URL 출력
    show_monitoring_urls
}

# ===== 통합 환경 함수들 =====
start_dev_environment() {
    echo -e "${GREEN}🚀 개발 환경 시작...${NC}"
    ensure_movie_mlops_network
    start_infrastructure_stack
    start_api_stack_all
    echo -e "${GREEN}✅ 개발 환경 준비 완료!${NC}"
    show_api_urls
}

start_workflow_environment() {
    echo -e "${GREEN}🚀 워크플로우 환경 시작...${NC}"
    ensure_movie_mlops_network
    start_infrastructure_stack
    start_api_stack_all
    start_workflow_stack_all
    echo -e "${GREEN}✅ 워크플로우 환경 준비 완료!${NC}"
    show_api_urls
    show_workflow_urls
}

start_ml_dev_environment() {
    echo -e "${GREEN}🚀 ML 개발 환경 시작...${NC}"
    ensure_movie_mlops_network
    start_infrastructure_stack
    start_api_stack_all
    start_ml_only_stack_all
    start_workflow_stack_all
    echo -e "${GREEN}✅ ML 개발 환경 준비 완료!${NC}"
    show_service_urls
}

# ===== 기존 테스트 및 상태 확인 함수들 (기존과 동일) =====
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
        echo "  - ML 스택: 메뉴에서 7번 선택"
        echo "  - 모니터링 스택: 메뉴에서 9번 선택"
    fi
}

view_logs() {
    print_log_menu
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

clean_containers() {
    echo -e "${YELLOW}🧹 기존 컨테이너 정리...${NC}"
    echo ""
    
    # 현재 실행 중인 movie-mlops 컨테이너 확인
    echo "현재 실행 중인 Movie MLOps 컨테이너:"
    running_containers=$(docker ps --filter "name=movie-mlops" --format "{{.Names}}" | wc -l)
    
    if [ "$running_containers" -gt 0 ]; then
        docker ps --filter "name=movie-mlops" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        echo ""
        read -p "위 컨테이너들을 모두 중지하고 제거하시겠습니까? (y/N): " confirm
        
        if [[ $confirm =~ ^[Yy]$ ]]; then
            echo "컨테이너들을 중지하고 제거합니다..."
            
            # 컨테이너 중지
            echo "1️⃣ 컨테이너 중지 중..."
            docker stop $(docker ps --filter "name=movie-mlops" -q) 2>/dev/null || true
            
            # 컨테이너 제거
            echo "2️⃣ 컨테이너 제거 중..."
            docker rm $(docker ps -aq --filter "name=movie-mlops") 2>/dev/null || true
            
            echo -e "${GREEN}✅ 모든 Movie MLOps 컨테이너가 정리되었습니다.${NC}"
        else
            echo "컨테이너 정리를 취소했습니다."
        fi
    else
        echo "실행 중인 Movie MLOps 컨테이너가 없습니다."
        
        # 중지된 컨테이너도 확인
        stopped_containers=$(docker ps -a --filter "name=movie-mlops" --format "{{.Names}}" | wc -l)
        if [ "$stopped_containers" -gt 0 ]; then
            echo ""
            echo "중지된 Movie MLOps 컨테이너:"
            docker ps -a --filter "name=movie-mlops" --format "table {{.Names}}\t{{.Status}}"
            echo ""
            read -p "중지된 컨테이너들을 제거하시겠습니까? (y/N): " confirm
            
            if [[ $confirm =~ ^[Yy]$ ]]; then
                docker rm $(docker ps -aq --filter "name=movie-mlops") 2>/dev/null || true
                echo -e "${GREEN}✅ 중지된 컨테이너들이 제거되었습니다.${NC}"
            fi
        else
            echo "정리할 컨테이너가 없습니다."
        fi
    fi
    
    # 사용하지 않는 볼륨과 네트워크 정리 옵션
    echo ""
    read -p "사용하지 않는 Docker 볼륨과 네트워크도 정리하시겠습니까? (y/N): " cleanup_system
    
    if [[ $cleanup_system =~ ^[Yy]$ ]]; then
        echo "3️⃣ 사용하지 않는 리소스 정리 중..."
        docker system prune -f
        echo -e "${GREEN}✅ Docker 시스템 정리가 완료되었습니다.${NC}"
    fi
}

# 메인 실행부
main() {
    print_header
    check_prerequisites
    
    while true; do
        print_menu
        read -p "선택해주세요 (0-15): " choice
        
        case $choice in
            1) setup_environment ;;
            2) start_all_stacks ;;
            3) stop_all_stacks ;;
            4) start_infrastructure ;;
            5) start_api_stack ;;
            6) start_ml_stack ;;
            7) start_workflow_stack ;;
            8) start_monitoring_stack ;;
            9) clean_containers ;;
            10) start_dev_environment ;;
            11) start_workflow_environment ;;
            12) start_ml_dev_environment ;;
            13) test_full_system ;;
            14) test_ml_stack ;;
            15) test_monitoring_stack ;;
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
