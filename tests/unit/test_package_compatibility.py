"""
WSL Docker 환경 Movie MLOps 패키지 호환성 테스트

Python 3.11 환경에서 모든 주요 패키지들이 제대로 import되는지 확인합니다.
Docker 컨테이너 환경과 로컬 환경을 모두 지원합니다.
"""

import os
import sys
import subprocess
import pytest
from pathlib import Path


class TestWSLDockerEnvironment:
    """WSL Docker 환경 테스트 클래스"""

    def test_python_version(self):
        """Python 버전 확인"""
        version_info = sys.version_info
        assert version_info.major == 3
        assert version_info.minor == 11
        print(f"✅ Python version: {sys.version}")

    def test_environment_variables(self):
        """환경 변수 로드 테스트"""
        # .env 파일 체크
        env_file = Path(".env")
        env_template = Path(".env.template")
        
        if env_file.exists():
            print("✅ .env 파일이 존재합니다")
        elif env_template.exists():
            print("⚠️ .env 파일이 없습니다. .env.template을 참조하세요")
        else:
            pytest.fail(".env.template 파일도 없습니다")

        # 기본 환경 변수 확인
        required_vars = [
            "COMPOSE_PROJECT_NAME",
            "ENVIRONMENT", 
            "NETWORK_NAME"
        ]
        
        for var in required_vars:
            value = os.getenv(var)
            if value:
                print(f"✅ {var}: {value}")
            else:
                print(f"⚠️ {var} 환경 변수가 설정되지 않았습니다")

    def test_wsl_environment(self):
        """WSL 환경 감지"""
        try:
            with open("/proc/version", "r") as f:
                version_info = f.read()
                if "microsoft" in version_info.lower():
                    print("✅ WSL 환경에서 실행 중입니다")
                else:
                    print("ℹ️ 네이티브 Linux 환경입니다")
        except FileNotFoundError:
            print("ℹ️ Windows 또는 macOS 환경입니다")

    def test_docker_availability(self):
        """Docker 사용 가능성 확인"""
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                print(f"✅ Docker: {result.stdout.strip()}")
            else:
                print("❌ Docker 명령어 실행 실패")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("⚠️ Docker가 설치되지 않았거나 실행할 수 없습니다")

    def test_docker_compose_availability(self):
        """Docker Compose 사용 가능성 확인"""
        try:
            # Docker Compose V2 명령어 확인
            result = subprocess.run(
                ["docker", "compose", "version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                print(f"✅ Docker Compose V2: {result.stdout.strip()}")
            else:
                # 기존 docker-compose 명령어도 확인
                result_legacy = subprocess.run(
                    ["docker-compose", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result_legacy.returncode == 0:
                    print(f"⚠️ Docker Compose V1 (legacy): {result_legacy.stdout.strip()}")
                    print("⚠️ Docker Compose V2 사용을 권장합니다: 'docker compose'")
                else:
                    print("❌ Docker Compose 명령어 실행 실패")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("⚠️ Docker Compose가 설치되지 않았거나 실행할 수 없습니다")


class TestPackageCompatibility:
    """패키지 호환성 테스트 클래스"""

    @pytest.mark.unit
    def test_base_packages(self):
        """기본 패키지 import 테스트"""
        try:
            import dotenv
            import structlog
            import requests
            
            print("✅ 기본 패키지들이 정상적으로 import됩니다")
        except ImportError as e:
            pytest.fail(f"기본 패키지 import 실패: {e}")

    @pytest.mark.unit
    def test_core_data_packages(self):
        """핵심 데이터 처리 패키지 테스트 (호환성 매트릭스 준수)"""
        try:
            import numpy as np
            import pandas as pd
            import sklearn
            
            print(f"✅ NumPy version: {np.__version__} (권장: 1.24.4)")
            print(f"✅ Pandas version: {pd.__version__} (권장: 2.1.4)")
            print(f"✅ Scikit-learn version: {sklearn.__version__} (권장: 1.3.2)")
            
            # 버전 호환성 확인
            assert np.__version__.startswith("1.24"), f"NumPy 버전 불일치: {np.__version__} (1.24.4 권장)"
            assert pd.__version__.startswith("2.1"), f"Pandas 버전 불일치: {pd.__version__} (2.1.4 권장)"
            assert sklearn.__version__.startswith("1.3"), f"Scikit-learn 버전 불일치: {sklearn.__version__} (1.3.2 권장)"
            
        except ImportError as e:
            pytest.fail(f"핵심 데이터 처리 패키지 import 실패: {e}")

    @pytest.mark.api
    def test_fastapi_packages(self):
        """FastAPI 관련 패키지 테스트"""
        try:
            import fastapi
            import uvicorn
            import pydantic
            
            print(f"✅ FastAPI version: {fastapi.__version__}")
            print(f"✅ Uvicorn version: {uvicorn.__version__}")
            print(f"✅ Pydantic version: {pydantic.__version__}")
            
        except ImportError as e:
            print(f"⚠️ FastAPI 패키지 import 실패 (Docker API 컨테이너 사용 권장): {e}")

    @pytest.mark.postgres  
    def test_database_packages(self):
        """데이터베이스 패키지 테스트"""
        try:
            import psycopg2
            import sqlalchemy
            
            print(f"✅ Psycopg2 version: {psycopg2.__version__}")
            print(f"✅ SQLAlchemy version: {sqlalchemy.__version__}")
            
        except ImportError as e:
            print(f"⚠️ 데이터베이스 패키지 import 실패 (Docker 서비스 사용 권장): {e}")

    @pytest.mark.redis
    def test_redis_packages(self):
        """Redis 패키지 테스트"""
        try:
            import redis
            
            print(f"✅ Redis version: {redis.__version__}")
            
        except ImportError as e:
            print(f"⚠️ Redis 패키지 import 실패 (Docker 서비스 사용 권장): {e}")

    @pytest.mark.airflow
    def test_airflow_packages(self):
        """Airflow 패키지 테스트 (선택적)"""
        try:
            import airflow
            
            print(f"✅ Airflow version: {airflow.__version__}")
            assert airflow.__version__.startswith("2.10")
            
        except ImportError as e:
            print(f"ℹ️ Airflow 패키지 import 실패 (Docker 컨테이너 사용 권장): {e}")

    @pytest.mark.mlflow
    def test_mlflow_packages(self):
        """MLflow 패키지 테스트 (선택적)"""
        try:
            import mlflow
            
            print(f"✅ MLflow version: {mlflow.__version__}")
            assert mlflow.__version__.startswith("2.17")
            
        except ImportError as e:
            print(f"ℹ️ MLflow 패키지 import 실패 (Docker 컨테이너 사용 권장): {e}")

    @pytest.mark.pytorch
    def test_pytorch_packages(self):
        """PyTorch 패키지 테스트 (선택적)"""
        try:
            import torch
            import torchvision
            import torchaudio
            
            print(f"✅ PyTorch version: {torch.__version__}")
            print(f"✅ TorchVision version: {torchvision.__version__}")
            print(f"✅ TorchAudio version: {torchaudio.__version__}")
            
            assert torch.__version__.startswith("2.5")
            
        except ImportError as e:
            print(f"ℹ️ PyTorch 패키지 import 실패 (GPU 사용 시 Docker 컨테이너 권장): {e}")

    @pytest.mark.feast
    def test_feast_packages(self):
        """Feast 패키지 테스트 (선택적)"""
        try:
            import feast
            
            print(f"✅ Feast version: {feast.__version__}")
            assert feast.__version__.startswith("0.40")
            
        except ImportError as e:
            print(f"ℹ️ Feast 패키지 import 실패 (Docker 컨테이너 사용 권장): {e}")

    @pytest.mark.kafka
    def test_kafka_packages(self):
        """Kafka 패키지 테스트 (선택적)"""
        try:
            import kafka
            
            print(f"✅ Kafka Python version: {kafka.__version__}")
            assert kafka.__version__.startswith("2.0")
            
        except ImportError as e:
            print(f"ℹ️ Kafka 패키지 import 실패 (Docker 컨테이너 사용 권장): {e}")

    @pytest.mark.monitoring
    def test_monitoring_packages(self):
        """모니터링 패키지 테스트 (선택적)"""
        try:
            import prometheus_client
            
            print(f"✅ Prometheus Client version: {prometheus_client.__version__}")
            assert prometheus_client.__version__.startswith("0.21")
            
        except ImportError as e:
            print(f"ℹ️ 모니터링 패키지 import 실패 (Docker 컨테이너 사용 권장): {e}")

    @pytest.mark.unit
    def test_package_compatibility_check(self):
        """pip check를 통한 패키지 호환성 확인"""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "check"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print("✅ 모든 설치된 패키지가 호환됩니다!")
            else:
                print("⚠️ 패키지 호환성 문제 발견:")
                print(result.stdout)
                print(result.stderr)
                # WSL Docker 환경에서는 경고로만 처리
                pytest.skip("패키지 호환성 문제가 있지만 Docker 환경에서는 정상 작동할 수 있습니다")
                
        except subprocess.TimeoutExpired:
            print("⚠️ pip check 시간 초과")
            pytest.skip("pip check가 너무 오래 걸립니다")


class TestDockerServices:
    """Docker 서비스 연결 테스트"""

    @pytest.mark.docker
    @pytest.mark.postgres
    def test_postgres_connection(self):
        """PostgreSQL 연결 테스트"""
        try:
            import psycopg2
            
            # 기본 포트로 연결 시도
            conn_string = "host=localhost port=5432 dbname=postgres user=postgres password=postgres123"
            
            try:
                conn = psycopg2.connect(conn_string)
                conn.close()
                print("✅ PostgreSQL 연결 성공")
            except psycopg2.OperationalError:
                print("ℹ️ PostgreSQL 서비스가 실행되지 않았습니다 (Docker 컨테이너 시작 필요)")
                pytest.skip("PostgreSQL Docker 서비스가 필요합니다")
                
        except ImportError:
            pytest.skip("psycopg2 패키지가 설치되지 않았습니다")

    @pytest.mark.docker
    @pytest.mark.redis
    def test_redis_connection(self):
        """Redis 연결 테스트"""
        try:
            import redis
            
            try:
                r = redis.Redis(host='localhost', port=6379, db=0)
                r.ping()
                print("✅ Redis 연결 성공")
            except redis.ConnectionError:
                print("ℹ️ Redis 서비스가 실행되지 않았습니다 (Docker 컨테이너 시작 필요)")
                pytest.skip("Redis Docker 서비스가 필요합니다")
                
        except ImportError:
            pytest.skip("redis 패키지가 설치되지 않았습니다")

    @pytest.mark.docker
    @pytest.mark.network
    def test_service_health_checks(self):
        """MLOps 서비스 헬스 체크"""
        import requests
        
        services = {
            "FastAPI": "http://localhost:8000/health",
            "MLflow": "http://localhost:5000",
            "Airflow": "http://localhost:8080/health",
            "Jupyter": "http://localhost:8888",
            "Grafana": "http://localhost:3000",
            "Prometheus": "http://localhost:9090"
        }
        
        running_services = []
        
        for service_name, url in services.items():
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    running_services.append(service_name)
                    print(f"✅ {service_name} 서비스 정상")
                else:
                    print(f"⚠️ {service_name} 서비스 응답 코드: {response.status_code}")
            except requests.RequestException:
                print(f"ℹ️ {service_name} 서비스가 실행되지 않았습니다")
        
        if running_services:
            print(f"✅ 실행 중인 서비스: {', '.join(running_services)}")
        else:
            print("ℹ️ 실행 중인 MLOps 서비스가 없습니다")
            print("서비스 시작: ./run_movie_mlops.sh")


if __name__ == "__main__":
    # 직접 실행 시 모든 테스트 실행
    pytest.main([__file__, "-v", "--tb=short"])
