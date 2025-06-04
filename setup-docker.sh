# WSL Ubuntu용 Docker 환경 설정 스크립트

echo "=== MLOps Docker 환경 설정 (WSL Ubuntu) ==="

# Docker 상태 확인
echo "🔍 Docker 환경 확인..."
if command -v docker &> /dev/null; then
    echo "✅ Docker 발견: $(docker --version)"
else
    echo "❌ Docker가 설치되지 않았습니다."
    echo "Docker Desktop WSL 통합을 활성화하거나 Docker를 직접 설치하세요."
    exit 1
fi

if docker compose version &> /dev/null; then
    echo "✅ Docker Compose 발견: $(docker compose version)"
else
    echo "❌ Docker Compose가 설치되지 않았습니다."
    exit 1
fi

# 환경변수 파일 확인
echo "⚙️ 환경변수 확인..."
if [ -f ".env" ]; then
    echo "✅ .env 파일이 존재합니다"
else
    echo "⚠️ .env 파일이 없습니다. .env.template을 복사합니다."
    cp .env.template .env
fi

# Docker 이미지 빌드
echo "🐳 Docker 이미지 빌드 (Python 3.11)..."
docker compose build dev

if [ $? -eq 0 ]; then
    echo "✅ Docker 이미지 빌드 성공"
else
    echo "❌ Docker 이미지 빌드 실패"
    exit 1
fi

# Docker 컨테이너 실행
echo "🚀 Docker 개발환경 시작..."
docker compose up -d dev

if [ $? -eq 0 ]; then
    echo "✅ Docker 컨테이너 실행 성공"
else
    echo "❌ Docker 컨테이너 실행 실패"
    exit 1
fi

# Python 버전 확인
echo "🐍 Python 버전 확인..."
python_version=$(docker exec mlops-dev python --version)
echo "✅ 컨테이너 Python 버전: $python_version"

# 초기 테스트 실행
echo "🧪 초기 테스트 실행..."
docker exec mlops-dev python src/data_processing/test_integration.py

# 사용법 안내
echo ""
echo "=== WSL Ubuntu Docker 환경 사용법 ==="
echo "컨테이너 접속:    docker exec -it mlops-dev bash"
echo "테스트 실행:      docker exec mlops-dev python src/data_processing/test_integration.py"
echo "컨테이너 중지:    docker-compose down"
echo "로그 확인:        docker-compose logs dev"

# 상태 확인
echo ""
echo "📊 컨테이너 상태:"
docker compose ps

echo ""
echo "✅ WSL Ubuntu Docker 환경 설정 완료! (Python 3.11)"
