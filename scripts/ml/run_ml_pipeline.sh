#!/bin/bash

# ==============================================================================
# ML 비즈니스 로직 실행 스크립트
# PyTorch 컨테이너에서 완전한 ML 파이프라인 실행
# 파일 위치: /mnt/c/dev/movie-mlops/scripts/ml/run_ml_pipeline.sh
# ==============================================================================

set -e  # 오류 시 스크립트 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 로고 출력
echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${PURPLE}   🎬 Movie-MLOps ML 파이프라인 실행기${NC}"
echo -e "${PURPLE}   PyTorch 기반 영화 추천 모델 훈련 및 평가${NC}"
echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# 스크립트 디렉토리 설정
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo -e "${BLUE}📂 프로젝트 루트: ${PROJECT_ROOT}${NC}"
cd "$PROJECT_ROOT"

# 함수: 컨테이너 상태 확인
check_container_status() {
    local container_name=$1
    if docker ps --format "table {{.Names}}" | grep -q "^${container_name}$"; then
        echo -e "${GREEN}✅ ${container_name} 실행 중${NC}"
        return 0
    else
        echo -e "${RED}❌ ${container_name} 실행되지 않음${NC}"
        return 1
    fi
}

# 함수: PyTorch 설치 확인
check_pytorch_installation() {
    local container_name=$1
    echo -e "${YELLOW}🔍 ${container_name}에서 PyTorch 설치 확인 중...${NC}"
    
    if docker exec -it "$container_name" python -c "import torch; print(f'PyTorch 버전: {torch.__version__}')" 2>/dev/null; then
        echo -e "${GREEN}✅ PyTorch 설치 확인됨${NC}"
        return 0
    else
        echo -e "${RED}❌ PyTorch 미설치${NC}"
        return 1
    fi
}

# 함수: ML 파이프라인 실행
run_ml_pipeline() {
    local container_name=$1
    local epochs=${2:-3}  # 기본값 3 에포크
    
    echo -e "${CYAN}🚀 ${container_name}에서 ML 파이프라인 실행 시작...${NC}"
    echo -e "${YELLOW}📊 훈련 에포크: ${epochs}${NC}"
    
    # ML 파이프라인 실행 스크립트
    docker exec -it "$container_name" python -c "
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from src.dataset.watch_log import get_datasets
from src.model.movie_predictor import MoviePredictor
from src.train.train import train
from src.evaluate.evaluate import evaluate
import time

print('=' * 60)
print('🎬 ML 파이프라인 시작')
print('=' * 60)
print(f'🔥 PyTorch 버전: {torch.__version__}')
print(f'💻 디바이스: {\"CUDA\" if torch.cuda.is_available() else \"CPU\"}')

try:
    # 1. 데이터셋 로드
    print('\n📊 1단계: 데이터셋 로드 중...')
    start_time = time.time()
    train_dataset, val_dataset, test_dataset = get_datasets()
    load_time = time.time() - start_time
    print(f'✅ 데이터셋 로드 완료 ({load_time:.2f}초)')
    print(f'   📈 훈련 데이터: {len(train_dataset):,}개')
    print(f'   📊 검증 데이터: {len(val_dataset):,}개')
    print(f'   🧪 테스트 데이터: {len(test_dataset):,}개')
    print(f'   🔢 특성 차원: {train_dataset.features_dim}')
    print(f'   🎯 클래스 수: {train_dataset.num_classes}')

    # 2. 데이터 로더 생성
    print('\n🔄 2단계: 데이터 로더 생성 중...')
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)
    print(f'✅ 데이터 로더 생성 완료')
    print(f'   📦 배치 크기: 32')
    print(f'   🔀 훈련 셔플: True')

    # 3. 모델 생성
    print('\n🧠 3단계: 모델 생성 중...')
    model = MoviePredictor(
        input_dim=train_dataset.features_dim,
        num_classes=train_dataset.num_classes
    )
    
    # 모델 파라미터 수 계산
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    
    print(f'✅ 모델 생성 완료')
    print(f'   🔢 입력 차원: {train_dataset.features_dim}')
    print(f'   🎯 출력 클래스: {train_dataset.num_classes}')
    print(f'   📊 총 파라미터: {total_params:,}개')
    print(f'   🎓 훈련 가능: {trainable_params:,}개')

    # 4. 모델 훈련
    print(f'\n🎯 4단계: 모델 훈련 시작 (에포크: ${epochs})...')
    train_start_time = time.time()
    trained_model = train(model, train_loader, val_loader, epochs=${epochs})
    train_time = time.time() - train_start_time
    print(f'✅ 모델 훈련 완료 ({train_time:.2f}초)')

    # 5. 모델 평가
    print('\n📊 5단계: 모델 평가 시작...')
    eval_start_time = time.time()
    test_accuracy = evaluate(trained_model, test_loader)
    eval_time = time.time() - eval_start_time
    
    total_time = time.time() - start_time
    
    print(f'✅ 모델 평가 완료 ({eval_time:.2f}초)')
    print(f'🎯 테스트 정확도: {test_accuracy:.4f} ({test_accuracy*100:.2f}%)')
    
    # 결과 요약
    print('\n' + '=' * 60)
    print('📈 ML 파이프라인 완료 - 결과 요약')
    print('=' * 60)
    print(f'⏱️  총 실행 시간: {total_time:.2f}초')
    print(f'📊 데이터 로드: {load_time:.2f}초')
    print(f'🎓 모델 훈련: {train_time:.2f}초')
    print(f'📊 모델 평가: {eval_time:.2f}초')
    print(f'🎯 최종 정확도: {test_accuracy:.4f} ({test_accuracy*100:.2f}%)')
    print(f'📦 모델 크기: {total_params:,} 파라미터')
    print('=' * 60)
    print('🎬 ML 파이프라인 성공적으로 완료!')
    print('=' * 60)
    
