#!/bin/bash
# ==============================================================================
# WSL Docker 환경 정리 및 최적화 스크립트
# venv 잔재물 정리 및 Docker 환경 준비
# ==============================================================================

set -e

echo "🧹 WSL Docker 환경 정리 중..."

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

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

print_header() {
    echo -e "${CYAN}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "   🐳 WSL Docker 환경 정리 및 최적화"
    echo "   Movie MLOps 프로젝트 - Docker 전용 환경"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${NC}"
}

# 현재 상태 확인
check_environment() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📊 현재 환경 상태 확인"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # WSL 환경 확인
    if grep -q microsoft /proc/version 2>/dev/null; then
        print_success "WSL 환경 감지됨"
        WSL_ENV=true
    else
        print_warning "WSL 환경이 아닐 수 있습니다"
        WSL_ENV=false
    fi
    
    # Docker 설치 확인
    if command -v docker &> /dev/null; then
        docker_version=$(docker --version 2>&1)
        print_success "Docker 발견: $docker_version"
        DOCKER_EXISTS=true
    else
        print_error "Docker가 설치되지 않음"
        DOCKER_EXISTS=false
    fi
    
    # Docker Compose 확인
    if command -v docker-compose &> /dev/null; then
        compose_version=$(docker-compose --version 2>&1)
        print_success "Docker Compose 발견: $compose_version"
        COMPOSE_EXISTS=true
    else
        print_error "Docker Compose가 설치되지 않음"
        COMPOSE_EXISTS=false
    fi
    
    # venv 잔재물 확인
    if [ -d "venv" ]; then
        print_warning "venv 폴더 발견 - 제거 필요"
        VENV_EXISTS=true
    elif [ -d "venv_backup_to_delete" ]; then
        print_warning "venv 백업 폴더 발견 - 수동 삭제 필요"
        VENV_BACKUP_EXISTS=true
    else
        print_success "venv 가상환경 없음 (정상)"
        VENV_EXISTS=false
        VENV_BACKUP_EXISTS=false
    fi
    
    # .env 파일 확인
    if [ -f ".env" ]; then
        print_success ".env 파일 존재"
        ENV_EXISTS=true
    else
        print_warning ".env 파일 없음"
        ENV_EXISTS=false
    fi
    
    # Python 전역 설치 확인 (정보 목적)
    if command -v python3 &> /dev/null; then
        python_version=$(python3 --version 2>&1)
        print_status "시스템 Python: $python_version"
    fi
}

# venv 잔재물 정리
cleanup_venv_remnants() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🗑️ venv 잔재물 정리"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # venv 폴더 제거
    if [ -d "venv" ]; then
        print_status "venv 폴더 제거 중..."
        rm -rf venv
        print_success "venv 폴더 제거 완료"
    fi
    
    # Python 캐시 정리
    print_status "Python 캐시 정리 중..."
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    find . -name "*.pyo" -delete 2>/dev/null || true
    print_success "Python 캐시 정리 완료"
    
    # pip 캐시 정리
    if command -v pip3 &> /dev/null; then
        print_status "pip 캐시 정리 중..."
        pip3 cache purge 2>/dev/null || true
        print_success "pip 캐시 정리 완료"
    fi
    
    # venv 백업 폴더 안내
    if [ -d "venv_backup_to_delete" ]; then
        print_warning "venv_backup_to_delete 폴더가 남아있습니다."
        print_warning "다음 명령으로 수동 삭제하세요:"
        echo "  rm -rf venv_backup_to_delete"
        echo "  또는 Windows 탐색기에서 삭제하세요."
    fi
}

# Docker 환경 확인 및 설정
setup_docker_environment() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🐳 Docker 환경 설정"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    if [ "$DOCKER_EXISTS" = false ]; then
        print_error "Docker가 설치되지 않았습니다."
        print_warning "다음 명령으로 Docker를 설치하세요:"
        echo "  curl -fsSL https://get.docker.com -o get-docker.sh"
        echo "  sudo sh get-docker.sh"
        echo "  sudo usermod -aG docker \$USER"
        return 1
    fi
    
    if [ "$COMPOSE_EXISTS" = false ]; then
        print_error "Docker Compose가 설치되지 않았습니다."
        print_warning "Docker Desktop을 설치하거나 다음 명령을 실행하세요:"
        echo "  sudo apt-get update && sudo apt-get install docker-compose-plugin"
        return 1
    fi
    
    # Docker 서비스 상태 확인
    if ! sudo systemctl is-active --quiet docker 2>/dev/null; then
        print_status "Docker 서비스 시작 중..."
        sudo systemctl start docker 2>/dev/null || print_warning "Docker 서비스를 수동으로 시작하세요"
    fi
    
    # Docker 네트워크 확인
    if ! docker network ls | grep -q "movie-mlops-network"; then
        print_status "Docker 네트워크 생성 중..."
        docker network create movie-mlops-network 2>/dev/null || print_warning "네트워크 생성 실패 (이미 존재할 수 있음)"
    fi
    
    print_success "Docker 환경 준비 완료"
}

# .env 파일 설정
setup_env_file() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "⚙️ 환경 변수 설정"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.template" ]; then
            print_status ".env 파일 생성 중..."
            cp .env.template .env
            print_success ".env 파일이 생성되었습니다"
            print_warning "필요한 환경 변수를 설정하세요:"
            echo "  - TMDB_API_KEY"
            echo "  - SECRET_KEY"
            echo "  - 데이터베이스 비밀번호들"
        else
            print_error ".env.template 파일이 없습니다"
        fi
    else
        print_success ".env 파일이 이미 존재합니다"
    fi
}

# Docker 이미지 정리
cleanup_docker() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🧹 Docker 이미지 정리 (선택사항)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    read -p "사용하지 않는 Docker 이미지를 정리하시겠습니까? (y/N): " cleanup_confirm
    if [[ $cleanup_confirm =~ ^[Yy]$ ]]; then
        print_status "Docker 이미지 정리 중..."
        docker system prune -f 2>/dev/null || print_warning "Docker 정리 실패"
        print_success "Docker 이미지 정리 완료"
    fi
}

# 디렉터리 구조 확인
check_directory_structure() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📁 디렉터리 구조 확인"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # 필요한 디렉터리 생성
    required_dirs=(
        "data/raw"
        "data/processed" 
        "data/external"
        "data/mlflow/artifacts"
        "data/feast"
        "logs/airflow"
        "logs/mlflow"
        "logs/api"
        "logs/postgres"
        "logs/redis"
        "models/trained"
        "models/deployed"
        "models/experiments"
        "notebooks"
        "feast_repo"
    )
    
    for dir in "${required_dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            print_status "생성: $dir"
        fi
    done
    
    print_success "디렉터리 구조 확인 완료"
}

# 최종 상태 확인
final_status() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ 정리 완료 상태"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    echo "✅ venv 가상환경 정리 완료"
    echo "✅ Python 캐시 정리 완료"
    echo "✅ Docker 환경 준비 완료"
    echo "✅ WSL Docker 환경 최적화 완료"
    
    echo ""
    echo "🎯 다음 단계:"
    echo "1. Docker 서비스 시작: ./run_movie_mlops.sh"
    echo "2. 개별 서비스 테스트: docker-compose -f docker/docker-compose.*.yml up -d"
    echo "3. 전체 테스트 실행: ./run_tests.sh"
    
    # venv 백업 폴더 경고
    if [ -d "venv_backup_to_delete" ]; then
        echo ""
        print_warning "⚠️  수동 작업 필요:"
        echo "   venv_backup_to_delete 폴더를 삭제하세요:"
        echo "   rm -rf venv_backup_to_delete"
    fi
    
    echo ""
    print_success "🎉 WSL Docker 환경 정리가 완료되었습니다!"
}

# 메인 실행 함수
main() {
    print_header
    
    # 환경 확인
    check_environment
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🎯 실행할 작업"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "1. ❌ venv 가상환경 잔재물 정리"
    echo "2. 🧹 Python 캐시 정리"
    echo "3. 🐳 Docker 환경 설정 확인"
    echo "4. ⚙️ .env 파일 설정 확인"
    echo "5. 📁 디렉터리 구조 확인"
    echo "6. 🗑️ Docker 정리 (선택사항)"
    
    echo ""
    read -p "위 작업을 진행하시겠습니까? (y/N): " confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        echo "작업이 취소되었습니다."
        exit 0
    fi
    
    # 작업 실행
    cleanup_venv_remnants
    setup_docker_environment
    setup_env_file
    check_directory_structure
    cleanup_docker
    final_status
}

# 스크립트가 직접 실행될 때만 main 함수 호출
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
