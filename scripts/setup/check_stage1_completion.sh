#!/bin/bash
# ==============================================================================
# 1단계 (Git 생태계) 완성도 확인 스크립트
# 3아키텍처 (Git + GitHub) + 4아키텍처 (GitHub Actions) = 100% 완성 목표
# ==============================================================================

set -e

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

print_header() {
    echo -e "${CYAN}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "   🎯 1단계 완성도 검사: Git 생태계 (3 + 4아키텍처)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${NC}"
}

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 점수 계산을 위한 변수
total_score=0
max_score=0

add_score() {
    local score=$1
    local max=$2
    total_score=$((total_score + score))
    max_score=$((max_score + max))
}

print_header

# ==============================================================================
# 3아키텍처: Git + GitHub 버전 관리 시스템 (50점)
# ==============================================================================
print_status "📊 3아키텍처: Git + GitHub 버전 관리 시스템 검사..."

arch3_score=0

# Git 저장소 확인
if [ -d ".git" ]; then
    print_success "✅ Git 저장소 초기화됨"
    arch3_score=$((arch3_score + 10))
else
    print_error "❌ Git 저장소가 초기화되지 않음"
fi

# Git 설정 확인
if git config user.name &> /dev/null && git config user.email &> /dev/null; then
    print_success "✅ Git 사용자 설정 완료"
    arch3_score=$((arch3_score + 5))
else
    print_warning "⚠️ Git 사용자 설정 필요"
fi

# 브랜치 전략 확인
current_branch=$(git branch --show-current 2>/dev/null || echo "unknown")
if [ "$current_branch" != "unknown" ]; then
    print_success "✅ Git 브랜치: $current_branch"
    arch3_score=$((arch3_score + 5))
fi

# 커밋 히스토리 확인
commit_count=$(git rev-list --count HEAD 2>/dev/null || echo "0")
if [ "$commit_count" -gt 0 ]; then
    print_success "✅ 커밋 히스토리: $commit_count 개 커밋"
    arch3_score=$((arch3_score + 5))
else
    print_warning "⚠️ 커밋 히스토리 없음"
fi

# .gitignore 확인
if [ -f ".gitignore" ]; then
    print_success "✅ .gitignore 파일 존재"
    arch3_score=$((arch3_score + 5))
    
    # .gitignore 내용 확인
    if grep -q "__pycache__" .gitignore && grep -q ".env" .gitignore; then
        print_success "✅ .gitignore 적절한 내용 포함"
        arch3_score=$((arch3_score + 5))
    fi
else
    print_warning "⚠️ .gitignore 파일 없음"
fi

# 리모트 저장소 확인
if git remote -v | grep -q "origin"; then
    remote_url=$(git remote get-url origin 2>/dev/null || echo "unknown")
    print_success "✅ 리모트 저장소 설정: $remote_url"
    arch3_score=$((arch3_score + 10))
else
    print_warning "⚠️ 리모트 저장소 설정되지 않음"
fi

# README.md 확인
if [ -f "README.md" ]; then
    print_success "✅ README.md 존재"
    arch3_score=$((arch3_score + 5))
    
    # README 내용 품질 확인
    if grep -q "MLOps" README.md && grep -q "Docker" README.md; then
        print_success "✅ README.md 적절한 내용 포함"
        arch3_score=$((arch3_score + 5))
    fi
else
    print_error "❌ README.md 없음"
fi

add_score $arch3_score 50
print_status "3아키텍처 점수: $arch3_score/50 ($(( arch3_score * 100 / 50 ))%)"

# ==============================================================================
# 4아키텍처: GitHub Actions CI/CD (50점)
# ==============================================================================
print_status "📊 4아키텍처: GitHub Actions CI/CD 시스템 검사..."

arch4_score=0

# .github 디렉터리 확인
if [ -d ".github" ]; then
    print_success "✅ .github 디렉터리 존재"
    arch4_score=$((arch4_score + 5))
else
    print_error "❌ .github 디렉터리 없음"
fi

# workflows 디렉터리 확인
if [ -d ".github/workflows" ]; then
    print_success "✅ .github/workflows 디렉터리 존재"
    arch4_score=$((arch4_score + 5))
else
    print_error "❌ .github/workflows 디렉터리 없음"
fi

# 워크플로우 파일들 확인
workflows=(
    "ci.yml:CI 파이프라인:10"
    "cd.yml:CD 파이프라인:10"  
    "ml-pipeline.yml:ML 파이프라인:8"
    "dependencies.yml:의존성 업데이트:7"
    "docs.yml:문서 자동화:5"
)

