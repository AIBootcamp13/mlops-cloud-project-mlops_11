#!/bin/bash
# ==============================================================================
# PostgreSQL 초기화 스크립트
# 영화 MLOps를 위한 데이터베이스 및 사용자 생성
# ==============================================================================

set -e

# Airflow 데이터베이스 및 사용자 생성
echo "Creating Airflow database and user..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE USER airflow WITH PASSWORD 'airflow';
    CREATE DATABASE airflow OWNER airflow;
    GRANT ALL PRIVILEGES ON DATABASE airflow TO airflow;
EOSQL

# MLflow 데이터베이스 및 사용자 생성
echo "Creating MLflow database and user..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE USER mlflow WITH PASSWORD 'mlflow';
    CREATE DATABASE mlflow OWNER mlflow;
    GRANT ALL PRIVILEGES ON DATABASE mlflow TO mlflow;
EOSQL

# 영화 데이터 데이터베이스 생성
echo "Creating movie data database..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE movie_data OWNER $POSTGRES_USER;
EOSQL

echo "Database initialization completed!"
