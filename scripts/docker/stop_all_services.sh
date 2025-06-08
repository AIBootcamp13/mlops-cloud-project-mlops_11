#!/bin/bash
# ==============================================================================
# 모든 MLOps 서비스 중지 스크립트
# WSL Docker 환경용
# ==============================================================================

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

print_status "🛑 Movie MLOps 전체 서비스 중지..."

# 모든 Docker Compose 서비스 중지
services=(
    "docker/docker-compose.kafka.yml"
    "docker/docker-compose.monitoring.yml"
    "docker/docker-compose.jupyter.yml"
    "docker/docker-compose.api.yml"
    "docker/docker-compose.feast.yml"
    "docker/docker-compose.airflow.yml"
    "docker/docker-compose.mlflow.yml"
    "docker/docker-compose.pytorch.yml"
    "docker/docker-compose.redis.yml"
    "docker/docker-compose.postgres.yml"
)

for service in "${services[@]}"; do
    if [ -f "$service" ]; then
        print_status "중지 중: $service"
        docker compose -f "$service" down
    fi
done

# 옵션: 볼륨도 함께 삭제
read -p "데이터 볼륨도 함께 삭제하시겠습니까? (데이터가 모두 삭제됩니다) (y/N): " remove_volumes
if [[ $remove_volumes =~ ^[Yy]$ ]]; then
    print_warning "모든 데이터 볼륨을 삭제합니다..."
    for service in "${services[@]}"; do
        if [ -f "$service" ]; then
            docker compose -f "$service" down -v
        fi
    done
    print_warning "모든 데이터가 삭제되었습니다."
fi

# 사용하지 않는 Docker 리소스 정리
read -p "사용하지 않는 Docker 이미지와 네트워크를 정리하시겠습니까? (y/N): " cleanup_docker
if [[ $cleanup_docker =~ ^[Yy]$ ]]; then
    print_status "Docker 리소스 정리 중..."
    docker system prune -f
    print_success "Docker 리소스 정리가 완료되었습니다."
fi

print_success "🎉 모든 서비스가 중지되었습니다!"

echo ""
echo "📝 참고사항:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔹 서비스 재시작: ./scripts/docker/start_all_services.sh"
echo "🔹 개별 서비스 시작: docker compose -f docker/docker-compose.[서비스].yml up -d"
echo "🔹 로그 확인: docker compose -f docker/docker-compose.[서비스].yml logs -f"
