#!/bin/bash
# ==============================================================================
# 1단계 완성 실행 스크립트
# Git 생태계의 부족한 10% 완성하기
# ==============================================================================

set -e

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

print_header() {
    echo -e "${CYAN}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "   🎯 1단계 완성: Git 생태계 (3 + 4아키텍처) 100% 달성"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${NC}"
}

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_header

print_status "🚀 1단계 완성 작업을 시작합니다..."

# 1. 실행 권한 부여
print_status "1️⃣ 스크립트 실행 권한 부여..."
chmod +x scripts/setup/check_github_actions.sh
chmod +x scripts/setup/check_stage1_completion.sh

# 2. GitHub Actions 워크플로우 상태 확인
print_status "2️⃣ GitHub Actions 워크플로우 확인..."
if ./scripts/setup/check_github_actions.sh; then
    print_success "✅ GitHub Actions 워크플로우 설정 완료"
else
    print_status "⚠️ GitHub Actions 설정에 일부 문제가 있지만 계속 진행합니다"
fi

# 3. 1단계 완성도 검사
print_status "3️⃣ 1단계 완성도 최종 검사..."
if ./scripts/setup/check_stage1_completion.sh; then
    print_success "🎉 1단계 완성!"
    
    echo ""
    echo "🎯 1단계 Git 생태계 100% 완성!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ 3아키텍처 (Git + GitHub): 완료"
    echo "✅ 4아키텍처 (GitHub Actions): 완료"
    echo ""
    echo "📊 달성한 기능:"
    echo "• Git 버전 관리 시스템 완전 구축"
    echo "• GitHub 리모트 저장소 연결"
    echo "• CI/CD 파이프라인 5개 워크플로우 구현"
    echo "• 코드 품질 자동 검사"
    echo "• Docker 이미지 자동 빌드"
    echo "• ML 파이프라인 자동화 프레임워크"
    echo "• 의존성 자동 업데이트"
    echo "• 문서 자동 생성 및 배포"
    echo ""
    echo "🚀 다음 단계:"
    echo "1. GitHub에 코드 푸시"
    echo "2. GitHub Secrets 설정 (TMDB_API_KEY)"
    echo "3. 첫 번째 워크플로우 실행 확인"
    echo "4. 2단계 Airflow 생태계 구현 시작"
    echo ""
    echo "🎉 축하합니다! 이제 2단계로 진행할 수 있습니다!"
    
else
    exit_code=$?
    if [ $exit_code -eq 1 ]; then
        print_status "⚠️ 1단계 거의 완성 (80% 이상)"
        echo "몇 가지 설정만 더 하면 완성됩니다."
    else
        print_status "🔧 1단계 추가 작업 필요"
        echo "기본 설정부터 차근차근 진행해주세요."
    fi
fi

echo ""
echo "📚 추가 리소스:"
echo "• GitHub Actions 문서: .github/workflows/*.yml"
echo "• 설정 가이드: docs/setup/QUICK_SETUP.md"
echo "• 구현 현황: docs/temp/IMPLEMENTATION_STATUS_ANALYSIS.md"
echo "• 아키텍처 가이드: docs/overview/"
