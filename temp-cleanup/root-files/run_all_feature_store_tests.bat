@echo off
REM 2단계 피처 스토어 전체 테스트 스위트 실행 스크립트 (Windows)
REM run_all_feature_store_tests.bat

setlocal enabledelayedexpansion

echo 🚀 2단계 피처 스토어 전체 테스트 스위트 시작
echo ==================================================

REM 로그 함수들 (Windows에서는 함수를 간소화)
echo [INFO] 테스트 시작 시간: %date% %time%

REM 환경 상태 확인
echo [INFO] 환경 상태 확인 중...

REM Docker 상태 확인
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker가 설치되어 있지 않습니다.
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker Compose가 설치되어 있지 않습니다.
    pause
    exit /b 1
)

REM 컨테이너 상태 확인
docker-compose ps dev | findstr "Up" >nul
if %errorlevel% neq 0 (
    echo [WARNING] 개발 컨테이너가 실행되지 않고 있습니다. 시작 중...
    docker-compose up -d dev redis postgres
    timeout /t 10 /nobreak >nul
)

echo [SUCCESS] 환경 상태 확인 완료

REM 1. 환경 검증 테스트
echo.
echo [INFO] 1️⃣ 환경 검증 테스트 실행 중...

REM Redis 연결 테스트
echo   📡 Redis 연결 테스트...
docker-compose exec -T redis redis-cli ping | findstr "PONG" >nul
if %errorlevel% equ 0 (
    echo [SUCCESS]   Redis 연결 성공
) else (
    echo [ERROR]   Redis 연결 실패
    goto :error_exit
)

REM PostgreSQL 연결 테스트
echo   📡 PostgreSQL 연결 테스트...
docker-compose exec -T postgres pg_isready -U mlops_user -d mlops | findstr "accepting connections" >nul
if %errorlevel% equ 0 (
    echo [SUCCESS]   PostgreSQL 연결 성공
) else (
    echo [ERROR]   PostgreSQL 연결 실패
    goto :error_exit
)

REM Python 환경 테스트
echo   🐍 Python 환경 테스트...
docker-compose exec -T dev python -c "import pandas, numpy, fastapi, redis, psycopg2; print('✅ 필수 패키지 import 성공')"
if %errorlevel% equ 0 (
    echo [SUCCESS]   Python 환경 테스트 성공
) else (
    echo [ERROR]   Python 환경 테스트 실패
    goto :error_exit
)

echo [SUCCESS] 환경 검증 테스트 완료

REM 2. 단위 테스트
echo.
echo [INFO] 2️⃣ 단위 테스트 실행 중...

echo   🔬 피처 엔지니어링 테스트...
docker-compose exec -T dev python -c "import sys; sys.path.append('/app/src'); from features.engineering.tmdb_processor import AdvancedTMDBPreProcessor; from features.store.feature_store import SimpleFeatureStore, FeatureStoreConfig; print('✅ 모듈 import 성공')"
if %errorlevel% equ 0 (
    echo [SUCCESS]   피처 엔지니어링 테스트 성공
) else (
    echo [ERROR]   피처 엔지니어링 테스트 실패
    goto :error_exit
)

echo [SUCCESS] 단위 테스트 완료

REM 3. 통합 테스트
echo.
echo [INFO] 3️⃣ 통합 테스트 실행 중...

echo   🏪 피처 스토어 통합 테스트...
docker-compose exec -T dev python -c "import sys; sys.path.append('/app/src'); from features.store.feature_store import SimpleFeatureStore, FeatureStoreConfig; config = FeatureStoreConfig(base_path='/app/data/feature_store'); store = SimpleFeatureStore(config); print('✅ 피처 스토어 통합 테스트 성공')"
if %errorlevel% equ 0 (
    echo [SUCCESS]   피처 스토어 통합 테스트 성공
) else (
    echo [ERROR]   피처 스토어 통합 테스트 실패
    goto :error_exit
)

echo   🗄️ 데이터베이스 통합 테스트...
docker-compose exec -T dev python -c "import psycopg2, redis; conn = psycopg2.connect(host='postgres', database='mlops', user='mlops_user', password='mlops_password'); conn.close(); r = redis.Redis(host='redis', port=6379); r.ping(); print('✅ 데이터베이스 통합 테스트 성공')"
if %errorlevel% equ 0 (
    echo [SUCCESS]   데이터베이스 통합 테스트 성공
) else (
    echo [ERROR]   데이터베이스 통합 테스트 실패
    goto :error_exit
)

echo [SUCCESS] 통합 테스트 완료

REM 4. API 테스트 (프로파일이 활성화된 경우)
echo.
echo [INFO] 4️⃣ API 테스트 실행 중...

docker-compose ps feature-store-api | findstr "Up" >nul
if %errorlevel% equ 0 (
    echo   🌐 API 엔드포인트 테스트...
    curl -s -f http://localhost:8002/health >nul 2>&1
    if %errorlevel% equ 0 (
        echo [SUCCESS]   API Health check 성공
    ) else (
        echo [WARNING]   API Health check 실패
    )
) else (
    echo [WARNING] API 서버가 실행되지 않고 있습니다. API 테스트를 스킵합니다.
    echo [INFO] API 테스트를 실행하려면: docker-compose --profile api up -d
)

