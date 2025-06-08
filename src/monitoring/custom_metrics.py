"""
커스텀 메트릭 정의
영화 추천 시스템에 특화된 비즈니스 메트릭과 ML 메트릭 정의
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from prometheus_client import Counter, Histogram, Gauge, Enum, Info
from prometheus_client.registry import CollectorRegistry

logger = logging.getLogger(__name__)

class MovieRecommendationMetrics:
    """영화 추천 시스템 전용 메트릭"""
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        self.registry = registry
        self._init_recommendation_metrics()
        self._init_user_behavior_metrics()
        self._init_content_metrics()
        self._init_performance_metrics()
    
    def _init_recommendation_metrics(self):
        """추천 시스템 관련 메트릭 초기화"""
        
        # 추천 요청 및 성공률
        self.recommendation_requests_total = Counter(
            'movie_recommendation_requests_total',
            'Total movie recommendation requests',
            ['algorithm', 'user_segment', 'request_type'],  # collaborative, content-based, hybrid
            registry=self.registry
        )
        
        self.recommendation_success_total = Counter(
            'movie_recommendation_success_total',
            'Successful movie recommendations',
            ['algorithm', 'user_segment'],
            registry=self.registry
        )
        
        # 추천 다양성 메트릭
        self.recommendation_diversity = Gauge(
            'movie_recommendation_diversity_score',
            'Recommendation diversity score (0-1)',
            ['algorithm', 'user_segment'],
            registry=self.registry
        )
        
        # 추천 신선도 (최신 영화 비율)
        self.recommendation_freshness = Gauge(
            'movie_recommendation_freshness_score',
            'Percentage of recent movies in recommendations',
            ['algorithm', 'days_threshold'],  # 30, 90, 365 days
            registry=self.registry
        )
        
        # 추천 정확도 메트릭
        self.recommendation_precision = Gauge(
            'movie_recommendation_precision',
            'Recommendation precision score',
            ['algorithm', 'evaluation_period'],
            registry=self.registry
        )
        
        self.recommendation_recall = Gauge(
            'movie_recommendation_recall',
            'Recommendation recall score',
            ['algorithm', 'evaluation_period'],
            registry=self.registry
        )
        
        self.recommendation_f1_score = Gauge(
            'movie_recommendation_f1_score',
            'Recommendation F1 score',
            ['algorithm', 'evaluation_period'],
            registry=self.registry
        )
    
    def _init_user_behavior_metrics(self):
        """사용자 행동 메트릭 초기화"""
        
        # 사용자 상호작용
        self.user_interactions_total = Counter(
            'movie_user_interactions_total',
            'Total user interactions',
            ['interaction_type', 'user_segment'],  # view, rating, watchlist, share
            registry=self.registry
        )
        
        # 클릭률 (CTR)
        self.recommendation_ctr = Gauge(
            'movie_recommendation_ctr',
            'Click-through rate for recommendations',
            ['algorithm', 'position', 'user_segment'],  # position: 1-10
            registry=self.registry
        )
        
        # 시청 완료율
        self.watch_completion_rate = Gauge(
            'movie_watch_completion_rate',
            'Movie watch completion rate',
            ['genre', 'duration_bucket', 'user_segment'],
            registry=self.registry
        )
        
        # 평점 분포
        self.rating_distribution = Gauge(
            'movie_rating_distribution',
            'Distribution of movie ratings',
            ['rating', 'genre', 'time_period'],  # rating: 1-5
            registry=self.registry
        )
        
        # 사용자 세션 지속시간
        self.user_session_duration_seconds = Histogram(
            'movie_user_session_duration_seconds',
            'User session duration in seconds',
            ['user_segment', 'device_type'],
            buckets=[60, 300, 900, 1800, 3600, 7200],  # 1min to 2hour
            registry=self.registry
        )
        
        # 재방문률
        self.user_return_rate = Gauge(
            'movie_user_return_rate',
            'User return rate within time period',
            ['time_period', 'user_segment'],  # 1day, 7day, 30day
            registry=self.registry
        )
    
    def _init_content_metrics(self):
        """콘텐츠 관련 메트릭 초기화"""
        
        # 영화 인기도
        self.movie_popularity_score = Gauge(
            'movie_popularity_score',
            'Movie popularity score',
            ['movie_id', 'genre', 'release_year'],
            registry=self.registry
        )
        
        # 장르별 선호도
        self.genre_preference = Gauge(
            'movie_genre_preference_score',
            'Genre preference score by user segment',
            ['genre', 'user_segment', 'time_period'],
            registry=self.registry
        )
        
        # 콘텐츠 커버리지 (추천된 영화의 비율)
        self.content_coverage = Gauge(
            'movie_content_coverage_rate',
            'Percentage of total movies being recommended',
            ['algorithm', 'time_period'],
            registry=self.registry
        )
        
        # 영화 카탈로그 크기
        self.catalog_size = Gauge(
            'movie_catalog_size_total',
            'Total number of movies in catalog',
            ['status'],  # active, inactive, new
            registry=self.registry
        )
        
        # 신규 콘텐츠 추가율
        self.new_content_rate = Counter(
            'movie_new_content_total',
            'New movies added to catalog',
            ['genre', 'source'],  # tmdb, manual, api
            registry=self.registry
        )
    
    def _init_performance_metrics(self):
        """성능 관련 메트릭 초기화"""
        
        # 추천 응답 시간
        self.recommendation_latency_seconds = Histogram(
            'movie_recommendation_latency_seconds',
            'Recommendation generation latency in seconds',
            ['algorithm', 'user_segment', 'cache_status'],  # hit, miss
            buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
            registry=self.registry
        )
        
        # 모델 추론 시간
        self.model_inference_duration_seconds = Histogram(
            'movie_model_inference_duration_seconds',
            'Model inference duration in seconds',
            ['model_type', 'model_version', 'batch_size'],
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0],
            registry=self.registry
        )
        
        # 특성 추출 시간
        self.feature_extraction_duration_seconds = Histogram(
            'movie_feature_extraction_duration_seconds',
            'Feature extraction duration in seconds',
            ['feature_type', 'data_source'],  # user_features, movie_features
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0],
            registry=self.registry
        )
        
        # 캐시 히트율
        self.cache_hit_rate = Gauge(
            'movie_cache_hit_rate',
            'Cache hit rate for recommendations',
            ['cache_type', 'time_window'],  # user_cache, movie_cache, feature_cache
            registry=self.registry
        )
        
        # 데이터 프레시니스 (마지막 업데이트 이후 시간)
        self.data_freshness_seconds = Gauge(
            'movie_data_freshness_seconds',
            'Seconds since last data update',
            ['data_type', 'source'],  # ratings, movies, users
            registry=self.registry
        )

class MLPipelineMetrics:
    """ML 파이프라인 전용 메트릭"""
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        self.registry = registry
        self._init_training_metrics()
        self._init_model_metrics()
        self._init_data_quality_metrics()
    
    def _init_training_metrics(self):
        """모델 훈련 관련 메트릭 초기화"""
        
        # 훈련 작업 상태
        self.training_jobs_total = Counter(
            'ml_training_jobs_total',
            'Total ML training jobs',
            ['model_type', 'status', 'trigger'],  # scheduled, manual, auto-retrain
            registry=self.registry
        )
        
        # 훈련 시간
        self.training_duration_seconds = Histogram(
            'ml_training_duration_seconds',
            'Model training duration in seconds',
            ['model_type', 'dataset_size', 'gpu_enabled'],
            buckets=[60, 300, 900, 1800, 3600, 7200, 14400],  # 1min to 4hour
            registry=self.registry
        )
        
        # 에포크별 손실
        self.training_loss = Gauge(
            'ml_training_loss',
            'Training loss value',
            ['model_type', 'epoch', 'split'],  # train, validation
            registry=self.registry
        )
        
        # 학습률
        self.learning_rate = Gauge(
            'ml_learning_rate',
            'Current learning rate',
            ['model_type', 'optimizer'],
            registry=self.registry
        )
        
        # 훈련 데이터셋 크기
        self.training_dataset_size = Gauge(
            'ml_training_dataset_size',
            'Training dataset size',
            ['model_type', 'split'],  # train, validation, test
            registry=self.registry
        )
    
    def _init_model_metrics(self):
        """모델 관련 메트릭 초기화"""
        
        # 모델 성능 메트릭
        self.model_rmse = Gauge(
            'ml_model_rmse',
            'Model Root Mean Square Error',
            ['model_type', 'model_version', 'dataset'],
            registry=self.registry
        )
        
        self.model_mae = Gauge(
            'ml_model_mae',
            'Model Mean Absolute Error',
            ['model_type', 'model_version', 'dataset'],
            registry=self.registry
        )
        
        # 모델 배포 상태
        self.model_deployment_status = Enum(
            'ml_model_deployment_status',
            'Model deployment status',
            ['model_type', 'model_version'],
            states=['training', 'testing', 'staging', 'production', 'retired'],
            registry=self.registry
        )
        
        # 모델 크기
        self.model_size_bytes = Gauge(
            'ml_model_size_bytes',
            'Model size in bytes',
            ['model_type', 'model_version'],
            registry=self.registry
        )
        
        # A/B 테스트 메트릭
        self.ab_test_traffic_split = Gauge(
            'ml_ab_test_traffic_split',
            'A/B test traffic split percentage',
            ['experiment_id', 'model_variant'],
            registry=self.registry
        )
        
        self.ab_test_conversion_rate = Gauge(
            'ml_ab_test_conversion_rate',
            'A/B test conversion rate',
            ['experiment_id', 'model_variant', 'metric_type'],
            registry=self.registry
        )
    
    def _init_data_quality_metrics(self):
        """데이터 품질 관련 메트릭 초기화"""
        
        # 데이터 드리프트 감지
        self.data_drift_score = Gauge(
            'ml_data_drift_score',
            'Data drift detection score',
            ['feature_name', 'drift_method'],  # psi, ks_test, chi2
            registry=self.registry
        )
        
        # 특성 중요도
        self.feature_importance = Gauge(
            'ml_feature_importance_score',
            'Feature importance score',
            ['model_type', 'feature_name', 'importance_method'],
            registry=self.registry
        )
        
        # 데이터 결측치 비율
        self.missing_data_rate = Gauge(
            'ml_missing_data_rate',
            'Missing data rate for features',
            ['feature_name', 'dataset'],
            registry=self.registry
        )
        
        # 데이터 이상치 비율
        self.outlier_detection_rate = Gauge(
            'ml_outlier_detection_rate',
            'Outlier detection rate',
            ['feature_name', 'detection_method', 'dataset'],
            registry=self.registry
        )
        
        # 데이터 스키마 변경
        self.schema_changes_total = Counter(
            'ml_schema_changes_total',
            'Total schema changes detected',
            ['table_name', 'change_type'],  # added, removed, modified
            registry=self.registry
        )

class BusinessMetrics:
    """비즈니스 메트릭"""
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        self.registry = registry
        self._init_revenue_metrics()
        self._init_engagement_metrics()
        self._init_satisfaction_metrics()
    
    def _init_revenue_metrics(self):
        """수익 관련 메트릭 초기화"""
        
        # 구독 전환율
        self.subscription_conversion_rate = Gauge(
            'business_subscription_conversion_rate',
            'Subscription conversion rate',
            ['recommendation_source', 'user_segment', 'time_period'],
            registry=self.registry
        )
        
        # 사용자 생애 가치 (LTV)
        self.user_lifetime_value = Gauge(
            'business_user_lifetime_value',
            'User lifetime value',
            ['user_segment', 'cohort'],
            registry=self.registry
        )
        
        # 이탈률
        self.churn_rate = Gauge(
            'business_churn_rate',
            'User churn rate',
            ['user_segment', 'time_period'],
            registry=self.registry
        )
    
    def _init_engagement_metrics(self):
        """참여도 관련 메트릭 초기화"""
        
        # 일일 활성 사용자 (DAU)
        self.daily_active_users = Gauge(
            'business_daily_active_users',
            'Daily active users',
            ['user_segment'],
            registry=self.registry
        )
        
        # 세션당 추천 클릭 수
        self.recommendations_per_session = Gauge(
            'business_recommendations_per_session',
            'Average recommendations clicked per session',
            ['user_segment', 'time_period'],
            registry=self.registry
        )
    
    def _init_satisfaction_metrics(self):
        """만족도 관련 메트릭 초기화"""
        
        # 사용자 만족도 점수
        self.user_satisfaction_score = Gauge(
            'business_user_satisfaction_score',
            'User satisfaction score (1-5)',
            ['feedback_source', 'user_segment'],
            registry=self.registry
        )
        
        # 추천 만족도
        self.recommendation_satisfaction = Gauge(
            'business_recommendation_satisfaction',
            'Recommendation satisfaction score',
            ['algorithm', 'user_segment'],
            registry=self.registry
        )

def create_custom_metrics(registry: Optional[CollectorRegistry] = None) -> Dict[str, Any]:
    """모든 커스텀 메트릭 생성 및 반환"""
    
    recommendation_metrics = MovieRecommendationMetrics(registry)
    ml_pipeline_metrics = MLPipelineMetrics(registry)
    business_metrics = BusinessMetrics(registry)
    
    return {
        'recommendation': recommendation_metrics,
        'ml_pipeline': ml_pipeline_metrics,
        'business': business_metrics
    }

# 글로벌 커스텀 메트릭 인스턴스
custom_metrics = create_custom_metrics()
