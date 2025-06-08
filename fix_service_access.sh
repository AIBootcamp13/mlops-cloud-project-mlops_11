#!/bin/bash
# ==============================================================================
# Movie MLOps 서비스 접속 문제 자동 해결 스크립트
# 접속이 안 되는 서비스들을 순차적으로 재시작하고 설정 수정
# ==============================================================================

echo "🔧 Movie MLOps 서비스 접속 문제 자동 해결 중..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 문제가 되는 서비스들
problem_services=(
    "movie-mlops-jupyter:8888:Jupyter Lab"
    "movie-mlops-feast:6566:Feast UI"
    "movie-mlops-prometheus:9090:Prometheus"
    "movie-mlops-kafka-ui:8082:Kafka UI"
    "movie-mlops-cadvisor:8083:cAdvisor"
)

restart_service() {
    local container=$1
    local port=$2
    local name=$3
    
    echo ""
    echo "🔄 ${name} (${container}) 재시작 중..."
    
    # 1. 컨테이너 재시작
    if docker ps -a --filter "name=${container}" --format "{{.Names}}" | grep -q "${container}"; then
        echo "   컨테이너 재시작 중..."
        docker restart ${container}
        
        # 2. 시작 대기
        echo "   시작 대기 중... (30초)"
        sleep 30
        
        # 3. 상태 확인
        if docker ps --filter "name=${container}" --format "{{.Status}}" | grep -q "Up"; then
            echo "   ✅ 컨테이너 재시작 성공"
            
            # 4. 접속 테스트
            echo -n "   접속 테스트: "
            for i in {1..6}; do
                response=$(timeout 10 curl -s -o /dev/null -w "%{http_code}" http://localhost:${port} 2>/dev/null)
                if [[ "$response" =~ ^[2345][0-9][0-9]$ ]]; then
                    echo "✅ 성공 (${response})"
                    echo "   🌐 접속 URL: http://localhost:${port}"
                    return 0
                fi
                echo -n "."
                sleep 10
            done
            echo "❌ 여전히 접속 불가"
            
            # 5. 로그 확인
            echo "   📋 최근 로그:"
            docker logs ${container} --tail=10 2>/dev/null | sed 's/^/      /'
            
        else
            echo "   ❌ 컨테이너 재시작 실패"
        fi
    else
        echo "   ❌ 컨테이너를 찾을 수 없음"
        
        # 컨테이너가 없는 경우 docker-compose로 시작 시도
        echo "   🚀 docker-compose로 서비스 시작 시도..."
        case $container in
            *jupyter*)
                cd /mnt/c/dev/movie-mlops && docker compose -f docker/docker-compose.jupyter.yml up -d
                ;;
            *feast*)
                cd /mnt/c/dev/movie-mlops && docker compose -f docker/stacks/docker-compose.ml-stack-fixed.yml up -d feast
                ;;
            *prometheus*)
                cd /mnt/c/dev/movie-mlops && docker compose -f docker/docker-compose.monitoring.yml up -d prometheus
                ;;
            *kafka-ui*)
                cd /mnt/c/dev/movie-mlops && docker compose -f docker/docker-compose.kafka.yml up -d kafka-ui
                ;;
            *cadvisor*)
                cd /mnt/c/dev/movie-mlops && docker compose -f docker/docker-compose.monitoring.yml up -d cadvisor
                ;;
        esac
        sleep 30
    fi
}

# 각 문제 서비스 해결 시도
for service_info in "${problem_services[@]}"; do
    IFS=':' read -r container port name <<< "$service_info"
    restart_service "$container" "$port" "$name"
done

echo ""
echo "🔍 추가 해결 시도..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Docker 네트워크 재설정
echo "🌐 Docker 네트워크 확인 및 재설정..."
if ! docker network ls | grep -q movie-mlops-network; then
    echo "   네트워크 생성 중..."
    docker network create movie-mlops-network 2>/dev/null || echo "   네트워크가 이미 존재하거나 생성 실패"
fi

# 포트 충돌 확인 및 해결
echo ""
echo "🔍 포트 충돌 확인..."
conflicted_ports=(8888 6566 9090 8082 8083)

for port in "${conflicted_ports[@]}"; do
    echo -n "   포트 ${port}: "
    if netstat -an 2>/dev/null | grep -q ":${port} "; then
        # Windows에서 포트 사용 프로세스 찾기
        process=$(netstat -ano 2>/dev/null | grep ":${port} " | head -1 | awk '{print $5}')
        if [ ! -z "$process" ]; then
            echo "사용 중 (PID: ${process})"
        else
            echo "사용 중"
        fi
    else
        echo "사용 가능"
    fi
done

echo ""
echo "🛠️ Docker 시스템 정리..."
echo "   사용하지 않는 컨테이너 정리..."
docker container prune -f 2>/dev/null || true

echo "   사용하지 않는 이미지 정리..."
docker image prune -f 2>/dev/null || true

echo ""
echo "📊 최종 상태 확인..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "🐳 현재 실행 중인 Movie MLOps 컨테이너:"
docker ps --filter "name=movie-mlops" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "🌐 서비스 접속 테스트:"
test_urls=(
    "Jupyter Lab:http://localhost:8888"
    "Feast UI:http://localhost:6566"
    "Prometheus:http://localhost:9090"
    "Kafka UI:http://localhost:8082"
    "cAdvisor:http://localhost:8083"
    "MLflow:http://localhost:5000"
    "Airflow:http://localhost:8080"
    "API Docs:http://localhost:8000/docs"
    "Grafana:http://localhost:3000"
)

for url_info in "${test_urls[@]}"; do
    IFS=':' read -r name url_part1 url_part2 <<< "$url_info"
    full_url="${url_part1}:${url_part2}"
    port=$(echo $full_url | sed 's/.*://')
    
    echo -n "   ${name}: "
    response=$(timeout 5 curl -s -o /dev/null -w "%{http_code}" $full_url 2>/dev/null)
    if [[ "$response" =~ ^[2345][0-9][0-9]$ ]]; then
        echo "✅ 접속 가능 (${response})"
    else
        echo "❌ 접속 불가 (${response:-타임아웃})"
    fi
done

echo ""
echo "💡 추가 해결 방법..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. Windows 방화벽 확인:"
echo "   제어판 > Windows Defender 방화벽 > 고급 설정"
echo "   인바운드 규칙에서 포트 8888, 6566, 9090, 8082, 8083 허용"
echo ""
echo "2. 브라우저 문제 해결:"
echo "   - 시크릿/비공개 모드로 접속 시도"
echo "   - 브라우저 캐시 및 쿠키 삭제"
echo "   - 다른 브라우저로 테스트 (Firefox, Edge 등)"
echo ""
echo "3. WSL Docker 서비스 확인:"
echo "   sudo service docker status  (Docker 데몬 상태 확인)"
echo "   sudo service docker restart  (필요시 Docker 재시작)"
echo ""
echo "4. 개별 서비스 수동 시작:"
echo "   ./run_movie_mlops.sh 에서 개별 스택 시작 선택"
echo ""
echo "🎉 자동 해결 완료! 여전히 문제가 있으면 위 방법들을 시도해보세요."
