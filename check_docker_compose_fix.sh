#!/bin/bash
# ==============================================================================
# Docker Compose 명령어 수정 완료 확인 스크립트
# V1(docker-compose) → V2(docker compose) 전환 검증
# ==============================================================================

echo "🔍 Docker Compose 명령어 수정 완료 확인 중..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 수정된 파일들 목록
files=(
    "run_movie_mlops.sh"
    "fix_service_access.sh"
    "fix_services.sh" 
    "restart_monitoring.sh"
    "quick_start_api.sh"
    "run_api_simple.sh"
    "start_jupyter.sh"
    "scripts/docker/start_all_services.sh"
    "scripts/docker/stop_all_services.sh"
    "scripts/ml/test_ml_stack.sh"
)

echo "✅ 수정 완료된 파일들:"
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ $file (파일 없음)"
    fi
done

echo ""
echo "🔧 변경 사항 요약:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   변경 전: docker-compose -f [파일명].yml [명령어]"
echo "   변경 후: docker compose -f [파일명].yml [명령어]"
echo ""
echo "💡 파일명은 그대로 유지됩니다:"
echo "   docker-compose.yml ← 파일명 (하이픈 유지)"
echo "   docker compose    ← 명령어 (공백 사용)"

echo ""
echo "🎯 이제 다음 명령어들이 정상 작동합니다:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   ./start_jupyter.sh"
echo "   ./fix_service_access.sh"
echo "   ./run_movie_mlops.sh"
echo "   ./quick_start_api.sh"
echo ""
echo "✅ Docker Compose V2 명령어 수정 완료!"
