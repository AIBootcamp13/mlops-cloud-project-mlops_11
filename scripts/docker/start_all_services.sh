#!/bin/bash
# ==============================================================================
# 모든 MLOps 서비스 시작 스크립트
# WSL Docker 환경용
# ==============================================================================

set -e

# 색상 정의
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

# 환경 변수 로드
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "❌ .env 파일이 없습니다. 먼저 setup_wsl_docker.sh를 실행하세요."
    exit 1
fi

print_status "🚀 Movie MLOps 전체 서비스 시작..."

# 1. 기본 인프라 서비스 시작
print_status "1️⃣ 기본 인프라 서비스 시작 (PostgreSQL, Redis)..."
docker compose -f docker/docker-compose.postgres.yml up -d
docker compose -f docker/docker-compose.redis.yml up -d

# 잠시 대기 (데이터베이스 초기화 시간)
print_status "데이터베이스 초기화 대기 중... (30초)"
sleep 30

# 2. MLOps 핵심 서비스 시작
print_status "2️⃣ MLOps 핵심 서비스 시작 (MLflow, Airflow)..."
docker compose -f docker/docker-compose.mlflow.yml up -d
docker compose -f docker/docker-compose.airflow.yml up -d

# 3. 피처 스토어 시작
print_status "3️⃣ 피처 스토어 시작 (Feast)..."
docker compose -f docker/docker-compose.feast.yml up -d

# 4. API 서비스 시작
print_status "4️⃣ API 서비스 시작 (FastAPI)..."
docker compose -f docker/docker-compose.api.yml up -d

# 5. 개발 환경 시작
print_status "5️⃣ 개발 환경 시작 (Jupyter)..."
docker compose -f docker/docker-compose.jupyter.yml up -d

# 6. 모니터링 서비스 시작
print_status "6️⃣ 모니터링 서비스 시작 (Prometheus, Grafana)..."
docker compose -f docker/docker-compose.monitoring.yml up -d

# 7. 이벤트 스트리밍 서비스 시작 (선택적)
read -p "Kafka 이벤트 스트리밍 서비스를 시작하시겠습니까? (y/N): " start_kafka
if [[ $start_kafka =~ ^[Yy]$ ]]; then
    print_status "7️⃣ 이벤트 스트리밍 서비스 시작 (Kafka)..."
    docker compose -f docker/docker-compose.kafka.yml up -d
fi

print_success "🎉 모든 서비스가 시작되었습니다!"

echo ""
echo "📊 서비스 접속 정보:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔹 Jupyter Notebook: http://localhost:${JUPYTER_PORT:-8888}"
echo "   토큰: ${JUPYTER_TOKEN:-movie-mlops-jupyter}"
echo ""
echo "🔹 FastAPI 문서: http://localhost:${API_PORT:-8000}/docs"
echo "🔹 MLflow UI: http://localhost:${MLFLOW_PORT:-5000}"
echo "🔹 Airflow UI: http://localhost:${AIRFLOW_WEBSERVER_PORT:-8080}"
echo "   사용자명/비밀번호: admin/admin"
echo ""
echo "🔹 Grafana 대시보드: http://localhost:${GRAFANA_PORT:-3000}"
echo "   사용자명/비밀번호: ${GRAFANA_ADMIN_USER:-admin}/${GRAFANA_ADMIN_PASSWORD:-admin123}"
echo "🔹 Prometheus: http://localhost:${PROMETHEUS_PORT:-9090}"
echo ""
echo "🔹 PostgreSQL: localhost:${POSTGRES_PORT:-5432}"
echo "🔹 Redis: localhost:${REDIS_PORT:-6379}"
echo ""
if [[ $start_kafka =~ ^[Yy]$ ]]; then
echo "🔹 Kafka UI: http://localhost:8082"
echo "🔹 Kafka: localhost:${KAFKA_PORT:-9092}"
echo ""
fi
echo "📝 로그 확인: docker compose logs -f [서비스명]"
echo "🛑 서비스 중지: ./scripts/docker/stop_all_services.sh"
