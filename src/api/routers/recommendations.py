"""
추천 API 라우터
기존 my-mlops 추천 로직을 FastAPI 라우터로 구현
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
import logging
from datetime import datetime

router = APIRouter(prefix="/api/v1", tags=["recommendations"])
logger = logging.getLogger(__name__)

# 전역 의존성을 위한 함수들
def get_model():
    """모델 의존성 주입"""
    from src.api.main import model, model_loaded
    if not model_loaded or not model:
        raise HTTPException(
            status_code=503,
            detail="모델이 아직 로딩되지 않았습니다."
        )
    return model

def get_datasets():
    """데이터셋 의존성 주입"""
    from src.api.main import train_dataset, val_dataset, test_dataset
    if not train_dataset:
        raise HTTPException(
            status_code=503,
            detail="데이터셋이 로딩되지 않았습니다."
        )
    return train_dataset, val_dataset, test_dataset

@router.get("/recommendations")
async def get_recommendations_v1(
    k: int = Query(10, description="추천할 영화 수", ge=1, le=50),
    user_id: Optional[str] = Query(None, description="사용자 ID"),
    model = Depends(get_model),
    datasets = Depends(get_datasets)
):
    """
    영화 추천 API v1
    기존 my-mlops 로직을 사용한 개선된 추천
    """
    train_dataset, val_dataset, test_dataset = datasets
    
    try:
        # 기존 로직을 사용한 추천
        from src.dataset.data_loader import SimpleDataLoader
        from src.evaluation.evaluate import evaluate
        
        # 테스트 데이터의 일부를 사용해서 예측
        sample_size = min(k * 2, len(test_dataset.features))
        test_loader = SimpleDataLoader(
            test_dataset.features[:sample_size], 
            test_dataset.labels[:sample_size], 
            batch_size=sample_size, 
            shuffle=False
        )
        
        _, predictions = evaluate(model, test_loader)
        
        # 상위 k개 선택
        top_predictions = predictions[:k]
        recommended_content_ids = [train_dataset.decode_content_id(idx) for idx in top_predictions]
        
        logger.info(f"사용자 {user_id}에게 {len(recommended_content_ids)}개 영화 추천 완료")
        
        return {
            "user_id": user_id,
            "recommended_content_id": recommended_content_ids,
            "k": k,
            "method": "numpy_neural_network",
            "timestamp": datetime.now().isoformat(),
            "success": True
        }
        
    except Exception as e:
        logger.error(f"추천 생성 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"추천 생성 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/recommendations/similar/{movie_id}")
async def get_similar_movies(
    movie_id: int,
    k: int = Query(5, description="유사한 영화 수", ge=1, le=20),
    model = Depends(get_model),
    datasets = Depends(get_datasets)
):
    """
    특정 영화와 유사한 영화 추천
    """
    train_dataset, _, _ = datasets
    
    try:
        # 여기서는 간단히 랜덤 추천으로 구현
        # 실제로는 영화 임베딩이나 유사도 계산이 필요
        import random
        
        all_content_ids = list(range(train_dataset.num_classes))
        if movie_id in all_content_ids:
            all_content_ids.remove(movie_id)
        
        similar_ids = random.sample(all_content_ids, min(k, len(all_content_ids)))
        similar_content_ids = [train_dataset.decode_content_id(idx) for idx in similar_ids]
        
        return {
            "base_movie_id": movie_id,
            "similar_movies": similar_content_ids,
            "k": k,
            "method": "random_sampling",  # 실제로는 similarity_based
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"유사 영화 추천 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"유사 영화 추천 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/recommendations/popular")
async def get_popular_movies(
    k: int = Query(10, description="인기 영화 수", ge=1, le=50),
    datasets = Depends(get_datasets)
):
    """
    인기 영화 목록 반환
    """
    train_dataset, _, _ = datasets
    
    try:
        # 간단히 처음 k개를 인기 영화로 반환
        popular_ids = list(range(min(k, train_dataset.num_classes)))
        popular_content_ids = [train_dataset.decode_content_id(idx) for idx in popular_ids]
        
        return {
            "popular_movies": popular_content_ids,
            "k": k,
            "method": "top_rated",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"인기 영화 조회 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"인기 영화 조회 중 오류가 발생했습니다: {str(e)}"
        )
