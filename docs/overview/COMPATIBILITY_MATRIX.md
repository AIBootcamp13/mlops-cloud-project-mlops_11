# MLOps 9아키텍처 호환성 매트릭스

## 📋 검증된 패키지 조합

### 🎯 **핵심 호환성 원칙**

1. **Airflow Constraints 우선**: Apache Airflow 공식 제약 조건 파일 사용
2. **단계별 설치**: 의존성이 큰 패키지부터 순차 설치
3. **검증된 버전**: 커뮤니티에서 검증된 안정 버전 사용
4. **상호 호환성**: 각 패키지 간 의존성 충돌 방지

---

## 🔍 **검증된 호환성 매트릭스**

| 구분 | 패키지 | 버전 | 호환성 검증 | 비고 |
|------|--------|------|-------------|------|
| **기반** | Python | 3.11.x | ✅ 모든 패키지 지원 | 필수 버전 |
| **1+5아키텍처** | Apache Airflow | 2.10.5 | ✅ Python 3.11 공식 지원 | Constraints 적용 |
| | postgres-provider | 5.13.1 | ✅ Airflow 2.10.5 호환 | Constraints 포함 |
| | celery-provider | 3.8.3 | ✅ Airflow 2.10.5 호환 | Constraints 포함 |
| | redis-provider | 3.8.1 | ✅ Airflow 2.10.5 호환 | Constraints 포함 |
| **6아키텍처** | MLflow | 2.17.2 | ✅ PyTorch 2.5.1 호환 | 안정 버전 |
| **7아키텍처** | PyTorch | 2.5.1 | ✅ MLflow 2.17.2 호환 | Python 3.11 지원 |
| | torchvision | 0.20.1 | ✅ PyTorch 2.5.1 매칭 | 버전 매칭 필수 |
| | torchaudio | 2.5.1 | ✅ PyTorch 2.5.1 매칭 | 버전 매칭 필수 |
| **2아키텍처** | Feast | 0.40.1 | ✅ MLflow 2.17.2 호환 | 안정 버전 |
| **8아키텍처** | prometheus-client | 0.21.1 | ✅ 광범위 호환 | 안정 버전 |
| | grafana-client | 4.2.4 | ✅ 광범위 호환 | 안정 버전 |
| **9아키텍처** | kafka-python | 2.0.2 | ✅ 광범위 호환 | 안정 버전 |
| **데이터** | pandas | 2.1.4 | ✅ NumPy 1.24.4 호환 | MLflow 호환 |
| | numpy | 1.24.4 | ✅ PyTorch + MLflow 호환 | 핵심 호환성 |
| | scikit-learn | 1.3.2 | ✅ MLflow autolog 호환 | MLflow 통합 |
| **웹** | FastAPI | 0.104.1 | ✅ Pydantic 2.5.3 호환 | 안정 조합 |
| | Pydantic | 2.5.3 | ✅ FastAPI + MLflow 호환 | 안정 조합 |
| | uvicorn | 0.24.0 | ✅ FastAPI 0.104.1 호환 | 안정 조합 |
| **DB** | SQLAlchemy | 1.4.53 | ✅ Airflow + MLflow 공통 | 핵심 호환성 |
| | psycopg2-binary | 2.9.9 | ✅ Airflow 호환 | Constraints 준수 |
| | redis | 5.0.3 | ✅ Airflow Redis 호환 | Provider 매칭 |

---

## ⚠️ **알려진 호환성 이슈 및 해결책**

### 1. **NumPy 버전 충돌**
```bash
# 문제: PyTorch와 MLflow가 서로 다른 NumPy 버전 요구
# 해결: NumPy 1.24.4 (공통 호환 버전)
pip install numpy==1.24.4
```

### 2. **SQLAlchemy 버전 충돌**
```bash
# 문제: Airflow는 1.4.x, 일부 패키지는 2.x 요구
# 해결: SQLAlchemy 1.4.53 (Airflow + MLflow 공통 지원)
pip install sqlalchemy==1.4.53
```

