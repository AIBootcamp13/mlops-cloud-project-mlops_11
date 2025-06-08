#!/bin/bash
# ==============================================================================
# venv 정리 테스트 스크립트
# ==============================================================================

echo "🧪 venv 정리 상태 테스트 중..."

# 현재 상태 확인
echo ""
echo "📊 현재 상태:"

# venv 폴더 확인
if [ -d "venv" ]; then
    echo "❌ venv 폴더가 아직 존재합니다"
    VENV_FOUND=true
else
    echo "✅ venv 폴더가 제거되었습니다"
    VENV_FOUND=false
fi

# venv 백업 폴더 확인  
if [ -d "venv_backup_to_delete" ]; then
    echo "⚠️  venv_backup_to_delete 폴더가 존재합니다 (수동 삭제 필요)"
    BACKUP_FOUND=true
else
    echo "✅ venv 백업 폴더가 없습니다"
    BACKUP_FOUND=false
fi

# Docker 환경 확인
if command -v docker &> /dev/null; then
    echo "✅ Docker가 설치되어 있습니다"
    DOCKER_OK=true
else
    echo "❌ Docker가 설치되지 않았습니다"
    DOCKER_OK=false
fi

# .env 파일 확인
if [ -f ".env" ]; then
    echo "✅ .env 파일이 존재합니다"
    ENV_OK=true
else
    echo "❌ .env 파일이 없습니다"
    ENV_OK=false
fi

# Python 캐시 확인
PYCACHE_COUNT=$(find . -name "__pycache__" -type d 2>/dev/null | wc -l)
if [ "$PYCACHE_COUNT" -eq 0 ]; then
    echo "✅ Python 캐시가 정리되었습니다"
else
    echo "⚠️  Python 캐시가 $PYCACHE_COUNT 개 발견되었습니다"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 정리 결과 요약"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ "$VENV_FOUND" = false ] && [ "$DOCKER_OK" = true ] && [ "$ENV_OK" = true ]; then
    echo "🎉 WSL Docker 환경 정리가 성공적으로 완료되었습니다!"
    echo ""
    echo "✅ venv 가상환경 제거됨"
    echo "✅ Docker 환경 준비됨"  
    echo "✅ .env 파일 설정됨"
    echo ""
    echo "🚀 다음 명령으로 서비스를 시작할 수 있습니다:"
    echo "   ./run_movie_mlops.sh"
    
    if [ "$BACKUP_FOUND" = true ]; then
        echo ""
        echo "⚠️  수동 작업 필요:"
        echo "   venv_backup_to_delete 폴더를 삭제하세요:"
        echo "   rm -rf venv_backup_to_delete"
    fi
    
else
    echo "⚠️  일부 작업이 미완료되었습니다:"
    
    if [ "$VENV_FOUND" = true ]; then
        echo "❌ venv 폴더가 아직 존재합니다"
    fi
    
    if [ "$DOCKER_OK" = false ]; then
        echo "❌ Docker 환경이 준비되지 않았습니다"
    fi
    
    if [ "$ENV_OK" = false ]; then
        echo "❌ .env 파일이 없습니다"
    fi
    
    echo ""
    echo "🔧 cleanup_python_environment.sh 스크립트를 실행하세요:"
    echo "   ./scripts/setup/cleanup_python_environment.sh"
fi

echo ""
echo "📊 현재 프로젝트는 WSL Docker 환경으로 구성되어 있습니다."
echo "   venv 가상환경 대신 Docker 컨테이너를 사용합니다."
