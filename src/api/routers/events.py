"""이벤트 처리 API 라우터"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["events"])


class UserInteractionEvent(BaseModel):
    """사용자 상호작용 이벤트"""
    user_id: str
    movie_id: int
    interaction_type: str  # "view", "click", "like", "share", "add_to_watchlist"
    session_id: Optional[str] = None
    device_type: Optional[str] = None
    duration_seconds: Optional[int] = None
    page_url: Optional[str] = None
    referrer: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SystemEvent(BaseModel):
    """시스템 이벤트"""
    event_type: str  # "model_prediction", "api_call", "error", "performance"
    service_name: str
    severity: str  # "info", "warning", "error", "critical"
    message: str
    metadata: Optional[Dict[str, Any]] = None


class ModelDriftEvent(BaseModel):
    """모델 드리프트 이벤트"""
    model_name: str
    model_version: str
    drift_score: float
    threshold: float
    drift_type: str  # "data_drift", "concept_drift", "prediction_drift"
    affected_features: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


@router.post("/events/user-interaction")
async def log_user_interaction(
    event: UserInteractionEvent, 
    background_tasks: BackgroundTasks
):
    """사용자 상호작용 이벤트 로깅"""
    try:
        # 이벤트 데이터 구성
        event_data = {
            "event_id": f"ui_{event.user_id}_{int(datetime.now().timestamp())}",
            "event_type": "user_interaction",
            "timestamp": datetime.now().isoformat(),
            **event.dict()
        }
        
        # 백그라운드에서 이벤트 처리
        background_tasks.add_task(process_user_interaction_event, event_data)
        
        logger.info(f"사용자 상호작용 이벤트 수신: {event_data['event_id']}")
        
        return {
            "event_id": event_data["event_id"],
            "status": "accepted",
            "message": "이벤트가 성공적으로 수신되었습니다",
            "timestamp": event_data["timestamp"]
        }
        
    except Exception as e:
        logger.error(f"사용자 상호작용 이벤트 처리 실패: {e}")
        raise HTTPException(status_code=500, detail=f"이벤트 처리 실패: {str(e)}")


@router.post("/events/system")
async def log_system_event(
    event: SystemEvent,
    background_tasks: BackgroundTasks
):
    """시스템 이벤트 로깅"""
    try:
        event_data = {
            "event_id": f"sys_{int(datetime.now().timestamp())}",
            "event_type": "system_event",
            "timestamp": datetime.now().isoformat(),
            **event.dict()
        }
        
        background_tasks.add_task(process_system_event, event_data)
        
        logger.info(f"시스템 이벤트 수신: {event_data['event_id']}")
        
        return {
            "event_id": event_data["event_id"],
            "status": "accepted",
            "timestamp": event_data["timestamp"]
        }
        
    except Exception as e:
        logger.error(f"시스템 이벤트 처리 실패: {e}")
        raise HTTPException(status_code=500, detail=f"이벤트 처리 실패: {str(e)}")


@router.post("/events/model-drift")
async def log_model_drift(
    event: ModelDriftEvent,
    background_tasks: BackgroundTasks
):
    """모델 드리프트 이벤트 로깅"""
    try:
        event_data = {
            "event_id": f"drift_{event.model_name}_{int(datetime.now().timestamp())}",
            "event_type": "model_drift",
            "timestamp": datetime.now().isoformat(),
            **event.dict()
        }
        
        background_tasks.add_task(process_model_drift_event, event_data)
        
        logger.warning(f"모델 드리프트 감지: {event_data['event_id']}")
        
        return {
            "event_id": event_data["event_id"],
            "status": "accepted",
            "alert_triggered": event.drift_score > event.threshold,
            "timestamp": event_data["timestamp"]
        }
        
    except Exception as e:
        logger.error(f"모델 드리프트 이벤트 처리 실패: {e}")
        raise HTTPException(status_code=500, detail=f"이벤트 처리 실패: {str(e)}")


@router.get("/events/stats")
async def get_event_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """이벤트 통계 조회"""
    try:
        stats = await get_event_statistics(start_date, end_date)
        
        return {
            "period": {
                "start_date": start_date,
                "end_date": end_date
            },
            "statistics": stats
        }
        
    except Exception as e:
        logger.error(f"이벤트 통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"통계 조회 실패: {str(e)}")


async def process_user_interaction_event(event_data: Dict[str, Any]):
    """사용자 상호작용 이벤트 처리"""
    try:
        # 1. 이벤트 저장
        await save_event_to_storage(event_data)
        
        # 2. 실시간 개인화를 위한 사용자 프로필 업데이트
        await update_user_profile(event_data)
        
        # 3. A/B 테스트 메트릭 업데이트
        await update_ab_test_metrics(event_data)
        
        # 4. Kafka로 이벤트 스트림 전송
        await send_to_kafka(event_data)
        
    except Exception as e:
        logger.error(f"사용자 상호작용 이벤트 처리 실패: {e}")


async def process_system_event(event_data: Dict[str, Any]):
    """시스템 이벤트 처리"""
    try:
        # 1. 이벤트 저장
        await save_event_to_storage(event_data)
        
        # 2. 경고 수준에 따른 알림 처리
        if event_data.get("severity") in ["error", "critical"]:
            await send_alert_notification(event_data)
        
        # 3. 모니터링 대시보드 업데이트
        await update_monitoring_dashboard(event_data)
        
    except Exception as e:
        logger.error(f"시스템 이벤트 처리 실패: {e}")


async def process_model_drift_event(event_data: Dict[str, Any]):
    """모델 드리프트 이벤트 처리"""
    try:
        # 1. 이벤트 저장
        await save_event_to_storage(event_data)
        
        # 2. 드리프트 임계값 초과 시 자동 재훈련 트리거
        if event_data.get("drift_score", 0) > event_data.get("threshold", 1.0):
            await trigger_model_retraining(event_data)
        
        # 3. 모델 성능 모니터링 업데이트
        await update_model_performance_metrics(event_data)
        
        # 4. 알림 발송
        await send_drift_alert(event_data)
        
    except Exception as e:
        logger.error(f"모델 드리프트 이벤트 처리 실패: {e}")


async def save_event_to_storage(event_data: Dict[str, Any]):
    """이벤트를 저장소에 저장"""
    try:
        import os
        import json
        
        # 이벤트 타입별 디렉터리 생성
        event_type = event_data.get("event_type", "unknown")
        event_dir = f"data/events/{event_type}"
        os.makedirs(event_dir, exist_ok=True)
        
        # 날짜별 파일에 저장
        date_str = datetime.now().strftime("%Y%m%d")
        filename = f"{event_dir}/events_{date_str}.jsonl"
        
        with open(filename, "a", encoding="utf-8") as f:
            f.write(json.dumps(event_data, ensure_ascii=False) + "\n")
            
    except Exception as e:
        logger.error(f"이벤트 저장 실패: {e}")


async def send_to_kafka(event_data: Dict[str, Any]):
    """Kafka로 이벤트 전송"""
    try:
        from src.events.kafka_producer import MovieEventProducer
        producer = MovieEventProducer()
        
        event_type = event_data.get("event_type")
        if event_type == "user_interaction":
            await producer.send_user_interaction(event_data)
        elif event_type == "system_event":
            await producer.send_system_event(event_data)
        elif event_type == "model_drift":
            await producer.send_model_drift(event_data)
            
    except ImportError:
        logger.warning("Kafka 프로듀서를 사용할 수 없습니다")
    except Exception as e:
        logger.error(f"Kafka 전송 실패: {e}")


async def update_user_profile(event_data: Dict[str, Any]):
    """사용자 프로필 업데이트"""
    # 실제 구현에서는 사용자 행동 분석 및 프로필 업데이트
    pass


async def update_ab_test_metrics(event_data: Dict[str, Any]):
    """A/B 테스트 메트릭 업데이트"""
    # 실제 구현에서는 A/B 테스트 결과 추적
    pass


async def send_alert_notification(event_data: Dict[str, Any]):
    """알림 발송"""
    # 실제 구현에서는 Slack, 이메일 등으로 알림 발송
    pass


async def update_monitoring_dashboard(event_data: Dict[str, Any]):
    """모니터링 대시보드 업데이트"""
    # 실제 구현에서는 Grafana 등 대시보드 업데이트
    pass


async def trigger_model_retraining(event_data: Dict[str, Any]):
    """모델 재훈련 트리거"""
    # 실제 구현에서는 Airflow DAG 트리거
    pass


async def update_model_performance_metrics(event_data: Dict[str, Any]):
    """모델 성능 메트릭 업데이트"""
    # 실제 구현에서는 MLflow 메트릭 업데이트
    pass


async def send_drift_alert(event_data: Dict[str, Any]):
    """드리프트 알림 발송"""
    # 실제 구현에서는 모델 관리자에게 알림
    pass


async def get_event_statistics(start_date: Optional[str], end_date: Optional[str]):
    """이벤트 통계 계산"""
    # 실제 구현에서는 데이터베이스에서 통계 조회
    return {
        "total_events": 1000,
        "user_interactions": 800,
        "system_events": 150,
        "model_drift_events": 5
    }
