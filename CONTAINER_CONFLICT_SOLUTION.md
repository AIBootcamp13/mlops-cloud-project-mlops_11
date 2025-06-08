# Movie MLOps 컨테이너 충돌 해결 가이드

## 🔍 문제 상황
Docker 컨테이너 이름 충돌로 인해 새로운 컨테이너를 시작할 수 없는 상황입니다.

```
Error response from daemon: Conflict. The container name "/movie-mlops-redis" is already in use
```

## 🛠️ 해결 방법

### 방법 1: 자동 해결 스크립트 실행 (권장)

```bash
# 충돌 해결 스크립트 실행
chmod +x fix_container_conflicts.sh
./fix_container_conflicts.sh

# 수정된 메인 스크립트 실행
chmod +x run_movie_mlops_fixed.sh
./run_movie_mlops_fixed.sh
```

### 방법 2: 수동 해결

```bash
# 1. 모든 Movie MLOps 컨테이너 중지
docker stop $(docker ps -aq --filter "name=movie-mlops")

# 2. 모든 Movie MLOps 컨테이너 제거
docker rm $(docker ps -aq --filter "name=movie-mlops")

# 3. 네트워크 재생성
docker network rm movie-mlops-network 2>/dev/null || true
docker network create movie-mlops-network

# 4. 정상 실행
./run_movie_mlops_fixed.sh
```

### 방법 3: 개별 서비스 정리

```bash
# 특정 서비스만 정리
docker stop movie-mlops-redis && docker rm movie-mlops-redis
docker stop movie-mlops-postgres && docker rm movie-mlops-postgres
```

## 📋 주요 변경사항

1. **분리된 스택 관리**: 인프라와 ML 서비스를 별도로 관리
2. **충돌 방지**: 컨테이너 이름 중복 해결
3. **안전한 정리**: 단계별 컨테이너 정리 프로세스
4. **에러 처리**: 더 나은 에러 핸들링 및 복구

## 🚀 올바른 실행 순서

1. 충돌 해결: `./fix_container_conflicts.sh`
2. 메인 실행: `./run_movie_mlops_fixed.sh`
3. 메뉴에서 선택:
   - 15번: 컨테이너 충돌 해결
   - 2번: 모든 스택 시작

## 💡 예방 방법

- 스택 중지 시 완전히 중지: 메뉴 3번 선택
- 정기적 정리: 메뉴 14번으로 정리
- 충돌 시 즉시 해결: 메뉴 15번 사용

## 🔧 추가 도구

- `docker ps -a --filter "name=movie-mlops"`: 모든 컨테이너 확인
- `docker system prune -f`: 시스템 정리
- `docker network ls`: 네트워크 확인
