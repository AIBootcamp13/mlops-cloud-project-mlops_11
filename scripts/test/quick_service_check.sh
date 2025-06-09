#!/bin/bash
# ==============================================================================
# Movie MLOps 서비스 빠른 상태 확인 스크립트
# 모든 서비스의 접속 가능 여부를 빠르게 확인
# ==============================================================================

echo "⚡ Movie MLOps 서비스 빠른 상태 확인"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 서비스 목록 (이름:포트:설명)
services=(
    "MLflow:5000:ML 실험 추적"
    "Airflow:8080:워크플로우 관리"
    "API:8000:FastAPI 서버"
    "Grafana:3000:모니터링 대시보드"
    "Jupyter:8888:Jupyter Lab"
    "Feast:6566:Feature Store UI"
    "Prometheus:9090:메트릭 수집"
    "Kafka UI:8082:Kafka 관리"
    "cAdvisor:8083:컨테이너 모니터링"
    "Redis Commander:8081:Redis 관리"
    "PgAdmin:5050:PostgreSQL 관리"
)

# 색상 코드
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_service_quick() {
    local name=$1
    local port=$2
    local desc=$3
    
    printf "%-15s (%-4s): " "$name" "$port"
    
    # HTTP 응답 확인 (5초 타임아웃)
    response=$(timeout 5 curl -s -o /dev/null -w "%{http_code}" http://localhost:$port 2>/dev/null)
    
    if [[ "$response" =~ ^[2345][0-9][0-9]$ ]]; then
        printf "${GREEN}✅ 접속 가능${NC} (${response}) - $desc\n"
        return 0
    else
        # 컨테이너가 실행 중인지 확인
        container_running=$(docker ps --filter "expose=$port" --format "{{.Names}}" 2>/dev/null | head -1)
        if [ ! -z "$container_running" ]; then
            printf "${YELLOW}⚠️  컨테이너 실행 중, HTTP 응답 없음${NC} - $desc\n"
        else
            printf "${RED}❌ 접속 불가${NC} - $desc\n"
        fi
        return 1
    fi
}

# 실행 중인 컨테이너 수 확인
echo "🐳 실행 중인 Movie MLOps 컨테이너: $(docker ps --filter 'name=movie-mlops' --format '{{.Names}}' | wc -l)개"
echo ""

# 각 서비스 상태 확인
working_count=0
total_count=${#services[@]}

for service_info in "${services[@]}"; do
    IFS=':' read -r name port desc <<< "$service_info"
    if check_service_quick "$name" "$port" "$desc"; then
        ((working_count++))
    fi
done

echo ""
echo "📊 전체 상태: $working_count/$total_count 서비스 정상 작동"

# 상태에 따른 권장 사항
if [ $working_count -eq $total_count ]; then
    printf "${GREEN}🎉 모든 서비스가 정상 작동 중입니다!${NC}\n"
elif [ $working_count -gt $((total_count / 2)) ]; then
    printf "${YELLOW}⚠️  일부 서비스에 문제가 있습니다. './diagnose_service_access.sh' 실행을 권장합니다.${NC}\n"
else
    printf "${RED}🚨 많은 서비스에 문제가 있습니다. './fix_service_access.sh' 실행을 권장합니다.${NC}\n"
fi

echo ""
echo "🔧 사용 가능한 도구:"
echo "   ./diagnose_service_access.sh  - 상세 진단"
echo "   ./fix_service_access.sh       - 자동 해결 시도"
echo "   ./run_movie_mlops.sh          - 전체 시스템 관리"
