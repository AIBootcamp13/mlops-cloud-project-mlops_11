"""
Kafka 프로듀서
이벤트를 Kafka 토픽으로 전송하는 프로듀서 구현
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import traceback

try:
    from kafka import KafkaProducer
    from kafka.errors import KafkaError
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    logging.warning("Kafka client not available. Install with: pip install kafka-python")

from .event_schemas import BaseEvent, EventFactory, EventValidator

logger = logging.getLogger(__name__)

class KafkaEventProducer:
    """Kafka 이벤트 프로듀서"""
    
    def __init__(self, bootstrap_servers: str = 'kafka:9092', 
                 client_id: str = 'movie-mlops-producer',
                 **kafka_config):
        """
        Kafka 프로듀서 초기화
        
        Args:
            bootstrap_servers: Kafka 브로커 주소
            client_id: 클라이언트 ID
            **kafka_config: 추가 Kafka 설정
        """
        self.bootstrap_servers = bootstrap_servers
        self.client_id = client_id
        self.kafka_config = kafka_config
        self.producer = None
        self.is_connected = False
        
        # 기본 토픽 설정
        self.topics = {
            'user_interactions': 'movie-user-interactions',
            'model_predictions': 'movie-model-predictions',
            'system_alerts': 'movie-system-alerts',
            'training_events': 'movie-training-events',
            'recommendation_events': 'movie-recommendations',
            'data_quality': 'movie-data-quality',
            'pipeline_events': 'movie-pipeline-events'
        }
        
        # 이벤트 전송 통계
        self.stats = {
            'total_sent': 0,
            'total_errors': 0,
            'last_error': None,
            'events_by_topic': {}
        }
        
        # 콜백 함수들
        self.on_success_callbacks: List[Callable] = []
        self.on_error_callbacks: List[Callable] = []
    
    def connect(self) -> bool:
        """Kafka에 연결"""
        if not KAFKA_AVAILABLE:
            logger.error("Kafka client is not available")
            return False
        
        try:
            # 기본 Kafka 설정
            config = {
                'bootstrap_servers': self.bootstrap_servers,
                'client_id': self.client_id,
                'value_serializer': lambda v: json.dumps(v, default=str).encode('utf-8'),
                'key_serializer': lambda k: k.encode('utf-8') if k else None,
                'acks': 'all',  # 모든 복제본에서 확인
                'retries': 3,
                'retry_backoff_ms': 100,
                'max_in_flight_requests_per_connection': 1,
                'compression_type': 'gzip',
                **self.kafka_config
            }
            
            self.producer = KafkaProducer(**config)
            self.is_connected = True
            logger.info(f"Connected to Kafka: {self.bootstrap_servers}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self):
        """Kafka 연결 해제"""
        if self.producer:
            try:
                self.producer.flush()
                self.producer.close()
                self.is_connected = False
                logger.info("Disconnected from Kafka")
            except Exception as e:
                logger.error(f"Error disconnecting from Kafka: {e}")
    
    def add_success_callback(self, callback: Callable):
        """성공 콜백 추가"""
        self.on_success_callbacks.append(callback)
    
    def add_error_callback(self, callback: Callable):
        """에러 콜백 추가"""
        self.on_error_callbacks.append(callback)
    
    def _on_send_success(self, record_metadata):
        """전송 성공 콜백"""
        self.stats['total_sent'] += 1
        topic = record_metadata.topic
        if topic not in self.stats['events_by_topic']:
            self.stats['events_by_topic'][topic] = 0
        self.stats['events_by_topic'][topic] += 1
        
        logger.debug(f"Event sent successfully to {topic} partition {record_metadata.partition} offset {record_metadata.offset}")
        
        # 사용자 정의 성공 콜백 실행
        for callback in self.on_success_callbacks:
            try:
                callback(record_metadata)
            except Exception as e:
                logger.error(f"Error in success callback: {e}")
    
    def _on_send_error(self, exception):
        """전송 실패 콜백"""
        self.stats['total_errors'] += 1
        self.stats['last_error'] = str(exception)
        logger.error(f"Failed to send event: {exception}")
        
        # 사용자 정의 에러 콜백 실행
        for callback in self.on_error_callbacks:
            try:
                callback(exception)
            except Exception as e:
                logger.error(f"Error in error callback: {e}")
    
    def send_event(self, event: BaseEvent, topic: Optional[str] = None, 
                   key: Optional[str] = None, partition: Optional[int] = None,
                   validate: bool = True) -> bool:
        """
        이벤트를 Kafka로 전송
        
        Args:
            event: 전송할 이벤트
            topic: 대상 토픽 (None이면 자동 선택)
            key: 파티션 키
            partition: 특정 파티션 지정
            validate: 이벤트 검증 여부
        
        Returns:
            전송 성공 여부
        """
        if not self.is_connected:
            if not self.connect():
                return False
        
        # 이벤트 검증
        if validate:
            errors = EventValidator.validate_event(event)
            if errors:
                logger.error(f"Event validation failed: {errors}")
                return False
        
        # 토픽 결정
        if topic is None:
            topic = self._get_topic_for_event(event)
        
        # 키 생성 (파티셔닝을 위해)
        if key is None:
            key = self._generate_key(event)
        
        try:
            # 이벤트를 딕셔너리로 변환
            event_data = event.to_dict()
            
            # Kafka로 전송
            future = self.producer.send(
                topic=topic,
                value=event_data,
                key=key,
                partition=partition
            )
            
            # 콜백 등록
            future.add_callback(self._on_send_success)
            future.add_errback(self._on_send_error)
            
            logger.debug(f"Event queued for sending to topic {topic}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending event: {e}")
            self._on_send_error(e)
            return False
    
    def send_events_batch(self, events: List[BaseEvent], topic: Optional[str] = None,
                         validate: bool = True) -> int:
        """
        여러 이벤트를 배치로 전송
        
        Args:
            events: 전송할 이벤트 리스트
            topic: 대상 토픽
            validate: 이벤트 검증 여부
        
        Returns:
            성공적으로 전송된 이벤트 수
        """
        if not events:
            return 0
        
        success_count = 0
        for event in events:
            if self.send_event(event, topic=topic, validate=validate):
                success_count += 1
        
        # 전송 완료 대기
        self.flush()
        
        logger.info(f"Batch send completed: {success_count}/{len(events)} events sent successfully")
        return success_count
    
    def flush(self, timeout: Optional[float] = None):
        """대기 중인 모든 메시지 전송 완료 대기"""
        if self.producer:
            try:
                self.producer.flush(timeout=timeout)
            except Exception as e:
                logger.error(f"Error flushing producer: {e}")
    
    def _get_topic_for_event(self, event: BaseEvent) -> str:
        """이벤트 타입에 따른 토픽 결정"""
        event_type = event.event_type.value
        
        topic_mapping = {
            'user_interaction': self.topics['user_interactions'],
            'model_prediction': self.topics['model_predictions'],
            'system_alert': self.topics['system_alerts'],
            'training_event': self.topics['training_events'],
            'recommendation_event': self.topics['recommendation_events'],
            'data_quality_event': self.topics['data_quality'],
            'pipeline_event': self.topics['pipeline_events']
        }
        
        return topic_mapping.get(event_type, 'movie-default')
    
    def _generate_key(self, event: BaseEvent) -> str:
        """이벤트에 대한 파티션 키 생성"""
        # 이벤트 타입에 따라 다른 키 생성 전략 사용
        if hasattr(event, 'user_id') and event.user_id:
            return f"user_{event.user_id}"
        elif hasattr(event, 'model_id') and event.model_id:
            return f"model_{event.model_id}"
        elif hasattr(event, 'service') and event.service:
            return f"service_{event.service}"
        else:
            return f"event_{event.event_type.value}"
    
    def get_stats(self) -> Dict[str, Any]:
        """전송 통계 반환"""
        return {
            **self.stats,
            'is_connected': self.is_connected,
            'topics': self.topics
        }
    
    def __enter__(self):
        """컨텍스트 매니저 진입"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료"""
        self.disconnect()


