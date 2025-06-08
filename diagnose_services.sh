#!/bin/bash
# ==============================================================================
# Movie MLOps 서비스 상태 진단 스크립트
# ==============================================================================

echo "🔍 Movie MLOps 서비스 상태 진단 중..."
echo ""

# 1. 실행 중인 컨테이너 확인
echo "1️⃣ 실행 중인 컨테이너 상태:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker ps --filter "name=movie-mlops" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | head -20

echo ""
echo "2️⃣ 컨테이너 헬스체크 상태:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
for container in movie-mlops-api movie-mlops-mlflow movie-mlops-feast movie-mlops-airflow-webserver movie-mlops-prometheus movie-mlops-grafana movie-mlops-kafka-ui; do
    if docker ps --format "{{.Names}}" | grep -q "^${container}$"; then
        echo "✅ ${container}: 실행 중"
        # 컨테이너 로그 마지막 5줄 확인
        echo "   마지막 로그:"
        docker logs --tail=3 "${container}" 2>&1 | sed 's/^/   /'
        echo ""
    else
        echo "❌ ${container}: 실행되지 않음"
    fi
done

echo ""
echo "3️⃣ 포트 연결 테스트:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 포트 연결 테스트 함수
test_port() {
    local service=$1
    local port=$2
    local path=$3
    
    echo -n "🔌 ${service} (${port}): "
    if command -v curl &> /dev/null; then
        if timeout 3 curl -s -o /dev/null -w "%{http_code}" "http://localhost:${port}${path}" | grep -q "200\|302\|401"; then
            echo "✅ 접속 가능"
        else
            echo "❌ 접속 불가 (HTTP 에러 또는 타임아웃)"
        fi
    else
        if timeout 3 bash -c "</dev/tcp/localhost/${port}" 2>/dev/null; then
            echo "✅ 포트 열림"
        else
            echo "❌ 포트 닫힘"
        fi
    fi
}

# 주요 서비스 포트 테스트
test_port "API" "8000" "/docs"
test_port "MLflow" "5000" "/"
test_port "Feast" "6566" "/"
test_port "Airflow" "8080" "/"
test_port "Grafana" "3000" "/"
test_port "Prometheus" "9090" "/"
test_port "Kafka UI" "8082" "/"
test_port "Jupyter" "8888" "/"

echo ""
echo "4️⃣ Docker 네트워크 상태:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if docker network inspect movie-mlops-network >/dev/null 2>&1; then
    echo "✅ movie-mlops-network 존재함"
    connected_containers=$(docker network inspect movie-mlops-network --format '{{range .Containers}}{{.Name}} {{end}}' | wc -w)
    echo "   연결된 컨테이너 수: ${connected_containers}개"
else
    echo "❌ movie-mlops-network 없음"
fi

echo ""
echo "5️⃣ 리소스 사용량:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
container_ids=$(docker ps --filter "name=movie-mlops" -q)
if [ ! -z "$container_ids" ]; then
    echo "상위 CPU/메모리 사용 컨테이너:"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" $container_ids | head -6
else
    echo "실행 중인 Movie MLOps 컨테이너 없음"
fi

echo ""
echo "6️⃣ 컨테이너 재시작 횟수:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker ps --filter "name=movie-mlops" --format "table {{.Names}}\t{{.Status}}" | grep -E "(Restarting|Exited|Up.*restart)"

echo ""
echo "💡 문제 해결 제안:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. 접속 불가 서비스가 있다면:"
echo "   - 컨테이너 로그 확인: docker logs [컨테이너명]"
echo "   - 서비스 재시작: ./restart_monitoring.sh"
echo ""
echo "2. 포트가 닫혀있다면:"
echo "   - 방화벽 확인"
echo "   - WSL 포트 포워딩 확인"
echo ""
echo "3. 전체 재시작이 필요하다면:"
echo "   - ./run_movie_mlops.sh → 메뉴 3번 (중지) → 2번 (시작)"
