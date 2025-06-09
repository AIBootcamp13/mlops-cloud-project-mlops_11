#!/bin/bash

# Feast 서버 시작 스크립트
set -e

echo "=== Feast 서버 시작 ==="

# 작업 디렉토리로 이동
cd /app/feast_repo

# Feast 레지스트리 확인
if [ ! -f "data/registry.db" ]; then
    echo "Feast 레지스트리가 없습니다. 초기화를 진행합니다..."
    
    # 필요한 디렉토리 생성
    mkdir -p data
    
    # Feast apply 실행 (피처 정의 등록)
    echo "Feast 피처 정의를 등록 중..."
    feast apply
    
    # 초기화 스크립트 실행 (있는 경우)
    if [ -f "init_feast.py" ]; then
        echo "Feast 초기화 스크립트 실행 중..."
        python init_feast.py
    fi
else
    echo "기존 Feast 레지스트리를 사용합니다."
fi

# Redis 연결 대기 (타임아웃 추가)
echo "Redis 연결을 확인 중..."
redis_ready=false
for i in {1..60}; do  # 60초 대기 (2초 * 30 -> 2초 * 60)
    if timeout 5 redis-cli -h movie-mlops-redis -p 6379 ping > /dev/null 2>&1; then
        echo "Redis 연결 성공"
        redis_ready=true
        break
    fi
    echo "Redis 연결 대기 중... ($i/60)"
    sleep 2
done

if [ "$redis_ready" = false ]; then
    echo "❌ Redis 연결 실패. Redis가 실행되지 않았거나 네트워크 문제가 있을 수 있습니다."
    echo "계속 진행하지만 온라인 피처 스토어 기능은 제한될 수 있습니다."
fi

# Feast 서버 시작 (커스텀 타이틀 적용)
echo "Feast 커스텀 서버를 시작합니다 (포트: ${FEAST_PORT:-6567})"
echo "접속 URL: http://localhost:${FEAST_PORT:-6567}"
echo "FastAPI 문서: http://localhost:${FEAST_PORT:-6567}/docs"
echo "Feast Feature Server는 내장된 FastAPI를 사용합니다"
echo "커스텀 타이틀: 'Feast Feature Server (Built-in FastAPI)'"

# 커스텀 Feast 서버 실행 (타이틀 수정됨)
exec python custom_feast_server.py
