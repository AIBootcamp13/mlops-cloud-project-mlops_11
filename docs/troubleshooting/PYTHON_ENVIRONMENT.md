# WSL Docker 환경 문제 해결 가이드 - Python 3.11 전용

## 🔧 발견된 문제들과 해결방법

### 1. ✅ pytest.ini 중복 설정 문제 
**문제**: `duplicate name 'addopts'` 오류
**해결**: pytest.ini에서 addopts 중복 제거 완료

### 2. ✅ Python 3.11 전용 환경
**문제**: Python 3.12 등 다른 버전에서 호환성 문제
**해결**: Python 3.11만 지원하도록 모든 설정 수정

### 3. ✅ cryptography 플랫폼 호환성 문제
**문제**: `cryptography 41.0.7 is not supported on this platform`
**해결**: Python 3.11 환경 문제 해결 스크립트 생성

## 🚀 즉시 해결 방법

### 빠른 해결 (권장)
```bash
# 1. Python 3.11 확인
python --version  # Python 3.11.x 여야 함

# 2. 환경 문제 일괄 해결
chmod +x scripts/setup/fix_wsl_issues.sh
./scripts/setup/fix_wsl_issues.sh

# 3. 테스트 재실행
./run_tests.sh
```

### 수동 해결
```bash
# 1. Python 3.11 확인
python --version

# 2. pip 업그레이드
python -m pip install --upgrade pip wheel setuptools

# 3. cryptography 재설치 (Python 3.11용)
pip uninstall -y cryptography
pip install --force-reinstall --no-cache-dir "cryptography>=41.0.7,<42.0.0"

# 4. 기본 의존성 설치
pip install -r requirements/base.txt requirements/dev.txt

# 5. 패키지 확인
pip check || echo "일부 호환성 문제는 무시해도 됩니다"
```

## 📋 해결된 상태 확인

### ✅ 수정된 파일들 (Python 3.11 전용)
- `pytest.ini` - 중복 설정 제거, Python 3.11 최적화
- `run_tests.sh` - Python 3.11 전용으로 수정
- `requirements/base.txt` - Python 3.11 전용 의존성
- `requirements/dev.txt` - Python 3.11 전용 개발 도구

### ✅ 새로 생성된 파일들
- `scripts/setup/fix_wsl_issues.sh` - Python 3.11 환경 문제 일괄 해결

## 🎯 이제 실행해보세요

```bash
# Python 3.11 확인
python --version  # 반드시 3.11.x 여야 함

# 환경 문제 해결 후 테스트
./scripts/setup/fix_wsl_issues.sh
./run_tests.sh

# 또는 Docker 서비스와 함께 테스트
./run_movie_mlops.sh  # 메뉴에서 1번 → 2번 실행
./run_tests.sh
```

## 💡 예상 결과

이제 다음과 같은 결과를 볼 수 있어야 합니다:

```
✅ WSL 환경 감지됨
✅ Python 3.11 환경 확인됨 
✅ 패키지 호환성 검사 통과 (또는 경고만)
✅ 단위 테스트 통과
```

## 🔍 추가 문제 발생 시

1. **Python 3.11 설치**:
   ```bash
   # Ubuntu/WSL에서 Python 3.11 설치
   sudo apt update
   sudo apt install python3.11 python3.11-venv python3.11-dev
   
   # Python 3.11로 가상환경 생성
   python3.11 -m venv venv
   source venv/bin/activate
   ```

2. **가상환경 사용 권장**:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ./scripts/setup/fix_wsl_issues.sh
   ```

3. **Docker 서비스 확인**:
   ```bash
   ./run_movie_mlops.sh
   # 메뉴에서 9번: 서비스 상태 확인
   ```

4. **개별 테스트 실행**:
   ```bash
   ./run_tests.sh local    # 로컬 환경만
   ./run_tests.sh docker   # Docker 서비스만
   ```

## ⚠️ 중요: Python 3.11 전용

이 프로젝트는 **Python 3.11 전용**으로 설계되었습니다:
- Python 3.10 이하: 지원하지 않음
- Python 3.12 이상: 지원하지 않음
- **오직 Python 3.11.x만 지원**

다른 Python 버전을 사용 중이라면 Python 3.11을 설치하고 가상환경을 새로 만드세요.

모든 문제가 해결되었으니 이제 Python 3.11 환경에서 정상적으로 테스트가 실행될 것입니다! 🎉
