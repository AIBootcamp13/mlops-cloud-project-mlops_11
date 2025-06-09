#!/usr/bin/env python3
"""
Custom Feast Server with Modified FastAPI Title
Feast Feature Server에 커스텀 타이틀을 적용하기 위한 래퍼
"""

import os
import sys
from feast import FeatureStore
from feast.feature_server import get_app
import uvicorn

def create_custom_feast_app():
    """커스텀 타이틀을 가진 Feast FastAPI 앱 생성"""
    
    # Feast 스토어 초기화
    store = FeatureStore(repo_path=".")
    
    # Feast의 기본 FastAPI 앱 가져오기
    app = get_app(store)
    
    # FastAPI 앱 메타데이터 수정
    app.title = "Feast Feature Server (Built-in FastAPI)"
    app.description = "ML Feature Store with Built-in FastAPI Server - Movie MLOps"
    app.version = "0.40.1"
    
    return app

if __name__ == "__main__":
    # 환경변수에서 포트 설정 가져오기
    port = int(os.getenv("FEAST_PORT", "6567"))
    host = os.getenv("FEAST_HOST", "0.0.0.0")
    
    print(f"🍃 Feast Feature Server 시작 중...")
    print(f"📡 서버 주소: http://{host}:{port}")
    print(f"📖 API 문서: http://localhost:{port}/docs")
    print(f"🚀 내장된 FastAPI 서버 사용")
    
    # 커스텀 앱 생성
    app = create_custom_feast_app()
    
    # 서버 실행
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )
