# Git 저장소 초기화 및 기초 설정 스크립트

Write-Host "=== Git 저장소 초기화 및 설정 ===" -ForegroundColor Green

# 1. Git 저장소 초기화
if (!(Test-Path ".git")) {
    Write-Host "Git 저장소 초기화 중..." -ForegroundColor Yellow
    git init
    Write-Host "✅ Git 저장소 초기화 완료" -ForegroundColor Green
} else {
    Write-Host "Git 저장소가 이미 존재합니다." -ForegroundColor Cyan
}

# 2. Git 사용자 설정 (필요한 경우)
$gitUserName = git config user.name
$gitUserEmail = git config user.email

if (-not $gitUserName) {
    $userName = Read-Host "Git 사용자 이름을 입력하세요"
    git config user.name "$userName"
    Write-Host "✅ Git 사용자 이름 설정: $userName" -ForegroundColor Green
}

if (-not $gitUserEmail) {
    $userEmail = Read-Host "Git 이메일을 입력하세요"
    git config user.email "$userEmail"
    Write-Host "✅ Git 이메일 설정: $userEmail" -ForegroundColor Green
}

# 3. 기본 브랜치를 main으로 설정
git config init.defaultBranch main

# 4. 필요한 디렉토리 생성 및 .gitkeep 파일 추가
$directories = @("data", "logs", "reports", "models", "artifacts")
foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        New-Item -ItemType File -Path "$dir\.gitkeep" -Force | Out-Null
        Write-Host "디렉토리 생성: $dir/" -ForegroundColor Cyan
    }
}

# 5. 첫 번째 커밋 (staging 및 커밋)
Write-Host "파일들을 staging area에 추가 중..." -ForegroundColor Yellow
git add .

# 커밋 메시지 생성
$commitMessage = "🎉 Initial commit: MLOps 프로젝트 기초 설정

✅ 완료된 구성:
- 프로젝트 구조 설정
- Git 저장소 초기화
- Docker 환경 구성
- 1.1 데이터 소스 연결 구현
- 개발환경 도구 설정
- 테스트 시스템 구축

📁 주요 파일:
- src/data_processing/: TMDB API 연동 시스템
- docker-compose.yml: Docker 개발환경
- requirements-dev.txt: 개발 의존성
- .pre-commit-config.yaml: 코드 품질 자동화

🎯 다음 단계: 1.2 데이터 크롤러 개발"

git commit -m "$commitMessage"

Write-Host "✅ 첫 번째 커밋 완료" -ForegroundColor Green

# 6. 원격 저장소 설정 안내
Write-Host "`n=== 원격 저장소 설정 안내 ===" -ForegroundColor Yellow
Write-Host "GitHub/GitLab에 저장소를 생성한 후 다음 명령어를 실행하세요:" -ForegroundColor White
Write-Host "git remote add origin <저장소_URL>" -ForegroundColor Cyan
Write-Host "git branch -M main" -ForegroundColor Cyan
Write-Host "git push -u origin main" -ForegroundColor Cyan

# 7. Git 상태 확인
Write-Host "`n=== Git 상태 확인 ===" -ForegroundColor Yellow
git status
git log --oneline -5

Write-Host "`n✅ Git 저장소 초기화 완료!" -ForegroundColor Green
