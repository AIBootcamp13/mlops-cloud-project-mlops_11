#!/usr/bin/env python3
"""
Movie MLOps 최소 API 서버
Docker 없이 바로 실행 가능한 단순 버전
"""

import sys
import os
import json
import logging
from datetime import datetime
from typing import List, Optional

# FastAPI 설치 확인 및 임포트
try:
    from fastapi import FastAPI, HTTPException, Query
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    import uvicorn
except ImportError:
    print("❌ FastAPI가 설치되지 않았습니다.")
    print("다음 명령어로 설치하세요:")
    print("pip install fastapi uvicorn")
    sys.exit(1)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 초기화
app = FastAPI(
    title="Movie MLOps API (Simple)",
    description="영화 추천 MLOps 시스템 - 간단 버전",
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

# 더미 데이터
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
]

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "service": "Movie MLOps API (Simple)",
        "version": "1.0.0", 
        "status": "running",
        "api_docs": "/docs",
        "endpoints": {
            "recommendations": "/api/v1/recommendations",
            "movies": "/api/v1/movies",
            "health": "/health"
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """헬스체크 엔드포인트"""
    return {
        "status": "healthy",
        "service": "movie-mlops-api-simple",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/recommendations")
async def get_recommendations(
    k: int = Query(10, description="추천할 영화 수", ge=1, le=100),
    user_id: Optional[str] = Query(None, description="사용자 ID")
):
    """영화 추천 API"""
    try:
        # 간단한 추천 로직 (인기도 기반)
        sorted_movies = sorted(DUMMY_MOVIES, key=lambda x: x["rating"], reverse=True)
        recommendations = [movie["id"] for movie in sorted_movies[:k]]
        
        logger.info(f"추천 완료: {len(recommendations)}개 영화 (사용자: {user_id})")
        
        return {
            "user_id": user_id,
            "recommendations": recommendations,
            "count": len(recommendations),
            "algorithm": "popularity_based",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"추천 생성 실패: {e}")
        return {
            "user_id": user_id,
            "recommendations": list(range(1, k+1)),
            "count": k,
            "algorithm": "fallback",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/v1/movies")
async def get_movies(
    limit: int = Query(10, description="반환할 영화 수", ge=1, le=100),
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
            "name": "simple_popularity_recommender",
            "type": "Rule-based",
            "framework": "Python",
            "version": "1.0.0",
            "status": "loaded"
        },
        "algorithm": "popularity_based_ranking",
        "dataset": {
            "total_movies": len(DUMMY_MOVIES),
            "last_updated": "2025-06-08"
        },
        "timestamp": datetime.now().isoformat()
    }

# 레거시 호환성
@app.get("/recommendations")
async def get_recommendations_legacy(k: int = Query(10, description="추천할 영화 수")):
    """기존 React 앱과의 하위 호환성을 위한 레거시 엔드포인트"""
    result = await get_recommendations(k=k)
    return {
        "recommended_content_id": result.get("recommendations", []),
        "k": k,
        "timestamp": result.get("timestamp")
    }

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
    print("🚀 Movie MLOps API (Simple) 시작...")
    print("📖 API 문서: http://localhost:8000/docs")
    print("🔍 헬스체크: http://localhost:8000/health")
    print("⚡ 추천 API: http://localhost:8000/api/v1/recommendations")
    print("🎬 영화 목록: http://localhost:8000/api/v1/movies")
    print("🔄 레거시 API: http://localhost:8000/recommendations")
    print("\nCtrl+C로 종료")
    
    uvicorn.run(
        "api_simple:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
