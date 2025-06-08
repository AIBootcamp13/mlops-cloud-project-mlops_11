#!/bin/bash
# ==============================================================================
# Movie MLOps PostgreSQL 수동 DB 생성 스크립트 (개별 명령 실행)
# ==============================================================================

echo "🔧 PostgreSQL 데이터베이스 수동 생성 중..."
echo ""

# 1. 기존 사용자 및 데이터베이스 개별 삭제
echo "1️⃣ 기존 데이터베이스 개별 삭제 중..."

# Airflow 관련 정리
echo "Airflow DB/사용자 정리 중..."
docker exec movie-mlops-postgres psql -U postgres -c "DROP DATABASE IF EXISTS airflow;" 2>/dev/null || echo "   airflow DB 없음 (정상)"
docker exec movie-mlops-postgres psql -U postgres -c "DROP USER IF EXISTS airflow;" 2>/dev/null || echo "   airflow 사용자 없음 (정상)"

# MLflow 관련 정리  
echo "MLflow DB/사용자 정리 중..."
docker exec movie-mlops-postgres psql -U postgres -c "DROP DATABASE IF EXISTS mlflow;" 2>/dev/null || echo "   mlflow DB 없음 (정상)"
docker exec movie-mlops-postgres psql -U postgres -c "DROP USER IF EXISTS mlflow;" 2>/dev/null || echo "   mlflow 사용자 없음 (정상)"

# Movie data 관련 정리
echo "Movie data DB 정리 중..."
docker exec movie-mlops-postgres psql -U postgres -c "DROP DATABASE IF EXISTS movie_data;" 2>/dev/null || echo "   movie_data DB 없음 (정상)"

echo "✅ 기존 데이터 정리 완료"

# 2. 새 사용자 및 데이터베이스 개별 생성
echo ""
echo "2️⃣ 새 사용자 및 데이터베이스 개별 생성 중..."

# Airflow 사용자 생성
echo "Airflow 사용자 생성 중..."
docker exec movie-mlops-postgres psql -U postgres -c "CREATE USER airflow WITH PASSWORD 'airflow';"
if [ $? -eq 0 ]; then
    echo "✅ Airflow 사용자 생성 성공"
else
    echo "❌ Airflow 사용자 생성 실패"
fi

# Airflow 데이터베이스 생성
echo "Airflow 데이터베이스 생성 중..."
docker exec movie-mlops-postgres psql -U postgres -c "CREATE DATABASE airflow OWNER airflow;"
if [ $? -eq 0 ]; then
    echo "✅ Airflow 데이터베이스 생성 성공"
else
    echo "❌ Airflow 데이터베이스 생성 실패"
fi

# Airflow 권한 부여
echo "Airflow 권한 부여 중..."
docker exec movie-mlops-postgres psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE airflow TO airflow;"
docker exec movie-mlops-postgres psql -U postgres -c "ALTER USER airflow CREATEDB;"

# MLflow 사용자 생성
echo "MLflow 사용자 생성 중..."
docker exec movie-mlops-postgres psql -U postgres -c "CREATE USER mlflow WITH PASSWORD 'mlflow';"
if [ $? -eq 0 ]; then
    echo "✅ MLflow 사용자 생성 성공"
else
    echo "❌ MLflow 사용자 생성 실패"
fi

# MLflow 데이터베이스 생성
echo "MLflow 데이터베이스 생성 중..."
docker exec movie-mlops-postgres psql -U postgres -c "CREATE DATABASE mlflow OWNER mlflow;"
if [ $? -eq 0 ]; then
    echo "✅ MLflow 데이터베이스 생성 성공"
else
    echo "❌ MLflow 데이터베이스 생성 실패"
fi

# MLflow 권한 부여
echo "MLflow 권한 부여 중..."
docker exec movie-mlops-postgres psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE mlflow TO mlflow;"
docker exec movie-mlops-postgres psql -U postgres -c "ALTER USER mlflow CREATEDB;"

# Movie data 데이터베이스 생성
echo "Movie data 데이터베이스 생성 중..."
docker exec movie-mlops-postgres psql -U postgres -c "CREATE DATABASE movie_data OWNER postgres;"

echo ""
echo "3️⃣ 데이터베이스 생성 결과 확인..."
docker exec movie-mlops-postgres psql -U postgres -l

echo ""
echo "4️⃣ 연결 테스트..."

# Airflow 연결 테스트
echo "Airflow DB 연결 테스트:"
if docker exec movie-mlops-postgres psql -U airflow -d airflow -c "SELECT 1;" >/dev/null 2>&1; then
    echo "✅ Airflow DB 연결 성공"
else
    echo "❌ Airflow DB 연결 실패"
fi

# MLflow 연결 테스트
echo "MLflow DB 연결 테스트:"
if docker exec movie-mlops-postgres psql -U mlflow -d mlflow -c "SELECT 1;" >/dev/null 2>&1; then
    echo "✅ MLflow DB 연결 성공"
else
    echo "❌ MLflow DB 연결 실패"
fi

echo ""
echo "5️⃣ 서비스 재시작..."

# 문제가 있는 서비스들 재시작
echo "MLflow 재시작 중..."
docker restart movie-mlops-mlflow

echo "Airflow 재시작 중..."
docker restart movie-mlops-airflow-webserver movie-mlops-airflow-scheduler 2>/dev/null || true

# 초기화 대기
echo "서비스 초기화 대기 중... (45초)"
sleep 45

echo ""
echo "6️⃣ 최종 서비스 상태 확인..."
docker ps --filter "name=movie-mlops" --format "table {{.Names}}\t{{.Status}}" | grep -E "(postgres|mlflow|airflow)"

echo ""
echo "7️⃣ 포트 연결 최종 테스트..."

# 포트 테스트 함수
test_service_final() {
    local service=$1
    local port=$2
    
    echo -n "${service} (포트 ${port}): "
    if timeout 5 bash -c "</dev/tcp/localhost/${port}" 2>/dev/null; then
        echo "✅ 접속 가능"
        return 0
    else
        echo "❌ 접속 불가"
        return 1
    fi
}

test_service_final "MLflow" "5000"
test_service_final "Airflow" "8080"

echo ""
echo "🎉 PostgreSQL DB 수동 생성 완료!"
echo ""
echo "📊 접속 정보:"
echo "   MLflow: http://localhost:5000"
echo "   Airflow: http://localhost:8080 (admin/admin)"
echo ""
echo "💡 Airflow가 여전히 연결되지 않으면:"
echo "   docker logs movie-mlops-airflow-webserver --tail=10"
