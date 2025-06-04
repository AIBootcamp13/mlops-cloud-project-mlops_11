# 개발환경 및 Git 통합 설정 스크립트

Write-Host "=== MLOps 프로젝트 완전 설정 시작 ===" -ForegroundColor Green

# Git 저장소 초기화
Write-Host "`n🔧 Git 저장소 설정..." -ForegroundColor Yellow
.\setup-git.ps1

# 개발환경 설정
Write-Host "`n🚀 개발환경 설정..." -ForegroundColor Yellow

# 1. 가상환경 생성 (이미 있으면 건너뜀)
if (!(Test-Path "venv")) {
    Write-Host "가상환경 생성 중..." -ForegroundColor Yellow
    python -m venv venv
}

# 2. 가상환경 활성화
Write-Host "가상환경 활성화 중..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

# 3. pip 업그레이드
Write-Host "pip 업그레이드 중..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# 4. 개발 의존성 설치
Write-Host "개발 패키지 설치 중..." -ForegroundColor Yellow
pip install -r requirements-dev.txt

# 5. Pre-commit 훅 설치
Write-Host "Pre-commit 훅 설치 중..." -ForegroundColor Yellow
pre-commit install

# 6. 환경변수 파일 생성 (없는 경우에만)
if (!(Test-Path ".env")) {
    Write-Host "환경변수 파일 생성 중..." -ForegroundColor Yellow
    Copy-Item ".env.template" ".env"
    Write-Host "⚠️  .env 파일에서 TMDB_API_KEY를 설정하세요!" -ForegroundColor Red
}

# 7. 필요한 디렉토리 생성
$directories = @("data", "data/raw", "data/processed", "data/test", "logs", "reports", "tests")
foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "디렉토리 생성: $dir" -ForegroundColor Cyan
    }
}

# 8. 테스트 실행
Write-Host "`n=== 초기 테스트 실행 ===" -ForegroundColor Green
python src\data_processing\test_integration.py

Write-Host "`n=== 프로젝트 완전 설정 완료! ===" -ForegroundColor Green
Write-Host "다음 단계:" -ForegroundColor Yellow
Write-Host "1. .env 파일에서 TMDB_API_KEY 설정" -ForegroundColor White
Write-Host "2. python src\data_processing\test_integration.py 재실행" -ForegroundColor White
Write-Host "3. 모든 테스트 통과 확인 후 1.2 단계 진행" -ForegroundColor White
Write-Host "`n🐳 Docker 사용 시: docker-compose up -d dev" -ForegroundColor Cyan
