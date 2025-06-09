#!/bin/bash
# ==============================================================================
# Movie MLOps 서비스 접속 문제 진단 스크립트
# 크롬에서 접속이 안 되는 서비스들 문제 해결
# ==============================================================================

echo "🔍 Movie MLOps 서비스 접속 문제 진단 중..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo "📦 Docker 컨테이너 상태 확인..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker ps --filter "name=movie-mlops" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "🌐 문제 포트들 상세 진단..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

check_service() {
    local service=$1
    local port=$2
    local container=$3
    
    echo ""
    echo "🔹 ${service} (포트 ${port}) 진단:"
    
    # 1. 컨테이너 상태 확인
    if docker ps --filter "name=${container}" --format "{{.Status}}" | grep -q "Up"; then
        echo "   ✅ 컨테이너 실행 중"
        
        # 2. 컨테이너 내부 헬스체크
        container_id=$(docker ps --filter "name=${container}" --format "{{.ID}}")
        if [ ! -z "$container_id" ]; then
            echo "   🔍 컨테이너 로그 (최근 5줄):"
            docker logs ${container} --tail=5 2>/dev/null | sed 's/^/      /'
        fi
        
    else
        echo "   ❌ 컨테이너 중지됨 또는 없음"
        return 1
    fi
    
    # 3. 포트 바인딩 확인 (Windows 호환)
    echo -n "   포트 바인딩: "
    if netstat -an 2>/dev/null | grep -q ":${port} " || ss -tuln 2>/dev/null | grep -q ":${port} "; then
        echo "✅ 바인딩됨"
    else
        echo "❌ 바인딩 안됨"
        return 1
    fi
    
    # 4. HTTP 응답 테스트
    echo -n "   HTTP 응답: "
    response=$(timeout 10 curl -s -o /dev/null -w "%{http_code}" http://localhost:${port} 2>/dev/null)
    if [[ "$response" =~ ^[2345][0-9][0-9]$ ]]; then
        echo "✅ 응답함 (${response})"
    else
        echo "❌ 응답 없음 (${response:-타임아웃})"
        
        # 5. 컨테이너 내부에서 직접 테스트
        echo "   🔍 컨테이너 내부 테스트 중..."
        if docker exec ${container} curl -s -o /dev/null -w "%{http_code}" http://localhost:${port} 2>/dev/null; then
            internal_response=$(docker exec ${container} curl -s -o /dev/null -w "%{http_code}" http://localhost:${port} 2>/dev/null)
            echo "   내부 응답: ${internal_response} (포트 매핑 문제 가능성)"
        else
            echo "   내부에서도 응답 없음 (서비스 자체 문제)"
        fi
    fi
}

# 문제가 되는 서비스들 진단
check_service "Jupyter Lab" "8888" "movie-mlops-jupyter"
check_service "Feast UI" "6566" "movie-mlops-feast"
check_service "Prometheus" "9090" "movie-mlops-prometheus"
check_service "Kafka UI" "8082" "movie-mlops-kafka-ui"
check_service "cAdvisor" "8083" "movie-mlops-cadvisor"

echo ""
echo "🛠️ 정상 작동 서비스 확인..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

working_services=(
    "MLflow:5000:movie-mlops-mlflow"
    "Airflow:8080:movie-mlops-airflow-webserver"
    "API:8000:movie-mlops-api"
    "Grafana:3000:movie-mlops-grafana"
)

for service_info in "${working_services[@]}"; do
    IFS=':' read -r name port container <<< "$service_info"
    echo -n "🔹 ${name} (${port}): "
    response=$(timeout 5 curl -s -o /dev/null -w "%{http_code}" http://localhost:${port} 2>/dev/null)
    if [[ "$response" =~ ^[2345][0-9][0-9]$ ]]; then
        echo "✅ 정상 (${response})"
    else
        echo "❌ 문제 (${response:-타임아웃})"
    fi
done

echo ""
echo "🔍 추가 진단 정보..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "🌐 네트워크 상태:"
docker network ls | grep movie-mlops

echo ""
echo "💾 볼륨 상태:"
docker volume ls | grep movie-mlops

echo ""
echo "📊 리소스 사용량:"
echo "메모리 사용량:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" | grep movie-mlops | head -10

echo ""
echo "🚨 일반적인 해결 방법..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. 서비스 재시작: docker restart [컨테이너명]"
echo "2. 로그 확인: docker logs [컨테이너명] --tail=20"
echo "3. 포트 충돌 확인: netstat -an | findstr :[포트번호]"
echo "4. 방화벽 확인: Windows Defender 방화벽 설정"
echo "5. 브라우저 캐시 클리어 및 시크릿 모드 테스트"
echo ""
echo "🔧 자동 해결 시도를 원하면 './fix_service_access.sh' 실행"
