"""
Kafka 컨슈머
Kafka 토픽에서 이벤트를 소비하고 처리하는 컨슈머 구현
"""

import asyncio
import json
import logging
import threading
import time
from typing import Dict, Any, Optional, List, Callable, Set
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import traceback

try:
    from kafka import KafkaConsumer
    from kafka.errors import KafkaError
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    logging.warning("Kafka client not available. Install with: pip install kafka-python")

from .event_schemas import BaseEvent, EventFactory, EventType
from ..monitoring.prometheus_metrics import get_metrics

logger = logging.getLogger(__name__)

class EventHandler:
    """이벤트 처리기 기본 클래스"""
    
    def __init__(self, name: str):
        self.name = name
        self.processed_count = 0
        self.error_count = 0
        self.last_error = None
        
    async def handle_event(self, event: BaseEvent) -> bool:
        """
        이벤트 처리 (서브클래스에서 구현)
        
        Args:
            event: 처리할 이벤트
            
        Returns:
            처리 성공 여부
        """
        raise NotImplementedError("Subclasses must implement handle_event method")
    
    def on_success(self, event: BaseEvent):
        """처리 성공 시 호출"""
        self.processed_count += 1
        logger.debug(f"Handler {self.name}: Successfully processed event {event.event_id}")
    
    def on_error(self, event: BaseEvent, error: Exception):
        """처리 실패 시 호출"""
        self.error_count += 1
        self.last_error = str(error)
        logger.error(f"Handler {self.name}: Failed to process event {event.event_id}: {error}")
    
    def get_stats(self) -> Dict[str, Any]:
        """처리 통계 반환"""
        return {
            'name': self.name,
            'processed_count': self.processed_count,
            'error_count': self.error_count,
            'last_error': self.last_error
        }

class UserInteractionHandler(EventHandler):
    """사용자 상호작용 이벤트 처리기"""
    
    def __init__(self):
        super().__init__("UserInteractionHandler")
        self.metrics = get_metrics()
    
    async def handle_event(self, event: BaseEvent) -> bool:
        """사용자 상호작용 이벤트 처리"""
        try:
            if event.event_type != EventType.USER_INTERACTION:
                return True
            
            # 메트릭 기록
            interaction_type = getattr(event, 'interaction_type', 'unknown')
            user_segment = 'default'  # 실제로는 사용자 세그먼트를 계산해야 함
            
            from ..monitoring.custom_metrics import custom_metrics
            custom_metrics['recommendation'].user_interactions_total.labels(
                interaction_type=str(interaction_type),
                user_segment=user_segment
            ).inc()
            
            # 추가 처리 로직
            if hasattr(event, 'rating') and event.rating:
                # 평점 이벤트 처리
                await self._process_rating_event(event)
            elif hasattr(event, 'search_query') and event.search_query:
                # 검색 이벤트 처리
                await self._process_search_event(event)
            
            logger.info(f"Processed user interaction: user_id={getattr(event, 'user_id', 'unknown')}, "
                       f"interaction_type={interaction_type}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing user interaction event: {e}")
            return False
    
    async def _process_rating_event(self, event):
        """평점 이벤트 처리"""
        # 평점 분포 업데이트
        from ..monitoring.custom_metrics import custom_metrics
        custom_metrics['recommendation'].rating_distribution.labels(
            rating=str(getattr(event, 'rating', 0)),
            genre='unknown',
            time_period='current'
        ).set(getattr(event, 'rating', 0))
    
    async def _process_search_event(self, event):
        """검색 이벤트 처리"""
        # 검색 쿼리 분석 및 로깅
        query = getattr(event, 'search_query', '')
        logger.info(f"Search query processed: {query}")

