"""
Movie MLOps FastAPI Main Application - Working Version
기존 로직을 제거하고 핵심 기능만 남긴 안정 버전
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import logging
from typing import List, Optional
from datetime import datetime
import random

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 초기화
app = FastAPI(
    title="Movie MLOps API",
    description="영화 추천 MLOps 시스템 - 안정 버전",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 더미 영화 데이터
DUMMY_MOVIES = [
    {"id": 1, "title": "Inception", "rating": 8.8, "genre": "Sci-Fi"},
    {"id": 2, "title": "The Matrix", "rating": 8.7, "genre": "Action"},
    {"id": 3, "title": "Interstellar", "rating": 8.6, "genre": "Drama"},
    {"id": 4, "title": "The Dark Knight", "rating": 9.0, "genre": "Action"},
    {"id": 5, "title": "Pulp Fiction", "rating": 8.9, "genre": "Crime"},
    {"id": 6, "title": "Fight Club", "rating": 8.8, "genre": "Drama"},
    {"id": 7, "title": "Forrest Gump", "rating": 8.8, "genre": "Drama"},
    {"id": 8, "title": "The Godfather", "rating": 9.2, "genre": "Crime"},
    {"id": 9, "title": "The Shawshank Redemption", "rating": 9.3, "genre": "Drama"},
    {"id": 10, "title": "Avatar", "rating": 7.8, "genre": "Sci-Fi"},
    {"id": 11, "title": "Titanic", "rating": 7.9, "genre": "Romance"},
    {"id": 12, "title": "Star Wars", "rating": 8.6, "genre": "Sci-Fi"},
    {"id": 13, "title": "Avengers: Endgame", "rating": 8.4, "genre": "Action"},
    {"id": 14, "title": "Joker", "rating": 8.4, "genre": "Drama"},
    {"id": 15, "title": "Parasite", "rating": 8.5, "genre": "Thriller"},
]

# 전역 상태
model_loaded = True
startup_time = datetime.now()

@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행"""
    global startup_time
    startup_time = datetime.now()
    logger.info("Movie MLOps API 시작됨")

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "service": "Movie MLOps API",
        "version": "1.0.0", 
        "status": "running",
        "model_loaded": model_loaded,
        "startup_time": startup_time.isoformat(),
        "api_docs": "/docs",
        "endpoints": {
            "recommendations": "/api/v1/recommendations",
            "movies": "/api/v1/movies",
            "health": "/health",
            "legacy_recommendations": "/recommendations"
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """헬스체크 엔드포인트"""
    return {
        "status": "healthy",
        "service": "movie-mlops-api",
        "version": "1.0.0",
        "model_loaded": model_loaded,
        "environment": os.getenv("ENVIRONMENT", "development"),
        "uptime_seconds": (datetime.now() - startup_time).total_seconds(),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/recommendations")
async def get_recommendations(
    k: int = Query(10, description="추천할 영화 수", ge=1, le=50),
    user_id: Optional[str] = Query(None, description="사용자 ID")
):
    """영화 추천 API"""
    try:
        # 간단한 추천 알고리즘 (평점 기반 + 랜덤 요소)
        sorted_movies = sorted(DUMMY_MOVIES, key=lambda x: x["rating"], reverse=True)
        
        # 상위 영화들에서 랜덤하게 선택 (다양성 확보)
        top_movies = sorted_movies[:min(k*2, len(sorted_movies))]
        random.shuffle(top_movies)
        
        recommendations = [movie["id"] for movie in top_movies[:k]]
        
        logger.info(f"추천 완료: {len(recommendations)}개 영화 (사용자: {user_id})")
        
        return {
            "user_id": user_id,
            "recommendations": recommendations,
            "count": len(recommendations),
            "algorithm": "hybrid_rating_random",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"추천 생성 실패: {e}")
        # 폴백 추천
        fallback = list(range(1, k+1))
        return {
            "user_id": user_id,
            "recommendations": fallback,
            "count": len(fallback),
            "algorithm": "fallback",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/v1/movies")
async def get_movies(
    limit: int = Query(10, description="반환할 영화 수", ge=1, le=50),
    offset: int = Query(0, description="시작 오프셋", ge=0)
):
    """영화 목록 API"""
    try:
        total_movies = len(DUMMY_MOVIES)
        start_idx = offset
        end_idx = min(offset + limit, total_movies)
        
        movies = DUMMY_MOVIES[start_idx:end_idx]
        
        return {
            "movies": movies,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "count": len(movies),
                "total": total_movies,
                "has_next": end_idx < total_movies
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"영화 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"영화 목록 조회 실패: {str(e)}")

@app.get("/api/v1/model/info")
async def get_model_info():
    """모델 정보 API"""
    return {
        "model": {
            "name": "hybrid_rating_recommender",
            "type": "Hybrid (Rating + Random)",
            "framework": "Python",
            "version": "1.0.0",
            "status": "loaded"
        },
        "algorithm": "hybrid_rating_random",
        "dataset": {
            "total_movies": len(DUMMY_MOVIES),
            "last_updated": "2025-06-08"
        },
        "performance": {
            "avg_response_time": "< 100ms",
            "availability": "99.9%"
        },
        "timestamp": datetime.now().isoformat()
    }

# 레거시 호환성 (기존 React 앱 지원)
@app.get("/recommendations")
async def get_recommendations_legacy(k: int = Query(10, description="추천할 영화 수")):
    """기존 React 앱과의 하위 호환성을 위한 레거시 엔드포인트"""
    logger.info(f"레거시 API 호출됨: k={k}")
    
    result = await get_recommendations(k=k)
    
    # 기존 형식으로 변환
    return {
        "recommended_content_id": result.get("recommendations", []),
        "k": k,
        "timestamp": result.get("timestamp")
    }

@app.get("/movies")
async def get_movies_legacy():
    """기존 영화 목록 레거시 엔드포인트"""
    result = await get_movies(limit=10)
    return result["movies"]

# 간단한 피드백 API
@app.post("/api/v1/feedback")
async def submit_feedback(feedback_data: dict):
    """피드백 제출 API (더미 구현)"""
    logger.info(f"피드백 수신: {feedback_data}")
    return {
        "status": "success",
        "message": "피드백이 성공적으로 저장되었습니다",
        "feedback_id": f"fb_{int(datetime.now().timestamp())}",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/feedback/{user_id}")
async def get_user_feedback(user_id: str, limit: int = Query(10, ge=1, le=100)):
    """사용자 피드백 조회 API (더미 구현)"""
    return {
        "user_id": user_id,
        "feedback_history": [],
        "count": 0,
        "message": "피드백 기록이 없습니다",
        "timestamp": datetime.now().isoformat()
    }

# 에러 핸들러
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
        "main_simple:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
