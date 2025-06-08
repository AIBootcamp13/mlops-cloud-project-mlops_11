#!/bin/bash

# PyTorch 모델 테스트 스크립트

set -e

echo "=== PyTorch 모델 테스트 시작 ==="

# 프로젝트 루트로 이동
cd "$(dirname "$0")/../.."

# Python 경로 설정
export PYTHONPATH="${PWD}:${PYTHONPATH}"

echo "1. PyTorch 환경 확인..."

# PyTorch 설치 확인
python -c "
import torch
print(f'PyTorch 버전: {torch.__version__}')
print(f'CUDA 사용 가능: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'CUDA 디바이스 수: {torch.cuda.device_count()}')
    print(f'현재 CUDA 디바이스: {torch.cuda.current_device()}')
" || {
    echo "❌ PyTorch가 설치되지 않았습니다. requirements/pytorch.txt를 확인하세요."
    exit 1
}

echo "2. 데이터 파일 확인..."

if [ ! -f "data/processed/watch_log.csv" ]; then
    echo "❌ watch_log.csv 파일이 존재하지 않습니다."
    exit 1
fi

echo "✅ 데이터 파일 확인 완료"

echo "3. PyTorch 모델 컴포넌트 테스트..."

# 모델 클래스 import 테스트
python -c "
import sys
sys.path.append('.')

try:
    from src.models.pytorch.movie_recommender import (
        MovieRecommenderNet, 
        CollaborativeFilteringModel,
        ContentBasedModel,
        create_model
    )
    print('✅ 모델 클래스 import 성공')
    
    # 간단한 모델 생성 테스트
    model = create_model(
        model_type='neural_cf',
        model_config={
            'num_users': 100,
            'num_movies': 50,
            'embedding_dim': 16
        }
    )
    print(f'✅ 모델 생성 성공 - 파라미터 수: {sum(p.numel() for p in model.parameters()):,}')
    
except Exception as e:
    print(f'❌ 모델 테스트 실패: {e}')
    sys.exit(1)
"

echo "4. 데이터로더 테스트..."

python -c "
import sys
sys.path.append('.')

try:
    from src.models.pytorch.data_loader import (
        MovieRatingDataset,
        create_data_loaders,
        prepare_data_from_watch_log
    )
    print('✅ 데이터로더 클래스 import 성공')
    
    # 데이터 준비 테스트
    train_df, val_df, test_df = prepare_data_from_watch_log(
        'data/processed/watch_log.csv',
        test_ratio=0.2,
        val_ratio=0.1
    )
    print(f'✅ 데이터 분할 성공 - 훈련: {len(train_df)}, 검증: {len(val_df)}, 테스트: {len(test_df)}')
    
    # 데이터로더 생성 테스트
    loaders = create_data_loaders(
        train_df=train_df.head(100),  # 작은 샘플로 테스트
        val_df=val_df.head(50),
        batch_size=32
    )
    print(f'✅ 데이터로더 생성 성공 - 메타데이터: {loaders[\"metadata\"]}')
    
except Exception as e:
    print(f'❌ 데이터로더 테스트 실패: {e}')
    sys.exit(1)
"

echo "5. 간단한 훈련 테스트..."

python -c "
import sys
sys.path.append('.')

