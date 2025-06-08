# ==============================================================================
# Docker Compose 명령어 수정 완료 보고서
# ==============================================================================

## 🎯 수정 목적
Docker Compose V1 (`docker-compose`) 명령어를 Docker Compose V2 (`docker compose`) 명령어로 업데이트

## ✅ 수정 완료된 파일들

### 1. 메인 스크립트
- **scripts/docker/start_all_services.sh**
  - 모든 `docker-compose -f` → `docker compose -f` 변경
  - 로그 확인 명령어 안내도 업데이트

- **scripts/docker/stop_all_services.sh**  
  - 모든 `docker-compose -f` → `docker compose -f` 변경
  - 사용법 안내 메시지도 업데이트

- **run_movie_mlops.sh**
  - 모든 개별 서비스 시작 함수들에서 명령어 변경
  - Docker Compose 설치 확인 로직을 V2로 업데이트
  - 로그 확인 함수들에서 명령어 변경

### 2. 문서
- **README.md**
  - 모든 사용 예제에서 `docker-compose` → `docker compose` 변경
  - 기본 인프라, 개발 환경, MLOps 서비스, 모니터링, 이벤트 스트리밍 섹션 모두 업데이트

- **docs/setup/QUICK_SETUP.md**
  - Docker Compose V2 오류 해결 섹션 추가
  - 올바른 명령어 사용법 안내

### 3. 테스트 코드
- **tests/unit/test_package_compatibility.py**
  - Docker Compose 설치 확인 테스트를 V2 우선으로 변경
  - V1과 V2 모두 확인하고 적절한 안내 메시지 출력

## 🔧 수정된 명령어 비교

| 구분 | 기존 (V1) | 변경 (V2) |
|------|-----------|-----------|
| **서비스 시작** | `docker-compose -f docker/docker-compose.api.yml up -d` | `docker compose -f docker/docker-compose.api.yml up -d` |
| **서비스 중지** | `docker-compose -f docker/docker-compose.api.yml down` | `docker compose -f docker/docker-compose.api.yml down` |
| **로그 확인** | `docker-compose -f docker/docker-compose.api.yml logs -f` | `docker compose -f docker/docker-compose.api.yml logs -f` |
| **버전 확인** | `docker-compose --version` | `docker compose version` |

## 📝 중요 사항

### ✅ 유지되는 것들
- **파일명**: `docker-compose.yml` 형식 그대로 유지
- **YAML 구조**: Docker Compose 파일 내용은 변경 없음
- **환경 변수**: `.env` 파일 로드 방식 동일
- **네트워크/볼륨**: 기존 설정 그대로 작동

### 🔄 변경되는 것들
- **명령어만**: `docker-compose` → `docker compose` (하이픈 제거)
- **설치 확인**: V2 우선 확인, V1은 레거시 경고

## 🚀 테스트 방법

### 1. Docker Compose V2 설치 확인
```bash
docker compose version
```

### 2. 수정 스크립트 실행
```bash
chmod +x scripts/docker/fix_docker_compose_commands.sh
./scripts/docker/fix_docker_compose_commands.sh
```

### 3. 기능 테스트
```bash
# 통합 테스트
./run_movie_mlops.sh

# 개별 서비스 테스트  
docker compose -f docker/docker-compose.api.yml up -d
docker compose -f docker/docker-compose.api.yml logs -f
docker compose -f docker/docker-compose.api.yml down
```

## 🔍 호환성

### Docker Compose V2 요구사항
- **Docker Desktop**: 3.6.0 이상 (자동 포함)
- **Docker Engine**: 20.10.13 이상
- **Linux 수동 설치**: https://docs.docker.com/compose/install/

### WSL 환경
- **Docker Desktop for Windows** 사용 시 자동으로 V2 지원
- **네이티브 WSL Docker** 설치 시 수동 V2 설치 필요

## 📋 문제 해결

### V2 명령어 오류 시
```bash
# 1. Docker Desktop 재시작
# 2. Docker Compose V2 설치 확인
docker compose version

# 3. 기존 컨테이너 정리 후 재시작
docker system prune -f
./run_movie_mlops.sh
```

### V1 → V2 마이그레이션
- 기존 실행 중인 서비스는 `docker compose` 명령어로도 관리 가능
- 컨테이너나 네트워크 재생성 불필요
- 설정 파일 변경 불필요

## ✨ 결과

모든 스크립트와 문서가 Docker Compose V2를 사용하도록 업데이트되었으며, 사용자는 이제 최신 Docker Compose 명령어로 전체 MLOps 시스템을 원활하게 관리할 수 있습니다! 🎉

