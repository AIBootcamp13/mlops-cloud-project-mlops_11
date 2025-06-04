# MLOps Cloud Project 🚀 (Python 3.11)

## 📋 프로젝트 개요

MLOps 시스템을 9단계로 체계적으로 구축하는 프로젝트입니다. **Python 3.11**을 기반으로 하며, 현재 **1.1 데이터 소스 연결** 단계가 완료되었습니다.

## 🏗️ 프로젝트 구조

```
mlops-cloud-project-mlops_11/
├── 📁 src/                          # 소스 코드 (Python 3.11)
│   └── 📁 data_processing/          # 1단계: 데이터 처리
│       ├── tmdb_api_connector.py    # TMDB API 연동
│       ├── environment_manager.py   # 환경변수 관리
│       ├── response_parser.py       # 응답 파싱
│       ├── rate_limiter.py         # Rate Limiting
│       └── test_integration.py     # 통합 테스트
├── 📁 docs/                        # 문서
│   ├── 📁 00-overview/             # 전체 개요
│   └── 📁 01-data-processing/      # 1단계 문서
├── 🐳 Docker 환경 (Python 3.11)
│   ├── Dockerfile.dev              # 개발용 도커 이미지
│   ├── docker-compose.yml          # 도커 컴포즈 설정
│   └── setup-docker.ps1           # Docker 자동 설정
├── ⚙️ 환경 설정
│   ├── .env.template               # 환경변수 템플릿
│   ├── requirements.txt            # 기본 패키지 (3.11 호환)
│   ├── requirements-dev.txt        # 개발 패키지 (3.11 최적화)
│   ├── pyproject.toml              # 프로젝트 설정 (3.11)
│   └── setup-dev.ps1              # 개발환경 자동 설정
└── 📋 설정 파일들
    ├── .gitignore                  # Git 제외 파일
    ├── .pre-commit-config.yaml     # 코드 품질 (Ruff 최적화)
    ├── pytest.ini                 # 테스트 설정
    └── mypy.ini                   # 타입 체커 (3.11)
```

## 🚀 빠른 시작 (Python 3.11)

### 방법 1: Docker 사용 (추천) 🐳

```bash
# 1. Docker 환경 자동 설정 (Python 3.11)
.\setup-docker.ps1

# 2. 환경변수 설정
# .env 파일에서 TMDB_API_KEY 설정

# 3. 컨테이너 접속
docker exec -it mlops-dev bash

# 4. Python 버전 확인
python --version  # Python 3.11.x

# 5. 테스트 실행
python src/data_processing/test_integration.py
```

### 방법 2: 로컬 환경 사용 (Python 3.11 필요)

```bash
# 1. Python 3.11 버전 확인
python --version  # Python 3.11.x 이어야 함

# 2. 가상환경 생성
python -m venv venv

# 3. 가상환경 활성화 (Windows)
venv\Scripts\activate

# 4. 개발 패키지 설치 (Python 3.11 최적화)
pip install -r requirements-dev.txt

# 5. 환경변수 설정
copy .env.template .env
# .env 파일에서 TMDB_API_KEY 설정

# 6. 테스트 실행
python src\data_processing\test_integration.py
```

### 방법 3: PowerShell 통합 설정

```powershell
# Git + 개발환경 자동 설정 (Python 3.11)
.\setup-dev.ps1
```

## 🎯 Python 3.11 주요 특징 활용

### **성능 향상**
- **10-60% 빠른 실행 속도** (CPython 최적화)
- **향상된 오류 메시지** (더 정확한 디버깅)
- **메모리 사용량 감소**

### **새로운 기능 활용**
- **Exception Groups** (여러 예외 동시 처리)
- **Task Groups** (asyncio 향상)
- **TOML 네이티브 지원** (pyproject.toml)

### **타입 힌팅 강화**
- **Self 타입** 지원
- **TypedDict 개선**
- **Literal 타입 확장**

## 📦 패키지 최적화 (Python 3.11)

### **핵심 패키지**
- **requests 2.31+**: HTTP 클라이언트
- **pandas 2.1+**: 데이터 처리 (3.11 최적화)
- **numpy 1.25+**: 수치 계산
- **pydantic 2.4+**: 데이터 검증