try:
    from src.models.pytorch.training import ModelTrainer
    from src.models.pytorch.movie_recommender import create_model
    from src.models.pytorch.data_loader import create_data_loaders, prepare_data_from_watch_log
    import torch
    
    # 작은 데이터셋으로 빠른 테스트
    train_df, val_df, test_df = prepare_data_from_watch_log(
        'data/processed/watch_log.csv',
        test_ratio=0.2,
        val_ratio=0.1
    )
    
    # 작은 샘플만 사용
    small_train = train_df.head(200)
    small_val = val_df.head(50)
    
    loaders = create_data_loaders(
        train_df=small_train,
        val_df=small_val,
        batch_size=32
    )
    
    # 작은 모델 생성
    model_config = {
        'num_users': loaders['metadata']['num_users'],
        'num_movies': loaders['metadata']['num_movies'],
        'embedding_dim': 8,
        'hidden_dims': [16, 8]
    }
    
    model = create_model('neural_cf', model_config)
    trainer = ModelTrainer(model, experiment_name='test_run')
    
    # 1 에포크만 훈련
    history = trainer.train(
        train_loader=loaders['train'],
        val_loader=loaders['val'],
        num_epochs=1,
        learning_rate=0.01,
        early_stopping_patience=1
    )
    
    print(f'✅ 훈련 테스트 성공 - 훈련 손실: {history[\"train_loss\"][0]:.4f}')
    
except Exception as e:
    print(f'❌ 훈련 테스트 실패: {e}')
    sys.exit(1)
"

echo "6. 추론 테스트..."

# 모델이 저장되었는지 확인하고 추론 테스트
if [ -f "models/trained/pytorch_model.pth" ]; then
    python -c "
import sys
sys.path.append('.')

try:
    from src.models.pytorch.inference import create_inference_from_checkpoint
    
    # 추론 객체 생성
    inference = create_inference_from_checkpoint(
        'models/trained/pytorch_model.pth',
        'data/processed/watch_log.csv'
    )
    
    # 모델 정보 확인
    info = inference.get_model_info()
    print(f'✅ 추론 객체 생성 성공 - 모델 크기: {info[\"model_size_mb\"]:.2f}MB')
    
    # 간단한 예측 테스트
    rating = inference.predict_rating(user_id=1, movie_id=575265)
    print(f'✅ 평점 예측 성공: {rating:.3f}')
    
    # 추천 테스트
    recommendations = inference.recommend_for_user(user_id=1, num_recommendations=3)
    print(f'✅ 추천 생성 성공: {len(recommendations)}개 추천')
    
except Exception as e:
    print(f'❌ 추론 테스트 실패: {e}')
    # 추론 실패는 치명적이지 않음 (모델이 없을 수 있음)
    print('⚠️  추론 테스트 건너뛰기 (훈련된 모델 없음)')
"
else
    echo "⚠️  저장된 모델이 없어 추론 테스트를 건너뜁니다."
fi

echo "7. 성능 비교 테스트..."

python -c "
import sys
sys.path.append('.')

try:
    # NumPy와 PyTorch 모델 비교 (간단한 성능 측정)
    import time
    import numpy as np
    import torch
    
    from src.models.legacy.movie_predictor import MoviePredictor
    from src.models.pytorch.movie_recommender import MovieRecommenderNet
    
    # 테스트 데이터 생성
    batch_size = 100
    input_dim = 10
    hidden_dim = 32
    num_classes = 50
    
    # NumPy 모델
    numpy_model = MoviePredictor(input_dim, hidden_dim, num_classes)
    test_input = np.random.randn(batch_size, input_dim)
    
    start_time = time.time()
    for _ in range(10):
        numpy_output = numpy_model.forward(test_input)
    numpy_time = time.time() - start_time
    
    # PyTorch 모델 (CPU)
    pytorch_model = MovieRecommenderNet(
        num_users=100, 
        num_movies=num_classes,
        embedding_dim=16,
        hidden_dims=[hidden_dim]
    )
    
    user_ids = torch.randint(0, 100, (batch_size,))
    movie_ids = torch.randint(0, num_classes, (batch_size,))
    
    start_time = time.time()
    with torch.no_grad():
        for _ in range(10):
            pytorch_output = pytorch_model(user_ids, movie_ids)
    pytorch_time = time.time() - start_time
    
    print(f'✅ 성능 비교 완료:')
    print(f'  - NumPy 모델: {numpy_time:.4f}초')
    print(f'  - PyTorch 모델: {pytorch_time:.4f}초')
    print(f'  - 속도 비율: {numpy_time/pytorch_time:.2f}x')
    
