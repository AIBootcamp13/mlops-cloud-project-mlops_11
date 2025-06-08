#!/bin/bash
# ==============================================================================
# Python 버전 확인 및 정리 스크립트
# ==============================================================================

echo "🔍 시스템 Python 환경 분석 중..."

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

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Python 설치 현황 분석"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. 기본 python 명령어들 확인
print_status "1. 기본 Python 명령어 확인"
echo ""

commands=("python" "python3" "python3.11" "python3.12" "python3.10" "python3.13")

for cmd in "${commands[@]}"; do
    if command -v $cmd &> /dev/null; then
        version=$($cmd --version 2>&1)
        location=$(which $cmd)
        print_success "$cmd: $version ($location)"
    else
        echo "   $cmd: 설치되지 않음"
    fi
done

echo ""
print_status "2. /usr/bin 디렉터리의 Python 바이너리 확인"
ls -la /usr/bin/python* 2>/dev/null | while read line; do
    echo "   $line"
done

echo ""
print_status "3. 현재 기본 python 명령어"
if command -v python &> /dev/null; then
    current_python=$(python --version 2>&1)
    current_location=$(which python)
    print_warning "python: $current_python ($current_location)"
else
    print_error "python 명령어가 없습니다"
fi

if command -v python3 &> /dev/null; then
    current_python3=$(python3 --version 2>&1)
    current_location3=$(which python3)
    print_warning "python3: $current_python3 ($current_location3)"
else
    print_error "python3 명령어가 없습니다"
fi

echo ""
print_status "4. 가상환경 확인"
if [[ -n "$VIRTUAL_ENV" ]]; then
    print_success "가상환경 활성화됨: $VIRTUAL_ENV"
    venv_python=$(python --version 2>&1)
    print_status "가상환경 Python: $venv_python"
else
    print_warning "가상환경이 활성화되지 않았습니다"
fi

echo ""
print_status "5. apt로 설치된 Python 패키지 확인"
dpkg -l | grep python3 | grep -E "(3\.[0-9]+)" | head -10

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 권장 조치"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Python 3.12 존재 여부 확인
if command -v python3.12 &> /dev/null; then
    print_warning "Python 3.12가 설치되어 있습니다!"
    print_status "Movie MLOps는 Python 3.11 전용입니다"
    echo ""
    echo "🔧 Python 3.12 제거 방법:"
    echo "   sudo apt remove python3.12 python3.12-dev python3.12-venv"
    echo "   sudo apt autoremove"
    echo ""
fi

# Python 3.11 존재 여부 확인
if command -v python3.11 &> /dev/null; then
    print_success "Python 3.11이 설치되어 있습니다 ✅"
    echo ""
    echo "🎯 권장 작업 순서:"
    echo "1. Python 3.11로 가상환경 생성:"
    echo "   python3.11 -m venv venv"
    echo "   source venv/bin/activate"
    echo ""
    echo "2. 환경 문제 해결:"
    echo "   ./scripts/setup/fix_wsl_issues.sh"
    echo ""
    echo "3. 테스트 실행:"
    echo "   ./run_tests.sh"
else
    print_error "Python 3.11이 설치되지 않았습니다!"
    echo ""
    echo "🔧 Python 3.11 설치 방법:"
    echo "   sudo apt update"
    echo "   sudo apt install python3.11 python3.11-dev python3.11-venv"
fi

echo ""
print_status "6. 현재 프로젝트 디렉터리의 가상환경 확인"
if [ -d "venv" ]; then
    print_warning "venv 폴더가 존재합니다"
    if [ -f "venv/pyvenv.cfg" ]; then
        venv_version=$(grep "version" venv/pyvenv.cfg)
        echo "   가상환경 정보: $venv_version"
        
        # 가상환경이 3.12라면 경고
        if grep -q "3.12" venv/pyvenv.cfg; then
            print_error "⚠️ 가상환경이 Python 3.12로 만들어졌습니다!"
            echo "   가상환경을 다시 만들어야 합니다:"
            echo "   rm -rf venv"
            echo "   python3.11 -m venv venv"
            echo "   source venv/bin/activate"
        fi
    fi
else
    print_status "venv 폴더가 없습니다 (정상)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