class ModelPredictionHandler(EventHandler):
    """모델 예측 이벤트 처리기"""
    
    def __init__(self):
        super().__init__("ModelPredictionHandler")
        self.metrics = get_metrics()
    
    async def handle_event(self, event: BaseEvent) -> bool:
        """모델 예측 이벤트 처리"""
        try:
            if event.event_type != EventType.MODEL_PREDICTION:
                return True
            
            model_id = getattr(event, 'model_id', 'unknown')
            model_version = getattr(event, 'model_version', 'unknown')
            inference_time = getattr(event, 'inference_time_ms', 0) / 1000.0  # Convert to seconds
            
            # 메트릭 기록
            self.metrics.record_model_prediction(model_id, model_version, inference_time)
            
            # 예측 결과 분석
            predictions = getattr(event, 'predictions', [])
            confidence_scores = getattr(event, 'confidence_scores', [])
            
            if confidence_scores:
                avg_confidence = sum(confidence_scores) / len(confidence_scores)
                logger.info(f"Model prediction: model={model_id}, confidence={avg_confidence:.3f}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing model prediction event: {e}")
            return False

class SystemAlertHandler(EventHandler):
    """시스템 알림 이벤트 처리기"""
    
    def __init__(self):
        super().__init__("SystemAlertHandler")
    
    async def handle_event(self, event: BaseEvent) -> bool:
        """시스템 알림 이벤트 처리"""
        try:
            if event.event_type != EventType.SYSTEM_ALERT:
                return True
            
            service = getattr(event, 'service', 'unknown')
            level = getattr(event, 'level', 'info')
            message = getattr(event, 'message', '')
            
            # 알림 레벨에 따른 처리
            if str(level) == 'critical':
                await self._handle_critical_alert(event)
            elif str(level) == 'error':
                await self._handle_error_alert(event)
            
            logger.info(f"System alert processed: service={service}, level={level}, message={message}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing system alert event: {e}")
            return False
    
    async def _handle_critical_alert(self, event):
        """크리티컬 알림 처리"""
        # 즉시 알림 전송, 에스컬레이션 등
        logger.critical(f"CRITICAL ALERT: {getattr(event, 'message', '')}")
    
    async def _handle_error_alert(self, event):
        """에러 알림 처리"""
        # 에러 로깅, 모니터링 등
        logger.error(f"ERROR ALERT: {getattr(event, 'message', '')}")

class RecommendationHandler(EventHandler):
    """추천 이벤트 처리기"""
    
    def __init__(self):
        super().__init__("RecommendationHandler")
    
    async def handle_event(self, event: BaseEvent) -> bool:
        """추천 이벤트 처리"""
        try:
            if event.event_type != EventType.RECOMMENDATION_EVENT:
                return True
            
            user_id = getattr(event, 'user_id', 0)
            algorithm = getattr(event, 'algorithm', 'unknown')
            recommendations = getattr(event, 'recommendations', [])
            response_time = getattr(event, 'response_time_ms', 0)
            
            # 추천 품질 메트릭 업데이트
            from ..monitoring.custom_metrics import custom_metrics
            custom_metrics['recommendation'].recommendation_requests_total.labels(
                algorithm=algorithm,
                user_segment='default',
                request_type='standard'
            ).inc()
            
            if response_time > 0:
                custom_metrics['recommendation'].recommendation_latency_seconds.labels(
                    algorithm=algorithm,
                    user_segment='default',
                    cache_status='miss'
                ).observe(response_time / 1000.0)
            
            logger.info(f"Recommendation processed: user_id={user_id}, algorithm={algorithm}, "
                       f"count={len(recommendations)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing recommendation event: {e}")
            return False

