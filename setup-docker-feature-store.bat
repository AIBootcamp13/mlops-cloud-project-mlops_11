@echo off
REM 2단계 피처 스토어 Docker 환경 설정 스크립트 (Windows)

echo 🚀 2단계 피처 스토어 Docker 환경 설정 시작

REM Docker 설치 확인
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker가 설치되지 않았습니다.
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose가 설치되지 않았습니다.
    pause
    exit /b 1
)

echo ✅ Docker 환경 확인 완료

REM 환경 변수 파일 확인
if not exist .env (
    echo ⚠️ .env 파일이 없습니다. .env.template에서 복사합니다.
    copy .env.template .env
    echo 📝 .env 파일을 수정한 후 다시 실행하세요.
    pause
    exit /b 1
)

echo ✅ 환경 변수 파일 확인 완료

REM 필요한 디렉토리 생성
echo 📁 필요한 디렉토리 생성 중...
if not exist data\feature_store mkdir data\feature_store
if not exist data\raw mkdir data\raw
if not exist data\processed mkdir data\processed
if not exist logs mkdir logs
if not exist feature_repo\data mkdir feature_repo\data
if not exist config\grafana mkdir config\grafana
if not exist reports mkdir reports

echo ✅ 디렉토리 생성 완료

REM Docker 이미지 빌드
echo 🏗️ Docker 이미지 빌드 중...
docker-compose build dev

if %errorlevel% neq 0 (
    echo ❌ Docker 이미지 빌드 실패
    pause
    exit /b 1
)

echo ✅ Docker 이미지 빌드 완료

REM 기본 서비스 시작
echo 🐳 기본 서비스 시작 중...
docker-compose up -d redis postgres

REM 잠시 대기
echo ⏳ 서비스 초기화 대기 중...
timeout /t 10 /nobreak >nul

REM 서비스 상태 확인
echo 🔍 서비스 상태 확인 중...
docker-compose ps

REM Redis 연결 테스트
echo 📡 Redis 연결 테스트...
docker-compose exec redis redis-cli ping
if %errorlevel% equ 0 (
    echo ✅ Redis 연결 성공
) else (
    echo ⚠️ Redis 연결 실패
)

REM PostgreSQL 연결 테스트
echo 📡 PostgreSQL 연결 테스트...
docker-compose exec postgres pg_isready -U mlops_user -d mlops
if %errorlevel% equ 0 (
    echo ✅ PostgreSQL 연결 성공
) else (
    echo ⚠️ PostgreSQL 연결 실패
)

echo.
echo 🎉 2단계 피처 스토어 Docker 환경 설정 완료!
echo.
echo 📋 다음 명령어로 서비스를 사용할 수 있습니다:
echo.
echo # 개발 환경 접속
echo docker-compose exec dev bash
echo.
echo # FastAPI 서버 시작 (선택사항)
echo docker-compose --profile api up -d
echo.
echo # 모니터링 시작 (선택사항)
echo docker-compose --profile monitoring up -d
echo.
echo # Jupyter 노트북 시작 (선택사항)
echo docker-compose --profile jupyter up -d
echo.
echo # 모든 서비스 중지
echo docker-compose down
echo.
echo 🔗 주요 서비스 URL:
echo   • API 문서: http://localhost:8001/docs (API 프로필 실행 시)
echo   • Prometheus: http://localhost:9090 (monitoring 프로필 실행 시)
echo   • Grafana: http://localhost:3000 (monitoring 프로필 실행 시)
echo   • Jupyter: http://localhost:8889 (jupyter 프로필 실행 시)
echo.
pause
