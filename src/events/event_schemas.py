"""
이벤트 스키마 정의
Kafka로 전송되는 이벤트들의 구조와 검증 로직
"""

from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import json
import uuid
import logging

logger = logging.getLogger(__name__)

class EventType(Enum):
    """이벤트 타입 정의"""
    USER_INTERACTION = "user_interaction"
    MODEL_PREDICTION = "model_prediction"
    SYSTEM_ALERT = "system_alert"
    TRAINING_EVENT = "training_event"
    RECOMMENDATION_EVENT = "recommendation_event"
    DATA_QUALITY_EVENT = "data_quality_event"
    PIPELINE_EVENT = "pipeline_event"

class InteractionType(Enum):
    """사용자 상호작용 타입"""
    VIEW = "view"
    CLICK = "click"
    RATING = "rating"
    SHARE = "share"
    WATCHLIST_ADD = "watchlist_add"
    WATCHLIST_REMOVE = "watchlist_remove"
    SEARCH = "search"
    FILTER = "filter"

class AlertLevel(Enum):
    """알림 레벨"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class BaseEvent:
    """기본 이벤트 클래스"""
    event_id: str
    event_type: EventType
    timestamp: datetime
    source: str
    version: str = "1.0"
    
    def __post_init__(self):
        if isinstance(self.event_type, str):
            self.event_type = EventType(self.event_type)
        if isinstance(self.timestamp, str):
            self.timestamp = datetime.fromisoformat(self.timestamp.replace('Z', '+00:00'))

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        data = asdict(self)
        data['event_type'] = self.event_type.value
        data['timestamp'] = self.timestamp.isoformat()
        return data

    def to_json(self) -> str:
        """JSON 문자열로 변환"""
        return json.dumps(self.to_dict(), default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseEvent':
        """딕셔너리에서 생성"""
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> 'BaseEvent':
        """JSON 문자열에서 생성"""
        return cls.from_dict(json.loads(json_str))

@dataclass
class UserInteractionEvent(BaseEvent):
    """사용자 상호작용 이벤트"""
    user_id: int
    content_id: Optional[int] = None
    interaction_type: InteractionType = InteractionType.VIEW
    session_id: Optional[str] = None
    rating: Optional[float] = None
    search_query: Optional[str] = None
    device_type: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    referrer: Optional[str] = None
    page_url: Optional[str] = None
    duration_seconds: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        super().__post_init__()
        if isinstance(self.interaction_type, str):
            self.interaction_type = InteractionType(self.interaction_type)
        if not self.event_id:
            self.event_id = str(uuid.uuid4())
        self.event_type = EventType.USER_INTERACTION
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data['interaction_type'] = self.interaction_type.value
        return data

@dataclass
class ModelPredictionEvent(BaseEvent):
    """모델 예측 이벤트"""
    model_id: str
    model_version: str
    user_id: Optional[int] = None
    input_features: Optional[Dict[str, Any]] = None
    predictions: Optional[List[Dict[str, Any]]] = None
    confidence_scores: Optional[List[float]] = None
    inference_time_ms: Optional[float] = None
    model_metadata: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None
    ab_test_group: Optional[str] = None
    
    def __post_init__(self):
        super().__post_init__()
        if not self.event_id:
            self.event_id = str(uuid.uuid4())
        self.event_type = EventType.MODEL_PREDICTION

@dataclass
class SystemAlertEvent(BaseEvent):
    """시스템 알림 이벤트"""
    service: str
    level: AlertLevel
    message: str
    alert_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    resolved: bool = False
    resolution_time: Optional[datetime] = None
    tags: Optional[List[str]] = None
    
    def __post_init__(self):
        super().__post_init__()
        if isinstance(self.level, str):
            self.level = AlertLevel(self.level)
        if not self.event_id:
            self.event_id = str(uuid.uuid4())
        self.event_type = EventType.SYSTEM_ALERT
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data['level'] = self.level.value
        if self.resolution_time:
            data['resolution_time'] = self.resolution_time.isoformat()
        return data

@dataclass
class TrainingEvent(BaseEvent):
    """모델 훈련 이벤트"""
    experiment_id: str
    run_id: str
    model_name: str
    status: str  # started, completed, failed
    epoch: Optional[int] = None
    loss: Optional[float] = None
    metrics: Optional[Dict[str, float]] = None
    hyperparameters: Optional[Dict[str, Any]] = None
    dataset_info: Optional[Dict[str, Any]] = None
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        super().__post_init__()
        if not self.event_id:
            self.event_id = str(uuid.uuid4())
        self.event_type = EventType.TRAINING_EVENT

@dataclass
class RecommendationEvent(BaseEvent):
    """추천 이벤트"""
    user_id: int
    algorithm: str
    recommendations: List[Dict[str, Any]]
    request_context: Optional[Dict[str, Any]] = None
    response_time_ms: Optional[float] = None
    cache_hit: bool = False
    diversity_score: Optional[float] = None
    novelty_score: Optional[float] = None
    coverage_score: Optional[float] = None
    ab_test_variant: Optional[str] = None
    
    def __post_init__(self):
        super().__post_init__()
        if not self.event_id:
            self.event_id = str(uuid.uuid4())
        self.event_type = EventType.RECOMMENDATION_EVENT

@dataclass
class DataQualityEvent(BaseEvent):
    """데이터 품질 이벤트"""
    dataset_name: str
    check_type: str  # completeness, consistency, validity, accuracy
    status: str  # passed, failed, warning
    score: Optional[float] = None
    threshold: Optional[float] = None
    affected_rows: Optional[int] = None
    total_rows: Optional[int] = None
    details: Optional[Dict[str, Any]] = None
    remediation_suggested: Optional[str] = None
    
    def __post_init__(self):
        super().__post_init__()
        if not self.event_id:
            self.event_id = str(uuid.uuid4())
        self.event_type = EventType.DATA_QUALITY_EVENT

@dataclass
class PipelineEvent(BaseEvent):
    """파이프라인 이벤트"""
    pipeline_name: str
    stage: str
    status: str  # started, completed, failed, skipped
    dag_id: Optional[str] = None
    task_id: Optional[str] = None
    execution_date: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    
    def __post_init__(self):
        super().__post_init__()
        if not self.event_id:
            self.event_id = str(uuid.uuid4())
        self.event_type = EventType.PIPELINE_EVENT
        if isinstance(self.execution_date, str):
            self.execution_date = datetime.fromisoformat(self.execution_date.replace('Z', '+00:00'))
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        if self.execution_date:
            data['execution_date'] = self.execution_date.isoformat()
        return data


class EventFactory:
    """이벤트 팩토리 클래스"""
    
    EVENT_CLASSES = {
        EventType.USER_INTERACTION: UserInteractionEvent,
        EventType.MODEL_PREDICTION: ModelPredictionEvent,
        EventType.SYSTEM_ALERT: SystemAlertEvent,
        EventType.TRAINING_EVENT: TrainingEvent,
        EventType.RECOMMENDATION_EVENT: RecommendationEvent,
        EventType.DATA_QUALITY_EVENT: DataQualityEvent,
        EventType.PIPELINE_EVENT: PipelineEvent,
    }
    
    @classmethod
    def create_event(cls, event_type: Union[EventType, str], **kwargs) -> BaseEvent:
        """이벤트 타입에 따라 적절한 이벤트 객체 생성"""
        if isinstance(event_type, str):
            event_type = EventType(event_type)
        
        event_class = cls.EVENT_CLASSES.get(event_type, BaseEvent)
        
        # 기본값 설정
        if 'event_id' not in kwargs:
            kwargs['event_id'] = str(uuid.uuid4())
        if 'timestamp' not in kwargs:
            kwargs['timestamp'] = datetime.utcnow()
        if 'source' not in kwargs:
            kwargs['source'] = 'movie-mlops'
        
        kwargs['event_type'] = event_type
        
        return event_class(**kwargs)
    
    @classmethod
    def create_user_interaction(cls, user_id: int, interaction_type: InteractionType,
                              content_id: Optional[int] = None, **kwargs) -> UserInteractionEvent:
        """사용자 상호작용 이벤트 생성"""
        return cls.create_event(
            EventType.USER_INTERACTION,
            user_id=user_id,
            interaction_type=interaction_type,
            content_id=content_id,
            **kwargs
        )
    
    @classmethod
    def create_model_prediction(cls, model_id: str, model_version: str,
                              predictions: List[Dict[str, Any]], **kwargs) -> ModelPredictionEvent:
        """모델 예측 이벤트 생성"""
        return cls.create_event(
            EventType.MODEL_PREDICTION,
            model_id=model_id,
            model_version=model_version,
            predictions=predictions,
            **kwargs
        )
    
    @classmethod
    def create_system_alert(cls, service: str, level: AlertLevel, message: str, **kwargs) -> SystemAlertEvent:
        """시스템 알림 이벤트 생성"""
        return cls.create_event(
            EventType.SYSTEM_ALERT,
            service=service,
            level=level,
            message=message,
            **kwargs
        )
    
    @classmethod
    def create_training_event(cls, experiment_id: str, run_id: str, model_name: str,
                            status: str, **kwargs) -> TrainingEvent:
        """훈련 이벤트 생성"""
        return cls.create_event(
            EventType.TRAINING_EVENT,
            experiment_id=experiment_id,
            run_id=run_id,
            model_name=model_name,
            status=status,
            **kwargs
        )
    
    @classmethod
    def create_recommendation_event(cls, user_id: int, algorithm: str,
                                  recommendations: List[Dict[str, Any]], **kwargs) -> RecommendationEvent:
        """추천 이벤트 생성"""
        return cls.create_event(
            EventType.RECOMMENDATION_EVENT,
            user_id=user_id,
            algorithm=algorithm,
            recommendations=recommendations,
            **kwargs
        )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BaseEvent:
        """딕셔너리에서 이벤트 생성"""
        event_type = EventType(data.get('event_type'))
        event_class = cls.EVENT_CLASSES.get(event_type, BaseEvent)
        return event_class.from_dict(data)
    
    @classmethod
    def from_json(cls, json_str: str) -> BaseEvent:
        """JSON 문자열에서 이벤트 생성"""
        data = json.loads(json_str)
        return cls.from_dict(data)


class EventValidator:
    """이벤트 검증기"""
    
    @staticmethod
    def validate_event(event: BaseEvent) -> List[str]:
        """이벤트 유효성 검증"""
        errors = []
        
        # 기본 필드 검증
        if not event.event_id:
            errors.append("event_id is required")
        if not event.timestamp:
            errors.append("timestamp is required")
        if not event.source:
            errors.append("source is required")
        
        # 이벤트 타입별 검증
        if isinstance(event, UserInteractionEvent):
            if not event.user_id:
                errors.append("user_id is required for user interaction events")
            if event.interaction_type == InteractionType.RATING and not event.rating:
                errors.append("rating is required for rating interaction events")
        
        elif isinstance(event, ModelPredictionEvent):
            if not event.model_id:
                errors.append("model_id is required for model prediction events")
            if not event.model_version:
                errors.append("model_version is required for model prediction events")
        
        elif isinstance(event, SystemAlertEvent):
            if not event.service:
                errors.append("service is required for system alert events")
            if not event.message:
                errors.append("message is required for system alert events")
        
        return errors
    
    @staticmethod
    def is_valid(event: BaseEvent) -> bool:
        """이벤트가 유효한지 확인"""
        return len(EventValidator.validate_event(event)) == 0


# 편의 함수들
def create_user_view_event(user_id: int, content_id: int, **kwargs) -> UserInteractionEvent:
    """사용자 조회 이벤트 생성 편의 함수"""
    return EventFactory.create_user_interaction(
        user_id=user_id,
        interaction_type=InteractionType.VIEW,
        content_id=content_id,
        **kwargs
    )

def create_user_rating_event(user_id: int, content_id: int, rating: float, **kwargs) -> UserInteractionEvent:
    """사용자 평점 이벤트 생성 편의 함수"""
    return EventFactory.create_user_interaction(
        user_id=user_id,
        interaction_type=InteractionType.RATING,
        content_id=content_id,
        rating=rating,
        **kwargs
    )

def create_recommendation_request_event(user_id: int, algorithm: str, 
                                      recommendations: List[Dict[str, Any]], **kwargs) -> RecommendationEvent:
    """추천 요청 이벤트 생성 편의 함수"""
    return EventFactory.create_recommendation_event(
        user_id=user_id,
        algorithm=algorithm,
        recommendations=recommendations,
        **kwargs
    )
