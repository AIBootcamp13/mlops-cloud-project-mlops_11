"""
Prometheus 메트릭 수집기
MLOps 파이프라인의 모든 구성 요소에서 메트릭을 수집하고 Prometheus로 전송
"""

import time
import logging
import psutil
import requests
from typing import Dict, Any, Optional
from prometheus_client import (
    Counter, Histogram, Gauge, Info, CollectorRegistry,
    multiprocess, generate_latest, CONTENT_TYPE_LATEST
)
from prometheus_client.metrics import MetricWrapperBase

logger = logging.getLogger(__name__)

class PrometheusMetrics:
    """Prometheus 메트릭 수집 및 관리"""
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        self.registry = registry or CollectorRegistry()
        self._init_metrics()
    
    def _init_metrics(self):
        """기본 메트릭 초기화"""
        
        # 시스템 메트릭
        self.system_cpu_usage = Gauge(
            'system_cpu_usage_percent',
            'System CPU usage percentage',
            registry=self.registry
        )
        
        self.system_memory_usage = Gauge(
            'system_memory_usage_bytes',
            'System memory usage in bytes',
            ['type'],  # available, used, total
            registry=self.registry
        )
        
        self.system_disk_usage = Gauge(
            'system_disk_usage_bytes',
            'System disk usage in bytes',
            ['path', 'type'],  # path, type (used, free, total)
            registry=self.registry
        )
        
        # API 메트릭
        self.http_requests_total = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status'],
            registry=self.registry
        )
        
        self.http_request_duration_seconds = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint'],
            registry=self.registry
        )
        
        # ML 메트릭
        self.model_predictions_total = Counter(
            'model_predictions_total',
            'Total model predictions',
            ['model_name', 'model_version'],
            registry=self.registry
        )
        
        self.model_prediction_duration_seconds = Histogram(
            'model_prediction_duration_seconds',
            'Model prediction duration in seconds',
            ['model_name', 'model_version'],
            registry=self.registry
        )
        
        self.model_accuracy = Gauge(
            'model_accuracy',
            'Model accuracy score',
            ['model_name', 'model_version'],
            registry=self.registry
        )
        
        # MLflow 메트릭
        self.mlflow_experiments_total = Gauge(
            'mlflow_experiments_total',
            'Total MLflow experiments',
            registry=self.registry
        )
        
        self.mlflow_runs_total = Counter(
            'mlflow_runs_total',
            'Total MLflow runs',
            ['experiment_id', 'status'],
            registry=self.registry
        )
        
        # Feast 메트릭
        self.feast_feature_requests_total = Counter(
            'feast_feature_requests_total',
            'Total Feast feature requests',
            ['feature_view', 'status'],
            registry=self.registry
        )
        
        self.feast_feature_retrieval_duration_seconds = Histogram(
            'feast_feature_retrieval_duration_seconds',
            'Feast feature retrieval duration in seconds',
            ['feature_view'],
            registry=self.registry
        )
        
        # Airflow 메트릭
        self.airflow_dag_runs_total = Counter(
            'airflow_dag_runs_total',
            'Total Airflow DAG runs',
            ['dag_id', 'state'],
            registry=self.registry
        )
        
        self.airflow_task_duration_seconds = Histogram(
            'airflow_task_duration_seconds',
            'Airflow task duration in seconds',
            ['dag_id', 'task_id'],
            registry=self.registry
        )
        
        # 데이터베이스 메트릭
        self.database_connections_active = Gauge(
            'database_connections_active',
            'Active database connections',
            ['database'],
            registry=self.registry
        )
        
        self.database_query_duration_seconds = Histogram(
            'database_query_duration_seconds',
            'Database query duration in seconds',
            ['database', 'query_type'],
            registry=self.registry
        )
        
        # 비즈니스 메트릭
        self.recommendation_clicks_total = Counter(
            'recommendation_clicks_total',
            'Total recommendation clicks',
            ['model_name', 'user_segment'],
            registry=self.registry
        )
        
        self.user_sessions_total = Counter(
            'user_sessions_total',
            'Total user sessions',
            registry=self.registry
        )
        
        # 시스템 정보
        self.system_info = Info(
            'system_info',
            'System information',
            registry=self.registry
        )
    
    def collect_system_metrics(self):
        """시스템 메트릭 수집"""
        try:
            # CPU 사용률
            cpu_percent = psutil.cpu_percent(interval=1)
            self.system_cpu_usage.set(cpu_percent)
            
            # 메모리 사용률
            memory = psutil.virtual_memory()
            self.system_memory_usage.labels(type='available').set(memory.available)
            self.system_memory_usage.labels(type='used').set(memory.used)
            self.system_memory_usage.labels(type='total').set(memory.total)
            
            # 디스크 사용률
            disk = psutil.disk_usage('/')
            self.system_disk_usage.labels(path='/', type='used').set(disk.used)
            self.system_disk_usage.labels(path='/', type='free').set(disk.free)
            self.system_disk_usage.labels(path='/', type='total').set(disk.total)
            
            logger.debug(f"System metrics collected: CPU={cpu_percent}%, Memory Used={memory.used/1e9:.1f}GB")
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    def record_http_request(self, method: str, endpoint: str, status: int, duration: float):
        """HTTP 요청 메트릭 기록"""
        self.http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=str(status)
        ).inc()
        
        self.http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    def record_model_prediction(self, model_name: str, model_version: str, duration: float):
        """모델 예측 메트릭 기록"""
        self.model_predictions_total.labels(
            model_name=model_name,
            model_version=model_version
        ).inc()
        
        self.model_prediction_duration_seconds.labels(
            model_name=model_name,
            model_version=model_version
        ).observe(duration)
    
    def update_model_accuracy(self, model_name: str, model_version: str, accuracy: float):
        """모델 정확도 업데이트"""
        self.model_accuracy.labels(
            model_name=model_name,
            model_version=model_version
        ).set(accuracy)
    
    def record_mlflow_run(self, experiment_id: str, status: str):
        """MLflow 실행 메트릭 기록"""
        self.mlflow_runs_total.labels(
            experiment_id=experiment_id,
            status=status
        ).inc()
    
    def record_feast_request(self, feature_view: str, status: str, duration: float):
        """Feast 요청 메트릭 기록"""
        self.feast_feature_requests_total.labels(
            feature_view=feature_view,
            status=status
        ).inc()
        
        self.feast_feature_retrieval_duration_seconds.labels(
            feature_view=feature_view
        ).observe(duration)
    
    def record_airflow_dag_run(self, dag_id: str, state: str):
        """Airflow DAG 실행 메트릭 기록"""
        self.airflow_dag_runs_total.labels(
            dag_id=dag_id,
            state=state
        ).inc()
    
    def record_airflow_task_duration(self, dag_id: str, task_id: str, duration: float):
        """Airflow 태스크 지속시간 기록"""
        self.airflow_task_duration_seconds.labels(
            dag_id=dag_id,
            task_id=task_id
        ).observe(duration)
    
    def update_database_connections(self, database: str, active_connections: int):
        """데이터베이스 연결 수 업데이트"""
        self.database_connections_active.labels(database=database).set(active_connections)
    
    def record_database_query(self, database: str, query_type: str, duration: float):
        """데이터베이스 쿼리 지속시간 기록"""
        self.database_query_duration_seconds.labels(
            database=database,
            query_type=query_type
        ).observe(duration)
    
    def record_recommendation_click(self, model_name: str, user_segment: str):
        """추천 클릭 메트릭 기록"""
        self.recommendation_clicks_total.labels(
            model_name=model_name,
            user_segment=user_segment
        ).inc()
    
    def record_user_session(self):
        """사용자 세션 메트릭 기록"""
        self.user_sessions_total.inc()
    
    def set_system_info(self, info: Dict[str, str]):
        """시스템 정보 설정"""
        self.system_info.info(info)
    
    def get_metrics(self) -> str:
        """현재 메트릭을 Prometheus 형식으로 반환"""
        return generate_latest(self.registry)


class MetricsCollector:
    """메트릭 수집기 - 주기적으로 시스템 메트릭 수집"""
    
    def __init__(self, metrics: PrometheusMetrics, interval: int = 15):
        self.metrics = metrics
        self.interval = interval
        self.running = False
    
    def start(self):
        """메트릭 수집 시작"""
        import threading
        
        self.running = True
        self.thread = threading.Thread(target=self._collect_loop, daemon=True)
        self.thread.start()
        logger.info(f"MetricsCollector started with {self.interval}s interval")
    
    def stop(self):
        """메트릭 수집 중지"""
        self.running = False
        if hasattr(self, 'thread'):
            self.thread.join()
        logger.info("MetricsCollector stopped")
    
    def _collect_loop(self):
        """메트릭 수집 루프"""
        while self.running:
            try:
                self.metrics.collect_system_metrics()
                time.sleep(self.interval)
            except Exception as e:
                logger.error(f"Error in metrics collection loop: {e}")
                time.sleep(self.interval)


class HealthChecker:
    """서비스 헬스체크"""
    
    def __init__(self, metrics: PrometheusMetrics):
        self.metrics = metrics
        self.services = {
            'postgres': 'http://localhost:5432',
            'redis': 'http://localhost:6379',
            'mlflow': 'http://localhost:5000',
            'feast': 'http://localhost:6566',
            'airflow': 'http://localhost:8080'
        }
    
    def check_service_health(self, service_name: str, url: str) -> bool:
        """개별 서비스 헬스체크"""
        try:
            response = requests.get(f"{url}/health", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def check_all_services(self) -> Dict[str, bool]:
        """모든 서비스 헬스체크"""
        health_status = {}
        
        for service_name, url in self.services.items():
            is_healthy = self.check_service_health(service_name, url)
            health_status[service_name] = is_healthy
            
            # 헬스체크 메트릭 기록
            health_metric = Gauge(
                f'{service_name}_service_healthy',
                f'{service_name} service health status',
                registry=self.metrics.registry
            )
            health_metric.set(1 if is_healthy else 0)
        
        return health_status


# 글로벌 메트릭 인스턴스
metrics_instance = PrometheusMetrics()
metrics_collector = MetricsCollector(metrics_instance)
health_checker = HealthChecker(metrics_instance)

def get_metrics() -> PrometheusMetrics:
    """글로벌 메트릭 인스턴스 반환"""
    return metrics_instance

def start_metrics_collection():
    """메트릭 수집 시작"""
    metrics_collector.start()

def stop_metrics_collection():
    """메트릭 수집 중지"""
    metrics_collector.stop()
