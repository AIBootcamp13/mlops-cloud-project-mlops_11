"""Feast 피처 스토어 API 라우터"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
import logging
from pydantic import BaseModel

from src.features.feast_client import get_feast_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/features", tags=["features"])


class FeatureRequest(BaseModel):
    """피처 요청 모델"""
    entity_ids: List[int]
    feature_groups: Optional[List[str]] = None


class MovieFeatureRequest(FeatureRequest):
    """영화 피처 요청 모델"""
    feature_groups: Optional[List[str]] = ["basic", "popularity", "category"]


class UserFeatureRequest(FeatureRequest):
    """사용자 피처 요청 모델"""
    feature_groups: Optional[List[str]] = ["behavior", "preferences", "activity"]


@router.get("/health")
async def features_health_check():
    """피처 스토어 상태 확인"""
    try:
        feast_client = get_feast_client()
        feature_views = feast_client.list_feature_views()
        
        return {
            "status": "healthy",
            "feast_client_initialized": feast_client.store is not None,
            "feature_views_count": len(feature_views),
            "available_feature_views": feature_views
        }
    except Exception as e:
        logger.error(f"피처 스토어 상태 확인 실패: {e}")
        raise HTTPException(status_code=500, detail=f"피처 스토어 상태 확인 실패: {str(e)}")


@router.get("/views")
async def list_feature_views():
    """등록된 피처 뷰 목록 조회"""
    try:
        feast_client = get_feast_client()
        feature_views = feast_client.list_feature_views()
        
        detailed_views = []
        for view_name in feature_views:
            view_info = feast_client.get_feature_view_info(view_name)
            detailed_views.append(view_info)
        
        return {
            "feature_views": detailed_views,
            "count": len(detailed_views)
        }
    except Exception as e:
        logger.error(f"피처 뷰 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"피처 뷰 조회 실패: {str(e)}")


@router.post("/movies")
async def get_movie_features(request: MovieFeatureRequest):
    """영화 피처 조회"""
    try:
        feast_client = get_feast_client()
        
        features = feast_client.get_movie_features(
            movie_ids=request.entity_ids,
            feature_groups=request.feature_groups
        )
        
        return {
            "movie_ids": request.entity_ids,
            "feature_groups": request.feature_groups,
            "features": features,
            "count": len(request.entity_ids)
        }
        
    except Exception as e:
        logger.error(f"영화 피처 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"영화 피처 조회 실패: {str(e)}")


@router.post("/users")
async def get_user_features(request: UserFeatureRequest):
    """사용자 피처 조회"""
    try:
        feast_client = get_feast_client()
        
        features = feast_client.get_user_features(
            user_ids=request.entity_ids,
            feature_groups=request.feature_groups
        )
        
        return {
            "user_ids": request.entity_ids,
            "feature_groups": request.feature_groups,
            "features": features,
            "count": len(request.entity_ids)
        }
        
    except Exception as e:
        logger.error(f"사용자 피처 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"사용자 피처 조회 실패: {str(e)}")


@router.get("/movies/{movie_id}")
async def get_single_movie_features(
    movie_id: int,
    feature_groups: List[str] = Query(default=["basic", "popularity"])
):
    """단일 영화 피처 조회"""
    try:
        feast_client = get_feast_client()
        
        features = feast_client.get_movie_features(
            movie_ids=[movie_id],
            feature_groups=feature_groups
        )
        
        return {
            "movie_id": movie_id,
            "feature_groups": feature_groups,
            "features": features
        }
        
    except Exception as e:
        logger.error(f"영화 피처 조회 실패 (ID: {movie_id}): {e}")
        raise HTTPException(status_code=500, detail=f"영화 피처 조회 실패: {str(e)}")


@router.get("/users/{user_id}")
async def get_single_user_features(
    user_id: int,
    feature_groups: List[str] = Query(default=["behavior", "preferences"])
):
    """단일 사용자 피처 조회"""
    try:
        feast_client = get_feast_client()
        
        features = feast_client.get_user_features(
            user_ids=[user_id],
            feature_groups=feature_groups
        )
        
        return {
            "user_id": user_id,
            "feature_groups": feature_groups,
            "features": features
        }
        
    except Exception as e:
        logger.error(f"사용자 피처 조회 실패 (ID: {user_id}): {e}")
        raise HTTPException(status_code=500, detail=f"사용자 피처 조회 실패: {str(e)}")


@router.post("/training-data")
async def prepare_training_data(
    entity_df: Dict[str, Any],
    features: List[str],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """모델 훈련용 피처 데이터 준비"""
    try:
        feast_client = get_feast_client()
        
        import pandas as pd
        from datetime import datetime
        
        # 엔티티 DataFrame 생성
        entity_dataframe = pd.DataFrame(entity_df)
        
        # 날짜 파싱
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        training_data = feast_client.prepare_training_data(
            entity_df=entity_dataframe,
            features=features,
            start_date=start_dt,
            end_date=end_dt
        )
        
        return {
            "training_data_shape": training_data.shape,
            "features": list(training_data.columns),
            "sample_data": training_data.head().to_dict() if not training_data.empty else {}
        }
        
    except Exception as e:
        logger.error(f"훈련 데이터 준비 실패: {e}")
        raise HTTPException(status_code=500, detail=f"훈련 데이터 준비 실패: {str(e)}")


@router.post("/materialize")
async def materialize_features(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """피처를 온라인 스토어에 실체화"""
    try:
        feast_client = get_feast_client()
        
        from datetime import datetime
        
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        feast_client.materialize_features(start_dt, end_dt)
        
        return {
            "status": "success",
            "message": "피처 실체화가 완료되었습니다",
            "start_date": start_date,
            "end_date": end_date
        }
        
    except Exception as e:
        logger.error(f"피처 실체화 실패: {e}")
        raise HTTPException(status_code=500, detail=f"피처 실체화 실패: {str(e)}")