### **개발 도구 (최신 버전)**
- **ruff 0.1.6+**: 빠른 린터 (flake8 대체)
- **black 23.11+**: 코드 포맷터 (3.11 지원)
- **mypy 1.7+**: 타입 체커 (3.11 네이티브)
- **pytest 7.4+**: 테스트 프레임워크

## 🧪 테스트 (Python 3.11 최적화)

```bash
# Docker 환경에서 테스트
docker exec mlops-dev python src/data_processing/test_integration.py

# 개별 컴포넌트 테스트
docker exec mlops-dev pytest src/data_processing/ -v

# 테스트 커버리지 (향상된 성능)
docker exec mlops-dev pytest src/data_processing/ --cov=src --cov-report=html

# 코드 품질 검사 (Ruff - 매우 빠름)
docker exec mlops-dev ruff check src/

# 타입 체크 (3.11 네이티브 지원)
docker exec mlops-dev mypy src/
```

## 🔧 개발 도구 (Python 3.11 최적화)

### **코드 품질 도구**
- **Ruff**: 초고속 린터 (flake8, isort 통합)
- **Black**: 코드 포맷터 (3.11 타겟)
- **MyPy**: 타입 체커 (3.11 네이티브)
- **Bandit**: 보안 검사
- **Pre-commit**: Git 훅 자동화

### **개발 환경**
- **JupyterLab 4.0+**: 최신 노트북 환경
- **IPython 8.17+**: 향상된 Python 쉘
- **Rich**: 터미널 출력 개선

## 📊 Docker 서비스들

```bash
# 모든 서비스 실행
docker-compose up -d

# Jupyter Notebook (Python 3.11)
docker-compose --profile jupyter up -d
# 접속: http://localhost:8889

# 데이터베이스 (선택사항)
docker-compose --profile database up -d

# Redis 캐시 (선택사항)
docker-compose --profile cache up -d

# 컨테이너 상태 확인
docker-compose ps
```

## 🔐 환경변수 (Python 3.11)

```env
# Python 버전 명시
PYTHON_VERSION=3.11

# TMDB API 설정
TMDB_API_KEY=your_api_key_here
TMDB_REGION=KR
TMDB_LANGUAGE=ko-KR

# 로깅 설정
LOG_LEVEL=INFO

# 데이터베이스 (선택사항)
DATABASE_URL=postgresql://mlops_user:mlops_password@localhost:5432/mlops
```

## 🎯 현재 진행 상황

### ✅ **완료된 단계 (Python 3.11 기반)**

#### **1.1 데이터 소스 연결**
- ✅ TMDB API 안전 연동 (requests 2.31+)
- ✅ 환경변수 관리 시스템 (python-dotenv 1.0+)
- ✅ API 응답 파싱 시스템 (pydantic 2.4+)
- ✅ Rate Limiting 처리 (asyncio 3.11 최적화)
- ✅ 통합 테스트 시스템 (pytest 7.4+)

### 🔄 **진행 예정**
- **1.2 데이터 크롤러 개발** (Python 3.11 성능 활용)
- **1.3 ~ 1.7 기타 구성요소들**

## 📈 다음 단계

1. **TMDB API 키 발급** 및 .env 설정
2. **Docker 환경 실행**: `.\setup-docker.ps1`
3. **1.1 단계 테스트 완료** 확인
4. **1.2 데이터 크롤러** 개발 시작

## 🚨 요구사항

- **Python 3.11+** (필수)
- **Docker Desktop** (추천)
- **Git** (버전 관리)
- **TMDB API 키** (데이터 수집)

## 📞 지원

### **문제 해결**
```bash
# Docker 환경 로그 확인
docker-compose logs dev

# 컨테이너 상태 확인
docker exec mlops-dev python --version

# 패키지 확인
docker exec mlops-dev pip list
```

### **도움말**
1. **통합 테스트**: `python src/data_processing/test_integration.py`
2. **로그 확인**: `logs/` 디렉토리
3. **보고서 확인**: `reports/` 디렉토리

---

**🎯 목표**: Python 3.11의 성능을 활용한 완전 자동화된 지능형 MLOps 생태계 구축!
