#!/bin/bash
# ==============================================================================
# WSL Docker 환경 빠른 문제 해결 스크립트 - Python 3.11 전용
# ==============================================================================

set -e

echo "🔧 WSL Docker 환경 문제 해결 중 (Python 3.11 전용)..."

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

# Python 버전 확인
print_status "Python 버전 확인 중..."
PYTHON_VERSION=$(python --version 2>&1 | cut -d " " -f 2 | cut -d "." -f 1-2)

if [[ "$PYTHON_VERSION" != "3.11" ]]; then
    print_error "Python 3.11이 필요합니다. 현재 버전: $PYTHON_VERSION"
    print_status "Python 3.11을 설치하고 다시 실행해주세요"
    exit 1
else
    print_success "Python 3.11 확인됨"
fi

# 가상환경 확인
if [[ -z "$VIRTUAL_ENV" ]]; then
    print_warning "가상환경이 활성화되지 않았습니다"
    print_status "가상환경 사용을 권장합니다:"
    echo "  python -m venv venv"
    echo "  source venv/bin/activate"
    echo ""
    read -p "가상환경 없이 계속하시겠습니까? (y/N): " continue_without_venv
    if [[ ! $continue_without_venv =~ ^[Yy]$ ]]; then
        echo "가상환경을 설정한 후 다시 실행해주세요"
        exit 1
    fi
else
    print_success "가상환경 활성화됨: $VIRTUAL_ENV"
fi

# 1. pip 업그레이드
print_status "pip 업그레이드 중..."
python -m pip install --upgrade pip

# 2. wheel 및 빌드 도구 설치
print_status "빌드 도구 설치 중..."
pip install --upgrade wheel setuptools build

# 3. cryptography 재설치 (Python 3.11 최적화)
print_status "cryptography 패키지 재설치 중..."
pip uninstall -y cryptography || true
pip install --force-reinstall --no-cache-dir "cryptography>=41.0.7,<42.0.0"

# 4. 기본 의존성 설치
print_status "기본 의존성 설치 중..."
pip install -r requirements/base.txt

# 5. 개발 의존성 설치 (선택적)
read -p "개발 의존성을 설치하시겠습니까? (y/N): " install_dev
if [[ $install_dev =~ ^[Yy]$ ]]; then
    print_status "개발 의존성 설치 중..."
    pip install -r requirements/dev.txt
fi

# 6. 패키지 호환성 확인
print_status "패키지 호환성 확인 중..."
if pip check; then
    print_success "모든 패키지가 호환됩니다!"
else
    print_warning "일부 패키지 호환성 문제가 있을 수 있습니다"
    print_status "하지만 기본 기능은 정상 작동할 것입니다"
fi

# 7. pytest 설치 확인
print_status "pytest 설치 확인 중..."
if pip list | grep -q pytest; then
    print_success "pytest가 설치되었습니다"
else
    print_status "pytest 설치 중..."
    pip install pytest
fi

print_success "🎉 Python 3.11 환경 문제 해결 완료!"
print_status "이제 다음 명령으로 테스트를 실행하세요:"
echo "  ./run_tests.sh"
