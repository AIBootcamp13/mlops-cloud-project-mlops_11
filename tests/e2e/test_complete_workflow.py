"""
WSL Docker 환경 End-to-End 테스트
전체 Movie MLOps 워크플로우 테스트
"""

import os
import pytest
import requests
import time
import subprocess
from pathlib import Path


class TestMovieMLOpsE2E:
    """Movie MLOps 전체 워크플로우 E2E 테스트"""

    @pytest.mark.e2e
    @pytest.mark.slow
    def test_complete_service_startup(self):
        """전체 서비스 시작 및 상호 연동 테스트"""
        
        # 1. Docker 네트워크 확인
        result = subprocess.run(
            ["docker", "network", "ls", "--filter", "name=movie-mlops-network"],
            capture_output=True,
            text=True
        )
        
        if "movie-mlops-network" not in result.stdout:
            pytest.skip("movie-mlops-network가 생성되지 않았습니다")
        
        print("✅ Docker 네트워크 확인됨")
        
        # 2. 실행 중인 서비스 확인
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=movie-mlops", "--format", "{{.Names}}"],
            capture_output=True,
            text=True
        )
        
        running_containers = result.stdout.strip().split('\n') if result.stdout.strip() else []
        running_containers = [c for c in running_containers if c]
        
        if len(running_containers) < 2:  # 최소 2개 서비스 필요
            pytest.skip(f"충분한 서비스가 실행되지 않았습니다. 현재: {len(running_containers)}개")
        
        print(f"✅ 실행 중인 서비스: {', '.join(running_containers)}")

    @pytest.mark.e2e
    @pytest.mark.network
    def test_service_connectivity_chain(self):
        """서비스 간 연결 체인 테스트"""
        services = {
            "PostgreSQL": {"host": "localhost", "port": 5432, "type": "db"},
            "Redis": {"host": "localhost", "port": 6379, "type": "db"},
            "API": {"url": "http://localhost:8000/health", "type": "http"},
            "MLflow": {"url": "http://localhost:5000", "type": "http"},
            "Jupyter": {"url": "http://localhost:8888", "type": "http"},
        }
        
        connectivity_results = {}
        
        for service_name, config in services.items():
            try:
                if config["type"] == "http":
                    response = requests.get(config["url"], timeout=10)
                    connectivity_results[service_name] = response.status_code == 200
                    if connectivity_results[service_name]:
                        print(f"✅ {service_name} 서비스 연결 성공")
                    else:
                        print(f"⚠️ {service_name} 서비스 응답 코드: {response.status_code}")
                        
                elif config["type"] == "db":
                    if service_name == "PostgreSQL":
                        try:
                            import psycopg2
                            conn = psycopg2.connect(
                                host=config["host"],
                                port=config["port"],
                                dbname="postgres",
                                user="postgres",
                                password="postgres123"
                            )
                            conn.close()
                            connectivity_results[service_name] = True
                            print(f"✅ {service_name} 데이터베이스 연결 성공")
                        except:
                            connectivity_results[service_name] = False
                            print(f"⚠️ {service_name} 데이터베이스 연결 실패")
                    
                    elif service_name == "Redis":
                        try:
                            import redis
                            r = redis.Redis(host=config["host"], port=config["port"])
                            r.ping()
                            connectivity_results[service_name] = True
                            print(f"✅ {service_name} 연결 성공")
                        except:
                            connectivity_results[service_name] = False
                            print(f"⚠️ {service_name} 연결 실패")
                            
            except Exception as e:
                connectivity_results[service_name] = False
                print(f"⚠️ {service_name} 연결 테스트 실패: {e}")
        
        # 최소 2개 이상의 서비스가 정상이어야 함
        successful_connections = sum(connectivity_results.values())
        
        if successful_connections >= 2:
            print(f"✅ {successful_connections}/{len(services)}개 서비스 연결 성공")
        else:
            pytest.fail(f"충분한 서비스가 연결되지 않았습니다: {successful_connections}/{len(services)}")

    @pytest.mark.e2e
    @pytest.mark.api
    def test_api_workflow(self):
        """API 워크플로우 E2E 테스트"""
        api_port = os.getenv("API_PORT", "8000")
        base_url = f"http://localhost:{api_port}"
        
        try:
            # 1. API 헬스 체크
            health_response = requests.get(f"{base_url}/health", timeout=10)
            assert health_response.status_code == 200
            print("✅ API 헬스 체크 성공")
            
            # 2. API 문서 접근
            docs_response = requests.get(f"{base_url}/docs", timeout=10)
            assert docs_response.status_code == 200
            print("✅ API 문서 접근 성공")
            
            # 3. OpenAPI 스키마 확인
            openapi_response = requests.get(f"{base_url}/openapi.json", timeout=10)
            assert openapi_response.status_code == 200
            
            openapi_data = openapi_response.json()
            assert "openapi" in openapi_data
            assert "info" in openapi_data
            print("✅ OpenAPI 스키마 유효")
            
            print("✅ API 워크플로우 E2E 테스트 완료")
            
        except requests.RequestException as e:
            pytest.skip(f"API 서비스가 실행되지 않았습니다: {e}")

    @pytest.mark.e2e
    @pytest.mark.mlflow
    def test_mlflow_workflow(self):
        """MLflow 워크플로우 E2E 테스트"""
        mlflow_port = os.getenv("MLFLOW_PORT", "5000")
        base_url = f"http://localhost:{mlflow_port}"
        
        try:
            # 1. MLflow UI 접근
            ui_response = requests.get(base_url, timeout=10)
            assert ui_response.status_code == 200
            print("✅ MLflow UI 접근 성공")
            
            # 2. API 버전 확인
            version_response = requests.get(f"{base_url}/version", timeout=10)
            if version_response.status_code == 200:
                print("✅ MLflow 버전 API 응답 성공")
            
            # 3. 실험 목록 조회
            experiments_response = requests.get(
                f"{base_url}/api/2.0/mlflow/experiments/list", 
                timeout=10
            )
            assert experiments_response.status_code == 200
            
            experiments_data = experiments_response.json()
            assert "experiments" in experiments_data
            print("✅ MLflow 실험 목록 조회 성공")
            
            print("✅ MLflow 워크플로우 E2E 테스트 완료")
            
        except requests.RequestException as e:
            pytest.skip(f"MLflow 서비스가 실행되지 않았습니다: {e}")

    @pytest.mark.e2e
    @pytest.mark.postgres
    def test_database_workflow(self):
        """데이터베이스 워크플로우 E2E 테스트"""
        try:
            import psycopg2
            
            # 환경 변수에서 설정 읽기
            db_config = {
                "host": os.getenv("POSTGRES_HOST", "localhost"),
                "port": int(os.getenv("POSTGRES_PORT", "5432")),
                "dbname": os.getenv("POSTGRES_DB", "postgres"),
                "user": os.getenv("POSTGRES_USER", "postgres"),
                "password": os.getenv("POSTGRES_PASSWORD", "postgres123")
            }
            
            # 1. 연결 테스트
            conn = psycopg2.connect(**db_config)
            cursor = conn.cursor()
            print("✅ PostgreSQL 연결 성공")
            
            # 2. 테스트 테이블 생성
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_movies (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    rating FLOAT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
            print("✅ 테스트 테이블 생성 성공")
            
            # 3. 데이터 삽입
            cursor.execute("""
                INSERT INTO test_movies (title, rating) 
                VALUES (%s, %s) 
                RETURNING id;
            """, ("Test Movie", 8.5))
            
            movie_id = cursor.fetchone()[0]
            conn.commit()
            print(f"✅ 테스트 데이터 삽입 성공 (ID: {movie_id})")
            
            # 4. 데이터 조회
            cursor.execute("SELECT title, rating FROM test_movies WHERE id = %s;", (movie_id,))
            result = cursor.fetchone()
            
            assert result[0] == "Test Movie"
            assert result[1] == 8.5
            print("✅ 데이터 조회 및 검증 성공")
            
            # 5. 정리
            cursor.execute("DELETE FROM test_movies WHERE id = %s;", (movie_id,))
            conn.commit()
            print("✅ 테스트 데이터 정리 완료")
            
            cursor.close()
            conn.close()
            
            print("✅ 데이터베이스 워크플로우 E2E 테스트 완료")
            
        except ImportError:
            pytest.skip("psycopg2 패키지가 설치되지 않았습니다")
        except psycopg2.Error as e:
            pytest.skip(f"PostgreSQL 연결 실패: {e}")

    @pytest.mark.e2e
    @pytest.mark.redis
    def test_cache_workflow(self):
        """캐시 워크플로우 E2E 테스트"""
        try:
            import redis
            import json
            
            # 환경 변수에서 설정 읽기
            redis_config = {
                "host": os.getenv("REDIS_HOST", "localhost"),
                "port": int(os.getenv("REDIS_PORT", "6379")),
                "db": int(os.getenv("REDIS_DB", "0"))
            }
            
            # 1. 연결 테스트
            r = redis.Redis(**redis_config)
            pong = r.ping()
            assert pong is True
            print("✅ Redis 연결 성공")
            
            # 2. 간단한 키-값 저장
            test_key = "test:movie:123"
            test_data = {
                "title": "Test Movie",
                "rating": 8.5,
                "genre": ["Action", "Drama"]
            }
            
            r.setex(test_key, 300, json.dumps(test_data))  # 5분 TTL
            print("✅ 테스트 데이터 저장 성공")
            
            # 3. 데이터 조회 및 검증
            retrieved_data = json.loads(r.get(test_key).decode('utf-8'))
            
            assert retrieved_data["title"] == test_data["title"]
            assert retrieved_data["rating"] == test_data["rating"]
            assert retrieved_data["genre"] == test_data["genre"]
            print("✅ 데이터 조회 및 검증 성공")
            
            # 4. TTL 확인
            ttl = r.ttl(test_key)
            assert ttl > 0
            print(f"✅ TTL 확인 성공 (남은 시간: {ttl}초)")
            
            # 5. 정리
            r.delete(test_key)
            assert r.get(test_key) is None
            print("✅ 테스트 데이터 정리 완료")
            
            print("✅ 캐시 워크플로우 E2E 테스트 완료")
            
        except ImportError:
            pytest.skip("redis 패키지가 설치되지 않았습니다")
        except redis.ConnectionError as e:
            pytest.skip(f"Redis 연결 실패: {e}")

    @pytest.mark.e2e
    @pytest.mark.env
    def test_environment_workflow(self):
        """환경 설정 워크플로우 E2E 테스트"""
        
        # 1. 환경 변수 로드 테스트
        try:
            from dotenv import load_dotenv
            load_dotenv()
            print("✅ 환경 변수 로드 성공")
        except ImportError:
            print("ℹ️ python-dotenv가 설치되지 않았습니다")
        
        # 2. 필수 환경 변수 확인
        required_vars = [
            "COMPOSE_PROJECT_NAME",
            "ENVIRONMENT",
            "NETWORK_NAME"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"⚠️ 누락된 환경 변수: {', '.join(missing_vars)}")
        else:
            print("✅ 필수 환경 변수 모두 설정됨")
        
        # 3. Docker Compose 파일 존재 확인
        compose_files = list(Path("docker").glob("docker-compose.*.yml"))
        
        if compose_files:
            print(f"✅ Docker Compose 파일 발견: {len(compose_files)}개")
        else:
            pytest.fail("Docker Compose 파일을 찾을 수 없습니다")
        
        # 4. .env.template 존재 확인
        if Path(".env.template").exists():
            print("✅ .env.template 파일 존재")
        else:
            pytest.fail(".env.template 파일이 없습니다")
        
        print("✅ 환경 설정 워크플로우 E2E 테스트 완료")


class TestMLOpsWorkflow:
    """MLOps 워크플로우 통합 테스트"""

    @pytest.mark.e2e
    @pytest.mark.slow
    @pytest.mark.external
    def test_data_pipeline_simulation(self):
        """데이터 파이프라인 시뮬레이션 테스트"""
        
        # 실제 데이터 파이프라인은 구현되지 않았으므로 기본 구조만 테스트
        
        # 1. 데이터 디렉터리 확인
        data_dirs = ["data/raw", "data/processed", "data/external"]
        
        for data_dir in data_dirs:
            data_path = Path(data_dir)
            if data_path.exists():
                print(f"✅ {data_dir} 디렉터리 존재")
            else:
                print(f"ℹ️ {data_dir} 디렉터리 없음 (필요시 생성)")
        
        # 2. 모델 디렉터리 확인
        model_dirs = ["models/trained", "models/deployed", "models/experiments"]
        
        for model_dir in model_dirs:
            model_path = Path(model_dir)
            if model_path.exists():
                print(f"✅ {model_dir} 디렉터리 존재")
            else:
                print(f"ℹ️ {model_dir} 디렉터리 없음 (필요시 생성)")
        
        print("✅ 데이터 파이프라인 구조 확인 완료")

    @pytest.mark.e2e
    @pytest.mark.monitoring
    def test_monitoring_workflow(self):
        """모니터링 워크플로우 테스트"""
        
        # Prometheus 메트릭 수집 테스트
        prometheus_port = os.getenv("PROMETHEUS_PORT", "9090")
        prometheus_url = f"http://localhost:{prometheus_port}"
        
        try:
            # Prometheus 메트릭 엔드포인트 확인
            metrics_response = requests.get(f"{prometheus_url}/api/v1/label/__name__/values", timeout=10)
            
            if metrics_response.status_code == 200:
                metrics_data = metrics_response.json()
                if metrics_data.get("status") == "success":
                    metric_count = len(metrics_data.get("data", []))
                    print(f"✅ Prometheus 메트릭 수집 중: {metric_count}개")
                else:
                    print("⚠️ Prometheus 메트릭 데이터 없음")
            else:
                print("⚠️ Prometheus 메트릭 엔드포인트 접근 실패")
                
        except requests.RequestException:
            print("ℹ️ Prometheus 서비스가 실행되지 않았습니다")
        
        # Grafana 대시보드 테스트
        grafana_port = os.getenv("GRAFANA_PORT", "3000")
        grafana_url = f"http://localhost:{grafana_port}"
        
        try:
            health_response = requests.get(f"{grafana_url}/api/health", timeout=10)
            
            if health_response.status_code == 200:
                print("✅ Grafana 서비스 정상")
            else:
                print("⚠️ Grafana 서비스 응답 문제")
                
        except requests.RequestException:
            print("ℹ️ Grafana 서비스가 실행되지 않았습니다")
        
        print("✅ 모니터링 워크플로우 테스트 완료")


if __name__ == "__main__":
    # 직접 실행 시 E2E 테스트만 실행
    pytest.main([__file__, "-v", "-m", "e2e", "--tb=short"])
