# Movie Recommendation MLOps Pipeline

🎬 영화 추천 시스템을 위한 완전한 MLOps 파이프라인

## 🚀 WSL Docker 환경에서 시작하기

### 📋 사전 요구사항

- Windows 11/10 with WSL2
- Docker Desktop for Windows (WSL2 백엔드 활성화)
- Git

### ⚡ 빠른 시작

1. **리포지토리 클론**
   ```bash
   git clone <repository-url>
   cd movie-mlops
   ```

2. **실행 권한 부여**
   ```bash
   chmod +x run_movie_mlops.sh
   chmod +x scripts/setup/*.sh
   chmod +x scripts/docker/*.sh
   ```

3. **통합 개발 환경 실행**
   ```bash
   ./run_movie_mlops.sh
   ```

4. **메뉴에서 선택**
   - `1` → 전체 환경 설정 (최초 1회)
   - `2` → 전체 서비스 시작

### 🐳 개별 서비스 실행

#### 기본 인프라
```bash
# PostgreSQL + Redis
docker compose -f docker/docker-compose.postgres.yml up -d
docker compose -f docker/docker-compose.redis.yml up -d
```

#### 개발 환경
```bash
# Jupyter Notebook
docker compose -f docker/docker-compose.jupyter.yml up -d

# FastAPI
docker compose -f docker/docker-compose.api.yml up -d
```

#### MLOps 서비스
```bash
# MLflow
docker compose -f docker/docker-compose.mlflow.yml up -d

# Airflow
docker compose -f docker/docker-compose.airflow.yml up -d

# Feast 피처 스토어 (내장된 FastAPI 서버)
docker compose -f docker/docker-compose.feast.yml up -d

# PyTorch 추론
docker compose -f docker/docker-compose.pytorch.yml up -d
```

#### 모니터링
```bash
# Prometheus + Grafana
docker compose -f docker/docker-compose.monitoring.yml up -d
```

#### 이벤트 스트리밍
```bash
# Kafka + Zookeeper
docker compose -f docker/docker-compose.kafka.yml up -d
```

## 📊 서비스 접속 정보

| 서비스 | URL | 인증 정보 |
|---------|-----|-----------|
| 🪐 Jupyter Notebook | http://localhost:8888 | Token: `movie-mlops-jupyter` |
| 🚀 FastAPI 문서 | http://localhost:8000/docs | - |
| 📈 MLflow UI | http://localhost:5000 | - |
| 🌊 Airflow UI | http://localhost:8080 | admin/admin |
| 🍃 Feast Feature Server (FastAPI) | http://localhost:6567/docs | - |
| 📊 Grafana | http://localhost:3000 | admin/admin123 |
| 🔍 Prometheus | http://localhost:9090 | - |
| 🗄️ pgAdmin | http://localhost:5050 | admin@movie-mlops.local/admin123 |
| 🔴 Redis Commander | http://localhost:8081 | - |
| 📡 Kafka UI | http://localhost:8082 | - |

## 🏗️ 아키텍처 구조

### 📁 디렉터리 구조
```
movie-mlops/
├── 📄 .env.template           # 환경 변수 템플릿
├── 🚀 run_movie_mlops.sh      # 메인 실행 스크립트
├── 📁 docker/                 # Docker 설정
│   ├── 📁 dockerfiles/        # 커스텀 Dockerfile들
│   ├── 📁 configs/            # 서비스 설정 파일들
│   └── 📄 docker-compose.*.yml # 서비스별 Docker Compose
├── 📁 requirements/           # 세분화된 의존성 관리
│   ├── 📄 base.txt           # 기본 의존성
│   ├── 📄 api.txt            # FastAPI 의존성
│   ├── 📄 mlflow.txt         # MLflow 의존성
│   ├── 📄 airflow.txt        # Airflow 의존성
│   ├── 📄 feast.txt          # Feast 의존성
│   ├── 📄 pytorch.txt        # PyTorch 의존성
│   ├── 📄 kafka.txt          # Kafka 의존성
│   ├── 📄 monitoring.txt     # 모니터링 의존성
│   ├── 📄 jupyter.txt        # Jupyter 의존성
│   ├── 📄 postgres.txt       # PostgreSQL 의존성
│   └── 📄 redis.txt          # Redis 의존성
├── 📁 scripts/               # 실행 스크립트들
│   ├── 📁 setup/             # 설정 스크립트
│   └── 📁 docker/            # Docker 관리 스크립트
├── 📁 src/                   # 소스 코드
├── 📁 tests/                 # 테스트 코드
├── 📁 docs/                  # 문서
├── 📁 data/                  # 데이터 디렉터리
├── 📁 models/                # 모델 디렉터리
├── 📁 logs/                  # 로그 디렉터리
└── 📁 notebooks/             # Jupyter 노트북
```

### 🔧 핵심 기능

