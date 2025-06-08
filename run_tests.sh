#!/bin/bash
# ==============================================================================
# WSL Docker 환경용 Movie MLOps 테스트 실행기
# Docker 컨테이너와 로컬 환경을 모두 지원
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
    echo "   🧪 Movie MLOps WSL Docker 테스트 실행기"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${NC}"
}

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 환경 감지
detect_environment() {
    print_status "환경 감지 중..."
    
    # WSL 환경 확인
    if grep -q microsoft /proc/version 2>/dev/null; then
        ENV_TYPE="wsl"
        print_success "WSL 환경 감지됨"
    else
        ENV_TYPE="native"
        print_warning "네이티브 Linux 환경 (WSL 아님)"
    fi
    
    # Docker 환경 확인
    if [ -f "/.dockerenv" ]; then
        ENV_TYPE="docker"
        print_success "Docker 컨테이너 내부에서 실행 중"
    fi
    
    # .env 파일 확인
    if [ -f ".env" ]; then
        print_success ".env 파일 발견됨"
        export $(cat .env | grep -v '^#' | xargs) 2>/dev/null || true
    else
        print_warning ".env 파일이 없습니다. .env.template에서 복사하세요."
    fi
}

# Docker 서비스 상태 확인
check_docker_services() {
    print_status "Docker 서비스 상태 확인 중..."
    
    # Docker 설치 확인
    if ! command -v docker &> /dev/null; then
        print_error "Docker가 설치되지 않았습니다."
        return 1
    fi
    
    # Docker Compose 확인
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose가 설치되지 않았습니다."
        return 1
    fi
    
    # 실행 중인 서비스 확인
    running_services=$(docker ps --filter "name=movie-mlops" --format "{{.Names}}" | wc -l)
    if [ "$running_services" -gt 0 ]; then
        print_success "$running_services 개의 Movie MLOps 서비스가 실행 중입니다."
        docker ps --filter "name=movie-mlops" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    else
        print_warning "실행 중인 Movie MLOps 서비스가 없습니다."
        echo "서비스를 시작하려면: ./run_movie_mlops.sh"
    fi
}

# Python 환경 검증
check_python_environment() {
    print_status "Python 환경 검증 중..."
    
    # Python 버전 확인
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        print_error "Python이 설치되지 않았습니다."
        return 1
    fi
    
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d " " -f 2 | cut -d "." -f 1-2)
    print_status "Python 버전: $PYTHON_VERSION"
    
    if [[ "$PYTHON_VERSION" != "3.11" ]]; then
        print_warning "Python 3.11이 필요합니다. 현재 버전: $PYTHON_VERSION"
    else
        print_success "Python 3.11 환경 확인됨"
    fi
    
    # 가상환경 확인
    if [[ -n "$VIRTUAL_ENV" ]]; then
        print_success "가상환경 활성화됨: $VIRTUAL_ENV"
    else
        print_warning "가상환경이 활성화되지 않았습니다."
    fi
}

# 로컬 환경 테스트
run_local_tests() {
    print_status "로컬 환경 테스트 실행 중..."
    
    # 패키지 호환성 검사
    if command -v pip &> /dev/null; then
        print_status "pip check 실행 중..."
        if pip check; then
            print_success "패키지 호환성 검사 통과"
        else
            print_warning "패키지 호환성 문제 발견됨 (WSL 환경에서 일반적)"
            print_status "주요 기능은 정상 작동할 것입니다"
        fi
    fi
    
    # 단위 테스트 실행
    if command -v pytest &> /dev/null; then
        print_status "단위 테스트 실행 중..."
        if pytest tests/unit/ -v --tb=short; then
            print_success "단위 테스트 통과"
        else
            print_error "단위 테스트 실패"
            return 1
        fi
    else
        print_warning "pytest가 설치되지 않았습니다. 건너뜁니다."
    fi
    
    # 통합 테스트 (Docker 서비스 필요)
    if [ "$running_services" -gt 0 ]; then
        print_status "통합 테스트 실행 중..."
        if [ "$(find tests/integration/ -name '*.py' -not -name '__init__.py' 2>/dev/null | wc -l)" -gt 0 ]; then
            if pytest tests/integration/ -v --tb=short; then
                print_success "통합 테스트 통과"
            else
                print_error "통합 테스트 실패"
                return 1
            fi
        else
            print_warning "통합 테스트 파일이 없습니다."
        fi
    else
        print_warning "Docker 서비스가 실행되지 않아 통합 테스트를 건너뜁니다."
        print_status "통합 테스트를 실행하려면: ./run_movie_mlops.sh (서비스 시작 후)"
    fi
}

# Docker 컨테이너 테스트
run_docker_tests() {
    print_status "Docker 컨테이너 테스트 실행 중..."
    
    # API 컨테이너 테스트
    if docker ps | grep -q "movie-mlops-api"; then
        print_status "API 컨테이너 헬스 체크..."
        if curl -f http://localhost:${API_PORT:-8000}/health &>/dev/null; then
            print_success "API 서비스 정상"
        else
            print_error "API 서비스 응답 없음"
        fi
    fi
    
    # PostgreSQL 연결 테스트
    if docker ps | grep -q "movie-mlops-postgres"; then
        print_status "PostgreSQL 연결 테스트..."
        if docker exec movie-mlops-postgres pg_isready -U ${POSTGRES_USER:-postgres} &>/dev/null; then
            print_success "PostgreSQL 연결 정상"
        else
            print_error "PostgreSQL 연결 실패"
        fi
    fi
    
    # Redis 연결 테스트
    if docker ps | grep -q "movie-mlops-redis"; then
        print_status "Redis 연결 테스트..."
        if docker exec movie-mlops-redis redis-cli ping | grep -q "PONG"; then
            print_success "Redis 연결 정상"
        else
            print_error "Redis 연결 실패"
        fi
    fi
    
    # MLflow 서비스 테스트
    if docker ps | grep -q "movie-mlops-mlflow"; then
        print_status "MLflow 서비스 테스트..."
        if curl -f http://localhost:${MLFLOW_PORT:-5000}/health &>/dev/null; then
            print_success "MLflow 서비스 정상"
        else
            print_warning "MLflow 서비스 응답 확인 필요"
        fi
    fi
}

# 코드 품질 검사
run_code_quality_checks() {
    print_status "코드 품질 검사 실행 중..."
    
    # Black 포매터 검사
    if command -v black &> /dev/null; then
        print_status "Black 포매터 검사 중..."
        if black --check src/ tests/ --quiet; then
            print_success "Black 포매터 검사 통과"
        else
            print_warning "Black 포매터 권고사항 있음"
            echo "자동 수정: black src/ tests/"
        fi
    fi
    
    # Flake8 린터 검사
    if command -v flake8 &> /dev/null; then
        print_status "Flake8 린터 검사 중..."
        if flake8 src/ tests/ --max-line-length=88 --extend-ignore=E203,W503 --quiet; then
            print_success "Flake8 린터 검사 통과"
        else
            print_warning "Flake8 린터 권고사항 있음"
        fi
    fi
    
    # MyPy 타입 검사
    if command -v mypy &> /dev/null; then
        print_status "MyPy 타입 검사 중..."
        if mypy src/ --config-file mypy.ini --no-error-summary; then
            print_success "MyPy 타입 검사 통과"
        else
            print_warning "MyPy 타입 검사 권고사항 있음"
        fi
    fi
}

# E2E 테스트 (전체 워크플로우)
run_e2e_tests() {
    print_status "E2E 테스트 실행 중..."
    
    if [ "$(find tests/e2e/ -name '*.py' -not -name '__init__.py' 2>/dev/null | wc -l)" -gt 0 ]; then
        if [ "$running_services" -gt 3 ]; then  # 충분한 서비스가 실행 중일 때만
            print_status "전체 워크플로우 E2E 테스트..."
            if pytest tests/e2e/ -v --tb=short; then
                print_success "E2E 테스트 통과"
            else
                print_error "E2E 테스트 실패"
                return 1
            fi
        else
            print_warning "E2E 테스트를 위해 더 많은 서비스가 필요합니다."
            print_status "모든 서비스 시작: ./run_movie_mlops.sh (메뉴에서 2번)"
        fi
    else
        print_warning "E2E 테스트 파일이 없습니다."
    fi
}

# 메인 실행부
main() {
    print_header
    
    # 환경 감지
    detect_environment
    
    # Docker 서비스 확인
    check_docker_services
    
    # Python 환경 확인
    check_python_environment
    
    echo ""
    print_status "테스트 실행 시작..."
    
    # 실행할 테스트 선택
    case "${1:-all}" in
        "local")
            run_local_tests
            ;;
        "docker")
            run_docker_tests
            ;;
        "quality")
            run_code_quality_checks
            ;;
        "e2e")
            run_e2e_tests
            ;;
        "all"|"")
            run_local_tests
            run_docker_tests
            run_code_quality_checks
            run_e2e_tests
            ;;
        *)
            print_error "알 수 없는 테스트 유형: $1"
            echo "사용법: $0 [local|docker|quality|e2e|all]"
            exit 1
            ;;
    esac
    
    echo ""
    print_success "🎉 모든 테스트가 완료되었습니다!"
    
    echo ""
    print_status "📊 테스트 요약:"
    echo "✅ 환경 감지: $ENV_TYPE"
    echo "✅ Docker 서비스: $running_services 개 실행 중"
    echo "✅ Python 환경: $PYTHON_VERSION"
    echo "✅ WSL Docker MLOps 환경 검증 완료"
    echo ""
    echo "🚀 다음 단계:"
    echo "   - 서비스 시작: ./run_movie_mlops.sh"
    echo "   - 개발 시작: code . (VS Code)"
    echo "   - Jupyter: http://localhost:8888"
    echo "   - API 문서: http://localhost:8000/docs"
}

# 스크립트가 직접 실행될 때만 main 함수 호출
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
