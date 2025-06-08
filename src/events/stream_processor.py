"""
스트림 처리기
실시간 이벤트 스트림 처리 및 집계
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Callable, DefaultDict
from datetime import datetime, timedelta
from collections import defaultdict, deque
import time
import threading
from dataclasses import dataclass

from .event_schemas import BaseEvent, EventType, UserInteractionEvent, ModelPredictionEvent
from .kafka_consumer import EventHandler
from ..monitoring.custom_metrics import custom_metrics

logger = logging.getLogger(__name__)

@dataclass
class StreamWindow:
    """스트림 윈도우 데이터 구조"""
    window_start: datetime
    window_end: datetime
    events: List[BaseEvent]
    aggregations: Dict[str, Any]

class StreamProcessor:
    """실시간 스트림 처리기"""
    
    def __init__(self, window_size_seconds: int = 60):
        """
        스트림 처리기 초기화
        
        Args:
            window_size_seconds: 윈도우 크기 (초)
        """
        self.window_size = timedelta(seconds=window_size_seconds)
        self.windows: Dict[str, StreamWindow] = {}
        self.processors: Dict[str, Callable] = {}
        self.lock = threading.Lock()
        
        # 기본 처리기 등록
        self._register_default_processors()
    
    def _register_default_processors(self):
        """기본 스트림 처리기 등록"""
        self.processors.update({
            'user_activity_rate': self._process_user_activity_rate,
            'recommendation_performance': self._process_recommendation_performance,
            'model_prediction_rate': self._process_model_prediction_rate,
            'system_health': self._process_system_health,
            'content_popularity': self._process_content_popularity
        })
    
    def process_event(self, event: BaseEvent):
        """이벤트를 스트림 처리"""
        with self.lock:
            current_time = datetime.utcnow()
            
            # 각 처리기에 대해 윈도우 업데이트
            for processor_name, processor_func in self.processors.items():
                window_key = f"{processor_name}_{current_time.strftime('%Y%m%d_%H%M')}"
                
                # 윈도우가 없으면 생성
                if window_key not in self.windows:
                    window_start = current_time.replace(second=0, microsecond=0)
                    window_end = window_start + self.window_size
                    
                    self.windows[window_key] = StreamWindow(
                        window_start=window_start,
                        window_end=window_end,
                        events=[],
                        aggregations={}
                    )
                
                # 윈도우에 이벤트 추가
                window = self.windows[window_key]
                if window.window_start <= event.timestamp <= window.window_end:
                    window.events.append(event)
                    
                    # 처리기 실행
                    try:
                        processor_func(window, event)
                    except Exception as e:
                        logger.error(f"Error in processor {processor_name}: {e}")
            
            # 오래된 윈도우 정리
            self._cleanup_old_windows(current_time)
    
    def _cleanup_old_windows(self, current_time: datetime):
        """오래된 윈도우 정리"""
        cutoff_time = current_time - self.window_size * 2
        
        windows_to_remove = []
        for window_key, window in self.windows.items():
            if window.window_end < cutoff_time:
                windows_to_remove.append(window_key)
        
        for window_key in windows_to_remove:
            del self.windows[window_key]
    
    def _process_user_activity_rate(self, window: StreamWindow, event: BaseEvent):
        """사용자 활동률 처리"""
        if event.event_type != EventType.USER_INTERACTION:
            return
        
        # 사용자별 활동 집계
        if 'user_interactions' not in window.aggregations:
            window.aggregations['user_interactions'] = defaultdict(int)
            window.aggregations['unique_users'] = set()
        
        user_id = getattr(event, 'user_id', None)
        if user_id:
            window.aggregations['user_interactions'][user_id] += 1
            window.aggregations['unique_users'].add(user_id)
        
        # 메트릭 업데이트
        active_users = len(window.aggregations['unique_users'])
        total_interactions = sum(window.aggregations['user_interactions'].values())
        
        # DAU 업데이트 (일일 활성 사용자)
        custom_metrics['business'].daily_active_users.labels(
            user_segment='all'
        ).set(active_users)
        
        logger.debug(f"User activity: {active_users} active users, {total_interactions} interactions")
    
    def _process_recommendation_performance(self, window: StreamWindow, event: BaseEvent):
        """추천 성능 처리"""
        if event.event_type != EventType.RECOMMENDATION_EVENT:
            return
        
        if 'recommendations' not in window.aggregations:
            window.aggregations['recommendations'] = {
                'total_requests': 0,
                'total_response_time': 0,
                'by_algorithm': defaultdict(lambda: {'count': 0, 'total_time': 0})
            }
        
        algorithm = getattr(event, 'algorithm', 'unknown')
        response_time = getattr(event, 'response_time_ms', 0)
        
        # 집계 업데이트
        agg = window.aggregations['recommendations']
        agg['total_requests'] += 1
        agg['total_response_time'] += response_time
        agg['by_algorithm'][algorithm]['count'] += 1
        agg['by_algorithm'][algorithm]['total_time'] += response_time
        
        # 평균 응답시간 계산 및 메트릭 업데이트
        if agg['total_requests'] > 0:
            avg_response_time = agg['total_response_time'] / agg['total_requests']
            
            # 추천 지연시간 메트릭 업데이트
            custom_metrics['recommendation'].recommendation_latency_seconds.labels(
                algorithm=algorithm,
                user_segment='default',
                cache_status='unknown'
            ).observe(avg_response_time / 1000.0)
    
    def _process_model_prediction_rate(self, window: StreamWindow, event: BaseEvent):
        """모델 예측률 처리"""
        if event.event_type != EventType.MODEL_PREDICTION:
            return
        
        if 'predictions' not in window.aggregations:
            window.aggregations['predictions'] = {
                'total_predictions': 0,
                'by_model': defaultdict(int),
                'total_inference_time': 0
            }
        
        model_id = getattr(event, 'model_id', 'unknown')
        inference_time = getattr(event, 'inference_time_ms', 0)
        
        # 집계 업데이트
        agg = window.aggregations['predictions']
        agg['total_predictions'] += 1
        agg['by_model'][model_id] += 1
        agg['total_inference_time'] += inference_time
        
        # 예측률 메트릭 업데이트
        predictions_per_minute = agg['total_predictions'] / (self.window_size.total_seconds() / 60)
        
        logger.debug(f"Model predictions: {predictions_per_minute:.1f} predictions/min for {model_id}")
    
    def _process_system_health(self, window: StreamWindow, event: BaseEvent):
        """시스템 헬스 처리"""
        if event.event_type != EventType.SYSTEM_ALERT:
            return
        
        if 'alerts' not in window.aggregations:
            window.aggregations['alerts'] = {
                'total_alerts': 0,
                'by_level': defaultdict(int),
                'by_service': defaultdict(int)
            }
        
        level = getattr(event, 'level', 'info')
        service = getattr(event, 'service', 'unknown')
        
        # 집계 업데이트
        agg = window.aggregations['alerts']
        agg['total_alerts'] += 1
        agg['by_level'][str(level)] += 1
        agg['by_service'][service] += 1
        
        # 알림률 계산
        critical_alerts = agg['by_level'].get('critical', 0)
        error_alerts = agg['by_level'].get('error', 0)
        
        if critical_alerts > 0 or error_alerts > 5:  # 임계값
            logger.warning(f"High alert rate: {critical_alerts} critical, {error_alerts} errors")
    
    def _process_content_popularity(self, window: StreamWindow, event: BaseEvent):
        """콘텐츠 인기도 처리"""
        if event.event_type != EventType.USER_INTERACTION:
            return
        
        content_id = getattr(event, 'content_id', None)
        if not content_id:
            return
        
        if 'content_stats' not in window.aggregations:
            window.aggregations['content_stats'] = defaultdict(lambda: {
                'views': 0, 'ratings': 0, 'total_rating': 0.0
            })
        
        interaction_type = getattr(event, 'interaction_type', 'view')
        rating = getattr(event, 'rating', None)
        
        # 콘텐츠 통계 업데이트
        stats = window.aggregations['content_stats'][content_id]
        
        if str(interaction_type) == 'view':
            stats['views'] += 1
        elif str(interaction_type) == 'rating' and rating:
            stats['ratings'] += 1
            stats['total_rating'] += rating
        
        # 인기도 점수 계산 (간단한 공식)
        popularity_score = stats['views'] * 0.1
        if stats['ratings'] > 0:
            avg_rating = stats['total_rating'] / stats['ratings']
            popularity_score += avg_rating * stats['ratings'] * 0.5
        
        # 인기도 메트릭 업데이트
        custom_metrics['recommendation'].movie_popularity_score.labels(
            movie_id=str(content_id),
            genre='unknown',
            release_year='unknown'
        ).set(popularity_score)
    
    def get_current_aggregations(self) -> Dict[str, Any]:
        """현재 집계 결과 반환"""
        with self.lock:
            current_time = datetime.utcnow()
            current_aggregations = {}
            
            for window_key, window in self.windows.items():
                if window.window_start <= current_time <= window.window_end:
                    processor_name = window_key.split('_')[0]
                    current_aggregations[processor_name] = window.aggregations
            
            return current_aggregations

class RealTimeAnalyzer(EventHandler):
    """실시간 분석 이벤트 핸들러"""
    
    def __init__(self):
        super().__init__("RealTimeAnalyzer")
        self.stream_processor = StreamProcessor(window_size_seconds=300)  # 5분 윈도우
        self.anomaly_detectors = {}
        self.baseline_metrics = {}
        
        # 이상 감지 임계값
        self.thresholds = {
            'high_error_rate': 0.1,  # 10% 에러율
            'low_recommendation_ctr': 0.01,  # 1% CTR
            'high_latency': 2.0,  # 2초
            'unusual_user_activity': 2.0  # 평소의 2배
        }
    
    async def handle_event(self, event: BaseEvent) -> bool:
        """실시간 분석 처리"""
        try:
            # 스트림 처리
            self.stream_processor.process_event(event)
            
            # 이상 감지
            await self._detect_anomalies(event)
            
            # 실시간 대시보드 업데이트
            await self._update_realtime_dashboard()
            
            return True
            
        except Exception as e:
            logger.error(f"Error in real-time analysis: {e}")
            return False
    
    async def _detect_anomalies(self, event: BaseEvent):
        """이상 감지"""
        current_time = datetime.utcnow()
        
        # 에러율 이상 감지
        if event.event_type == EventType.SYSTEM_ALERT:
            await self._check_error_rate_anomaly(current_time)
        
        # 사용자 활동 이상 감지
        if event.event_type == EventType.USER_INTERACTION:
            await self._check_user_activity_anomaly(current_time)
        
        # 모델 성능 이상 감지
        if event.event_type == EventType.MODEL_PREDICTION:
            await self._check_model_performance_anomaly(current_time)
    
    async def _check_error_rate_anomaly(self, current_time: datetime):
        """에러율 이상 감지"""
        aggregations = self.stream_processor.get_current_aggregations()
        alerts_data = aggregations.get('system_health', {}).get('alerts', {})
        
        if alerts_data:
            total_alerts = alerts_data.get('total_alerts', 0)
            error_alerts = alerts_data.get('by_level', {}).get('error', 0)
            critical_alerts = alerts_data.get('by_level', {}).get('critical', 0)
            
            error_rate = (error_alerts + critical_alerts) / max(total_alerts, 1)
            
            if error_rate > self.thresholds['high_error_rate']:
                await self._trigger_anomaly_alert(
                    'high_error_rate',
                    f"High error rate detected: {error_rate:.2%}",
                    {'error_rate': error_rate, 'threshold': self.thresholds['high_error_rate']}
                )
    
    async def _check_user_activity_anomaly(self, current_time: datetime):
        """사용자 활동 이상 감지"""
        aggregations = self.stream_processor.get_current_aggregations()
        activity_data = aggregations.get('user_activity_rate', {})
        
        if activity_data:
            current_users = len(activity_data.get('unique_users', set()))
            
            # 기준선과 비교 (간단한 구현)
            baseline_users = self.baseline_metrics.get('average_users_5min', 100)
            
            if current_users > baseline_users * self.thresholds['unusual_user_activity']:
                await self._trigger_anomaly_alert(
                    'unusual_user_activity',
                    f"Unusual user activity spike: {current_users} users (baseline: {baseline_users})",
                    {'current_users': current_users, 'baseline_users': baseline_users}
                )
    
    async def _check_model_performance_anomaly(self, current_time: datetime):
        """모델 성능 이상 감지"""
        aggregations = self.stream_processor.get_current_aggregations()
        prediction_data = aggregations.get('model_prediction_rate', {}).get('predictions', {})
        
        if prediction_data:
            total_time = prediction_data.get('total_inference_time', 0)
            total_predictions = prediction_data.get('total_predictions', 0)
            
            if total_predictions > 0:
                avg_inference_time = total_time / total_predictions / 1000.0  # 초로 변환
                
                if avg_inference_time > self.thresholds['high_latency']:
                    await self._trigger_anomaly_alert(
                        'high_latency',
                        f"High model inference latency: {avg_inference_time:.2f}s",
                        {'avg_latency': avg_inference_time, 'threshold': self.thresholds['high_latency']}
                    )
    
    async def _trigger_anomaly_alert(self, anomaly_type: str, message: str, details: Dict[str, Any]):
        """이상 상황 알림 발생"""
        from .event_schemas import EventFactory, AlertLevel
        
        # 시스템 알림 이벤트 생성
        alert_event = EventFactory.create_system_alert(
            service='real-time-analyzer',
            level=AlertLevel.WARNING,
            message=message,
            alert_code=anomaly_type,
            details=details
        )
        
        # 알림 이벤트 전송 (필요시)
        logger.warning(f"ANOMALY DETECTED [{anomaly_type}]: {message}")
        
        # 메트릭 업데이트
        # (여기에 이상 감지 메트릭 업데이트 로직 추가)
    
    async def _update_realtime_dashboard(self):
        """실시간 대시보드 업데이트"""
        # 현재 집계 결과를 가져와서 대시보드용 메트릭 업데이트
        aggregations = self.stream_processor.get_current_aggregations()
        
        # 사용자 활동 메트릭
        if 'user_activity_rate' in aggregations:
            unique_users = len(aggregations['user_activity_rate'].get('unique_users', set()))
            total_interactions = sum(aggregations['user_activity_rate'].get('user_interactions', {}).values())
            
            # 실시간 메트릭 업데이트
            logger.debug(f"Real-time metrics: {unique_users} active users, {total_interactions} interactions")
        
        # 추천 성능 메트릭
        if 'recommendation_performance' in aggregations:
            rec_data = aggregations['recommendation_performance']['recommendations']
            if rec_data['total_requests'] > 0:
                avg_response_time = rec_data['total_response_time'] / rec_data['total_requests']
                logger.debug(f"Average recommendation response time: {avg_response_time:.1f}ms")

# 글로벌 스트림 처리기 인스턴스
stream_processor = StreamProcessor()
realtime_analyzer = RealTimeAnalyzer()
