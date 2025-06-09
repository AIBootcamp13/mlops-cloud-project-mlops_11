#!/bin/bash
# ==============================================================================
# Jupyter Lab 빠른 시작 스크립트 (대안)
# 기존 이미지로 빠르게 시작
# ==============================================================================

echo "🚀 Jupyter Lab 빠른 시작 중..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 기존 Jupyter 컨테이너 정리
echo "1️⃣ 기존 컨테이너 정리..."
docker stop movie-mlops-jupyter 2>/dev/null || true
docker rm movie-mlops-jupyter 2>/dev/null || true

# 네트워크 확인
echo "2️⃣ 네트워크 확인..."
if ! docker network ls | grep -q movie-mlops-network; then
    echo "   네트워크 생성 중..."
    docker network create movie-mlops-network
fi

# Jupyter 컨테이너 시작 (간단한 방법)
echo "3️⃣ Jupyter Lab 컨테이너 시작..."
docker run -d \
    --name movie-mlops-jupyter \
    --network movie-mlops-network \
    -p 8888:8888 \
    -v /mnt/c/dev/movie-mlops:/home/jovyan/work \
    -e JUPYTER_ENABLE_LAB=yes \
    -e JUPYTER_TOKEN=movie-mlops-jupyter \
    jupyter/datascience-notebook:python-3.11 \
    start-notebook.sh \
    --NotebookApp.token='movie-mlops-jupyter' \
    --NotebookApp.allow_root=True \
    --NotebookApp.ip='0.0.0.0' \
    --LabApp.default_url='/lab'

echo "4️⃣ 시작 대기 중... (30초)"
sleep 30

echo "5️⃣ 상태 확인..."
if docker ps | grep -q movie-mlops-jupyter; then
    echo "✅ Jupyter Lab 컨테이너 실행 중"
    
    echo "6️⃣ 접속 테스트..."
    for i in {1..6}; do
        echo -n "   시도 ${i}/6: "
        response=$(timeout 10 curl -s -o /dev/null -w "%{http_code}" http://localhost:8888 2>/dev/null)
        if [[ "$response" =~ ^[2345][0-9][0-9]$ ]]; then
            echo "✅ 성공! (${response})"
            echo ""
            echo "🎉 Jupyter Lab 접속 가능!"
            echo "🌐 URL: http://localhost:8888/lab"
            echo "🔑 토큰: movie-mlops-jupyter"
            echo ""
            echo "📋 컨테이너 로그 확인:"
            docker logs movie-mlops-jupyter --tail=5
            exit 0
        else
            echo "대기 중... (${response:-타임아웃})"
            sleep 10
        fi
    done
    
    echo "❌ Jupyter Lab 응답 없음"
    echo "📋 상세 로그:"
    docker logs movie-mlops-jupyter --tail=20
else
    echo "❌ Jupyter Lab 컨테이너 시작 실패"
    echo "📋 Docker 로그:"
    docker logs movie-mlops-jupyter 2>/dev/null || echo "컨테이너 로그 없음"
fi

echo ""
echo "🔧 수동 해결 방법:"
echo "1. docker logs movie-mlops-jupyter"
echo "2. docker stop movie-mlops-jupyter && docker rm movie-mlops-jupyter"
echo "3. 다시 실행: ./start_jupyter_simple.sh"
