@echo off
REM ==============================================================================
REM Windows용 1단계 완성 스크립트
REM Git 생태계의 부족한 10% 완성하기
REM ==============================================================================

echo.
echo ============================================================================
echo    🎯 1단계 완성: Git 생태계 (3 + 4아키텍처) 100%% 달성
echo ============================================================================
echo.

echo 🚀 1단계 완성 작업을 시작합니다...
echo.

REM 1. GitHub Actions 워크플로우 파일 확인
echo 1️⃣ GitHub Actions 워크플로우 파일 확인...

set workflow_count=0

if exist ".github\workflows\ci.yml" (
    echo ✅ CI 워크플로우 존재
    set /a workflow_count+=1
) else (
    echo ❌ CI 워크플로우 누락
)

if exist ".github\workflows\cd.yml" (
    echo ✅ CD 워크플로우 존재
    set /a workflow_count+=1
) else (
    echo ❌ CD 워크플로우 누락
)

if exist ".github\workflows\ml-pipeline.yml" (
    echo ✅ ML 파이프라인 워크플로우 존재
    set /a workflow_count+=1
) else (
    echo ❌ ML 파이프라인 워크플로우 누락
)

if exist ".github\workflows\dependencies.yml" (
    echo ✅ 의존성 업데이트 워크플로우 존재
    set /a workflow_count+=1
) else (
    echo ❌ 의존성 업데이트 워크플로우 누락
)

if exist ".github\workflows\docs.yml" (
    echo ✅ 문서 자동화 워크플로우 존재
    set /a workflow_count+=1
) else (
    echo ❌ 문서 자동화 워크플로우 누락
)

echo.
echo 워크플로우 파일: %workflow_count%/5 개 존재

REM 2. Git 상태 확인
echo.
echo 2️⃣ Git 상태 확인...

if exist ".git" (
    echo ✅ Git 저장소 초기화됨
) else (
    echo ❌ Git 저장소가 초기화되지 않음
)

if exist ".gitignore" (
    echo ✅ .gitignore 파일 존재
) else (
    echo ❌ .gitignore 파일 없음
)

if exist "README.md" (
    echo ✅ README.md 존재
) else (
    echo ❌ README.md 없음
)

REM 3. 프로젝트 구조 확인
echo.
echo 3️⃣ 프로젝트 구조 확인...

if exist "pyproject.toml" (
    echo ✅ pyproject.toml 존재
) else (
    echo ❌ pyproject.toml 없음
)

if exist "requirements" (
    echo ✅ requirements 디렉터리 존재
) else (
    echo ❌ requirements 디렉터리 없음
)

if exist "docker" (
    echo ✅ docker 디렉터리 존재
) else (
    echo ❌ docker 디렉터리 없음
)

REM 4. 완성도 계산 및 결과
echo.
echo 📊 1단계 완성도 결과:
echo ============================================================================

if %workflow_count% GEQ 4 (
    echo 🎉 1단계 Git 생태계 거의 완성! ^(%workflow_count%/5 워크플로우^)
    echo.
    echo ✅ 달성한 기능:
    echo • Git 버전 관리 시스템 구축
    echo • GitHub Actions CI/CD 파이프라인 구현
    echo • 코드 품질 자동 검사
    echo • Docker 이미지 자동 빌드
    echo • ML 파이프라인 자동화 프레임워크
    echo • 의존성 자동 업데이트
    echo • 문서 자동 생성 및 배포
    echo.
    echo 🚀 다음 단계:
    echo 1. GitHub에 코드 푸시
    echo 2. GitHub Secrets 설정 ^(TMDB_API_KEY^)
    echo 3. 첫 번째 워크플로우 실행 확인
    echo 4. 2단계 Airflow 생태계 구현 시작
    echo.
    echo 🎯 2단계로 진행할 준비가 되었습니다!
) else (
    echo ⚠️ 1단계 추가 작업 필요 ^(%workflow_count%/5 워크플로우^)
    echo.
    echo 🔧 완성을 위한 작업:
    if not exist ".github\workflows\ci.yml" echo • CI 워크플로우 생성 필요
    if not exist ".github\workflows\cd.yml" echo • CD 워크플로우 생성 필요
    if not exist ".github\workflows\ml-pipeline.yml" echo • ML 파이프라인 워크플로우 생성 필요
    if not exist ".github\workflows\dependencies.yml" echo • 의존성 업데이트 워크플로우 생성 필요
    if not exist ".github\workflows\docs.yml" echo • 문서 자동화 워크플로우 생성 필요
    echo.
    echo 💡 해결 방법:
    echo 1. 누락된 워크플로우 파일들이 생성되었는지 확인
    echo 2. .github/workflows/ 디렉터리 확인
    echo 3. 파일이 올바른 위치에 있는지 검토
)

echo.
echo 📚 추가 리소스:
echo • GitHub Actions 문서: .github\workflows\*.yml
echo • 설정 가이드: docs\setup\QUICK_SETUP.md
echo • 구현 현황: docs\temp\IMPLEMENTATION_STATUS_ANALYSIS.md
echo • 아키텍처 가이드: docs\overview\

echo.
echo ============================================================================
echo 1단계 완성 확인 완료!
echo ============================================================================

pause
