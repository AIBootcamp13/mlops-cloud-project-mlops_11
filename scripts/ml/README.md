# 🎬 Movie-MLOps 통합 실행 스크립트

이 디렉토리에는 Movie-MLOps 시스템의 ML 비즈니스 로직과 전체 스택을 실행하기 위한 통합 스크립트가 포함되어 있습니다.

## 📁 메인 스크립트

```
/
├── run_ml.sh                   # 🎯 메인 통합 실행 스크립트
├── run_movie_mlops.sh          # 기존 Docker 스택 관리 스크립트
└── scripts/ml/
    ├── README.md               # 이 파일
    ├── run_ml_pipeline.sh      # 완전한 ML 파이프라인 스크립트
    ├── run_ml_pipeline.py      # Python 버전 ML 스크립트
    └── quick_ml_run.sh         # 간단한 ML 실행 스크립트
```

## 🚀 사용 방법

### 1. **ML만 실행** (기본)
```bash
cd /mnt/c/dev/movie-mlops
chmod +x run_ml.sh
./run_ml.sh
```

### 2. **전체 스택 실행** (백엔드 + 프론트엔드 + ML)
```bash
cd /mnt/c/dev/movie-mlops
./run_ml.sh --full-stack
# 또는
./run_ml.sh -f
```

## 📋 기능 비교

| 실행 모드 | 명령어 | 포함 서비스 |
|-----------|--------|-------------|
| **ML만** | `./run_ml.sh` | ML 파이프라인만 실행 |
| **전체 스택** | `./run_ml.sh --full-stack` | 백엔드 + 프론트엔드 + ML + 인프라 |

## 🎯 실행 후 확인할 수 있는 서비스

### ML만 실행 시:
- ✅ **ML 파이프라인**: 모델 훈련 및 평가
- ✅ **MLflow**: http://localhost:5000
- ✅ **API 문서**: http://localhost:8000/docs

### 전체 스택 실행 시:
- ✅ **백엔드 API**: http://localhost:8000
- ✅ **프론트엔드**: http://localhost:3000  
- ✅ **MLflow**: http://localhost:5000
- ✅ **Jupyter**: http://localhost:8888
- ✅ **Grafana**: http://localhost:3000
- ✅ **Airflow**: http://localhost:8080
- ✅ **ML 파이프라인**: 자동 실행

## 🔧 스크립트 특징

### 자동 의존성 관리
- ✅ **PyTorch 자동 설치**: torch, torchvision, torchaudio
- ✅ **ML 라이브러리 자동 설치**: tqdm, scikit-learn, matplotlib, seaborn, icecream
- ✅ **컨테이너 자동 감지**: 최적의 컨테이너를 자동으로 찾아 실행

### 스마트 실행
- ✅ **컨테이너 상태 확인**: 실행 중인 컨테이너를 자동 감지
- ✅ **자동 스택 시작**: 필요 시 Docker 스택을 자동으로 시작
- ✅ **의존성 확인**: 설치된 패키지를 확인하고 필요 시에만 설치

## 🐛 문제 해결

### 1. 컨테이너를 찾을 수 없음
```bash
❌ API 컨테이너가 실행되지 않았습니다.
```

**해결책:**
```bash
# ML 스택 시작
./run_movie_mlops.sh
# 메뉴에서 2번 선택

# 또는 전체 스택으로 실행
./run_ml.sh --full-stack
```

### 2. 의존성 오류
```bash
ModuleNotFoundError: No module named 'torch'
```

**해결책:**
- 스크립트가 자동으로 의존성을 설치합니다
- 수동 설치가 필요한 경우:
```bash
docker exec movie-mlops-api pip install torch tqdm scikit-learn
```

### 3. 포트 충돌
```bash
port is already allocated
```

**해결책:**
```bash
# 기존 스택 종료
docker compose down

# 포트 사용 프로세스 확인
lsof -i :8000
lsof -i :3000
```

### 4. 프론트엔드 시작 실패
```bash
⚠️  프론트엔드 서버 시작 중...
```

**해결책:**
```bash
# 수동으로 프론트엔드 시작
cd src/frontend
npm install
npm start
```

## 💡 추가 팁

### 개발 워크플로우
1. **첫 실행**: `./run_ml.sh --full-stack` (모든 것 포함)
2. **ML 개발**: `./run_ml.sh` (ML만 빠르게)
3. **전체 테스트**: `./run_ml.sh --full-stack` (전체 확인)

### 로그 확인
```bash
# 컨테이너 로그
docker logs movie-mlops-api
docker logs movie-mlops-jupyter

# 프론트엔드 로그
tail -f logs/frontend.log
```

### 성능 모니터링
- **Grafana**: http://localhost:3000 (admin/admin123)
- **MLflow**: http://localhost:5000 (실험 추적)
- **API 메트릭**: http://localhost:8000/metrics

## 📝 추가 스크립트

프로젝트 내 다른 유용한 스크립트들:

```bash
# 기본 Docker 스택 관리
./run_movie_mlops.sh

# ML 전용 스크립트들
./scripts/ml/run_ml_pipeline.sh      # 상세한 ML 파이프라인
./scripts/ml/quick_ml_run.sh         # 간단한 ML 실행
python scripts/ml/run_ml_pipeline.py # Python 버전
```

---

*"하나의 명령으로 ML부터 전체 스택까지 완벽하게 실행하세요!"* 🚀