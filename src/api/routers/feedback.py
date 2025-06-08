"""사용자 피드백 API 라우터"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["feedback"])


class FeedbackRequest(BaseModel):
    """사용자 피드백 요청 모델"""
    user_id: str
    movie_id: int
    interaction_type: str  # "like", "dislike", "view", "click", "rating"
    rating: Optional[float] = None
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class FeedbackResponse(BaseModel):
    """피드백 응답 모델"""
    feedback_id: str
    status: str
    message: str
    timestamp: str


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(feedback: FeedbackRequest):
    """사용자 피드백 수집"""
    try:
        # 피드백 ID 생성
        feedback_id = f"fb_{feedback.user_id}_{feedback.movie_id}_{int(datetime.now().timestamp())}"
        
        # 피드백 데이터 구성
        feedback_data = {
            "feedback_id": feedback_id,
            "user_id": feedback.user_id,
            "movie_id": feedback.movie_id,
            "interaction_type": feedback.interaction_type,
            "rating": feedback.rating,
            "session_id": feedback.session_id,
            "metadata": feedback.metadata or {},
            "timestamp": datetime.now().isoformat(),
            "processed": False
        }
        
        # 피드백 저장 (실제로는 데이터베이스나 Kafka로 전송)
        await save_feedback_to_storage(feedback_data)
        
        # 실시간 모델 업데이트 트리거 (선택사항)
        await trigger_model_update_if_needed(feedback_data)
        
        logger.info(f"피드백 수집 완료: {feedback_id}")
        
        return FeedbackResponse(
            feedback_id=feedback_id,
            status="success", 
            message="피드백이 성공적으로 수집되었습니다",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"피드백 수집 실패: {e}")
        raise HTTPException(status_code=500, detail=f"피드백 수집 실패: {str(e)}")


@router.get("/feedback/{user_id}")
async def get_user_feedback(user_id: str, limit: int = 100):
    """사용자의 피드백 히스토리 조회"""
    try:
        feedback_history = await get_feedback_from_storage(user_id, limit)
        
        return {
            "user_id": user_id,
            "feedback_count": len(feedback_history),
            "feedback_history": feedback_history
        }
        
    except Exception as e:
        logger.error(f"피드백 히스토리 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"피드백 조회 실패: {str(e)}")


async def save_feedback_to_storage(feedback_data: Dict[str, Any]):
    """피드백을 저장소에 저장"""
    try:
        # 방법 1: 파일 시스템에 저장 (개발용)
        import os
        feedback_dir = "data/feedback"
        os.makedirs(feedback_dir, exist_ok=True)
        
        filename = f"{feedback_dir}/feedback_{datetime.now().strftime('%Y%m%d')}.jsonl"
        with open(filename, "a", encoding="utf-8") as f:
            f.write(json.dumps(feedback_data, ensure_ascii=False) + "\n")
        
        # 방법 2: Kafka에 전송 (프로덕션용)
        try:
            from src.events.kafka_producer import MovieEventProducer
            producer = MovieEventProducer()
            await producer.send_user_feedback(feedback_data)
        except ImportError:
            logger.warning("Kafka 프로듀서를 사용할 수 없습니다. 파일로만 저장됩니다.")
            
    except Exception as e:
        logger.error(f"피드백 저장 실패: {e}")
        raise


async def get_feedback_from_storage(user_id: str, limit: int):
    """저장소에서 피드백 조회"""
    try:
        feedback_history = []
        
        # 방법 1: 파일에서 읽기 (개발용)
        import os
        import glob
        
        feedback_files = glob.glob("data/feedback/feedback_*.jsonl")
        
        for file_path in sorted(feedback_files, reverse=True):
            if len(feedback_history) >= limit:
                break
                
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    if len(feedback_history) >= limit:
                        break
                        
                    try:
                        feedback = json.loads(line.strip())
                        if feedback.get("user_id") == user_id:
                            feedback_history.append(feedback)
                    except json.JSONDecodeError:
                        continue
        
        return feedback_history[:limit]
        
    except Exception as e:
        logger.error(f"피드백 조회 실패: {e}")
        return []


async def trigger_model_update_if_needed(feedback_data: Dict[str, Any]):
    """필요시 모델 업데이트 트리거"""
    try:
        # 특정 조건에서만 모델 업데이트 (예: 평점 피드백)
        if feedback_data.get("interaction_type") == "rating":
            logger.info(f"평점 피드백으로 인한 모델 업데이트 트리거: {feedback_data['feedback_id']}")
            
            # 실제로는 비동기 작업 큐에 추가
            # await queue_model_retraining_task(feedback_data)
            
    except Exception as e:
        logger.warning(f"모델 업데이트 트리거 실패: {e}")
