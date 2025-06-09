#!/bin/bash

# ==============================================================================
# 간단한 ML 파이프라인 실행 스크립트 (경량화 버전)
# 파일 위치: /mnt/c/dev/movie-mlops/scripts/ml/quick_ml_run.sh
# ==============================================================================

set -e

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🎬 Movie-MLOps 간단 실행기${NC}"

# 프로젝트 루트로 이동
cd "$(dirname "$0")/../.."

# 컨테이너 찾기
CONTAINER=""
for cont in movie-mlops-pytorch movie-mlops-api movie-mlops-jupyter; do
    if docker ps --format "table {{.Names}}" | grep -q "^${cont}$"; then
        if docker exec -it "$cont" python -c "import torch" 2>/dev/null; then
            CONTAINER="$cont"
            echo -e "${GREEN}✅ 사용 컨테이너: $CONTAINER${NC}"
            break
        fi
    fi
done

if [ -z "$CONTAINER" ]; then
    echo -e "${RED}❌ PyTorch 컨테이너를 찾을 수 없습니다.${NC}"
    echo -e "${YELLOW}먼저 ./run_movie_mlops.sh를 실행하세요.${NC}"
    exit 1
fi

echo -e "${YELLOW}🚀 ML 파이프라인 실행 중...${NC}"

# ML 파이프라인 실행
docker exec -it "$CONTAINER" python -c "
import torch
from torch.utils.data import DataLoader
from src.dataset.watch_log import get_datasets
from src.model.movie_predictor import MoviePredictor
from src.train.train import train
from src.evaluate.evaluate import evaluate

print('🎬 ML 파이프라인 시작')
print(f'PyTorch: {torch.__version__}')

# 데이터 로드
train_dataset, val_dataset, test_dataset = get_datasets()
print(f'✅ 데이터: 훈련({len(train_dataset)}) 검증({len(val_dataset)}) 테스트({len(test_dataset)})')

# 데이터 로더
train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False)
test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)

# 모델 생성
model = MoviePredictor(
    input_dim=train_dataset.features_dim,
    num_classes=train_dataset.num_classes
)
print(f'✅ 모델: {train_dataset.features_dim} → {train_dataset.num_classes}')

# 훈련 (3 에포크)
print('🎓 훈련 시작...')
trained_model = train(model, train_loader, val_loader, epochs=3)

# 평가
print('📊 평가 시작...')
test_accuracy = evaluate(trained_model, test_loader)

print(f'🎯 최종 정확도: {test_accuracy:.4f} ({test_accuracy*100:.2f}%)')
print('✅ 완료!')
"

echo -e "${GREEN}🎉 ML 파이프라인 완료!${NC}"