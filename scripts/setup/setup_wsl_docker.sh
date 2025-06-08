#!/bin/bash
# ==============================================================================
# WSL Docker 환경 설정 스크립트
# 영화 MLOps 프로젝트 초기 설정
# ==============================================================================

set -e

echo "🚀 Movie MLOps WSL Docker 환경 설정 시작..."

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 함수 정의
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

# .env 파일 확인 및 생성
print_status ".env 파일 확인 중..."
if [ ! -f ".env" ]; then
    print_warning ".env 파일이 없습니다. .env.template에서 복사합니다."
    cp .env.template .env
    print_success ".env 파일이 생성되었습니다. 필요한 설정을 수정해주세요."
else
    print_success ".env 파일이 존재합니다."
fi

# Docker 네트워크 생성
print_status "Docker 네트워크 확인 중..."
if ! docker network ls | grep -q "movie-mlops-network"; then
    print_status "movie-mlops-network 생성 중..."
    docker network create movie-mlops-network
    print_success "Docker 네트워크가 생성되었습니다."
else
    print_success "Docker 네트워크가 이미 존재합니다."
fi

# 필요한 디렉토리 생성
print_status "필요한 디렉토리 생성 중..."
mkdir -p {data,logs,models,notebooks,feast_repo}
mkdir -p logs/{airflow,mlflow,api,feast,postgres,redis,kafka,prometheus,grafana}
mkdir -p data/{raw,processed,external,mlflow/artifacts,feast}
mkdir -p models/{trained,deployed,experiments}

print_success "디렉토리 구조가 생성되었습니다."

# Docker 이미지 빌드
print_status "Docker 이미지 빌드 준비..."
print_warning "다음 명령으로 개별 서비스를 실행할 수 있습니다:"
echo ""
echo "기본 인프라:"
echo "  docker-compose -f docker/docker-compose.postgres.yml up -d"
echo "  docker-compose -f docker/docker-compose.redis.yml up -d"
echo ""
echo "개발 환경:"
echo "  docker-compose -f docker/docker-compose.jupyter.yml up -d"
echo "  docker-compose -f docker/docker-compose.api.yml up -d"
echo ""
echo "MLOps 서비스:"
echo "  docker-compose -f docker/docker-compose.mlflow.yml up -d"
echo "  docker-compose -f docker/docker-compose.airflow.yml up -d"
echo "  docker-compose -f docker/docker-compose.feast.yml up -d"
echo ""
echo "모니터링:"
echo "  docker-compose -f docker/docker-compose.monitoring.yml up -d"
echo ""
echo "이벤트 스트리밍:"
echo "  docker-compose -f docker/docker-compose.kafka.yml up -d"
echo ""
echo "전체 실행:"
echo "  ./scripts/start_all_services.sh"

print_success "WSL Docker 환경 설정이 완료되었습니다!"
print_warning "다음 단계:"
print_warning "1. .env 파일에서 필요한 환경 변수를 설정하세요"
print_warning "2. TMDB_API_KEY 등 외부 API 키를 설정하세요"
print_warning "3. 필요한 서비스를 개별적으로 또는 전체적으로 시작하세요"
