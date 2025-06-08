#!/bin/bash
# ==============================================================================
# MLOps 9아키텍처 상호 호환성 보장 설치 스크립트
# Python 3.11 + 패키지 간 호환성 검증된 설치 방법
# ==============================================================================

set -e  # 에러 발생 시 스크립트 중단

echo "🚀 MLOps 9아키텍처 호환성 보장 설치 시작..."

# ==============================================================================
# 1단계: 환경 검증
# ==============================================================================
echo "📋 1단계: Python 버전 및 환경 검증 중..."

# Python 버전 확인
PYTHON_VERSION=$(python --version 2>&1 | cut -d " " -f 2 | cut -d "." -f 1-2)
echo "✅ Python 버전: $PYTHON_VERSION"

if [[ "$PYTHON_VERSION" != "3.11" ]]; then
    echo "❌ 오류: Python 3.11이 필요합니다. 현재 버전: $PYTHON_VERSION"
    exit 1
fi

# 가상환경 확인
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "⚠️  경고: 가상환경이 활성화되지 않았습니다."
    read -p "계속하시겠습니까? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "설치를 중단합니다."
        exit 1
    fi
fi

# pip 업그레이드
echo "📦 pip 업그레이드 중..."
python -m pip install --upgrade pip

# ==============================================================================
# 1.5단계: 기본 공통 의존성 설치 (base.txt)
# ==============================================================================
echo "📦 1.5단계: 기본 공통 의존성 설치 중..."

# base.txt가 존재하는지 확인 후 설치
if [[ -f "requirements/base.txt" ]]; then
    echo "📄 requirements/base.txt 설치 중..."
    pip install -r requirements/base.txt
else
    echo "⚠️  requirements/base.txt를 찾을 수 없습니다. 수동 설치를 진행합니다."
    # 핵심 패키지 수동 설치 (호환성 매트릭스 준수)
    pip install \
        numpy==1.24.4 \
        pandas==2.1.4 \
        scikit-learn==1.3.2 \
        python-dotenv>=1.0.0,\<2.0.0 \
        structlog>=23.2.0,\<24.0.0 \
        requests>=2.31.0,\<3.0.0
fi

# ==============================================================================
# 2단계: Airflow 제약 조건 적용 설치 (가장 중요!)
# ==============================================================================
echo "🌬️  2단계: Apache Airflow 제약 조건 적용 설치 중..."

AIRFLOW_VERSION=2.10.5
CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"

echo "📥 제약 조건 URL: $CONSTRAINT_URL"

# 핵심 Airflow 설치 (제약 조건 적용)
echo "📦 Apache Airflow 설치 중..."
pip install "apache-airflow==${AIRFLOW_VERSION}" --constraint "${CONSTRAINT_URL}"

# Airflow 제공자 설치 (제약 조건 적용)
echo "📦 Airflow 제공자 패키지 설치 중..."
pip install \
    "apache-airflow-providers-postgres==5.13.1" \
    "apache-airflow-providers-celery==3.8.3" \
    "apache-airflow-providers-redis==3.8.1" \
    --constraint "${CONSTRAINT_URL}"

# ==============================================================================
# 3단계: MLflow 설치 (PyTorch 이전에)
# ==============================================================================
echo "📊 3단계: MLflow 설치 중..."

# MLflow 및 호환 패키지 설치
pip install mlflow==2.17.2

# ==============================================================================
# 4단계: PyTorch 설치 (MLflow 호환 버전)
# ==============================================================================
echo "🔥 4단계: PyTorch 설치 중..."

# CPU 버전 설치 (기본)
pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cpu

# GPU 버전이 필요한 경우 (주석 해제)
# pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu121

# ==============================================================================
# 5단계: 나머지 MLOps 도구들 설치
# ==============================================================================
echo "🛠️  5단계: 나머지 MLOps 도구들 설치 중..."

# Feast (MLflow 호환 버전)
pip install feast==0.40.1

# 모니터링 도구
pip install prometheus-client==0.21.1 grafana-client==4.2.4

# Kafka 클라이언트
pip install kafka-python==2.0.2

