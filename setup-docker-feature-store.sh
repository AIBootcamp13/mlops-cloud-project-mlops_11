#!/bin/bash

# 2단계 피처 스토어 Docker 환경 설정 스크립트

echo "🚀 2단계 피처 스토어 Docker 환경 설정 시작"

# 환경 확인
if ! command -v docker &> /dev/null; then
    echo "❌ Docker가 설치되지 않았습니다."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose가 설치되지 않았습니다."
    exit 1
fi

echo "✅ Docker 환경 확인 완료"

# 환경 변수 파일 확인
if [ ! -f .env ]; then
    echo "⚠️ .env 파일이 없습니다. .env.template에서 복사합니다."
    cp .env.template .env
    echo "📝 .env 파일을 수정한 후 다시 실행하세요."
    exit 1
fi

echo "✅ 환경 변수 파일 확인 완료"

# 필요한 디렉토리 생성
echo "📁 필요한 디렉토리 생성 중..."
mkdir -p data/feature_store
mkdir -p data/raw
mkdir -p data/processed  
mkdir -p logs
mkdir -p feature_repo/data
mkdir -p config/grafana
mkdir -p reports

echo "✅ 디렉토리 생성 완료"

# Docker 이미지 빌드
echo "🏗️ Docker 이미지 빌드 중..."
docker-compose build dev

if [ $? -eq 0 ]; then
    echo "✅ Docker 이미지 빌드 완료"
else
    echo "❌ Docker 이미지 빌드 실패"
    exit 1
fi

# 기본 서비스 시작 (dev, redis, postgres)
echo "🐳 기본 서비스 시작 중..."
docker-compose up -d redis postgres

# 잠시 대기 (서비스 초기화)
echo "⏳ 서비스 초기화 대기 중..."
sleep 10

# 서비스 상태 확인
echo "🔍 서비스 상태 확인 중..."
docker-compose ps

# Redis 연결 테스트
echo "📡 Redis 연결 테스트..."
if docker-compose exec redis redis-cli ping; then
    echo "✅ Redis 연결 성공"
else
    echo "⚠️ Redis 연결 실패"
fi

# PostgreSQL 연결 테스트
echo "📡 PostgreSQL 연결 테스트..."
if docker-compose exec postgres pg_isready -U mlops_user -d mlops; then
    echo "✅ PostgreSQL 연결 성공"
else
    echo "⚠️ PostgreSQL 연결 실패"
fi

echo ""
echo "🎉 2단계 피처 스토어 Docker 환경 설정 완료!"
echo ""
echo "📋 다음 명령어로 서비스를 사용할 수 있습니다:"
echo ""
echo "# 개발 환경 접속"
echo "docker-compose exec dev bash"
echo ""
echo "# FastAPI 서버 시작 (선택사항)"
echo "docker-compose --profile api up -d"
echo ""
echo "# 모니터링 시작 (선택사항)"  
echo "docker-compose --profile monitoring up -d"
echo ""
echo "# Jupyter 노트북 시작 (선택사항)"
echo "docker-compose --profile jupyter up -d"
echo ""
echo "# 모든 서비스 중지"
echo "docker-compose down"
echo ""
echo "🔗 주요 서비스 URL:"
echo "  • API 문서: http://localhost:8001/docs (API 프로필 실행 시)"
echo "  • Prometheus: http://localhost:9090 (monitoring 프로필 실행 시)"
echo "  • Grafana: http://localhost:3000 (monitoring 프로필 실행 시)"
echo "  • Jupyter: http://localhost:8889 (jupyter 프로필 실행 시)"
