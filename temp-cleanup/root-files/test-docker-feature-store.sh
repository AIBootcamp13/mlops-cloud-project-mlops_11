#!/bin/bash

# 2단계 피처 스토어 Docker 환경 테스트 스크립트

echo "🧪 2단계 피처 스토어 Docker 환경 테스트 시작"

# 개발 컨테이너가 실행 중인지 확인
if ! docker-compose ps dev | grep -q "Up"; then
    echo "❌ 개발 컨테이너가 실행되지 않고 있습니다."
    echo "다음 명령어로 시작하세요: docker-compose up -d"
    exit 1
fi

echo "✅ 개발 컨테이너 실행 중"

# Redis 연결 테스트
echo "📡 Redis 연결 테스트..."
if docker-compose exec -T redis redis-cli ping | grep -q "PONG"; then
    echo "✅ Redis 연결 성공"
else
    echo "❌ Redis 연결 실패"
    exit 1
fi

# PostgreSQL 연결 테스트
echo "📡 PostgreSQL 연결 테스트..."
if docker-compose exec -T postgres pg_isready -U mlops_user -d mlops | grep -q "accepting connections"; then
    echo "✅ PostgreSQL 연결 성공"
else
    echo "❌ PostgreSQL 연결 실패"
    exit 1
fi

# Python 환경 및 패키지 테스트
echo "🐍 Python 환경 테스트..."
docker-compose exec -T dev python -c "
import sys
print(f'Python 버전: {sys.version}')

# 필수 패키지 import 테스트
try:
    import pandas as pd
    import numpy as np
    import fastapi
    import redis
    import psycopg2
    import prometheus_client
    import category_encoders
    import feature_engine
    import jsonschema
    print('✅ 모든 필수 패키지 import 성공')
except ImportError as e:
    print(f'❌ 패키지 import 실패: {e}')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo "✅ Python 환경 테스트 성공"
else
    echo "❌ Python 환경 테스트 실패"
    exit 1
fi

# 피처 스토어 테스트
echo "🏪 피처 스토어 테스트..."
docker-compose exec -T dev python -c "
import sys
sys.path.append('/app/src')

try:
    from features.engineering.tmdb_processor import AdvancedTMDBPreProcessor
    from features.store.feature_store import SimpleFeatureStore, FeatureStoreConfig
    print('✅ 피처 스토어 모듈 import 성공')
except ImportError as e:
    print(f'❌ 피처 스토어 모듈 import 실패: {e}')
    exit(1)

# 간단한 피처 스토어 테스트
try:
    config = FeatureStoreConfig(base_path='/app/data/feature_store')
    store = SimpleFeatureStore(config)
    print('✅ 피처 스토어 초기화 성공')
except Exception as e:
    print(f'❌ 피처 스토어 초기화 실패: {e}')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo "✅ 피처 스토어 테스트 성공"
else
    echo "❌ 피처 스토어 테스트 실패"
    exit 1
fi

# API 서버 테스트 (프로필이 활성화된 경우)
if docker-compose ps feature-store-api | grep -q "Up"; then
    echo "🌐 API 서버 테스트..."
    sleep 5  # API 서버 초기화 대기
    
    if curl -s http://localhost:8002/health | grep -q "healthy"; then
        echo "✅ API 서버 테스트 성공"
    else
        echo "⚠️ API 서버 응답 없음 (정상적일 수 있음)"
    fi
fi

# Feast 테스트 (선택사항)
echo "🍽️ Feast 통합 테스트..."
docker-compose exec -T dev python -c "
try:
    import feast
    print('✅ Feast 패키지 사용 가능')
except ImportError:
    print('⚠️ Feast 패키지 없음 (선택사항)')
"

# 파일 시스템 테스트
echo "📁 파일 시스템 테스트..."
docker-compose exec -T dev bash -c "
if [ -d '/app/data/feature_store' ]; then
    echo '✅ 피처 스토어 디렉토리 존재'
else
    echo '❌ 피처 스토어 디렉토리 없음'
    exit 1
fi

if [ -d '/app/feature_repo' ]; then
    echo '✅ Feast 레포지토리 디렉토리 존재'
else
    echo '❌ Feast 레포지토리 디렉토리 없음'
    exit 1
fi
"

if [ $? -eq 0 ]; then
    echo "✅ 파일 시스템 테스트 성공"
else
    echo "❌ 파일 시스템 테스트 실패"
    exit 1
fi

echo ""
echo "🎉 모든 테스트 성공!"
echo ""
echo "📋 Docker 환경에서 2단계 피처 스토어가 정상적으로 작동합니다."
echo ""
echo "🚀 다음 단계:"
echo "1. 개발 환경 접속: docker-compose exec dev bash"
echo "2. 테스트 실행: python test_feature_store.py"
echo "3. API 서버 시작: docker-compose --profile api up -d"
echo "4. 모니터링 시작: docker-compose --profile monitoring up -d"
