# 데이터 처리 구현 가이드

이 폴더는 MLOps 데이터 처리 시스템의 구체적인 구현 방법과 기술적 가이드를 제공합니다.

## 📁 구현 가이드 목록

### 기본 인프라 및 환경 설정
- [1.1 데이터 소스 연결 (WSL Ubuntu) 가이드](./1.1-data-source-connection-wsl-ubuntu-guide.md)
- [1.4 데이터 저장소 설정 가이드](./1.4-data-storage-setup-guide.md)
- [1.7 로깅 시스템 설정 가이드](./1.7-logging-system-setup-guide.md)

### 데이터 수집 및 처리
- [1.2 데이터 크롤러 개발 가이드](./1.2-data-crawler-development-guide.md)
- [1.3 데이터 수집 스케줄링 가이드](./1.3-data-collection-scheduling-guide.md)
- [1.5 데이터 품질 검증 가이드](./1.5-data-quality-validation-guide.md)

### 워크플로우 및 오케스트레이션
- [1.8 Apache Airflow 기본 설정 가이드](./1.8-apache-airflow-basic-setup-guide.md)

### 프로젝트 관리
- [1.6 완료 기준](./1.6-completion-criteria.md)

## 🎯 학습 순서

### Phase 1: 환경 준비 (1-2일)
1. **WSL Ubuntu 환경 설정** (1.1): 개발 환경 구축
2. **로깅 시스템 설정** (1.7): 시스템 모니터링 기반 구축
3. **데이터 저장소 설정** (1.4): 데이터 저장 인프라 준비

### Phase 2: 데이터 수집 (3-4일)
1. **데이터 크롤러 개발** (1.2): 핵심 데이터 수집 로직
2. **데이터 품질 검증** (1.5): 수집된 데이터 품질 보장
3. **스케줄링 시스템** (1.3): 자동화된 데이터 수집

### Phase 3: 워크플로우 자동화 (2-3일)
1. **Apache Airflow 설정** (1.8): 전체 파이프라인 오케스트레이션
2. **완료 기준 검증** (1.6): 시스템 완성도 확인

## 📋 전제 조건

### 시스템 요구사항
- Windows 10/11 with WSL2
- Ubuntu 20.04+ (WSL)
- Python 3.8+
- Docker (선택사항)

### 필요한 지식
- 기본적인 Linux 명령어
- Python 프로그래밍
- 웹 스크래핑 기초
- 데이터베이스 기본 개념

## 🔧 주요 기술 스택

```yaml
개발 환경:
  - WSL2 Ubuntu
  - Python 3.8+
  - pip/conda 패키지 관리

데이터 수집:
  - requests, BeautifulSoup
  - Selenium (필요시)
  - pandas, numpy

데이터 저장:
  - SQLite (개발용)
  - PostgreSQL (프로덕션)
  - 파일 시스템 (CSV, JSON)

워크플로우:
  - Apache Airflow
  - cron (기본 스케줄링)

모니터링:
  - Python logging
  - 사용자 정의 로그 시스템
```

## 🔗 관련 문서

- [전체 구현 가이드](../1.data-processing-implementation-guide.md)
- [종합 테스팅 가이드](../2.comprehensive-testing-guide.md)
- [다음 단계: Feature Store](../../02-feature-store/)

## 📈 예상 구현 시간

| 단계 | 예상 시간 | 난이도 |
|------|-----------|--------|
| 환경 설정 (1.1, 1.4, 1.7) | 6-8시간 | ⭐⭐ |
| 데이터 수집 (1.2, 1.3, 1.5) | 12-16시간 | ⭐⭐⭐ |
| 워크플로우 (1.8) | 4-6시간 | ⭐⭐⭐ |
| 검증 및 완료 (1.6) | 2-3시간 | ⭐ |
| **총 예상 시간** | **24-33시간** | **⭐⭐⭐** |

## 🚀 시작하기

1. [WSL Ubuntu 환경 설정](./1.1-data-source-connection-wsl-ubuntu-guide.md)부터 시작
2. 각 가이드의 전제 조건 확인
3. 단계별로 순차 진행
4. 완료 기준에 따라 검증

## 💡 팁

- 각 단계 완료 후 테스트 진행 권장
- 로그 확인 습관화
- 문제 발생 시 관련 문서 참조
- 커뮤니티 리소스 활용
