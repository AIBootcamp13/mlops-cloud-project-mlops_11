# 루트 폴더 정리 보고서

## 📋 정리 개요
**날짜**: 2025-06-06  
**작업**: 불필요한 파일들을 temp-cleanup 폴더로 이동

---

## 🗂️ 이동된 파일들

### **1. 임시/테스트 파일**
- `nul` - 빈 파일 (Windows 명령어 오류로 생성된 것으로 추정)

### **2. 설정 스크립트 (중복/구버전)**
- `fix-docker-setup.bat` - 임시 Docker 설정 수정 스크립트
- `quick-setup-wsl.sh` - WSL용 퀵 설정 스크립트
- `setup-git.ps1` - Git 초기 설정 스크립트
- `setup-dev.ps1` - 개발환경 설정 스크립트
- `setup-docker.sh` - Docker 설정 스크립트
- `setup-docker-feature-store.bat` - Docker 피처 스토어 설정 (배치)
- `setup-docker-feature-store.sh` - Docker 피처 스토어 설정 (쉘)
- `setup-feature-store-prerequisites.bat` - 사전 요구사항 설정 (배치)
- `setup-feature-store-prerequisites.ps1` - 사전 요구사항 설정 (PowerShell)
- `setup-feature-store-prerequisites.sh` - 사전 요구사항 설정 (쉘)

### **3. 매뉴얼/문서**
- `MANUAL_SETUP_COMMANDS.md` - 수동 설정 명령어 가이드

### **4. 백업 폴더**
- `backup_feature_store_20250605_150649/` - 2025-06-05 피처 스토어 백업

### **5. 외부 도구 설정**
- `.obsidian/` - Obsidian 노트 앱 설정 폴더

### **6. 빈 디렉토리**
- `feature_repo/` - 빈 디렉토리 (Feast 관련)

---

## ✅ 유지된 중요 파일들

### **환경 설정**
- `.env` / `.env.template` - 환경 변수 설정
- `.gitignore` - Git 무시 파일 설정
- `.pre-commit-config.yaml` - 코드 품질 자동화

### **Docker 환경**
- `docker-compose.yml` - 메인 Docker 구성
- `Dockerfile.dev` - 개발환경 Docker 이미지

### **Python 설정**
- `pyproject.toml` - 프로젝트 메타데이터 및 설정
- `requirements.txt` / `requirements-dev.txt` - 의존성 관리
- `mypy.ini` - 타입 체크 설정
- `pytest.ini` - 테스트 설정

### **프로젝트 구조**
- `src/` - 소스 코드
- `docs/` - 문서
- `data/` - 데이터 저장소
- `logs/` - 로그 파일
- `reports/` - 보고서
- `scripts/` - 유틸리티 스크립트
- `config/` - 설정 파일
- `airflow/` - 워크플로우 관리

### **기타 중요 파일**
- `README.md` - 프로젝트 설명서

---

## 🎯 정리 결과

### **정리 전 파일 수**: 28개 파일/폴더
### **정리 후 파일 수**: 15개 파일/폴더 (핵심 파일만 유지)
### **이동된 파일 수**: 13개

---

## 💡 권장사항

1. **temp-cleanup 폴더 검토**: 
   - 30일 후 완전 삭제 권장
   - 필요한 파일이 있다면 다시 루트로 이동

2. **스크립트 통합**:
   - 현재 `scripts/` 폴더에 정리된 스크립트 사용
   - 중복된 설정 스크립트들은 제거됨

3. **향후 관리**:
   - 새로운 설정 파일은 `scripts/` 또는 `config/` 폴더 사용
   - 임시 파일은 즉시 삭제하거나 `.gitignore`에 추가

---

## 🔍 참고사항

- **백업 보존**: 중요한 백업은 temp-cleanup에서 별도 보관
- **설정 스크립트**: 필요 시 temp-cleanup에서 복구 가능
- **Git 히스토리**: 모든 파일의 이력은 Git에서 확인 가능

**루트 폴더가 깔끔하게 정리되어 프로젝트 구조가 명확해졌습니다!** ✨
