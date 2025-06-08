"""
Movie MLOps FastAPI Main Application
기존 my-mlops 로직을 FastAPI로 래핑
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
    description="영화 추천 MLOps 시스템 - 기존 my-mlops 로직 통합",
    version="1.0.0",
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

# 라우터 등록
if recommendations_router:
    app.include_router(recommendations_router)
if features_router:
    app.include_router(features_router)
if mlflow_router:
    app.include_router(mlflow_router)

# 메트릭 라우터 추가
try:
    from src.api.routers.metrics import router as metrics_router
    app.include_router(metrics_router)
except ImportError:
    logging.warning("metrics 라우터 import 실패")

# 새로 추가된 라우터들
try:
    from src.api.routers.feedback import router as feedback_router
    app.include_router(feedback_router)
except ImportError:
    logging.warning("feedback 라우터 import 실패")

try:
    from src.api.routers.events import router as events_router
    app.include_router(events_router)
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
        # 여기서는 빠른 테스트를 위해 몇 번만 훈련
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

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "Movie MLOps API",
        "status": "running",
        "model_loaded": model_loaded,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """헬스체크 엔드포인트"""
    return {
        "status": "healthy" if model_loaded else "loading",
        "service": "movie-mlops-api",
        "model_loaded": model_loaded,
        "environment": os.getenv("ENVIRONMENT", "development"),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/")
async def get_recommendations(k: int = Query(10, description="추천할 영화 수")):
    """
    영화 추천 엔드포인트 (기존 my-mlops-web API와 호환)
    """
    if not model_loaded or not model or not train_dataset:
        raise HTTPException(
            status_code=503, 
            detail="모델이 아직 로딩되지 않았습니다. 잠시 후 다시 시도해주세요."
        )
    
    try:
        # 기존 로직을 사용한 추천
        # 실제로는 사용자별 추천을 해야 하지만, 여기서는 샘플 예측을 반환
        
        # 테스트 데이터의 첫 번째 배치를 사용해서 예측
        test_loader = SimpleDataLoader(test_dataset.features[:k], test_dataset.labels[:k], batch_size=k, shuffle=False)
        
        from src.evaluation.evaluate import evaluate
        _, predictions = evaluate(model, test_loader)
        
        # content_id로 디코딩
        recommended_content_ids = [train_dataset.decode_content_id(idx) for idx in predictions[:k]]
        
        logger.info(f"추천 완료: {len(recommended_content_ids)}개 영화")
        
        return {
            "recommended_content_id": recommended_content_ids,
            "k": k,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"추천 생성 실패: {e}")
        # 실패 시 더미 데이터 반환 (기존 동작 유지)
        dummy_ids = list(range(1, k+1))
        return {
            "recommended_content_id": dummy_ids,
            "k": k,
            "fallback": True,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/movies")
async def get_movies():
    """영화 목록 반환"""
    try:
        # 실제 데이터가 있다면 사용
        if train_dataset:
            # 일부 영화 ID들을 샘플로 반환
            sample_movies = []
            for i in range(min(10, train_dataset.num_classes)):
                content_id = train_dataset.decode_content_id(i)
                sample_movies.append({
                    "id": content_id,
                    "title": f"Movie {content_id}",
                    "rating": 8.0 + (i % 3) * 0.3  # 가상 평점
                })
            
            return {
                "movies": sample_movies,
                "count": len(sample_movies),
                "total_movies": train_dataset.num_classes
            }
        else:
            # 기본 더미 데이터
            return {
                "movies": [
                    {"id": 1, "title": "Inception", "rating": 8.8},
                    {"id": 2, "title": "The Matrix", "rating": 8.7},
                    {"id": 3, "title": "Interstellar", "rating": 8.6}
                ],
                "count": 3
            }
    except Exception as e:
        logger.error(f"영화 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"영화 목록 조회 실패: {str(e)}")

@app.get("/model/info")
async def get_model_info():
    """모델 정보 반환"""
    if not model_loaded or not model:
        raise HTTPException(status_code=503, detail="모델이 로딩되지 않았습니다.")
    
    try:
        return {
            "model_name": model.name,
            "model_type": "NumPy-based Neural Network",
            "input_dim": train_dataset.features_dim if train_dataset else "unknown",
            "num_classes": train_dataset.num_classes if train_dataset else "unknown",
            "hidden_dim": 64,
            "framework": "NumPy",
            "status": "loaded",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"모델 정보 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"모델 정보 조회 실패: {str(e)}")

@app.get("/dataset/info")
async def get_dataset_info():
    """데이터셋 정보 반환"""
    if not train_dataset:
        raise HTTPException(status_code=503, detail="데이터셋이 로딩되지 않았습니다.")
    
    try:
        return {
            "train_size": len(train_dataset.features),
            "val_size": len(val_dataset.features) if val_dataset else 0,
            "test_size": len(test_dataset.features) if test_dataset else 0,
            "features_dim": train_dataset.features_dim,
            "num_classes": train_dataset.num_classes,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"데이터셋 정보 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"데이터셋 정보 조회 실패: {str(e)}")

# 에러 핸들러
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"예상치 못한 에러: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"내부 서버 에러: {str(exc)}"}
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
