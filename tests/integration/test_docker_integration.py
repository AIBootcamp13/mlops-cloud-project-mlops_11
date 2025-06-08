"""
WSL Docker 환경 통합 테스트
Docker 서비스들 간의 연동 테스트
"""

import os
import pytest
import requests
import subprocess
import time
from pathlib import Path


class TestDockerIntegration:
    """Docker 서비스 통합 테스트"""

    @pytest.mark.integration
    @pytest.mark.docker
    def test_docker_network_exists(self):
        """Docker 네트워크 존재 확인"""
        try:
            result = subprocess.run(
                ["docker", "network", "ls", "--filter", "name=movie-mlops-network"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if "movie-mlops-network" in result.stdout:
                print("✅ movie-mlops-network 네트워크가 존재합니다")
            else:
                pytest.fail("movie-mlops-network가 생성되지 않았습니다. './scripts/setup/setup_wsl_docker.sh' 실행이 필요합니다")
                
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("Docker가 사용 불가능합니다")

    @pytest.mark.integration
    @pytest.mark.docker
    def test_running_containers(self):
        """실행 중인 Movie MLOps 컨테이너 확인"""
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", "name=movie-mlops", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            containers = result.stdout.strip().split('\n') if result.stdout.strip() else []
            containers = [c for c in containers if c]  # 빈 문자열 제거
            
            if containers:
                print(f"✅ 실행 중인 컨테이너: {', '.join(containers)}")
                return containers
            else:
                print("ℹ️ 실행 중인 Movie MLOps 컨테이너가 없습니다")
                pytest.skip("Docker 서비스가 실행되지 않았습니다")
                
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("Docker가 사용 불가능합니다")

    @pytest.mark.integration
    @pytest.mark.postgres
    def test_postgres_integration(self):
        """PostgreSQL 통합 테스트"""
        try:
            import psycopg2
            
            # 환경 변수에서 설정 읽기
            db_host = os.getenv("POSTGRES_HOST", "localhost")
            db_port = os.getenv("POSTGRES_PORT", "5432")
            db_user = os.getenv("POSTGRES_USER", "postgres")
            db_password = os.getenv("POSTGRES_PASSWORD", "postgres123")
            db_name = os.getenv("POSTGRES_DB", "postgres")
            
            conn_string = f"host={db_host} port={db_port} dbname={db_name} user={db_user} password={db_password}"
            
            try:
                conn = psycopg2.connect(conn_string)
                cursor = conn.cursor()
                
                # 테스트 쿼리 실행
                cursor.execute("SELECT version();")
                version = cursor.fetchone()[0]
                print(f"✅ PostgreSQL 버전: {version}")
                
                # 데이터베이스 목록 확인
                cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
                databases = cursor.fetchall()
                db_names = [db[0] for db in databases]
                print(f"✅ 사용 가능한 데이터베이스: {', '.join(db_names)}")
                
                cursor.close()
                conn.close()
                
            except psycopg2.Error as e:
                pytest.fail(f"PostgreSQL 연결 실패: {e}")
                
        except ImportError:
            pytest.skip("psycopg2 패키지가 설치되지 않았습니다")

    @pytest.mark.integration
    @pytest.mark.redis
    def test_redis_integration(self):
        """Redis 통합 테스트"""
        try:
            import redis
            
            # 환경 변수에서 설정 읽기
            redis_host = os.getenv("REDIS_HOST", "localhost")
            redis_port = int(os.getenv("REDIS_PORT", "6379"))
            redis_db = int(os.getenv("REDIS_DB", "0"))
            
            try:
                r = redis.Redis(host=redis_host, port=redis_port, db=redis_db)
                
                # 연결 테스트
                pong = r.ping()
                assert pong is True
                print("✅ Redis PING 성공")
                
                # 읽기/쓰기 테스트
                test_key = "test:movie-mlops"
                test_value = "integration_test"
                
                r.set(test_key, test_value, ex=60)  # 60초 후 만료
                retrieved_value = r.get(test_key).decode('utf-8')
                
                assert retrieved_value == test_value
                print("✅ Redis 읽기/쓰기 테스트 성공")
                
                # 정리
                r.delete(test_key)
                
            except redis.ConnectionError as e:
                pytest.fail(f"Redis 연결 실패: {e}")
                
        except ImportError:
            pytest.skip("redis 패키지가 설치되지 않았습니다")

    @pytest.mark.integration
    @pytest.mark.api
    @pytest.mark.network
    def test_api_service_integration(self):
        """FastAPI 서비스 통합 테스트"""
        api_port = os.getenv("API_PORT", "8000")
        api_url = f"http://localhost:{api_port}"
        
        try:
            # 헬스 체크
            health_response = requests.get(f"{api_url}/health", timeout=10)
            assert health_response.status_code == 200
            print("✅ API 헬스 체크 성공")
            
            # API 문서 접근
            docs_response = requests.get(f"{api_url}/docs", timeout=10)
            assert docs_response.status_code == 200
            print("✅ API 문서 접근 성공")
            
        except requests.RequestException as e:
            pytest.skip(f"API 서비스가 실행되지 않았습니다: {e}")

    @pytest.mark.integration
    @pytest.mark.mlflow
    @pytest.mark.network
    def test_mlflow_integration(self):
        """MLflow 서비스 통합 테스트"""
        mlflow_port = os.getenv("MLFLOW_PORT", "5000")
        mlflow_url = f"http://localhost:{mlflow_port}"
        
        try:
            # MLflow UI 접근
            response = requests.get(mlflow_url, timeout=10)
            assert response.status_code == 200
            print("✅ MLflow UI 접근 성공")
            
            # API 엔드포인트 테스트
            api_response = requests.get(f"{mlflow_url}/api/2.0/mlflow/experiments/list", timeout=10)
            assert api_response.status_code == 200
            print("✅ MLflow API 접근 성공")
            
        except requests.RequestException as e:
            pytest.skip(f"MLflow 서비스가 실행되지 않았습니다: {e}")

    @pytest.mark.integration
    @pytest.mark.airflow
    @pytest.mark.network
    def test_airflow_integration(self):
        """Airflow 서비스 통합 테스트"""
        airflow_port = os.getenv("AIRFLOW_WEBSERVER_PORT", "8080")
        airflow_url = f"http://localhost:{airflow_port}"
        
        try:
            # Airflow 헬스 체크
            health_response = requests.get(f"{airflow_url}/health", timeout=10)
            assert health_response.status_code == 200
            print("✅ Airflow 헬스 체크 성공")
            
        except requests.RequestException as e:
            pytest.skip(f"Airflow 서비스가 실행되지 않았습니다: {e}")

    @pytest.mark.integration
    @pytest.mark.monitoring
    @pytest.mark.network
    def test_monitoring_integration(self):
        """모니터링 서비스 통합 테스트"""
        # Prometheus
        prometheus_port = os.getenv("PROMETHEUS_PORT", "9090")
        prometheus_url = f"http://localhost:{prometheus_port}"
        
        try:
            prometheus_response = requests.get(f"{prometheus_url}/-/healthy", timeout=10)
            assert prometheus_response.status_code == 200
            print("✅ Prometheus 서비스 정상")
        except requests.RequestException:
            print("ℹ️ Prometheus 서비스가 실행되지 않았습니다")
        
        # Grafana
        grafana_port = os.getenv("GRAFANA_PORT", "3000")
        grafana_url = f"http://localhost:{grafana_port}"
        
        try:
            grafana_response = requests.get(f"{grafana_url}/api/health", timeout=10)
            assert grafana_response.status_code == 200
            print("✅ Grafana 서비스 정상")
        except requests.RequestException:
            print("ℹ️ Grafana 서비스가 실행되지 않았습니다")


class TestEnvironmentConfiguration:
    """환경 설정 통합 테스트"""

    @pytest.mark.integration
    @pytest.mark.env
    def test_env_file_loading(self):
        """환경 변수 파일 로딩 테스트"""
        try:
            from dotenv import load_dotenv
            
            # .env 파일 로드
            env_loaded = load_dotenv()
            
            if env_loaded:
                print("✅ .env 파일 로드 성공")
            else:
                print("ℹ️ .env 파일이 없거나 로드 실패")
            
            # 주요 환경 변수 확인
            important_vars = [
                "COMPOSE_PROJECT_NAME",
                "ENVIRONMENT", 
                "NETWORK_NAME",
                "POSTGRES_PASSWORD",
                "SECRET_KEY"
            ]
            
            for var in important_vars:
                value = os.getenv(var)
                if value:
                    print(f"✅ {var}: ****")  # 보안상 값은 마스킹
                else:
                    print(f"⚠️ {var}: 설정되지 않음")
                    
        except ImportError:
            pytest.skip("python-dotenv 패키지가 설치되지 않았습니다")

    @pytest.mark.integration
    @pytest.mark.docker
    def test_docker_compose_config(self):
        """Docker Compose 설정 유효성 테스트"""
        compose_files = list(Path("docker").glob("docker-compose.*.yml"))
        
        if not compose_files:
            pytest.fail("Docker Compose 파일을 찾을 수 없습니다")
        
        valid_files = []
        
        for compose_file in compose_files:
            try:
                result = subprocess.run(
                    ["docker-compose", "-f", str(compose_file), "config"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=Path.cwd()
                )
                
                if result.returncode == 0:
                    valid_files.append(compose_file.name)
                    print(f"✅ {compose_file.name} 설정 유효")
                else:
                    print(f"❌ {compose_file.name} 설정 오류:")
                    print(result.stderr)
                    
            except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                print(f"⚠️ {compose_file.name} 검증 실패: {e}")
        
        if valid_files:
            print(f"✅ 유효한 Docker Compose 파일: {', '.join(valid_files)}")
        else:
            pytest.fail("유효한 Docker Compose 파일이 없습니다")


if __name__ == "__main__":
    # 직접 실행 시 통합 테스트만 실행
    pytest.main([__file__, "-v", "-m", "integration", "--tb=short"])