workflow_count=0
for workflow_info in "${workflows[@]}"; do
    IFS=':' read -r filename description points <<< "$workflow_info"
    
    if [ -f ".github/workflows/$filename" ]; then
        print_success "✅ $description ($filename)"
        arch4_score=$((arch4_score + points))
        workflow_count=$((workflow_count + 1))
    else
        print_error "❌ $description ($filename) 누락"
    fi
done

# 워크플로우 품질 확인
if [ $workflow_count -ge 3 ]; then
    print_success "✅ 핵심 워크플로우 구성 완료"
    arch4_score=$((arch4_score + 5))
fi

add_score $arch4_score 50
print_status "4아키텍처 점수: $arch4_score/50 ($(( arch4_score * 100 / 50 ))%)"

# ==============================================================================
# 전체 1단계 완성도 계산
# ==============================================================================
print_status "📊 1단계 전체 완성도 계산..."

percentage=$(( total_score * 100 / max_score ))

echo ""
echo "🎯 1단계 완성도 결과:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 3아키텍처 (Git + GitHub): $arch3_score/50 ($(( arch3_score * 100 / 50 ))%)"
echo "📊 4아키텍처 (GitHub Actions): $arch4_score/50 ($(( arch4_score * 100 / 50 ))%)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 1단계 전체 점수: $total_score/$max_score ($percentage%)"

# 완성도에 따른 메시지
if [ $percentage -ge 95 ]; then
    print_success "🎉 1단계 완성! (95% 이상)"
    echo ""
    echo "✅ 축하합니다! 1단계 Git 생태계가 완성되었습니다."
    echo "🚀 이제 2단계 (Airflow 생태계) 구현을 시작할 수 있습니다."
    echo ""
    echo "🔄 다음 단계:"
    echo "1. GitHub에 코드 푸시하여 워크플로우 테스트"
    echo "2. GitHub Secrets 설정 (TMDB_API_KEY 등)"
    echo "3. 첫 번째 CI/CD 실행 확인"
    echo "4. 2단계 Airflow 생태계 구현 시작"
    
elif [ $percentage -ge 80 ]; then
    print_warning "⚠️ 1단계 거의 완성 (80-94%)"
    echo ""
    echo "🔧 완성을 위해 다음 항목들을 확인하세요:"
    
    if [ $arch3_score -lt 45 ]; then
        echo "- Git 설정 및 리모트 저장소 연결"
        echo "- .gitignore 및 README.md 개선"
    fi
    
    if [ $arch4_score -lt 45 ]; then
        echo "- 누락된 GitHub Actions 워크플로우 추가"
        echo "- 워크플로우 YAML 구문 검사"
    fi
    
elif [ $percentage -ge 60 ]; then
    print_warning "⚠️ 1단계 진행 중 (60-79%)"
    echo ""
    echo "🔧 다음 작업이 필요합니다:"
    echo "1. Git 저장소 및 기본 설정 완료"
    echo "2. GitHub Actions 워크플로우 구현"
    echo "3. CI/CD 파이프라인 테스트"
    
else
    print_error "❌ 1단계 미완성 (60% 미만)"
    echo ""
    echo "🔧 기본 설정부터 시작하세요:"
    echo "1. Git 초기화 및 기본 설정"
    echo "2. GitHub 리포지토리 생성 및 연결"
    echo "3. .github/workflows 디렉터리 생성"
    echo "4. 기본 CI 워크플로우 작성"
fi

echo ""
echo "📋 상세 개선 사항:"

# 개선 사항 제안
if [ ! -f ".github/workflows/ci.yml" ]; then
    echo "🔧 GitHub Actions CI 워크플로우 생성 필요"
fi

if [ ! -f ".github/workflows/cd.yml" ]; then
    echo "🔧 GitHub Actions CD 워크플로우 생성 필요"
fi

if [ $arch3_score -lt 40 ]; then
    echo "🔧 Git 기본 설정 및 리모트 저장소 연결 필요"
fi

if [ $arch4_score -lt 40 ]; then
    echo "🔧 GitHub Actions 워크플로우 구현 필요"
fi

echo ""
echo "💡 도움말:"
echo "- GitHub Actions 상태 확인: ./scripts/setup/check_github_actions.sh"
echo "- Git 설정 가이드: docs/setup/QUICK_SETUP.md"
echo "- 전체 구현 현황: docs/temp/IMPLEMENTATION_STATUS_ANALYSIS.md"

# 종료 코드 설정
if [ $percentage -ge 95 ]; then
    exit 0  # 완성
elif [ $percentage -ge 80 ]; then
    exit 1  # 거의 완성
else
    exit 2  # 미완성
fi
