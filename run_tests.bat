@echo off
REM ==============================================================================
REM MLOps 9아키텍처 Windows 테스트 실행기
REM 모든 호환성 및 기능 테스트를 실행합니다
REM ==============================================================================

echo 🧪 MLOps 9아키텍처 테스트 실행 시작...

REM ==============================================================================
REM 1단계: 환경 검증
REM ==============================================================================
echo 📋 1단계: 환경 검증 중...

REM Python 버전 확인
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Python 버전: %PYTHON_VERSION%

REM Python 3.11 버전 확인
echo %PYTHON_VERSION% | findstr /C:"3.11" >nul
if errorlevel 1 (
    echo ❌ 오류: Python 3.11이 필요합니다. 현재 버전: %PYTHON_VERSION%
    exit /b 1
)

REM 가상환경 확인
if "%VIRTUAL_ENV%"=="" (
    echo ⚠️  경고: 가상환경이 활성화되지 않았습니다.
)

REM ==============================================================================
REM 2단계: 패키지 호환성 검사
REM ==============================================================================
echo 🔍 2단계: 패키지 호환성 검사 중...

echo pip check 실행 중...
pip check
if errorlevel 1 (
    echo ❌ 패키지 호환성 문제 발견
    exit /b 1
) else (
    echo ✅ 패키지 호환성 검사 통과
)

REM ==============================================================================
REM 3단계: 단위 테스트 실행
REM ==============================================================================
echo 🧪 3단계: 단위 테스트 실행 중...

pytest tests/unit/ -v --tb=short
if errorlevel 1 (
    echo ❌ 단위 테스트 실패
    exit /b 1
) else (
    echo ✅ 단위 테스트 통과
)

REM ==============================================================================
REM 4단계: 통합 테스트 실행 (있는 경우)
REM ==============================================================================
echo 🔗 4단계: 통합 테스트 확인 중...

dir /b tests\integration\*.py 2>nul | findstr /v "__init__.py" >nul
if not errorlevel 1 (
    echo 통합 테스트 실행 중...
    pytest tests/integration/ -v --tb=short
    if errorlevel 1 (
        echo ❌ 통합 테스트 실패
        exit /b 1
    ) else (
        echo ✅ 통합 테스트 통과
    )
) else (
    echo ℹ️  통합 테스트 파일이 없습니다. 건너뜁니다.
)

REM ==============================================================================
REM 5단계: E2E 테스트 실행 (있는 경우)
REM ==============================================================================
echo 🎯 5단계: E2E 테스트 확인 중...

dir /b tests\e2e\*.py 2>nul | findstr /v "__init__.py" >nul
if not errorlevel 1 (
    echo E2E 테스트 실행 중...
    pytest tests/e2e/ -v --tb=short
    if errorlevel 1 (
        echo ❌ E2E 테스트 실패
        exit /b 1
    ) else (
        echo ✅ E2E 테스트 통과
    )
) else (
    echo ℹ️  E2E 테스트 파일이 없습니다. 건너뜁니다.
)

REM ==============================================================================
REM 6단계: 코드 품질 검사 (선택적)
REM ==============================================================================
echo 🎨 6단계: 코드 품질 검사 중...

where black >nul 2>&1
if not errorlevel 1 (
    echo Black 포매터 검사 중...
    black --check .
    if errorlevel 1 (
        echo ⚠️  Black 포매터 권고사항 있음
    ) else (
        echo ✅ Black 포매터 검사 통과
    )
) else (
    echo ℹ️  Black이 설치되지 않았습니다. 건너뜁니다.
)

where flake8 >nul 2>&1
if not errorlevel 1 (
    echo Flake8 린터 검사 중...
    flake8 src/ tests/ --max-line-length=88 --extend-ignore=E203,W503
    if errorlevel 1 (
        echo ⚠️  Flake8 린터 권고사항 있음
    ) else (
        echo ✅ Flake8 린터 검사 통과
    )
) else (
    echo ℹ️  Flake8이 설치되지 않았습니다. 건너뜁니다.
)

REM ==============================================================================
REM 완료
REM ==============================================================================
echo.
echo 🎉 모든 테스트가 완료되었습니다!
echo.
echo 📊 테스트 요약:
echo ✅ Python 3.11 환경 확인
echo ✅ 패키지 호환성 검사
echo ✅ 단위 테스트
echo ℹ️  통합 테스트 (필요시)
echo ℹ️  E2E 테스트 (필요시)
echo ℹ️  코드 품질 검사 (선택적)
echo.
echo 🚀 MLOps 9아키텍처 환경이 정상적으로 설정되었습니다!

pause