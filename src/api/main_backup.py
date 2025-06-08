"""
Movie MLOps FastAPI Main Application
기존 my-mlops 로직을 FastAPI로 래핑 - API 경로 표준화
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import sys
import os
import json
import logging
from typing import List, Optional
from datetime import datetime

# 경로 설정
sys.path.append('/app')
sys.path.append('/app/src')

# 기존 로직 import
try:
    from src.models.legacy.movie_predictor import MoviePredictor
    from src.dataset.data_loader import SimpleDataLoader
    from src.dataset.watch_log import get_datasets
    from src.utils.utils import init_seed
except ImportError as e:
    logging.warning(f"일부 모듈 import 실패: {e}")

# 라우터 import
try:
    from src.api.routers.recommendations import router as recommendations_router
except ImportError:
    recommendations_router = None
    logging.warning("recommendations 라우터 import 실패")

try:
    from src.api.routers.features import router as features_router
except ImportError:
    features_router = None
    logging.warning("features 라우터 import 실패")

try:
    from src.api.routers.mlflow import router as mlflow_router
except ImportError:
    mlflow_router = None
    logging.warning("mlflow 라우터 import 실패")

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 초기화
app = FastAPI(
    title="Movie MLOps API",
    description="영화 추천 MLOps 시스템 - RESTful API 표준 준수",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정 (React 앱과 연동)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 환경용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록 (v1 API 표준화)
if recommendations_router:
    app.include_router(recommendations_router, prefix="/api/v1")
if features_router:
    app.include_router(features_router, prefix="/api/v1")
if mlflow_router:
    app.include_router(mlflow_router, prefix="/api/v1")

# 추가 라우터들
try:
    from src.api.routers.metrics import router as metrics_router
    app.include_router(metrics_router, prefix="/api/v1")
except ImportError:
    logging.warning("metrics 라우터 import 실패")

try:
    from src.api.routers.feedback import router as feedback_router
    app.include_router(feedback_router)  # 이미 /api/v1 prefix 포함
except ImportError:
    logging.warning("feedback 라우터 import 실패")

try:
    from src.api.routers.events import router as events_router
    app.include_router(events_router)  # 이미 /api/v1 prefix 포함
except ImportError:
    logging.warning("events 라우터 import 실패")

# 전역 변수 (모델 및 데이터셋)
model = None
train_dataset = None
val_dataset = None
test_dataset = None
model_loaded = False

@app.on_event("startup")
async def load_model():
    """애플리케이션 시작 시 모델 로딩"""
    global model, train_dataset, val_dataset, test_dataset, model_loaded
    
    try:
        logger.info("모델 로딩 시작...")
        
        # 시드 초기화
        init_seed()
        
        # 데이터셋 로딩
        train_dataset, val_dataset, test_dataset = get_datasets()
        logger.info(f"데이터셋 로딩 완료 - 훈련: {len(train_dataset.features)}, 검증: {len(val_dataset.features)}, 테스트: {len(test_dataset.features)}")
        
        # 모델 초기화
        model_params = {
            "input_dim": train_dataset.features_dim,
            "num_classes": train_dataset.num_classes,
            "hidden_dim": 64
        }
        model = MoviePredictor(**model_params)
        logger.info(f"모델 초기화 완료 - input_dim: {model_params['input_dim']}, num_classes: {model_params['num_classes']}")
        
        # 간단한 훈련 (실제로는 사전 훈련된 모델을 로드해야 함)
        from src.training.train import train
        train_loader = SimpleDataLoader(train_dataset.features, train_dataset.labels, batch_size=32, shuffle=True)
        
        for epoch in range(3):  # 빠른 테스트용
            train_loss = train(model, train_loader)
            logger.info(f"빠른 훈련 Epoch {epoch + 1}/3, Loss: {train_loss:.4f}")
        
        model_loaded = True
        logger.info("모델 로딩 및 초기 훈련 완료!")
        
    except Exception as e:
        logger.error(f"모델 로딩 실패: {e}")
        model_loaded = False

# ==========================================
# 기본 시스템 엔드포인트들 (표준화)
# ==========================================

@app.get("/")
async def root():
    """루트 엔드포인트 - API 정보 제공"""
    return {
        "service": "Movie MLOps API",
        "version": "2.0.0", 
        "status": "running",
        "model_loaded": model_loaded,
        "api_docs": "/docs",
        "api_redoc": "/redoc",
        "endpoints": {
            "recommendations": "/api/v1/recommendations",
            "features": "/api/v1/features",
            "feedback": "/api/v1/feedback", 
            "events": "/api/v1/events",
            "mlflow": "/api/v1/mlflow",
            "health": "/health",
            "movies": "/api/v1/movies",
            "model_info": "/api/v1/model/info"
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """헬스체크 엔드포인트"""
    return {
        "status": "healthy" if model_loaded else "loading",
        "service": "movie-mlops-api",
        "version": "2.0.0",
        "model_loaded": model_loaded,
        "environment": os.getenv("ENVIRONMENT", "development"),
        "uptime": "running",
        "timestamp": datetime.now().isoformat()
    }

# ==========================================
# v1 API 엔드포인트들 (RESTful 표준)
# ==========================================

@app.get("/api/v1/recommendations")
async def get_recommendations(
    k: int = Query(10, description="추천할 영화 수", ge=1, le=100),
    user_id: Optional[str] = Query(None, description="사용자 ID")
):
    """
    영화 추천 API - RESTful 표준
    """
    if not model_loaded or not model or not train_dataset:
        raise HTTPException(
            status_code=503, 
            detail="모델이 아직 로딩되지 않았습니다. 잠시 후 다시 시도해주세요."
        )
    
    try:
        # 테스트 데이터를 사용한 추천
        test_loader = SimpleDataLoader(test_dataset.features[:k], test_dataset.labels[:k], batch_size=k, shuffle=False)
        
        from src.evaluation.evaluate import evaluate
        _, predictions = evaluate(model, test_loader)
        
        # content_id로 디코딩
        recommended_content_ids = [train_dataset.decode_content_id(idx) for idx in predictions[:k]]
        
        logger.info(f"추천 완료: {len(recommended_content_ids)}개 영화 (사용자: {user_id})")
        
        return {
            "user_id": user_id,
            "recommendations": recommended_content_ids,
            "count": len(recommended_content_ids),
            "algorithm": "neural_network_v1",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"추천 생성 실패: {e}")
        # 실패 시 더미 데이터 반환 (기존 동작 유지)
        dummy_ids = list(range(1, k+1))
        return {
            "user_id": user_id,
            "recommendations": dummy_ids,
            "count": len(dummy_ids),
            "algorithm": "fallback",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/v1/movies")
async def get_movies(
    limit: int = Query(10, description="반환할 영화 수", ge=1, le=100),
    offset: int = Query(0, description="시작 오프셋", ge=0)
):
    """영화 목록 API - RESTful 표준"""
    try:
        if train_dataset:
            # 페이지네이션 적용
            total_movies = train_dataset.num_classes
            start_idx = offset
            end_idx = min(offset + limit, total_movies)
            
            sample_movies = []
            for i in range(start_idx, end_idx):
                content_id = train_dataset.decode_content_id(i)
                sample_movies.append({
                    "id": content_id,
                    "title": f"Movie {content_id}",
                    "rating": round(8.0 + (i % 3) * 0.3, 1),
                    "genre": ["Action", "Drama", "Comedy"][i % 3]
                })
            
            return {
                "movies": sample_movies,
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "count": len(sample_movies),
                    "total": total_movies,
                    "has_next": end_idx < total_movies
                },
                "timestamp": datetime.now().isoformat()
            }
        else:
            # 기본 더미 데이터
            return {
                "movies": [
                    {"id": 1, "title": "Inception", "rating": 8.8, "genre": "Sci-Fi"},
                    {"id": 2, "title": "The Matrix", "rating": 8.7, "genre": "Action"},
                    {"id": 3, "title": "Interstellar", "rating": 8.6, "genre": "Drama"}
                ][:limit],
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "count": min(3, limit),
                    "total": 3,
                    "has_next": False
                }
            }
    except Exception as e:
        logger.error(f"영화 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"영화 목록 조회 실패: {str(e)}")

@app.get("/api/v1/model/info")
async def get_model_info():
    """모델 정보 API - RESTful 표준"""
    if not model_loaded or not model:
        raise HTTPException(status_code=503, detail="모델이 로딩되지 않았습니다.")
    
    try:
        return {
            "model": {
                "name": model.name,
                "type": "Neural Network",
                "framework": "NumPy",
                "version": "1.0.0",
                "status": "loaded"
            },
            "architecture": {
                "input_dim": train_dataset.features_dim if train_dataset else "unknown",
                "hidden_dim": 64,
                "output_dim": train_dataset.num_classes if train_dataset else "unknown"
            },
            "dataset": {
                "train_size": len(train_dataset.features) if train_dataset else 0,
                "val_size": len(val_dataset.features) if val_dataset else 0,
                "test_size": len(test_dataset.features) if test_dataset else 0
            },
            "performance": {
                "last_training_loss": "available_after_training",
                "accuracy": "available_after_evaluation"
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"모델 정보 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"모델 정보 조회 실패: {str(e)}")

# ==========================================
# 하위 호환성 유지 (기존 React 앱 지원)
# ==========================================

@app.get("/recommendations")
async def get_recommendations_legacy(k: int = Query(10, description="추천할 영화 수")):
    """기존 React 앱과의 하위 호환성을 위한 레거시 엔드포인트"""
    logger.warning("레거시 API 호출됨. /api/v1/recommendations 사용을 권장합니다.")
    
    # 새로운 API로 리다이렉트
    result = await get_recommendations(k=k)
    
    # 기존 형식으로 변환
    return {
        "recommended_content_id": result.get("recommendations", []),
        "k": k,
        "timestamp": result.get("timestamp")
    }

# ==========================================
# 에러 핸들러
# ==========================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"예상치 못한 에러: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": f"서버에서 예상치 못한 오류가 발생했습니다: {str(exc)}",
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
