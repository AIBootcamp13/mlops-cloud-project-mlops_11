#!/bin/bash

# Feast 피처 스토어 테스트 스크립트

set -e

echo "=== Feast 피처 스토어 테스트 시작 ==="

# 프로젝트 루트로 이동
cd "$(dirname "$0")/../.."

# Python 경로 설정
export PYTHONPATH="${PWD}:${PYTHONPATH}"

echo "1. Feast 환경 확인..."

# Feast 설치 확인
python -c "import feast; print(f'Feast 버전: {feast.__version__}')" || {
    echo "❌ Feast가 설치되지 않았습니다. requirements/feast.txt를 확인하세요."
    exit 1
}

echo "2. Feast 레포지토리 초기화..."

cd feast_repo

# feature_store.yaml 존재 확인
if [ ! -f "feature_store.yaml" ]; then
    echo "❌ feature_store.yaml이 존재하지 않습니다."
    exit 1
fi

echo "3. 피처 정의 적용..."

# Feast apply 실행
feast apply || {
    echo "❌ Feast apply 실패"
    exit 1
}

echo "4. 피처 뷰 확인..."

# 피처 뷰 목록 조회
feast feature-views list || {
    echo "❌ 피처 뷰 조회 실패"
    exit 1
}

echo "5. 샘플 데이터 생성 및 실체화..."

# 프로젝트 루트로 다시 이동
cd ..

# 초기화 스크립트 실행
python feast_repo/init_feast.py || {
    echo "❌ Feast 초기화 실패"
    exit 1
}

echo "6. Python 클라이언트 테스트..."

# Feast 클라이언트 테스트
python -c "
import sys
sys.path.append('.')
from src.features.feast_client import get_feast_client

try:
    client = get_feast_client()
    views = client.list_feature_views()
    print(f'✅ 등록된 피처 뷰: {views}')
    
    # 간단한 피처 조회 테스트
    if views:
        print('✅ Feast 클라이언트 정상 동작')
    else:
        print('⚠️  등록된 피처 뷰가 없습니다')
        
except Exception as e:
    print(f'❌ Feast 클라이언트 테스트 실패: {e}')
    sys.exit(1)
" || {
    echo "❌ Python 클라이언트 테스트 실패"
    exit 1
}

echo "7. API 엔드포인트 테스트..."

# API 서버가 실행 중인지 확인 (포트 8000)
if curl -s http://localhost:8000/features/health > /dev/null; then
    echo "✅ Feast API 엔드포인트 접근 가능"
    
    # 피처 뷰 목록 API 테스트
    curl -s http://localhost:8000/features/views | jq . || {
        echo "⚠️  API 응답 파싱 실패 (jq 미설치?)"
    }
else
    echo "⚠️  API 서버가 실행 중이 아닙니다. 수동으로 확인하세요:"
    echo "   python src/api/main.py"
    echo "   curl http://localhost:8000/features/health"
fi

echo "8. 데이터 파일 확인..."

# 생성된 데이터 파일들 확인
if [ -d "data/feast" ]; then
    echo "✅ Feast 데이터 디렉토리 존재"
    ls -la data/feast/ || true
else
    echo "⚠️  Feast 데이터 디렉토리가 생성되지 않았습니다"
fi

echo ""
echo "=== Feast 테스트 완료 ==="
echo ""
echo "📋 테스트 결과 요약:"
echo "  - Feast 설치: ✅"
echo "  - 피처 정의 적용: ✅"
echo "  - Python 클라이언트: ✅"
echo "  - 데이터 초기화: ✅"
echo ""
echo "🚀 다음 단계:"
echo "  1. API 서버 시작: python src/api/main.py"
echo "  2. 피처 조회 테스트: curl http://localhost:8000/features/views"
echo "  3. 영화 피처 조회: curl http://localhost:8000/features/movies/1"
echo ""

exit 0
