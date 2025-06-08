# Movie MLOps 설정 가이드

## 🚀 빠른 설정 (권장)

### 1단계: 환경 준비
```bash
# 실행 권한 부여
chmod +x run_movie_mlops.sh
chmod +x scripts/setup/*.sh
chmod +x scripts/docker/*.sh

# 환경 변수 설정
cp .env.template .env
# .env 파일에서 필수 값 설정
```

### 2단계: 통합 실행
```bash
./run_movie_mlops.sh
# 메뉴에서 1번 → 2번 순서로 실행
```

### 3단계: 서비스 확인
- ✅ http://localhost:8888 (Jupyter)
- ✅ http://localhost:8000/docs (FastAPI)
- ✅ http://localhost:5000 (MLflow)

## 🔧 문제 해결

### Docker Compose V2 오류
```bash
# ❌ 잘못된 예: docker-compose -f docker/docker-compose.api.yml up -d
# ✅ 올바른 예: docker compose -f docker/docker-compose.api.yml up -d

# Docker Compose V2 설치 확인
docker compose version
```

### 포트 충돌
```bash
# 실행 중인 서비스 확인
docker ps
netstat -tulpn | grep :[포트번호]
```

### 메모리 부족
```bash
# Docker 리소스 정리
docker system prune -a
```

### 권한 문제 (WSL)
```bash
chmod +x scripts/**/*.sh
```

## 📋 호환성 정보

패키지 호환성 및 버전 정보는 [COMPATIBILITY_MATRIX.md](../overview/COMPATIBILITY_MATRIX.md)를 참조하세요.

## 🎯 개발 워크플로우

1. **기본 환경**: Jupyter + FastAPI + PostgreSQL + Redis
2. **ML 실험**: MLflow 추가
3. **워크플로우**: Airflow 추가  
4. **모니터링**: Prometheus + Grafana 추가
5. **스트리밍**: Kafka 추가

각 단계별로 필요한 서비스만 선택적으로 시작할 수 있습니다.
