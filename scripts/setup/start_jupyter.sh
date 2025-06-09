#!/bin/bash
# ==============================================================================
# Jupyter Lab 서비스 시작 스크립트
# ==============================================================================

echo "🚀 Jupyter Lab 컨테이너 시작 중..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd /mnt/c/dev/movie-mlops

# Jupyter 서비스 시작
echo "1️⃣ Jupyter 서비스 시작..."
docker compose -f docker/docker-compose.jupyter.yml up -d

echo ""
echo "2️⃣ 시작 대기 중... (30초)"
sleep 30

echo ""
echo "3️⃣ 컨테이너 상태 확인..."
docker ps --filter "name=jupyter" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "4️⃣ 접속 테스트..."
for i in {1..6}; do
    echo -n "   시도 ${i}/6: "
    response=$(timeout 10 curl -s -o /dev/null -w "%{http_code}" http://localhost:8888 2>/dev/null)
    if [[ "$response" =~ ^[2345][0-9][0-9]$ ]]; then
        echo "✅ 성공! (${response})"
        echo ""
        echo "🎉 Jupyter Lab 접속 가능: http://localhost:8888"
        echo ""
        echo "📋 토큰 확인 (필요시):"
        docker logs movie-mlops-jupyter 2>/dev/null | grep -E "(token=|http://127.0.0.1:8888)" | tail -3
        exit 0
    else
        echo "대기 중... (${response:-타임아웃})"
        sleep 10
    fi
done

echo ""
echo "❌ Jupyter Lab이 여전히 시작되지 않습니다."
echo "📋 로그 확인:"
docker logs movie-mlops-jupyter --tail=20 2>/dev/null || echo "   컨테이너 로그를 찾을 수 없습니다."

echo ""
echo "🔧 수동 해결 방법:"
echo "1. docker-compose -f docker/docker-compose.jupyter.yml logs"
echo "2. docker-compose -f docker/docker-compose.jupyter.yml down"
echo "3. docker-compose -f docker/docker-compose.jupyter.yml up -d"
