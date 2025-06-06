@echo off
echo 🔨 Docker 환경 설정 및 문제 해결 시작...
echo.

echo 📦 1. Docker 이미지 빌드 중...
docker-compose build dev
if %ERRORLEVEL% neq 0 (
    echo ❌ Docker 빌드 실패
    exit /b 1
)
echo ✅ Docker 이미지 빌드 완료

echo.
echo 🚀 2. 서비스 시작 중...
docker-compose up -d dev redis postgres
if %ERRORLEVEL% neq 0 (
    echo ❌ 서비스 시작 실패
    exit /b 1
)

echo.
echo ⏳ 3. 서비스 초기화 대기 (10초)...
timeout /t 10 /nobreak > nul

echo.
echo 🔍 4. 서비스 상태 확인...
docker-compose ps

echo.
echo 🧪 5. 기본 연결 테스트...
docker-compose exec -T dev python -c "
import redis, psycopg2
import sys

print('🔍 기본 환경 검증 시작...')

# Redis 연결 테스트
try:
    r = redis.Redis(host='redis', port=6379, decode_responses=True)
    r.ping()
    print('✅ Redis: 연결 성공')
except Exception as e:
    print(f'❌ Redis 연결 실패: {e}')
    sys.exit(1)

# PostgreSQL 연결 테스트
try:
    conn = psycopg2.connect(
        host='postgres', 
        database='mlops', 
        user='mlops_user', 
        password='mlops_password'
    )
    conn.close()
    print('✅ PostgreSQL: 연결 성공')
except Exception as e:
    print(f'❌ PostgreSQL 연결 실패: {e}')
    sys.exit(1)

print('✅ 기본 환경 검증 완료')
"

if %ERRORLEVEL% neq 0 (
    echo.
    echo ❌ 환경 검증 실패 - 로그 확인:
    docker-compose logs --tail=20 dev
    exit /b 1
)

echo.
echo 🎉 환경 설정 완료! 이제 2.1 환경 설정 테스트를 진행할 수 있습니다.
echo.
echo 📋 다음 명령어로 상세 테스트를 진행하세요:
echo    docker-compose exec dev bash
echo.

pause
