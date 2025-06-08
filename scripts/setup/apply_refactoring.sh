#!/bin/bash
# ==============================================================================
# Movie MLOps 리팩토링 완료 - 권한 설정 스크립트
# Phase 기반 명명에서 기능 기반 명명으로 전환 완료
# ==============================================================================

echo "🔧 리팩토링된 파일들에 실행 권한 부여 중..."

# 새로운 스크립트들에 실행 권한 부여
chmod +x run_movie_mlops_v2.sh
chmod +x scripts/ml/test_ml_stack.sh
chmod +x scripts/monitoring/test_monitoring_stack.sh

# 기존 스크립트들 권한 유지
chmod +x scripts/test/*.sh
chmod +x scripts/setup/*.sh
chmod +x scripts/docker/*.sh
chmod +x run_movie_mlops.sh
chmod +x run_tests.sh

echo "✅ 실행 권한 부여 완료!"
echo ""
echo "📋 리팩토링 완료 요약:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🐳 새로운 Docker Compose 구조:"
echo "  ✅ docker/stacks/docker-compose.ml-stack.yml      (ML 통합 환경)"
echo "  ✅ docker/stacks/docker-compose.monitoring.yml    (모니터링 통합 환경)"
echo ""
echo "🧪 새로운 테스트 스크립트:"
echo "  ✅ scripts/ml/test_ml_stack.sh                     (ML 스택 통합 테스트)"
echo "  ✅ scripts/monitoring/test_monitoring_stack.sh     (모니터링 스택 테스트)"
echo ""
echo "🎮 개선된 메인 실행기:"
echo "  ✅ run_movie_mlops_v2.sh                          (기능별 스택 관리)"
echo ""
echo "📚 개선사항:"
echo "  🔄 Phase2/3/4 → 기능별 명명 (ML Stack, Monitoring Stack)"
echo "  📦 모듈화된 Docker Compose 구조"
echo "  🎯 직관적인 파일명과 디렉토리 구조"
echo "  🧪 기능별 독립 테스트 시스템"
echo "  ⚡ 선택적 스택 실행 가능"
echo ""
echo "🚀 새로운 실행 방법:"
echo "  # 리팩토링된 메인 실행기 (권장)"
echo "  ./run_movie_mlops_v2.sh"
echo ""
echo "  # ML 스택만 실행"
echo "  docker compose -f docker/stacks/docker-compose.ml-stack.yml up -d"
echo ""
echo "  # 모니터링 스택만 실행"  
echo "  docker compose -f docker/stacks/docker-compose.monitoring.yml up -d"
echo ""
echo "  # ML 스택 테스트"
echo "  ./scripts/ml/test_ml_stack.sh"
echo ""
echo "  # 모니터링 스택 테스트"
echo "  ./scripts/monitoring/test_monitoring_stack.sh"
echo ""
echo "🎉 리팩토링 완료!"
echo "   이제 Phase 기반 임시 명명에서 기능 기반 영구 명명으로 전환되었습니다."
echo "   새로운 개발자도 파일 용도를 직관적으로 파악할 수 있습니다!"
