"""
PyTorch 모델 메트릭 통합
훈련, 추론, 평가 과정에서 메트릭을 자동으로 수집하고 Prometheus로 전송
"""

import time
import logging
from typing import Dict, Any, Optional, Tuple
import torch
import torch.nn as nn
from contextlib import contextmanager

from ..monitoring.prometheus_metrics import get_metrics
from ..monitoring.custom_metrics import custom_metrics

logger = logging.getLogger(__name__)

class ModelMetricsTracker:
    """모델 메트릭 추적기"""
    
    def __init__(self, model_name: str, model_version: str = "v1.0"):
        self.model_name = model_name
        self.model_version = model_version
        self.metrics = get_metrics()
        self.custom_metrics = custom_metrics
        
    def record_training_start(self, dataset_size: int, epochs: int, batch_size: int):
        """훈련 시작 메트릭 기록"""
        self.custom_metrics['ml_pipeline'].training_dataset_size.labels(
            model_type=self.model_name,
            split='train'
        ).set(dataset_size)
        
        logger.info(f"Training started: {self.model_name} v{self.model_version}, Dataset: {dataset_size}, Epochs: {epochs}")
    
    def record_training_epoch(self, epoch: int, train_loss: float, val_loss: Optional[float] = None, 
                             learning_rate: float = None, metrics_dict: Optional[Dict[str, float]] = None):
        """에포크별 훈련 메트릭 기록"""
        
        # 훈련 손실 기록
        self.custom_metrics['ml_pipeline'].training_loss.labels(
            model_type=self.model_name,
            epoch=str(epoch),
            split='train'
        ).set(train_loss)
        
        # 검증 손실 기록
        if val_loss is not None:
            self.custom_metrics['ml_pipeline'].training_loss.labels(
                model_type=self.model_name,
                epoch=str(epoch),
                split='validation'
            ).set(val_loss)
        
        # 학습률 기록
        if learning_rate is not None:
            self.custom_metrics['ml_pipeline'].learning_rate.labels(
                model_type=self.model_name,
                optimizer='adam'  # 실제로는 옵티마이저 타입을 받아야 함
            ).set(learning_rate)
        
        # 추가 메트릭 기록
        if metrics_dict:
            for metric_name, value in metrics_dict.items():
                if metric_name == 'accuracy':
                    self.metrics.update_model_accuracy(
                        self.model_name, 
                        self.model_version, 
                        value
                    )
        
        logger.debug(f"Epoch {epoch}: train_loss={train_loss:.4f}, val_loss={val_loss}, lr={learning_rate}")
    
    def record_training_complete(self, duration: float, final_loss: float, success: bool = True):
        """훈련 완료 메트릭 기록"""
        
        # 훈련 작업 완료 기록
        status = 'success' if success else 'failed'
        self.custom_metrics['ml_pipeline'].training_jobs_total.labels(
            model_type=self.model_name,
            status=status,
            trigger='manual'
        ).inc()
        
        # 훈련 시간 기록
        self.custom_metrics['ml_pipeline'].training_duration_seconds.labels(
            model_type=self.model_name,
            dataset_size='medium',  # 실제로는 데이터셋 크기 범주를 계산해야 함
            gpu_enabled=str(torch.cuda.is_available())
        ).observe(duration)
        
        logger.info(f"Training completed: {self.model_name}, Duration: {duration:.2f}s, Final loss: {final_loss:.4f}")
    
    @contextmanager
    def track_inference(self, batch_size: int = 1):
        """추론 시간 추적 컨텍스트 매니저"""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            
            # 추론 시간 메트릭 기록
            self.custom_metrics['recommendation'].model_inference_duration_seconds.labels(
                model_type=self.model_name,
                model_version=self.model_version,
                batch_size=str(batch_size)
            ).observe(duration)
            
            # 예측 횟수 기록
            self.metrics.record_model_prediction(
                self.model_name,
                self.model_version,
                duration
            )
    
    def record_model_performance(self, rmse: float, mae: float, dataset_name: str = 'test'):
        """모델 성능 메트릭 기록"""
        
        # RMSE 기록
        self.custom_metrics['ml_pipeline'].model_rmse.labels(
            model_type=self.model_name,
            model_version=self.model_version,
            dataset=dataset_name
        ).set(rmse)
        
        # MAE 기록
        self.custom_metrics['ml_pipeline'].model_mae.labels(
            model_type=self.model_name,
            model_version=self.model_version,
            dataset=dataset_name
        ).set(mae)
        
        logger.info(f"Model performance: RMSE={rmse:.4f}, MAE={mae:.4f} on {dataset_name}")
    
    def record_data_quality(self, feature_stats: Dict[str, Any]):
        """데이터 품질 메트릭 기록"""
        
        for feature_name, stats in feature_stats.items():
            # 결측치 비율
            if 'missing_rate' in stats:
                self.custom_metrics['ml_pipeline'].missing_data_rate.labels(
                    feature_name=feature_name,
                    dataset='train'
                ).set(stats['missing_rate'])
            
            # 이상치 비율
            if 'outlier_rate' in stats:
                self.custom_metrics['ml_pipeline'].outlier_detection_rate.labels(
                    feature_name=feature_name,
                    detection_method='iqr',
                    dataset='train'
                ).set(stats['outlier_rate'])


