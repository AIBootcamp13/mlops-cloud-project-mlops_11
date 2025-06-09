#!/bin/bash
# ==============================================================================
# Movie MLOps PostgreSQL 완전 재초기화 및 서비스 복구 스크립트
# ==============================================================================

echo "🔧 PostgreSQL 완전 재초기화 및 서비스 복구 중..."
echo ""

# 1. 모든 관련 서비스 중지
echo "1️⃣ 관련 서비스들 중지 중..."
docker stop movie-mlops-airflow-webserver movie-mlops-airflow-scheduler movie-mlops-mlflow movie-mlops-jupyter 2>/dev/null || true
docker rm movie-mlops-airflow-webserver movie-mlops-airflow-scheduler movie-mlops-mlflow movie-mlops-jupyter 2>/dev/null || true

# 2. PostgreSQL 컨테이너와 데이터 완전 제거
echo "2️⃣ PostgreSQL 데이터 완전 초기화..."
docker stop movie-mlops-postgres movie-mlops-pgadmin 2>/dev/null || true
docker rm movie-mlops-postgres movie-mlops-pgadmin 2>/dev/null || true

# PostgreSQL 볼륨 제거 (데이터 완전 삭제)
docker volume rm movie-mlops-postgres-data 2>/dev/null || true

echo "✅ PostgreSQL 데이터 완전 삭제 완료"

# 3. PostgreSQL 재시작
echo "3️⃣ PostgreSQL 컨테이너 재시작..."
docker compose -f docker/docker-compose.postgres.yml up -d

# PostgreSQL 완전 초기화 대기
echo "PostgreSQL 초기화 대기 중... (30초)"
sleep 30

# 4. 데이터베이스 및 사용자 수동 생성
echo "4️⃣ 데이터베이스 및 사용자 수동 생성..."

# 메인 데이터베이스에 MLOps 관련 DB들 생성
docker exec movie-mlops-postgres psql -U postgres -c "
-- Airflow 사용자 및 데이터베이스 생성
DROP DATABASE IF EXISTS airflow;
DROP USER IF EXISTS airflow;
CREATE USER airflow WITH PASSWORD 'airflow';
CREATE DATABASE airflow OWNER airflow;
GRANT ALL PRIVILEGES ON DATABASE airflow TO airflow;

-- MLflow 사용자 및 데이터베이스 생성  
DROP DATABASE IF EXISTS mlflow;
DROP USER IF EXISTS mlflow;
CREATE USER mlflow WITH PASSWORD 'mlflow';
CREATE DATABASE mlflow OWNER mlflow;
GRANT ALL PRIVILEGES ON DATABASE mlflow TO mlflow;

-- 영화 데이터 데이터베이스 생성
DROP DATABASE IF EXISTS movie_data;
CREATE DATABASE movie_data OWNER postgres;

-- 추가 권한 설정
ALTER USER airflow CREATEDB;
ALTER USER mlflow CREATEDB;
"

echo "✅ 데이터베이스 생성 완료"

# 5. 데이터베이스 생성 확인
echo "5️⃣ 데이터베이스 생성 확인..."
docker exec movie-mlops-postgres psql -U postgres -l

echo ""
echo "6️⃣ 연결 테스트..."
echo "Airflow DB 연결 테스트:"
docker exec movie-mlops-postgres psql -U airflow -d airflow -c "SELECT 1;" || echo "❌ Airflow DB 연결 실패"

echo "MLflow DB 연결 테스트:"
docker exec movie-mlops-postgres psql -U mlflow -d mlflow -c "SELECT 1;" || echo "❌ MLflow DB 연결 실패"

# 7. MLflow 재시작 (수정된 connection string 사용)
echo ""
echo "7️⃣ MLflow 서비스 재시작..."
if [ -f "docker/stacks/docker-compose.ml-stack-fixed.yml" ]; then
    docker compose -f docker/stacks/docker-compose.ml-stack-fixed.yml --project-directory . up -d mlflow
else
    docker compose -f docker/stacks/docker-compose.ml-stack.yml --project-directory . up -d mlflow  
fi

# 잠시 대기
echo "MLflow 재연결 대기 중... (20초)"
sleep 20

# 8. Airflow 재시작
echo "8️⃣ Airflow 서비스 재시작..."
if [ -f "docker/stacks/docker-compose.ml-stack-fixed.yml" ]; then
    docker compose -f docker/stacks/docker-compose.ml-stack-fixed.yml --project-directory . up -d airflow-webserver airflow-scheduler
else
    docker compose -f docker/stacks/docker-compose.ml-stack.yml --project-directory . up -d airflow-webserver airflow-scheduler
fi

echo "Airflow 재연결 대기 중... (30초)"
sleep 30

# 9. 서비스 상태 확인
echo ""
echo "9️⃣ 서비스 상태 최종 확인..."
echo "실행 중인 컨테이너:"
docker ps --filter "name=movie-mlops" --format "table {{.Names}}\t{{.Status}}" | grep -E "(postgres|mlflow|airflow)"

echo ""
echo "포트 연결 테스트:"
# 포트 테스트 함수
test_service_final() {
    local service=$1
    local port=$2
    local max_attempts=3
    local attempt=1
    
    echo -n "${service} (포트 ${port}): "
    
    while [ $attempt -le $max_attempts ]; do
        if timeout 3 bash -c "</dev/tcp/localhost/${port}" 2>/dev/null; then
            echo "✅ 접속 가능"
            return 0
        fi
        echo -n "."
        sleep 3
        ((attempt++))
    done
    
    echo " ❌ 접속 불가"
    return 1
}

test_service_final "MLflow" "5000"
test_service_final "Airflow" "8080"

echo ""
echo "🎉 PostgreSQL 재초기화 및 서비스 복구 완료!"
echo ""
echo "📊 접속 정보:"
echo "   MLflow: http://localhost:5000"
echo "   Airflow: http://localhost:8080 (admin/admin)"
echo ""
echo "💡 문제가 지속되면:"
echo "   1. docker logs movie-mlops-mlflow"
echo "   2. docker logs movie-mlops-airflow-webserver"
echo "   3. ./diagnose_services.sh 재실행"
