# 📋 MLOps 개발 가이드

> **팀: mlops-cloud-project-mlops_11 | 빠르고 간결한 개발 환경 설정 및 일일 워크플로**

---

## 🚀 **필수 설정** (4단계, ~5분)

### 1️⃣ **저장소 클론 및 이동**
```bash
git clone https://github.com/AIBootcamp13/mlops-cloud-project-mlops_11.git
cd mlops-cloud-project-mlops_11
```

### 2️⃣ **가상환경 생성 및 활성화**
```bash
# Python 3.11 가상환경 생성 (없으면 python3 사용)
python3.11 -m venv mlops-env
source mlops-env/bin/activate

# pip 업그레이드
pip install --upgrade pip
```

### 3️⃣ **의존성 설치**
```bash
# 모든 필수 패키지 설치
pip install -r requirements.txt

# 설치 확인
python -c "import pandas, numpy, sklearn, fastapi, mlflow; print('✅ 설치 완료!')"
```

### 4️⃣ **서비스 시작 및 테스트**
```bash
# Docker로 전체 스택 시작
docker-compose -f docker/docker-compose.monitoring.yml up -d

# API 테스트
curl http://localhost:8000/health
```

---

## 💻 **일일 개발 워크플로**

### **로컬 개발 (Docker 사용)**
```bash
# 1. 가상환경 활성화
source mlops-env/bin/activate

# 2. 서비스 시작
docker-compose up -d

# 3. 개발 서버 시작 (hot reload)
uvicorn src.api.main:app --reload --port 8000

# 4. MLflow UI 확인
open http://localhost:5000
```

### **API 개발 및 테스트**
```bash
# 기본 엔드포인트 테스트
curl http://localhost:8000
curl http://localhost:8000/health
curl http://localhost:8000/docs  # Swagger UI

# 영화 예측 테스트
curl -X POST "http://localhost:8000/predict/movie" \
  -H "Content-Type: application/json" \
  -d '{"startYear": 2010, "runtimeMinutes": 148, "numVotes": 1000000}'
```

### **모델 훈련 및 실험**
```bash
# 모델 훈련
python scripts/train_model.py

# MLflow 실험 추적
mlflow ui --port 5000

# 모델 평가
python scripts/evaluate_model.py
```

---

## 🛠️ **자주 사용하는 명령어**

### **Docker 관리**
```bash
# 서비스 시작/중지
docker-compose up -d                    # 백그라운드 시작
docker-compose down                     # 중지
docker-compose restart api             # API 서비스 재시작
docker-compose logs -f api             # 실시간 로그

# 이미지 관리
docker-compose build --no-cache        # 캐시 없이 빌드
docker system prune -f                 # 불필요한 이미지 정리
```

### **개발 도구**
```bash
# 코드 품질 검사
black src/ scripts/ tests/              # 포매팅
flake8 src/ --max-line-length=88        # 린팅
python scripts/tests/test_section*.py   # 테스트 실행

# Git 워크플로
git checkout -b feature/새기능          # 피처 브랜치
git add . && git commit -m "feat: 설명"  # 커밋
git push origin feature/새기능          # 푸시
```

---

## 🔧 **빠른 문제 해결**

### **포트 충돌**
```bash
# 포트 8000 사용 중인 프로세스 확인 및 종료
lsof -i :8000
kill -9 $(lsof -t -i:8000)

# 다른 포트 사용
uvicorn src.api.main:app --port 8001
```

### **Docker 문제**
```bash
# 컨테이너 상태 확인
docker-compose ps

# 모든 컨테이너 재시작
docker-compose down && docker-compose up -d

# 로그 확인
docker-compose logs api
```

### **모델 로딩 문제**
```bash
# 모델 파일 확인
ls -la models/

# 모델 재훈련
python scripts/train_model.py

# 권한 문제 해결
chmod -R 755 models/
```

### **패키지 충돌**
```bash
# 캐시 정리 후 재설치
pip cache purge
pip install --no-cache-dir -r requirements.txt

# 가상환경 재생성
deactivate
rm -rf mlops-env
python3.11 -m venv mlops-env
source mlops-env/bin/activate
```

---

## 📱 **접속 주소**

| 서비스 | URL | 설명 |
|--------|-----|------|
| **API 서버** | http://localhost:8000 | 메인 API |
| **API 문서** | http://localhost:8000/docs | Swagger UI |
| **MLflow** | http://localhost:5000 | 실험 추적 |
| **Grafana** | http://localhost:3000 | 모니터링 (admin/mlops123) |
| **Prometheus** | http://localhost:9090 | 메트릭 수집 |

---

## 🧪 **섹션별 테스트**

```bash
# 전체 테스트 실행
for section in 1 2 3 4 5 6_1 6_2; do
  echo "🧪 Section $section 테스트 중..."
  python scripts/tests/test_section${section}.py
done

# 개별 섹션 테스트
python scripts/tests/test_section1.py   # 데이터 파이프라인
python scripts/tests/test_section2.py   # 전처리
python scripts/tests/test_section3.py   # 모델 훈련
python scripts/tests/test_section4.py   # API
python scripts/tests/test_section5.py   # Docker
```

---

## 📋 **체크리스트**

### **개발 환경 확인**
- [ ] Python 3.11 가상환경 활성화
- [ ] 모든 패키지 설치 완료
- [ ] Docker 서비스 정상 실행
- [ ] API 헬스 체크 통과
- [ ] MLflow UI 접근 가능

### **배포 전 확인**
- [ ] 모든 테스트 통과
- [ ] 코드 품질 검사 완료
- [ ] Docker 이미지 빌드 성공
- [ ] API 엔드포인트 정상 동작
- [ ] 모니터링 메트릭 정상 수집

---

## 📚 **상세 문서**

| 주제 | 파일 | 설명 |
|------|------|------|
| **전체 시스템** | [README.md](./README.md) | 프로젝트 개요 및 아키텍처 |
| **Docker 설정** | [docker/](./docker/) | 컨테이너화 및 배포 |
| **모니터링** | [docs/guide/Section6_1_Monitoring_Instructions.md](./docs/guide/Section6_1_Monitoring_Instructions.md) | Prometheus/Grafana 설정 |
| **CI/CD** | [docs/guide/Section6_2_CICD_Instructions.md](./docs/guide/Section6_2_CICD_Instructions.md) | GitHub Actions 파이프라인 |
| **아키텍처** | [docs/guide/diagrams/](./docs/guide/diagrams/) | 시스템 다이어그램 |

---


---

*MLOps Team 11 | 마지막 업데이트: 2024.06.11*