class AsyncKafkaEventProducer:
    """비동기 Kafka 이벤트 프로듀서"""
    
    def __init__(self, bootstrap_servers: str = 'kafka:9092',
                 client_id: str = 'movie-mlops-async-producer',
                 **kafka_config):
        """
        비동기 Kafka 프로듀서 초기화
        """
        self.sync_producer = KafkaEventProducer(
            bootstrap_servers=bootstrap_servers,
            client_id=client_id,
            **kafka_config
        )
        self.loop = None
        self.executor = None
    
    async def connect(self) -> bool:
        """비동기적으로 Kafka에 연결"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.sync_producer.connect)
    
    async def send_event(self, event: BaseEvent, **kwargs) -> bool:
        """비동기적으로 이벤트 전송"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.sync_producer.send_event, event, **kwargs)
    
    async def send_events_batch(self, events: List[BaseEvent], **kwargs) -> int:
        """비동기적으로 배치 이벤트 전송"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.sync_producer.send_events_batch, events, **kwargs)
    
    async def disconnect(self):
        """비동기적으로 연결 해제"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.sync_producer.disconnect)


class MockKafkaProducer:
    """테스트용 모킹 프로듀서"""
    
    def __init__(self, **kwargs):
        self.events = []
        self.is_connected = True
        self.stats = {
            'total_sent': 0,
            'total_errors': 0,
            'events_by_topic': {}
        }
    
    def connect(self) -> bool:
        logger.info("Mock Kafka producer connected")
        return True
    
    def disconnect(self):
        logger.info("Mock Kafka producer disconnected")
    
    def send_event(self, event: BaseEvent, topic: Optional[str] = None, **kwargs) -> bool:
        self.events.append({
            'event': event,
            'topic': topic or 'default',
            'timestamp': datetime.utcnow()
        })
        self.stats['total_sent'] += 1
        logger.info(f"Mock: Event sent to topic {topic}")
        return True
    
    def send_events_batch(self, events: List[BaseEvent], **kwargs) -> int:
        for event in events:
            self.send_event(event, **kwargs)
        return len(events)
    
    def flush(self, timeout: Optional[float] = None):
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        return self.stats
    
    def clear_events(self):
        """저장된 이벤트 초기화"""
        self.events.clear()


# 글로벌 프로듀서 인스턴스
_global_producer: Optional[KafkaEventProducer] = None

def get_event_producer() -> KafkaEventProducer:
    """글로벌 이벤트 프로듀서 반환"""
    global _global_producer
    if _global_producer is None:
        # 환경에 따라 Mock 또는 실제 프로듀서 사용
        import os
        if os.getenv('KAFKA_MOCK', 'false').lower() == 'true':
            _global_producer = MockKafkaProducer()
        else:
            _global_producer = KafkaEventProducer()
    return _global_producer

def send_event(event: BaseEvent, **kwargs) -> bool:
    """편의 함수: 이벤트 전송"""
    producer = get_event_producer()
    return producer.send_event(event, **kwargs)

def send_events_batch(events: List[BaseEvent], **kwargs) -> int:
    """편의 함수: 배치 이벤트 전송"""
    producer = get_event_producer()
    return producer.send_events_batch(events, **kwargs)