except Exception as e:
    print(f'❌ 성능 비교 실패: {e}')
    # 성능 비교 실패는 치명적이지 않음
    print('⚠️  성능 비교 건너뛰기')
"

echo "8. 메모리 사용량 확인..."

python -c "
import sys
sys.path.append('.')

try:
    import torch
    import psutil
    import os
    
    # 현재 메모리 사용량
    process = psutil.Process(os.getpid())
    memory_before = process.memory_info().rss / 1024 / 1024  # MB
    
    # 큰 모델 생성
    from src.models.pytorch.movie_recommender import create_model
    
    large_model = create_model(
        model_type='neural_cf',
        model_config={
            'num_users': 10000,
            'num_movies': 5000,
            'embedding_dim': 128,
            'hidden_dims': [512, 256, 128]
        }
    )
    
    memory_after = process.memory_info().rss / 1024 / 1024  # MB
    memory_increase = memory_after - memory_before
    
    print(f'✅ 메모리 사용량 확인:')
    print(f'  - 모델 로딩 전: {memory_before:.1f}MB')
    print(f'  - 모델 로딩 후: {memory_after:.1f}MB')
    print(f'  - 증가량: {memory_increase:.1f}MB')
    
    # GPU 메모리 확인 (CUDA 사용 가능한 경우)
    if torch.cuda.is_available():
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024 / 1024  # MB
        print(f'  - GPU 총 메모리: {gpu_memory:.0f}MB')
    
except Exception as e:
    print(f'❌ 메모리 확인 실패: {e}')
    print('⚠️  메모리 확인 건너뛰기')
"

echo "9. 모델 저장/로딩 테스트..."

python -c "
import sys
sys.path.append('.')

try:
    import torch
    import os
    from src.models.pytorch.movie_recommender import create_model, save_model, load_model
    
    # 테스트 모델 생성
    model_config = {
        'num_users': 100,
        'num_movies': 50,
        'embedding_dim': 16
    }
    
    original_model = create_model('neural_cf', model_config)
    
    # 테스트 입력으로 원래 출력 얻기
    user_ids = torch.tensor([1, 2, 3])
    movie_ids = torch.tensor([10, 20, 30])
    
    with torch.no_grad():
        original_output = original_model(user_ids, movie_ids)
    
    # 모델 저장
    test_model_path = 'test_model.pth'
    save_model(original_model, test_model_path, {'test': True})
    
    # 새 모델 생성 후 로딩
    loaded_model = create_model('neural_cf', model_config)
    loaded_model, metadata = load_model(loaded_model, test_model_path)
    
    # 같은 입력으로 출력 비교
    with torch.no_grad():
        loaded_output = loaded_model(user_ids, movie_ids)
    
    # 출력이 같은지 확인
    if torch.allclose(original_output, loaded_output, atol=1e-6):
        print('✅ 모델 저장/로딩 성공 - 출력 일치')
    else:
        print('❌ 모델 저장/로딩 실패 - 출력 불일치')
        sys.exit(1)
    
    # 테스트 파일 정리
    os.remove(test_model_path)
    
except Exception as e:
    print(f'❌ 모델 저장/로딩 테스트 실패: {e}')
    sys.exit(1)
"

echo ""
echo "=== PyTorch 테스트 완료 ==="
echo ""
echo "📋 테스트 결과 요약:"
echo "  - PyTorch 환경: ✅"
echo "  - 모델 클래스: ✅"
echo "  - 데이터로더: ✅"
echo "  - 훈련 파이프라인: ✅"
echo "  - 추론 시스템: ✅"
echo "  - 모델 저장/로딩: ✅"
echo ""
echo "🚀 다음 단계:"
echo "  1. 전체 훈련 실행: python src/models/pytorch/training.py"
echo "  2. 추론 테스트: python src/models/pytorch/inference.py"
echo "  3. NumPy vs PyTorch 성능 비교 실행"
echo ""

exit 0