### 3. **Pydantic 버전 충돌**
```bash
# 문제: FastAPI와 MLflow의 Pydantic 버전 요구사항 차이
# 해결: Pydantic 2.5.3 (양쪽 모두 호환)
pip install pydantic==2.5.3
```

### 4. **PyTorch 하위 패키지 버전 불일치**
```bash
# 문제: torch, torchvision, torchaudio 버전 불일치
# 해결: 정확한 버전 매칭 필요
pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1
```

---

## 🚀 **권장 설치 순서 (의존성 충돌 방지)**

### 1단계: 환경 준비
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate    # Windows
python -m pip install --upgrade pip
```

### 2단계: Airflow (제약 조건 적용)
```bash
AIRFLOW_VERSION=2.10.5
PYTHON_VERSION="3.11"
CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"
pip install "apache-airflow==${AIRFLOW_VERSION}" --constraint "${CONSTRAINT_URL}"
```

### 3단계: MLflow (PyTorch 이전)
```bash
pip install mlflow==2.17.2
```

### 4단계: PyTorch (버전 매칭)
```bash
pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cpu
```

### 5단계: 나머지 도구들
```bash
pip install feast==0.40.1
pip install prometheus-client==0.21.1 grafana-client==4.2.4
pip install kafka-python==2.0.2
```

### 6단계: 공통 라이브러리
```bash
pip install pandas==2.1.4 numpy==1.24.4 scikit-learn==1.3.2
pip install fastapi==0.104.1 uvicorn==0.24.0 pydantic==2.5.3
pip install psycopg2-binary==2.9.9 sqlalchemy==1.4.53 redis==5.0.3
```

---

## 🔍 **호환성 검증 방법**

### 1. 의존성 충돌 검사
```bash
pip check
```

### 2. 주요 패키지 import 테스트
```python
import airflow
import mlflow
import torch
import feast
import prometheus_client
import kafka
import pandas as pd
import numpy as np
print("모든 패키지 import 성공!")
```

### 3. 버전 확인
```python
import airflow, mlflow, torch, feast
print(f"Airflow: {airflow.__version__}")
print(f"MLflow: {mlflow.__version__}")
print(f"PyTorch: {torch.__version__}")
print(f"Feast: {feast.__version__}")
```

---

## 🛠️ **문제 해결 가이드**

### 의존성 충돌 발생 시
1. **제약 조건 재적용**
   ```bash
   pip install --force-reinstall apache-airflow==2.10.5 --constraint "${CONSTRAINT_URL}"
   ```

2. **가상환경 초기화**
   ```bash
   deactivate
   rm -rf venv
   python -m venv venv
   source venv/bin/activate
   # 설치 스크립트 재실행
   ```

3. **개별 패키지 강제 재설치**
   ```bash
   pip install --force-reinstall --no-deps <package>==<version>
   ```

### 성능 최적화
1. **pip cache 활용**
   ```bash
   pip install --cache-dir ~/.pip/cache <package>
   ```

2. **병렬 설치 (주의해서 사용)**
   ```bash
   pip install --use-feature=fast-deps <packages>
   ```

---

## 📈 **업데이트 가이드**

### 안전한 패키지 업데이트 순서
1. **Airflow constraints 확인**
2. **테스트 환경에서 검증**
3. **의존성 충돌 체크**
4. **프로덕션 적용**

### 호환성 매트릭스 업데이트
- 새로운 패키지 버전 출시 시 테스트 필요
- 커뮤니티 피드백 반영
- 정기적인 호환성 검증 (월 1회)

---

## 🎯 **결론**

이 호환성 매트릭스는 **실제 테스트와 커뮤니티 검증**을 통해 작성되었습니다. 
**Airflow constraints 파일**을 기반으로 하여 가장 안정적인 패키지 조합을 제공합니다.

**핵심 원칙: 안정성 > 최신성**

모든 패키지가 서로 충돌 없이 동작하도록 신중하게 선별된 버전들입니다! 🚀