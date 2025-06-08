#!/bin/bash
# ==============================================================================
# Docker Compose 명령어 수정 스크립트
# docker-compose → docker compose (Docker Compose V2)
# ==============================================================================

set -e

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

print_status "🔄 Docker Compose 명령어 수정 시작..."

# 1. Docker Compose V2 설치 확인
print_status "Docker Compose V2 설치 확인 중..."
if ! docker compose version &> /dev/null; then
    print_warning "Docker Compose V2가 설치되지 않았습니다."
    print_warning "Docker Desktop을 최신 버전으로 업데이트하거나 Docker Compose V2를 설치하세요."
    echo ""
    echo "설치 방법:"
    echo "1. Docker Desktop 업데이트 (권장)"
    echo "2. 또는 수동 설치: https://docs.docker.com/compose/install/"
    exit 1
else
    COMPOSE_VERSION=$(docker compose version --short)
    print_success "Docker Compose V2 $COMPOSE_VERSION 설치 확인됨"
fi

# 2. 수정된 파일들 확인
print_status "수정된 파일들 확인 중..."

modified_files=(
    "scripts/docker/start_all_services.sh"
    "scripts/docker/stop_all_services.sh"
    "run_movie_mlops.sh"
    "README.md"
    "tests/unit/test_package_compatibility.py"
    "docs/setup/QUICK_SETUP.md"
)

for file in "${modified_files[@]}"; do
    if [ -f "$file" ]; then
        # docker-compose 명령어가 남아있는지 확인
        if grep -q "docker-compose -f" "$file"; then
            print_warning "$file에 아직 'docker-compose' 명령어가 남아있습니다"
        else
            print_success "$file: 모든 명령어가 'docker compose'로 업데이트됨"
        fi
    else
        print_warning "$file 파일이 존재하지 않습니다"
    fi
done

# 3. 기능 테스트
print_status "기능 테스트 실행 중..."

# 간단한 Docker Compose 명령어 테스트
if docker compose version > /dev/null 2>&1; then
    print_success "Docker Compose V2 명령어 테스트 성공"
else
    print_warning "Docker Compose V2 명령어 테스트 실패"
fi

# 4. 사용법 안내
print_success "🎉 Docker Compose 명령어 수정 완료!"

echo ""
echo "📝 변경 사항 요약:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "❌ 기존: docker-compose -f docker/docker-compose.api.yml up -d"
echo "✅ 변경: docker compose -f docker/docker-compose.api.yml up -d"
echo ""
echo "🔹 파일명은 그대로 유지: docker-compose.yml"
echo "🔹 명령어만 변경: docker-compose → docker compose"
echo ""
echo "📋 수정된 파일 목록:"
for file in "${modified_files[@]}"; do
    echo "  - $file"
done

echo ""
echo "🚀 다음 단계:"
echo "1. 변경사항 테스트: ./run_movie_mlops.sh"
echo "2. 개별 서비스 테스트: docker compose -f docker/docker-compose.api.yml up -d"
echo "3. 문제 발생 시: Docker Desktop 재시작 또는 Docker Compose V2 재설치"