except Exception as e:
    print(f'\n❌ 오류 발생: {str(e)}')
    import traceback
    traceback.print_exc()
    exit(1)
"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}🎉 ML 파이프라인 실행 완료!${NC}"
        return 0
    else
        echo -e "${RED}💥 ML 파이프라인 실행 실패!${NC}"
        return 1
    fi
}

# 함수: 사용법 출력
show_usage() {
    echo -e "${CYAN}사용법:${NC}"
    echo -e "  $0 [OPTIONS]"
    echo -e ""
    echo -e "${CYAN}옵션:${NC}"
    echo -e "  -c, --container CONTAINER_NAME  대상 컨테이너 이름 (기본값: auto-detect)"
    echo -e "  -e, --epochs EPOCHS            훈련 에포크 수 (기본값: 3)"
    echo -e "  -h, --help                     도움말 출력"
    echo -e ""
    echo -e "${CYAN}예시:${NC}"
    echo -e "  $0                                    # 자동 감지된 컨테이너에서 3 에포크 훈련"
    echo -e "  $0 -e 5                              # 5 에포크 훈련"
    echo -e "  $0 -c movie-mlops-api -e 10          # 특정 컨테이너에서 10 에포크 훈련"
}

# 메인 실행 로직
main() {
    local target_container=""
    local epochs=3
    
    # 인자 파싱
    while [[ $# -gt 0 ]]; do
        case $1 in
            -c|--container)
                target_container="$2"
                shift 2
                ;;
            -e|--epochs)
                epochs="$2"
                shift 2
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            *)
                echo -e "${RED}❌ 알 수 없는 옵션: $1${NC}"
                show_usage
                exit 1
                ;;
        esac
    done
    
    echo -e "${BLUE}🔍 컨테이너 상태 확인 중...${NC}"
    
    # 컨테이너 자동 감지 (target_container가 지정되지 않은 경우)
    if [ -z "$target_container" ]; then
        echo -e "${YELLOW}🤖 자동으로 적절한 컨테이너 감지 중...${NC}"
        
        # 우선순위별로 컨테이너 확인
        containers_to_check=("movie-mlops-pytorch" "movie-mlops-api" "movie-mlops-jupyter" "movie-mlops-mlflow")
        
        for container in "${containers_to_check[@]}"; do
            if check_container_status "$container"; then
                if check_pytorch_installation "$container"; then
                    target_container="$container"
                    echo -e "${GREEN}✅ 사용할 컨테이너: ${target_container}${NC}"
                    break
                fi
            fi
        done
        
        if [ -z "$target_container" ]; then
            echo -e "${RED}❌ PyTorch가 설치된 실행 중인 컨테이너를 찾을 수 없습니다.${NC}"
            echo -e "${YELLOW}💡 다음 중 하나를 실행해보세요:${NC}"
            echo -e "   ./run_movie_mlops.sh (메뉴에서 2번 또는 7번 선택)"
            echo -e "   docker-compose -f docker/docker-compose.ml.yml up -d"
            exit 1
        fi
    else
        # 지정된 컨테이너 확인
        if ! check_container_status "$target_container"; then
            echo -e "${RED}❌ 지정된 컨테이너 '${target_container}'가 실행되지 않았습니다.${NC}"
            exit 1
        fi
        
        if ! check_pytorch_installation "$target_container"; then
            echo -e "${RED}❌ 컨테이너 '${target_container}'에 PyTorch가 설치되지 않았습니다.${NC}"
            exit 1
        fi
    fi
    
    # 에포크 수 검증
    if ! [[ "$epochs" =~ ^[0-9]+$ ]] || [ "$epochs" -lt 1 ]; then
        echo -e "${RED}❌ 에포크 수는 1 이상의 정수여야 합니다.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}🎯 설정 확인:${NC}"
    echo -e "   📦 컨테이너: ${target_container}"
    echo -e "   🔄 에포크: ${epochs}"
    echo -e ""
    
    # 사용자 확인
    read -p "$(echo -e ${YELLOW}계속 진행하시겠습니까? [Y/n]: ${NC})" -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        echo -e "${YELLOW}⏹️  사용자에 의해 취소되었습니다.${NC}"
        exit 0
    fi
    
    # ML 파이프라인 실행
    echo -e "${CYAN}🚀 ML 파이프라인 실행 시작...${NC}"
    if run_ml_pipeline "$target_container" "$epochs"; then
        echo -e "${GREEN}🎉 모든 작업이 성공적으로 완료되었습니다!${NC}"
        echo -e "${CYAN}📊 결과를 확인하려면 다음 URL을 방문하세요:${NC}"
        echo -e "   MLflow: http://localhost:5000"
        echo -e "   API 테스트: http://localhost:8000/docs"
        exit 0
    else
        echo -e "${RED}💥 ML 파이프라인 실행에 실패했습니다.${NC}"
        exit 1
    fi
}

# 스크립트 직접 실행 시
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi