"""
메트릭 API 라우터
Prometheus가 메트릭을 스크래핑할 수 있는 엔드포인트 제공
"""

import time
import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST

from ..monitoring.prometheus_metrics import get_metrics, health_checker
from ..monitoring.custom_metrics import custom_metrics

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/metrics", tags=["metrics"])

@router.get("/", response_class=PlainTextResponse)
async def get_prometheus_metrics():
    """
    Prometheus 메트릭 엔드포인트
    모든 수집된 메트릭을 Prometheus 형식으로 반환
    """
    try:
        metrics = get_metrics()
        metrics_data = metrics.get_metrics()
        
        return Response(
            content=metrics_data,
            media_type=CONTENT_TYPE_LATEST
        )
    except Exception as e:
        logger.error(f"Error generating metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate metrics")

@router.get("/health")
async def health_check():
    """
    서비스 헬스체크 엔드포인트
    모든 의존 서비스의 상태 확인
    """
    try:
        health_status = health_checker.check_all_services()
        
        all_healthy = all(health_status.values())
        
        return {
            "status": "healthy" if all_healthy else "unhealthy",
            "timestamp": time.time(),
            "services": health_status,
            "overall_health": all_healthy
        }
    except Exception as e:
        logger.error(f"Error during health check: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")

@router.get("/system")
async def get_system_metrics():
    """
    시스템 메트릭 조회
    CPU, 메모리, 디스크 사용률 등 시스템 메트릭 반환
    """
    try:
        metrics = get_metrics()
        
        # 현재 시스템 메트릭 수집
        metrics.collect_system_metrics()
        
        # 시스템 정보 반환 (예시)
        import psutil
        
        return {
            "cpu_percent": psutil.cpu_percent(),
            "memory": {
                "total": psutil.virtual_memory().total,
                "available": psutil.virtual_memory().available,
                "used": psutil.virtual_memory().used,
                "percent": psutil.virtual_memory().percent
            },
            "disk": {
                "total": psutil.disk_usage('/').total,
                "used": psutil.disk_usage('/').used,
                "free": psutil.disk_usage('/').free,
                "percent": (psutil.disk_usage('/').used / psutil.disk_usage('/').total) * 100
            },
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system metrics")

@router.post("/custom/recommendation")
async def record_recommendation_metrics(request: Dict[str, Any]):
    """
    추천 시스템 커스텀 메트릭 기록
    """
    try:
        algorithm = request.get('algorithm', 'unknown')
        user_segment = request.get('user_segment', 'default')
        request_type = request.get('request_type', 'standard')
        success = request.get('success', True)
        latency = request.get('latency', 0.0)
        
        # 추천 요청 메트릭 기록
        custom_metrics['recommendation'].recommendation_requests_total.labels(
            algorithm=algorithm,
            user_segment=user_segment,
            request_type=request_type
        ).inc()
        
        # 성공한 경우 성공 메트릭 기록
        if success:
            custom_metrics['recommendation'].recommendation_success_total.labels(
                algorithm=algorithm,
                user_segment=user_segment
            ).inc()
        
        # 지연시간 기록
        if latency > 0:
            custom_metrics['recommendation'].recommendation_latency_seconds.labels(
                algorithm=algorithm,
                user_segment=user_segment,
                cache_status='miss'  # 실제로는 캐시 상태를 확인해야 함
            ).observe(latency)
        
        return {"status": "recorded", "timestamp": time.time()}
        
    except Exception as e:
        logger.error(f"Error recording recommendation metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to record metrics")

@router.post("/custom/user_interaction")
async def record_user_interaction_metrics(request: Dict[str, Any]):
    """
    사용자 상호작용 메트릭 기록
    """
    try:
        interaction_type = request.get('interaction_type', 'view')
        user_segment = request.get('user_segment', 'default')
        movie_id = request.get('movie_id')
        rating = request.get('rating')
        session_duration = request.get('session_duration')
        
        # 사용자 상호작용 메트릭 기록
        custom_metrics['recommendation'].user_interactions_total.labels(
            interaction_type=interaction_type,
            user_segment=user_segment
        ).inc()
        
        # 평점이 있는 경우 평점 분포 업데이트
        if rating:
            custom_metrics['recommendation'].rating_distribution.labels(
                rating=str(rating),
                genre='unknown',  # 실제로는 영화 장르를 조회해야 함
                time_period='current'
            ).set(rating)
        
        # 세션 지속시간이 있는 경우 기록
        if session_duration:
            custom_metrics['recommendation'].user_session_duration_seconds.labels(
                user_segment=user_segment,
                device_type='web'  # 실제로는 디바이스 타입을 감지해야 함
            ).observe(session_duration)
        
        return {"status": "recorded", "timestamp": time.time()}
        
    except Exception as e:
        logger.error(f"Error recording user interaction metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to record metrics")

@router.post("/custom/model_performance")
async def record_model_performance_metrics(request: Dict[str, Any]):
    """
    모델 성능 메트릭 기록
    """
    try:
        model_type = request.get('model_type', 'unknown')
        model_version = request.get('model_version', 'v1.0')
        rmse = request.get('rmse')
        mae = request.get('mae')
        inference_time = request.get('inference_time')
        
        # 모델 성능 메트릭 기록
        if rmse is not None:
            custom_metrics['ml_pipeline'].model_rmse.labels(
                model_type=model_type,
                model_version=model_version,
                dataset='production'
            ).set(rmse)
        
        if mae is not None:
            custom_metrics['ml_pipeline'].model_mae.labels(
                model_type=model_type,
                model_version=model_version,
                dataset='production'
            ).set(mae)
        
        # 추론 시간 기록
        if inference_time is not None:
            custom_metrics['recommendation'].model_inference_duration_seconds.labels(
                model_type=model_type,
                model_version=model_version,
                batch_size='1'
            ).observe(inference_time)
        
        return {"status": "recorded", "timestamp": time.time()}
        
    except Exception as e:
        logger.error(f"Error recording model performance metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to record metrics")

@router.get("/summary")
async def get_metrics_summary():
    """
    메트릭 요약 정보 반환
    대시보드나 모니터링 도구에서 사용할 요약 정보 제공
    """
    try:
        # 현재 시간
        current_time = time.time()
        
        # 헬스체크 실행
        health_status = health_checker.check_all_services()
        
        # 시스템 메트릭 수집
        import psutil
        
        summary = {
            "timestamp": current_time,
            "system": {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": (psutil.disk_usage('/').used / psutil.disk_usage('/').total) * 100
            },
            "services": health_status,
            "overall_health": all(health_status.values()),
            "metrics_collected": True
        }
        
        return summary
        
    except Exception as e:
        logger.error(f"Error generating metrics summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate summary")

# 미들웨어 함수들
async def record_request_metrics(request: Request, call_next):
    """
    HTTP 요청 메트릭을 자동으로 기록하는 미들웨어
    """
    start_time = time.time()
    
    response = await call_next(request)
    
    # 요청 처리 시간 계산
    duration = time.time() - start_time
    
    # 메트릭 기록
    metrics = get_metrics()
    metrics.record_http_request(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code,
        duration=duration
    )
    
    return response