class MetricsCallback:
    """훈련 중 메트릭을 추적하는 콜백"""
    
    def __init__(self, tracker: ModelMetricsTracker):
        self.tracker = tracker
        self.epoch_start_time = None
    
    def on_epoch_start(self, epoch: int):
        """에포크 시작 시 호출"""
        self.epoch_start_time = time.time()
    
    def on_epoch_end(self, epoch: int, logs: Dict[str, float]):
        """에포크 종료 시 호출"""
        if self.epoch_start_time:
            epoch_duration = time.time() - self.epoch_start_time
            
        # 메트릭 기록
        self.tracker.record_training_epoch(
            epoch=epoch,
            train_loss=logs.get('train_loss', 0.0),
            val_loss=logs.get('val_loss'),
            learning_rate=logs.get('learning_rate'),
            metrics_dict=logs
        )


def add_metrics_to_model(model: nn.Module, model_name: str, model_version: str = "v1.0") -> Tuple[nn.Module, ModelMetricsTracker]:
    """
    기존 PyTorch 모델에 메트릭 추적 기능 추가
    
    Args:
        model: PyTorch 모델
        model_name: 모델 이름
        model_version: 모델 버전
    
    Returns:
        메트릭이 추가된 모델과 메트릭 추적기
    """
    
    tracker = ModelMetricsTracker(model_name, model_version)
    
    # 모델의 forward 메서드를 래핑
    original_forward = model.forward
    
    def tracked_forward(self, *args, **kwargs):
        with tracker.track_inference(batch_size=args[0].size(0) if args else 1):
            return original_forward(*args, **kwargs)
    
    # 메서드 바인딩
    model.forward = tracked_forward.__get__(model, model.__class__)
    
    return model, tracker


def calculate_feature_stats(features: torch.Tensor, feature_names: Optional[list] = None) -> Dict[str, Dict[str, float]]:
    """
    특성 통계 계산 (데이터 품질 메트릭용)
    
    Args:
        features: 특성 텐서 [batch_size, feature_dim]
        feature_names: 특성 이름 리스트
    
    Returns:
        특성별 통계 딕셔너리
    """
    
    if feature_names is None:
        feature_names = [f"feature_{i}" for i in range(features.size(1))]
    
    stats = {}
    
    for i, name in enumerate(feature_names):
        feature_values = features[:, i]
        
        # 기본 통계
        mean = feature_values.mean().item()
        std = feature_values.std().item()
        
        # 결측치 비율 (NaN 값)
        missing_rate = torch.isnan(feature_values).float().mean().item()
        
        # 이상치 비율 (IQR 방법)
        q1 = torch.quantile(feature_values, 0.25).item()
        q3 = torch.quantile(feature_values, 0.75).item()
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        outliers = ((feature_values < lower_bound) | (feature_values > upper_bound))
        outlier_rate = outliers.float().mean().item()
        
        stats[name] = {
            'mean': mean,
            'std': std,
            'missing_rate': missing_rate,
            'outlier_rate': outlier_rate,
            'q1': q1,
            'q3': q3
        }
    
    return stats


class RecommendationMetricsLogger:
    """추천 시스템 전용 메트릭 로거"""
    
    def __init__(self):
        self.custom_metrics = custom_metrics
    
    def log_recommendation_request(self, algorithm: str, user_segment: str, request_type: str = 'standard'):
        """추천 요청 로그"""
        self.custom_metrics['recommendation'].recommendation_requests_total.labels(
            algorithm=algorithm,
            user_segment=user_segment,
            request_type=request_type
        ).inc()
    
    def log_recommendation_success(self, algorithm: str, user_segment: str):
        """추천 성공 로그"""
        self.custom_metrics['recommendation'].recommendation_success_total.labels(
            algorithm=algorithm,
            user_segment=user_segment
        ).inc()
    
    def log_user_interaction(self, interaction_type: str, user_segment: str):
        """사용자 상호작용 로그"""
        self.custom_metrics['recommendation'].user_interactions_total.labels(
            interaction_type=interaction_type,
            user_segment=user_segment
        ).inc()
    
    def log_recommendation_latency(self, algorithm: str, user_segment: str, latency: float, cache_hit: bool = False):
        """추천 지연시간 로그"""
        cache_status = 'hit' if cache_hit else 'miss'
        self.custom_metrics['recommendation'].recommendation_latency_seconds.labels(
            algorithm=algorithm,
            user_segment=user_segment,
            cache_status=cache_status
        ).observe(latency)
    
    def update_recommendation_metrics(self, algorithm: str, user_segment: str, 
                                   precision: float, recall: float, diversity: float):
        """추천 품질 메트릭 업데이트"""
        
        # F1 점수 계산
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        # 메트릭 업데이트
        self.custom_metrics['recommendation'].recommendation_precision.labels(
            algorithm=algorithm,
            evaluation_period='daily'
        ).set(precision)
        
        self.custom_metrics['recommendation'].recommendation_recall.labels(
            algorithm=algorithm,
            evaluation_period='daily'
        ).set(recall)
        
        self.custom_metrics['recommendation'].recommendation_f1_score.labels(
            algorithm=algorithm,
            evaluation_period='daily'
        ).set(f1_score)
        
        self.custom_metrics['recommendation'].recommendation_diversity.labels(
            algorithm=algorithm,
            user_segment=user_segment
        ).set(diversity)


# 글로벌 추천 메트릭 로거 인스턴스
recommendation_logger = RecommendationMetricsLogger()