#### 1️⃣ 데이터 파이프라인
- **Airflow**: 워크플로우 오케스트레이션
- **PostgreSQL**: 메타데이터 및 피처 저장소
- **Feast**: 실시간 피처 서빙 (내장된 FastAPI 서버 사용)

#### 2️⃣ 모델 관리
- **MLflow**: 실험 추적 및 모델 레지스트리
- **PyTorch**: 딥러닝 모델 추론
- **FastAPI**: 모델 서빙 API

#### 3️⃣ 모니터링
- **Prometheus**: 메트릭 수집
- **Grafana**: 대시보드 시각화
- **로그 관리**: 중앙집중식 로깅

#### 4️⃣ 이벤트 스트리밍
- **Kafka**: 실시간 데이터 스트리밍
- **Schema Registry**: 스키마 관리

## 🛠️ 개발 워크플로우

### 🔄 일반적인 개발 사이클

1. **환경 설정**
   ```bash
   ./run_movie_mlops.sh
   # 메뉴에서 1번 선택 (최초 1회)
   ```

2. **개발 환경 시작**
   ```bash
   # 메뉴에서 5번 선택 (Jupyter + API)
   ```

3. **데이터 탐색 및 모델 개발**
   - Jupyter Notebook에서 데이터 분석
   - MLflow로 실험 추적

4. **모델 배포**
   - MLflow에서 모델 등록
   - FastAPI로 서빙

5. **모니터링**
   - Grafana에서 성능 모니터링
   - Prometheus 메트릭 확인

### 🧪 테스트

```bash
# 전체 테스트 실행
./run_tests.sh

# 개별 서비스 테스트
python -m pytest tests/unit/
python -m pytest tests/integration/
python -m pytest tests/e2e/
```

## 🌍 환경 설정

### 📝 .env 파일 설정

1. `.env.template`을 `.env`로 복사
2. 필수 환경 변수 설정:

```bash
# 외부 API
TMDB_API_KEY=your-tmdb-api-key-here

# 보안
SECRET_KEY=your-super-secret-key-change-this-in-production

# 데이터베이스
POSTGRES_PASSWORD=your-secure-password

# MLOps 설정
AIRFLOW__WEBSERVER__SECRET_KEY=your-airflow-secret-key
```

### 🔧 리소스 제한 조정

Docker 리소스 제한은 `.env` 파일에서 조정 가능:

```bash
# CPU 및 메모리 제한
AIRFLOW_MEMORY_LIMIT=2g
MLFLOW_MEMORY_LIMIT=1g
PYTORCH_MEMORY_LIMIT=4g
API_MEMORY_LIMIT=1g
POSTGRES_MEMORY_LIMIT=1g
REDIS_MEMORY_LIMIT=512m
```

## 🚨 문제 해결

### 일반적인 문제들

#### Docker 네트워크 오류
```bash
# 네트워크 재생성
docker network rm movie-mlops-network
docker network create movie-mlops-network
```

#### 포트 충돌
```bash
# 실행 중인 컨테이너 확인
docker ps

# 특정 포트 사용 프로세스 확인
netstat -tulpn | grep :8080
```

#### 권한 문제 (WSL)
```bash
# 실행 권한 부여
chmod +x run_movie_mlops.sh
chmod +x scripts/**/*.sh

# 파일 소유권 확인
ls -la
```

#### 메모리 부족
```bash
# Docker 리소스 확인
docker system df

# 사용하지 않는 리소스 정리
docker system prune -a
```

### 🎯 Python 환경 문제

Python 3.11 버전 및 패키지 설치 문제가 발생하면:

```bash
# Python 3.11 확인
python --version  # 반드시 3.11.x 여야 함

# 환경 문제 일괄 해결
./scripts/setup/fix_wsl_issues.sh

# 상세한 문제 해결은 문서 참조
# docs/troubleshooting/PYTHON_ENVIRONMENT.md
```

### 🔍 로그 확인

```bash
# 특정 서비스 로그
docker compose -f docker/docker-compose.[서비스].yml logs -f

# 전체 로그
./run_movie_mlops.sh
# 메뉴에서 10번 선택
```

## 📚 추가 문서

- [아키텍처 가이드](docs/overview/)
- [빠른 설정 가이드](docs/setup/QUICK_SETUP.md)
- [상세 문제 해결](docs/troubleshooting/PYTHON_ENVIRONMENT.md) - Python 3.11 환경 문제
- [API 문서](http://localhost:8000/docs) (서비스 실행 후)

## 🤝 기여하기

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 있습니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 📞 지원

문제가 발생하거나 질문이 있으시면:

- 🐛 [Issues](../../issues) 페이지에 버그 리포트
- 💡 [Discussions](../../discussions) 페이지에 아이디어 공유
- 📧 이메일: [프로젝트 담당자 이메일]

---

**Made with ❤️ by Movie MLOps Team**