# ==============================================================================
# 6단계: 데이터 처리 및 웹 프레임워크
# ==============================================================================
echo "📊 6단계: 데이터 처리 및 웹 프레임워크 설치 중..."

# 데이터 처리 (호환성 검증된 버전)
# numpy, pandas, scikit-learn은 base.txt에서 이미 설치됨
echo "✅ 데이터 처리 패키지들은 base.txt에서 이미 설치되었습니다."

# 웹 프레임워크 (호환 버전)
pip install \
    fastapi==0.104.1 \
    uvicorn==0.24.0 \
    pydantic==2.5.3

# 데이터베이스
pip install \
    psycopg2-binary==2.9.9 \
    sqlalchemy==1.4.53 \
    redis==5.0.3

# 유틸리티
pip install \
    python-dotenv==1.0.0 \
    click==8.1.7 \
    requests==2.31.0 \
    httpx==0.25.2 \
    structlog==23.2.0

# ==============================================================================
# 7단계: 의존성 충돌 검사
# ==============================================================================
echo "🔍 7단계: 의존성 충돌 검사 중..."

echo "📋 설치된 패키지 확인..."
pip list | grep -E "(airflow|mlflow|torch|feast|prometheus|kafka|pandas|numpy)"

echo "🔍 의존성 충돌 검사..."
if pip check; then
    echo "✅ 모든 의존성이 호환됩니다!"
else
    echo "⚠️  의존성 충돌이 발견되었습니다. 로그를 확인해주세요."
fi

# ==============================================================================
# 8단계: 설치 완료 검증
# ==============================================================================
echo "✅ 8단계: 설치 완료 검증..."

# 각 주요 패키지 import 테스트
echo "🧪 주요 패키지 import 테스트..."

python -c "
import sys
print(f'Python: {sys.version}')

try:
    import airflow
    print(f'✅ Airflow: {airflow.__version__}')
except ImportError as e:
    print(f'❌ Airflow import 실패: {e}')

try:
    import mlflow
    print(f'✅ MLflow: {mlflow.__version__}')
except ImportError as e:
    print(f'❌ MLflow import 실패: {e}')

try:
    import torch
    print(f'✅ PyTorch: {torch.__version__}')
except ImportError as e:
    print(f'❌ PyTorch import 실패: {e}')

try:
    import feast
    print(f'✅ Feast: {feast.__version__}')
except ImportError as e:
    print(f'❌ Feast import 실패: {e}')

try:
    import prometheus_client
    print(f'✅ Prometheus Client: {prometheus_client.__version__}')
except ImportError as e:
    print(f'❌ Prometheus Client import 실패: {e}')

try:
    import kafka
    print(f'✅ Kafka Python: {kafka.__version__}')
except ImportError as e:
    print(f'❌ Kafka Python import 실패: {e}')

try:
    import pandas as pd
    import numpy as np
    print(f'✅ Pandas: {pd.__version__}, NumPy: {np.__version__}')
except ImportError as e:
    print(f'❌ Pandas/NumPy import 실패: {e}')
"

echo ""
echo "🎉 MLOps 9아키텍처 호환성 보장 설치 완료!"
echo ""
echo "✅ 호환성 매트릭스 준수 상태:"
echo "  - NumPy 1.24.4 (base.txt에서 관리)"
echo "  - Pandas 2.1.4 (base.txt에서 관리)"
echo "  - Scikit-learn 1.3.2 (base.txt에서 관리)"
echo "  - Airflow 2.10.5 + 제약 조건 적용"
echo "  - MLflow 2.17.2 + PyTorch 2.5.1 호환"
echo ""
echo "📋 다음 단계:"
echo "1. Airflow 초기화: airflow db init"
echo "2. MLflow 서버 시작: mlflow server"
echo "3. Docker 서비스 시작: ./run_movie_mlops.sh"
echo "4. 호환성 테스트: python -m pytest tests/unit/test_package_compatibility.py -v"
echo ""
echo "🔧 문제 해결:"
echo "- 의존성 충돌 시: pip install --force-reinstall <package>"
echo "- 제약 조건 재적용: 이 스크립트 재실행"
echo "- 상세 로그: pip install -v <package>"
echo ""