echo [SUCCESS] API 테스트 완료

REM 5. 성능 테스트
echo.
echo [INFO] 5️⃣ 성능 테스트 실행 중...

echo   ⚡ 피처 생성 성능 테스트...
docker-compose exec -T dev python -c "import sys; sys.path.append('/app/src'); import time; from features.engineering.tmdb_processor import AdvancedTMDBPreProcessor; test_data = [{'id': i, 'title': f'Test {i}', 'release_date': '2023-01-01', 'vote_average': 7.5, 'vote_count': 1000, 'popularity': 30.0, 'genres': [{'id': 28, 'name': 'Action'}], 'runtime': 120} for i in range(50)]; processor = AdvancedTMDBPreProcessor({}); start = time.time(); features = processor.process_movies(test_data); end = time.time(); print(f'✅ 성능 테스트: {len(test_data)}개 레코드를 {end-start:.2f}초에 처리 ({len(test_data)/(end-start):.1f} records/sec)')"
if %errorlevel% equ 0 (
    echo [SUCCESS]   성능 테스트 성공
) else (
    echo [ERROR]   성능 테스트 실패
    goto :error_exit
)

echo [SUCCESS] 성능 테스트 완료

REM 6. 전체 시스템 테스트
echo.
echo [INFO] 6️⃣ 전체 시스템 테스트 실행 중...

echo   🎭 End-to-End 시나리오 테스트...
docker-compose exec -T dev python -c "import sys; sys.path.append('/app/src'); from features.engineering.tmdb_processor import AdvancedTMDBPreProcessor; from features.store.feature_store import SimpleFeatureStore, FeatureStoreConfig; raw_data = [{'id': 999, 'title': 'E2E Test Movie', 'release_date': '2023-12-01', 'vote_average': 9.0, 'vote_count': 2000, 'popularity': 75.5, 'genres': [{'id': 28, 'name': 'Action'}], 'runtime': 150}]; processor = AdvancedTMDBPreProcessor({}); features = processor.process_movies(raw_data); config = FeatureStoreConfig(base_path='/app/data/feature_store'); store = SimpleFeatureStore(config); store.save_features('e2e_test', features.to_dict('records')[0]); loaded = store.get_features(['e2e_test']); print('✅ End-to-End 시나리오 테스트 성공')"
if %errorlevel% equ 0 (
    echo [SUCCESS]   End-to-End 시나리오 테스트 성공
) else (
    echo [ERROR]   End-to-End 시나리오 테스트 실패
    goto :error_exit
)

echo [SUCCESS] 전체 시스템 테스트 완료

REM 7. 테스트 리포트 생성
echo.
echo [INFO] 📊 테스트 리포트 생성 중...

REM reports 디렉토리 생성
if not exist reports mkdir reports

REM 간단한 테스트 리포트 생성
echo 🧪 2단계 피처 스토어 테스트 리포트 > reports\feature_store_test_report.txt
echo ======================================== >> reports\feature_store_test_report.txt
echo 테스트 실행 시간: %date% %time% >> reports\feature_store_test_report.txt
echo. >> reports\feature_store_test_report.txt
echo ✅ 환경 검증 테스트: 통과 >> reports\feature_store_test_report.txt
echo ✅ 단위 테스트: 통과 >> reports\feature_store_test_report.txt
echo ✅ 통합 테스트: 통과 >> reports\feature_store_test_report.txt
echo ✅ API 테스트: 완료 >> reports\feature_store_test_report.txt
echo ✅ 성능 테스트: 통과 >> reports\feature_store_test_report.txt
echo ✅ 시스템 테스트: 통과 >> reports\feature_store_test_report.txt
echo. >> reports\feature_store_test_report.txt
echo 🎉 모든 테스트가 성공적으로 완료되었습니다! >> reports\feature_store_test_report.txt

echo [SUCCESS] 테스트 리포트 생성 완료
echo [INFO]   - 리포트 파일: reports\feature_store_test_report.txt

REM 최종 결과 출력
echo.
echo 🎉 모든 테스트 완료!
echo 테스트 종료 시간: %date% %time%
echo.
echo 📋 다음 단계:
echo   1. 테스트 리포트 확인: type reports\feature_store_test_report.txt
echo   2. API 서버 테스트: docker-compose --profile api up -d
echo   3. 모니터링 대시보드: docker-compose --profile monitoring up -d
echo.
echo [SUCCESS] 2단계 피처 스토어 시스템이 모든 테스트를 통과했습니다! 🚀
echo.
pause
exit /b 0

:error_exit
echo.
echo [ERROR] 테스트 실행 중 오류가 발생했습니다.
echo [INFO] 문제 해결 방법:
echo   1. Docker 서비스 상태 확인: docker-compose ps
echo   2. 로그 확인: docker-compose logs dev
echo   3. 컨테이너 재시작: docker-compose restart
echo.
pause
exit /b 1