class KafkaEventConsumer:
    """Kafka 이벤트 컨슈머"""
    
    def __init__(self, bootstrap_servers: str = 'kafka:9092',
                 group_id: str = 'movie-mlops-consumer',
                 **kafka_config):
        """
        Kafka 컨슈머 초기화
        
        Args:
            bootstrap_servers: Kafka 브로커 주소
            group_id: 컨슈머 그룹 ID
            **kafka_config: 추가 Kafka 설정
        """
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.kafka_config = kafka_config
        self.consumer = None
        self.is_running = False
        self.is_connected = False
        
        # 토픽 설정
        self.topics = [
            'movie-user-interactions',
            'movie-model-predictions', 
            'movie-system-alerts',
            'movie-training-events',
            'movie-recommendations',
            'movie-data-quality',
            'movie-pipeline-events'
        ]
        
        # 이벤트 핸들러
        self.handlers: Dict[EventType, List[EventHandler]] = {
            EventType.USER_INTERACTION: [UserInteractionHandler()],
            EventType.MODEL_PREDICTION: [ModelPredictionHandler()],
            EventType.SYSTEM_ALERT: [SystemAlertHandler()],
            EventType.RECOMMENDATION_EVENT: [RecommendationHandler()],
        }
        
        # 통계
        self.stats = {
            'total_consumed': 0,
            'total_processed': 0,
            'total_errors': 0,
            'messages_by_topic': {},
            'last_error': None,
            'start_time': None
        }
        
        # 스레드 풀
        self.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="event-handler")
    
    def connect(self) -> bool:
        """Kafka에 연결"""
        if not KAFKA_AVAILABLE:
            logger.error("Kafka client is not available")
            return False
        
        try:
            # 기본 Kafka 설정
            config = {
                'bootstrap_servers': self.bootstrap_servers,
                'group_id': self.group_id,
                'value_deserializer': lambda m: json.loads(m.decode('utf-8')),
                'key_deserializer': lambda k: k.decode('utf-8') if k else None,
                'auto_offset_reset': 'earliest',
                'enable_auto_commit': True,
                'auto_commit_interval_ms': 1000,
                'session_timeout_ms': 30000,
                'max_poll_records': 100,
                **self.kafka_config
            }
            
            self.consumer = KafkaConsumer(*self.topics, **config)
            self.is_connected = True
            logger.info(f"Connected to Kafka as consumer group: {self.group_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self):
        """Kafka 연결 해제"""
        if self.consumer:
            try:
                self.consumer.close()
                self.is_connected = False
                logger.info("Disconnected from Kafka")
            except Exception as e:
                logger.error(f"Error disconnecting from Kafka: {e}")
    
    def add_handler(self, event_type: EventType, handler: EventHandler):
        """이벤트 핸들러 추가"""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
        logger.info(f"Added handler {handler.name} for event type {event_type.value}")
    
    def remove_handler(self, event_type: EventType, handler: EventHandler):
        """이벤트 핸들러 제거"""
        if event_type in self.handlers and handler in self.handlers[event_type]:
            self.handlers[event_type].remove(handler)
            logger.info(f"Removed handler {handler.name} for event type {event_type.value}")
    
    async def process_event(self, event_data: Dict[str, Any], topic: str):
        """단일 이벤트 처리"""
        try:
            # 이벤트 객체 생성
            event = EventFactory.from_dict(event_data)
            
            # 해당 이벤트 타입의 핸들러들 실행
            handlers = self.handlers.get(event.event_type, [])
            
            if not handlers:
                logger.warning(f"No handlers found for event type: {event.event_type.value}")
                return
            
            # 병렬로 핸들러 실행
            tasks = []
            for handler in handlers:
                task = asyncio.create_task(self._handle_with_stats(handler, event))
                tasks.append(task)
            
            # 모든 핸들러 완료 대기
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 결과 확인
            success_count = sum(1 for result in results if result is True)
            error_count = len(results) - success_count
            
            if error_count > 0:
                logger.warning(f"Event {event.event_id}: {success_count} handlers succeeded, {error_count} failed")
            
            self.stats['total_processed'] += 1
            
        except Exception as e:
            logger.error(f"Error processing event from topic {topic}: {e}")
            self.stats['total_errors'] += 1
            self.stats['last_error'] = str(e)
    
    async def _handle_with_stats(self, handler: EventHandler, event: BaseEvent) -> bool:
        """핸들러 실행 및 통계 업데이트"""
        try:
            result = await handler.handle_event(event)
            if result:
                handler.on_success(event)
            return result
        except Exception as e:
            handler.on_error(event, e)
            return False
    
    def start_consuming(self):
        """이벤트 소비 시작"""
        if not self.is_connected:
            if not self.connect():
                return
        
        self.is_running = True
        self.stats['start_time'] = datetime.utcnow()
        
        logger.info("Starting event consumption...")
        
        try:
            # 메인 소비 루프
            for message in self.consumer:
                if not self.is_running:
                    break
                
                try:
                    # 통계 업데이트
                    self.stats['total_consumed'] += 1
                    topic = message.topic
                    if topic not in self.stats['messages_by_topic']:
                        self.stats['messages_by_topic'][topic] = 0
                    self.stats['messages_by_topic'][topic] += 1
                    
                    # 이벤트 처리 (비동기)
                    asyncio.run(self.process_event(message.value, topic))
                    
                except Exception as e:
                    logger.error(f"Error processing message from {message.topic}: {e}")
                    self.stats['total_errors'] += 1
                    self.stats['last_error'] = str(e)
        
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, stopping consumer...")
        except Exception as e:
            logger.error(f"Consumer error: {e}")
        finally:
            self.stop_consuming()
    
    def stop_consuming(self):
        """이벤트 소비 중지"""
        self.is_running = False
        logger.info("Stopped event consumption")
    
    def start_consuming_async(self):
        """비동기적으로 이벤트 소비 시작"""
        if not self.is_connected:
            if not self.connect():
                return
        
        def consume_loop():
            self.start_consuming()
        
        # 별도 스레드에서 소비 시작
        consume_thread = threading.Thread(target=consume_loop, daemon=True)
        consume_thread.start()
        logger.info("Started async event consumption")
    
    def get_stats(self) -> Dict[str, Any]:
        """소비 통계 반환"""
        runtime = None
        if self.stats['start_time']:
            runtime = (datetime.utcnow() - self.stats['start_time']).total_seconds()
        
        handler_stats = {}
        for event_type, handlers in self.handlers.items():
            handler_stats[event_type.value] = [h.get_stats() for h in handlers]
        
        return {
            **self.stats,
            'runtime_seconds': runtime,
            'is_running': self.is_running,
            'is_connected': self.is_connected,
            'handler_stats': handler_stats
        }
    
    def __enter__(self):
        """컨텍스트 매니저 진입"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료"""
        self.stop_consuming()
        self.disconnect()
        self.executor.shutdown(wait=True)

class MockKafkaConsumer:
    """테스트용 모킹 컨슈머"""
    
    def __init__(self, **kwargs):
        self.is_connected = True
        self.is_running = False
        self.handlers = {}
        self.processed_events = []
        self.stats = {
            'total_consumed': 0,
            'total_processed': 0,
            'total_errors': 0
        }
    
    def connect(self) -> bool:
        logger.info("Mock Kafka consumer connected")
        return True
    
    def disconnect(self):
        logger.info("Mock Kafka consumer disconnected")
    
    def add_handler(self, event_type: EventType, handler: EventHandler):
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
    
    def start_consuming(self):
        self.is_running = True
        logger.info("Mock consumer started")
    
    def stop_consuming(self):
        self.is_running = False
        logger.info("Mock consumer stopped")
    
    def simulate_event(self, event: BaseEvent):
        """테스트용 이벤트 시뮬레이션"""
        self.processed_events.append(event)
        self.stats['total_consumed'] += 1
        self.stats['total_processed'] += 1
        logger.info(f"Mock: Processed event {event.event_id}")
    
    def get_stats(self) -> Dict[str, Any]:
        return self.stats

# 글로벌 컨슈머 인스턴스
_global_consumer: Optional[KafkaEventConsumer] = None

def get_event_consumer() -> KafkaEventConsumer:
    """글로벌 이벤트 컨슈머 반환"""
    global _global_consumer
    if _global_consumer is None:
        # 환경에 따라 Mock 또는 실제 컨슈머 사용
        import os
        if os.getenv('KAFKA_MOCK', 'false').lower() == 'true':
            _global_consumer = MockKafkaConsumer()
        else:
            _global_consumer = KafkaEventConsumer()
    return _global_consumer
