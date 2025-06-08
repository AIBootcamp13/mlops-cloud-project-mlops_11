#!/bin/bash
# 모니터링 스택 재시작 스크립트 (포트 충돌 해결)

echo "🛑 모니터링 스택 정리 중..."

# 모니터링 스택 중지 및 제거
docker compose -f docker/stacks/docker-compose.monitoring.yml --project-directory . down 2>/dev/null || true

# 관련 컨테이너 강제 제거
for container in movie-mlops-prometheus movie-mlops-grafana movie-mlops-alertmanager movie-mlops-kafka movie-mlops-zookeeper movie-mlops-kafka-ui movie-mlops-node-exporter movie-mlops-cadvisor movie-mlops-blackbox-exporter; do
    if docker ps -a --format "{{.Names}}" | grep -q "^${container}$"; then
        echo "제거 중: ${container}"
        docker stop "${container}" 2>/dev/null || true
        docker rm "${container}" 2>/dev/null || true
    fi
done

echo "🚀 모니터링 스택 재시작 중..."

# 모니터링 스택 시작
docker compose -f docker/stacks/docker-compose.monitoring.yml --project-directory . up -d

echo "✅ 모니터링 스택 재시작 완료!"
echo ""
echo "📊 서비스 접속 정보:"
echo "   Prometheus: http://localhost:9090"
echo "   Grafana: http://localhost:3000 (admin/admin123)"
echo "   Kafka UI: http://localhost:8082"
echo "   AlertManager: http://localhost:9093"
echo "   cAdvisor: http://localhost:8083 (포트 변경됨)"
echo "   Node Exporter: http://localhost:9100"
echo "   Blackbox Exporter: http://localhost:9115"
