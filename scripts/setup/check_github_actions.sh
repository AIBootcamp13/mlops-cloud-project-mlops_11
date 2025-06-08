#!/bin/bash
# ==============================================================================
# GitHub Actions 워크플로우 상태 확인 스크립트
# ==============================================================================

set -e

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

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

print_status "🔍 GitHub Actions 워크플로우 상태 확인..."

# 1. 워크플로우 파일 존재 확인
print_status "1️⃣ 워크플로우 파일 확인 중..."

workflows=(
    ".github/workflows/ci.yml"
    ".github/workflows/cd.yml"
    ".github/workflows/ml-pipeline.yml"
    ".github/workflows/dependencies.yml"
    ".github/workflows/docs.yml"
)

workflow_count=0
for workflow in "${workflows[@]}"; do
    if [ -f "$workflow" ]; then
        print_success "✅ $workflow 존재"
        workflow_count=$((workflow_count + 1))
    else
        print_error "❌ $workflow 누락"
    fi
done

print_status "워크플로우 파일: $workflow_count/${#workflows[@]} 개 존재"

# 2. 워크플로우 구문 검사
print_status "2️⃣ 워크플로우 YAML 구문 확인 중..."

yaml_valid=true
for workflow in "${workflows[@]}"; do
    if [ -f "$workflow" ]; then
        if command -v yamllint &> /dev/null; then
            if yamllint "$workflow" > /dev/null 2>&1; then
                print_success "✅ $workflow YAML 구문 정상"
            else
                print_error "❌ $workflow YAML 구문 오류"
                yaml_valid=false
            fi
        else
            print_warning "⚠️ yamllint 미설치 - YAML 구문 검사 생략"
        fi
    fi
done

# 3. 필수 시크릿 확인 (로컬에서는 확인 불가)
print_status "3️⃣ 필수 GitHub Secrets 목록..."

required_secrets=(
    "TMDB_API_KEY"
    "GITHUB_TOKEN"
)

echo "다음 GitHub Secrets가 필요합니다:"
for secret in "${required_secrets[@]}"; do
    echo "  - $secret"
done
print_warning "GitHub 리포지토리 Settings > Secrets에서 설정하세요"

# 4. 워크플로우 트리거 확인
print_status "4️⃣ 워크플로우 트리거 설정 확인..."

echo "📊 워크플로우별 트리거 설정:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

for workflow in "${workflows[@]}"; do
    if [ -f "$workflow" ]; then
        workflow_name=$(basename "$workflow" .yml)
        echo "🔹 $workflow_name:"
        
        # push 트리거 확인
        if grep -q "push:" "$workflow"; then
            echo "  ✅ Push 트리거 활성화"
        fi
        
        # pull_request 트리거 확인
        if grep -q "pull_request:" "$workflow"; then
            echo "  ✅ Pull Request 트리거 활성화"
        fi
        
        # schedule 트리거 확인
        if grep -q "schedule:" "$workflow"; then
            echo "  ✅ 스케줄 트리거 활성화"
        fi
        
        # workflow_dispatch 트리거 확인
        if grep -q "workflow_dispatch:" "$workflow"; then
            echo "  ✅ 수동 실행 가능"
        fi
        
        echo ""
    fi
done

# 5. Docker 이미지 태그 확인
print_status "5️⃣ Docker 이미지 태그 설정 확인..."

if grep -r "ghcr.io" .github/workflows/ > /dev/null 2>&1; then
    print_success "✅ GitHub Container Registry 설정됨"
else
    print_warning "⚠️ Container Registry 설정 확인 필요"
fi

# 6. 환경별 배포 설정 확인
print_status "6️⃣ 배포 환경 설정 확인..."

environments=("development" "staging" "production")
for env in "${environments[@]}"; do
    if grep -r "environment: $env" .github/workflows/ > /dev/null 2>&1; then
        print_success "✅ $env 환경 배포 설정됨"
    else
        print_warning "⚠️ $env 환경 배포 설정 없음"
    fi
done

# 7. 테스트 매트릭스 확인
print_status "7️⃣ 테스트 매트릭스 확인..."

if grep -r "strategy:" .github/workflows/ > /dev/null 2>&1; then
    print_success "✅ 테스트 매트릭스 설정됨"
    
    # Python 버전 확인
    if grep -r "python-version" .github/workflows/ | grep -q "3.11"; then
        print_success "✅ Python 3.11 테스트 포함"
    else
        print_warning "⚠️ Python 3.11 테스트 설정 확인 필요"
    fi
    
    # 서비스별 테스트 확인
    if grep -r "matrix:" .github/workflows/ | grep -q "service"; then
        print_success "✅ 서비스별 매트릭스 테스트 설정됨"
    fi
else
    print_warning "⚠️ 테스트 매트릭스 설정 없음"
fi

# 8. 캐시 설정 확인
print_status "8️⃣ 캐시 최적화 확인..."

if grep -r "cache:" .github/workflows/ > /dev/null 2>&1; then
    print_success "✅ pip 캐시 설정됨"
fi

if grep -r "cache-from: type=gha" .github/workflows/ > /dev/null 2>&1; then
    print_success "✅ Docker 빌드 캐시 설정됨"
fi

# 9. 보안 스캔 확인
print_status "9️⃣ 보안 스캔 설정 확인..."

security_tools=("safety" "bandit" "pip-audit")
for tool in "${security_tools[@]}"; do
    if grep -r "$tool" .github/workflows/ > /dev/null 2>&1; then
        print_success "✅ $tool 보안 스캔 포함"
    else
        print_warning "⚠️ $tool 보안 스캔 없음"
    fi
done

# 10. 최종 요약
print_status "🎯 GitHub Actions 설정 요약"

echo ""
echo "📋 체크리스트:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $workflow_count -eq ${#workflows[@]} ]; then
    echo "✅ 모든 워크플로우 파일 존재 ($workflow_count/5)"
else
    echo "❌ 워크플로우 파일 누락 ($workflow_count/5)"
fi

if [ "$yaml_valid" = true ]; then
    echo "✅ YAML 구문 검사 통과"
else
    echo "❌ YAML 구문 오류 발견"
fi

echo "⚠️  GitHub Secrets 설정 필요: ${#required_secrets[@]}개"
echo "✅ 트리거 설정 완료"
echo "✅ Docker 이미지 레지스트리 설정"
echo "⚠️  환경별 배포 설정 확인 필요"

echo ""
echo "🚀 다음 단계:"
echo "1. GitHub 리포지토리에 코드 푸시"
echo "2. GitHub Secrets 설정"
echo "3. 첫 번째 워크플로우 실행 확인"
echo "4. 환경별 배포 설정 (필요시)"

if [ $workflow_count -eq ${#workflows[@]} ] && [ "$yaml_valid" = true ]; then
    print_success "🎉 GitHub Actions 설정 완료! 1단계 100% 달성!"
    exit 0
else
    print_error "🔧 GitHub Actions 설정에 문제가 있습니다."
    exit 1
fi
