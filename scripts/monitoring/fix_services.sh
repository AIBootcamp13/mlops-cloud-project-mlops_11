#!/bin/bash
# ==============================================================================
# Movie MLOps 서비스 문제 해결 스크립트
# ==============================================================================

echo "🛠️ Movie MLOps 서비스 문제 해결 중..."
echo ""

# 1. 문제가 있는 서비스들 중지
echo "1️⃣ 문제 서비스들 중지 중..."
docker stop movie-mlops-airflow-webserver movie-mlops-airflow-scheduler movie-mlops-mlflow 2>/dev/null || true
docker rm movie-mlops-airflow-webserver movie-mlops-airflow-scheduler movie-mlops-mlflow 2>/dev/null || true

# 2. PostgreSQL 데이터베이스 재초기화
echo "2️⃣ PostgreSQL 데이터베이스 재초기화..."
echo "PostgreSQL 컨테이너에서 데이터베이스 생성 중..."

# Airflow 데이터베이스 생성
docker exec movie-mlops-postgres psql -U postgres -d movie_mlops -c "
DROP DATABASE IF EXISTS airflow;
DROP USER IF EXISTS airflow;
CREATE USER airflow WITH PASSWORD 'airflow';
CREATE DATABASE airflow OWNER airflow;
GRANT ALL PRIVILEGES ON DATABASE airflow TO airflow;
" 2>/dev/null || echo "Airflow DB 생성 중 일부 에러 발생 (정상적일 수 있음)"

# MLflow 데이터베이스 생성
docker exec movie-mlops-postgres psql -U postgres -d movie_mlops -c "
DROP DATABASE IF EXISTS mlflow;
DROP USER IF EXISTS mlflow;
CREATE USER mlflow WITH PASSWORD 'mlflow';
CREATE DATABASE mlflow OWNER mlflow;
GRANT ALL PRIVILEGES ON DATABASE mlflow TO mlflow;
" 2>/dev/null || echo "MLflow DB 생성 중 일부 에러 발생 (정상적일 수 있음)"

echo "✅ 데이터베이스 재초기화 완료"

# 3. 서비스들 순차적으로 재시작
echo "3️⃣ 서비스들 순차적으로 재시작..."

# MLflow 먼저 시작
echo "MLflow 시작 중..."
if [ -f "docker/stacks/docker-compose.ml-stack-fixed.yml" ]; then
    docker compose -f docker/stacks/docker-compose.ml-stack-fixed.yml --project-directory . up -d mlflow
else
    docker compose -f docker/stacks/docker-compose.ml-stack.yml --project-directory . up -d mlflow
fi

# 잠시 대기
echo "MLflow 초기화 대기 중... (30초)"
sleep 30

# Airflow 시작
echo "Airflow 시작 중..."
if [ -f "docker/stacks/docker-compose.ml-stack-fixed.yml" ]; then
    docker compose -f docker/stacks/docker-compose.ml-stack-fixed.yml --project-directory . up -d airflow-webserver airflow-scheduler
else
    docker compose -f docker/stacks/docker-compose.ml-stack.yml --project-directory . up -d airflow-webserver airflow-scheduler
fi

echo "4️⃣ Jupyter 서비스 시작..."
# Jupyter는 development 프로필에 있으므로 별도 시작
if [ -f "docker/stacks/docker-compose.ml-stack-fixed.yml" ]; then
    docker compose -f docker/stacks/docker-compose.ml-stack-fixed.yml --project-directory . --profile development up -d jupyter
else
    docker compose -f docker/stacks/docker-compose.ml-stack.yml --project-directory . --profile development up -d jupyter
fi

echo ""
echo "5️⃣ 서비스 상태 확인 중..."
sleep 10

echo "현재 실행 중인 컨테이너:"
docker ps --filter "name=movie-mlops" --format "table {{.Names}}\t{{.Status}}" | grep -E "(airflow|mlflow|jupyter)"

echo ""
echo "6️⃣ 서비스 연결 테스트..."

# 포트 테스트 함수
test_service() {
    local service=$1
    local port=$2
    local max_attempts=6
    local attempt=1
    
    echo -n "${service} (포트 ${port}) 테스트: "
    
    while [ $attempt -le $max_attempts ]; do
        if timeout 3 bash -c "</dev/tcp/localhost/${port}" 2>/dev/null; then
            echo "✅ 접속 가능"
            return 0
        fi
        echo -n "."
        sleep 5
        ((attempt++))
    done
    
    echo " ❌ 접속 불가"
    return 1
}

test_service "MLflow" "5000"
test_service "Airflow" "8080"  
test_service "Jupyter" "8888"

echo ""
echo "✅ 문제 해결 스크립트 완료!"
echo ""
echo "📊 접속 정보:"
echo "   MLflow: http://localhost:5000"
echo "   Airflow: http://localhost:8080 (admin/admin)"
echo "   Jupyter: http://localhost:8888"
echo ""
echo "💡 만약 여전히 문제가 있다면:"
echo "   1. docker logs movie-mlops-airflow-webserver"
echo "   2. docker logs movie-mlops-mlflow"
echo "   3. ./diagnose_services.sh 재실행"
