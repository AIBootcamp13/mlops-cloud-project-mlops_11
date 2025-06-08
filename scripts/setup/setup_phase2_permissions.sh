#!/bin/bash
# ==============================================================================
# Phase 2 구현 완료 - 권한 설정 스크립트
# ==============================================================================

echo "🔧 Phase 2 구현 파일들에 실행 권한 부여 중..."

# 스크립트 파일들에 실행 권한 부여
chmod +x scripts/test/test_api.sh
chmod +x scripts/test/test_phase2_integration.sh
chmod +x run_movie_mlops.sh
chmod +x scripts/setup/*.sh
chmod +x scripts/docker/*.sh

echo "✅ 실행 권한 부여 완료!"
echo ""
echo "📋 Phase 2 구현 완료 요약:"
echo "  ✅ FastAPI 메인 애플리케이션: src/api/main.py"
echo "  ✅ 추천 API 라우터: src/api/routers/recommendations.py"
echo "  ✅ 데이터 수집 DAG: airflow/dags/movie_data_collection.py"
echo "  ✅ 모델 훈련 DAG: airflow/dags/movie_training_pipeline.py"
echo "  ✅ 통합 테스트 스크립트: scripts/test/test_phase2_integration.sh"
echo "  ✅ API 테스트 스크립트: scripts/test/test_api.sh"
echo "  ✅ Docker 파일 업데이트: docker/dockerfiles/Dockerfile.api"
echo "  ✅ 환경 변수 업데이트: .env"
echo ""
echo "🚀 Phase 2 테스트 실행:"
echo "  ./scripts/test/test_phase2_integration.sh"
echo ""
echo "🎉 Phase 2 구현 완료!"
