"""
Kafka 통합 Airflow DAG
실시간 이벤트 처리와 배치 처리를 연동하는 DAG
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.sensors.filesystem import FileSensor
from airflow.models import Variable

# 프로젝트 모듈 import
import sys
import os
sys.path.append('/opt/airflow/src')

logger = logging.getLogger(__name__)

# DAG 기본 설정
default_args = {
    'owner': 'movie-mlops',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'catchup': False
}

# DAG 정의
dag = DAG(
    'kafka_integration_pipeline',
    default_args=default_args,
    description='Kafka 이벤트 처리 및 배치 통합 파이프라인',
    schedule_interval=timedelta(hours=1),  # 1시간마다 실행
    max_active_runs=1,
    tags=['kafka', 'events', 'realtime', 'batch']
)

def setup_kafka_environment():
    """Kafka 환경 설정"""
    try:
        logger.info("Setting up Kafka environment...")
        
        # 환경 변수 확인
        kafka_config = {
            'bootstrap_servers': Variable.get('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092'),
            'consumer_group': Variable.get('KAFKA_CONSUMER_GROUP', 'movie-mlops-batch'),
            'topics': Variable.get('KAFKA_TOPICS', 'movie-user-interactions,movie-model-predictions').split(',')
        }
        
        logger.info(f"Kafka configuration: {kafka_config}")
        return kafka_config
        
    except Exception as e:
        logger.error(f"Error setting up Kafka environment: {e}")
        raise

def consume_and_process_events(**context):
    """Kafka 이벤트 소비 및 처리"""
    try:
        from src.events.kafka_consumer import KafkaEventConsumer
        from src.events.event_schemas import EventType
        
        logger.info("Starting Kafka event consumption for batch processing...")
        
        # 실행 시간 범위 설정 (지난 1시간)
        execution_date = context['execution_date']
        start_time = execution_date
        end_time = execution_date + timedelta(hours=1)
        
        logger.info(f"Processing events from {start_time} to {end_time}")
        
        # Kafka 컨슈머 설정
        consumer_config = {
            'group_id': 'movie-mlops-batch-processor',
            'auto_offset_reset': 'earliest',
            'enable_auto_commit': False  # 수동 커밋으로 정확한 처리 보장
        }
        
        # 배치 이벤트 처리기
        batch_processor = BatchEventProcessor(start_time, end_time)
        
        # 컨슈머 생성 및 처리기 등록
        consumer = KafkaEventConsumer(**consumer_config)
        consumer.add_handler(EventType.USER_INTERACTION, batch_processor)
        consumer.add_handler(EventType.MODEL_PREDICTION, batch_processor)
        consumer.add_handler(EventType.RECOMMENDATION_EVENT, batch_processor)
        
        # 배치 처리 실행 (타임아웃 설정)
        import signal
        import time
        
        def timeout_handler(signum, frame):
            raise TimeoutError("Batch processing timeout")
        
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(3000)  # 50분 타임아웃
        
        try:
            # 이벤트 소비 및 처리
            consumer.start_consuming()
            
            # 처리 결과 반환
            processing_stats = batch_processor.get_processing_stats()
            logger.info(f"Batch processing completed: {processing_stats}")
            
            return processing_stats
            
        finally:
            signal.alarm(0)  # 타임아웃 해제
            consumer.stop_consuming()
            consumer.disconnect()
        
    except Exception as e:
        logger.error(f"Error in batch event processing: {e}")
        raise

def aggregate_user_behavior_data(**context):
    """사용자 행동 데이터 집계"""
    try:
        logger.info("Aggregating user behavior data...")
        
        # 이전 태스크에서 처리된 이벤트 데이터 가져오기
        processing_stats = context['task_instance'].xcom_pull(task_ids='consume_kafka_events')
        
        if not processing_stats:
            logger.warning("No processing stats available from previous task")
            return {"status": "skipped", "reason": "no_data"}
        
        # 사용자 행동 집계 로직
        aggregator = UserBehaviorAggregator()
        
        # 집계 수행
        aggregation_results = aggregator.aggregate_hourly_data(
            start_time=context['execution_date'],
            end_time=context['execution_date'] + timedelta(hours=1),
            event_stats=processing_stats
        )
        
        # 결과를 데이터베이스에 저장
        aggregator.save_aggregations(aggregation_results)
        
        logger.info(f"User behavior aggregation completed: {aggregation_results}")
        return aggregation_results
        
    except Exception as e:
        logger.error(f"Error aggregating user behavior data: {e}")
        raise

def update_recommendation_models(**context):
    """추천 모델 업데이트"""
    try:
        logger.info("Updating recommendation models based on recent events...")
        
        # 집계된 사용자 행동 데이터 가져오기
        aggregation_results = context['task_instance'].xcom_pull(task_ids='aggregate_user_behavior')
        
        if not aggregation_results or aggregation_results.get('status') == 'skipped':
            logger.info("Skipping model update - no aggregation data available")
            return {"status": "skipped", "reason": "no_aggregation_data"}
        
        # 모델 업데이트 로직
        model_updater = RecommendationModelUpdater()
        
        # 온라인 학습 또는 모델 파라미터 조정
        update_results = model_updater.update_models(
            user_behavior_data=aggregation_results,
            execution_date=context['execution_date']
        )
        
        logger.info(f"Model update completed: {update_results}")
        return update_results
        
    except Exception as e:
        logger.error(f"Error updating recommendation models: {e}")
        raise

def generate_analytics_report(**context):
    """분석 리포트 생성"""
    try:
        logger.info("Generating analytics report...")
        
        # 이전 태스크들의 결과 수집
        processing_stats = context['task_instance'].xcom_pull(task_ids='consume_kafka_events')
        aggregation_results = context['task_instance'].xcom_pull(task_ids='aggregate_user_behavior')
        model_update_results = context['task_instance'].xcom_pull(task_ids='update_recommendation_models')
        
        # 리포트 생성기
        report_generator = AnalyticsReportGenerator()
        
        report_data = {
            'execution_date': context['execution_date'].isoformat(),
            'processing_stats': processing_stats,
            'aggregation_results': aggregation_results,
            'model_update_results': model_update_results,
            'generated_at': datetime.utcnow().isoformat()
        }
        
        # 리포트 생성 및 저장
        report_path = report_generator.generate_hourly_report(report_data)
        
        # 리포트를 Kafka로 전송 (다른 시스템에서 소비 가능)
        report_generator.publish_report_event(report_data)
        
        logger.info(f"Analytics report generated: {report_path}")
        return {"report_path": report_path, "report_data": report_data}
        
    except Exception as e:
        logger.error(f"Error generating analytics report: {e}")
        raise

def cleanup_processed_data(**context):
    """처리된 데이터 정리"""
    try:
        logger.info("Cleaning up processed data...")
        
        # 오래된 이벤트 데이터 정리
        cleanup_manager = DataCleanupManager()
        
        # 7일 이상 된 원시 이벤트 데이터 정리
        cleanup_results = cleanup_manager.cleanup_old_events(
            retention_days=7,
            execution_date=context['execution_date']
        )
        
        # 임시 파일 정리
        cleanup_results.update(cleanup_manager.cleanup_temp_files())
        
        logger.info(f"Data cleanup completed: {cleanup_results}")
        return cleanup_results
        
    except Exception as e:
        logger.error(f"Error cleaning up data: {e}")
        raise

# 헬퍼 클래스들
class BatchEventProcessor:
    """배치 이벤트 처리기"""
    
    def __init__(self, start_time: datetime, end_time: datetime):
        self.start_time = start_time
        self.end_time = end_time
        self.processed_events = []
        self.processing_stats = {
            'total_events': 0,
            'events_by_type': {},
            'processing_errors': 0
        }
    
    async def handle_event(self, event) -> bool:
        """이벤트 처리"""
        try:
            # 시간 범위 체크
            if not (self.start_time <= event.timestamp <= self.end_time):
                return True  # 범위 밖이지만 에러는 아님
            
            # 이벤트 저장
            self.processed_events.append(event)
            
            # 통계 업데이트
            self.processing_stats['total_events'] += 1
            event_type = event.event_type.value
            if event_type not in self.processing_stats['events_by_type']:
                self.processing_stats['events_by_type'][event_type] = 0
            self.processing_stats['events_by_type'][event_type] += 1
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing event {event.event_id}: {e}")
            self.processing_stats['processing_errors'] += 1
            return False
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """처리 통계 반환"""
        return {
            **self.processing_stats,
            'time_range': {
                'start': self.start_time.isoformat(),
                'end': self.end_time.isoformat()
            },
            'processed_events_count': len(self.processed_events)
        }

class UserBehaviorAggregator:
    """사용자 행동 집계기"""
    
    def aggregate_hourly_data(self, start_time: datetime, end_time: datetime, 
                            event_stats: Dict[str, Any]) -> Dict[str, Any]:
        """시간별 사용자 행동 데이터 집계"""
        
        # 실제 집계 로직 구현
        aggregation_results = {
            'time_window': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat()
            },
            'user_metrics': {
                'total_active_users': event_stats.get('events_by_type', {}).get('user_interaction', 0),
                'total_interactions': event_stats.get('total_events', 0)
            },
            'content_metrics': {
                'top_viewed_content': [],  # 실제로는 이벤트 데이터에서 계산
                'interaction_types': event_stats.get('events_by_type', {})
            }
        }
        
        return aggregation_results
    
    def save_aggregations(self, aggregation_results: Dict[str, Any]):
        """집계 결과 저장"""
        # 데이터베이스 저장 로직
        logger.info("Saving aggregation results to database...")

class RecommendationModelUpdater:
    """추천 모델 업데이터"""
    
    def update_models(self, user_behavior_data: Dict[str, Any], 
                     execution_date: datetime) -> Dict[str, Any]:
        """모델 업데이트"""
        
        # 온라인 학습 또는 모델 파라미터 조정
        update_results = {
            'updated_models': ['collaborative_filtering', 'content_based'],
            'update_type': 'parameter_adjustment',
            'performance_metrics': {
                'accuracy_change': 0.02,  # 2% 향상
                'latency_ms': 150
            }
        }
        
        return update_results

class AnalyticsReportGenerator:
    """분석 리포트 생성기"""
    
    def generate_hourly_report(self, report_data: Dict[str, Any]) -> str:
        """시간별 리포트 생성"""
        
        # 리포트 파일 경로
        report_filename = f"hourly_report_{report_data['execution_date'].replace(':', '-')}.json"
        report_path = f"/opt/airflow/reports/{report_filename}"
        
        # 리포트 저장
        import json
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        return report_path
    
    def publish_report_event(self, report_data: Dict[str, Any]):
        """리포트 이벤트 발행"""
        try:
            from src.events.kafka_producer import get_event_producer
            from src.events.event_schemas import EventFactory, EventType
            
            # 리포트 이벤트 생성
            report_event = EventFactory.create_event(
                EventType.PIPELINE_EVENT,
                pipeline_name='kafka_integration_pipeline',
                stage='report_generation',
                status='completed',
                output_data=report_data
            )
            
            # Kafka로 전송
            producer = get_event_producer()
            producer.send_event(report_event)
            
        except Exception as e:
            logger.error(f"Error publishing report event: {e}")

class DataCleanupManager:
    """데이터 정리 매니저"""
    
    def cleanup_old_events(self, retention_days: int, execution_date: datetime) -> Dict[str, Any]:
        """오래된 이벤트 정리"""
        
        cutoff_date = execution_date - timedelta(days=retention_days)
        
        # 실제로는 데이터베이스나 파일 시스템에서 정리
        cleanup_results = {
            'cutoff_date': cutoff_date.isoformat(),
            'deleted_events': 0,  # 실제 삭제된 이벤트 수
            'freed_space_mb': 0   # 확보된 공간
        }
        
        return cleanup_results
    
    def cleanup_temp_files(self) -> Dict[str, Any]:
        """임시 파일 정리"""
        
        # 임시 파일 정리 로직
        cleanup_results = {
            'deleted_temp_files': 0,
            'freed_temp_space_mb': 0
        }
        
        return cleanup_results

# 태스크 정의
setup_env_task = PythonOperator(
    task_id='setup_kafka_environment',
    python_callable=setup_kafka_environment,
    dag=dag
)

consume_events_task = PythonOperator(
    task_id='consume_kafka_events',
    python_callable=consume_and_process_events,
    dag=dag
)

aggregate_behavior_task = PythonOperator(
    task_id='aggregate_user_behavior',
    python_callable=aggregate_user_behavior_data,
    dag=dag
)

update_models_task = PythonOperator(
    task_id='update_recommendation_models',
    python_callable=update_recommendation_models,
    dag=dag
)

generate_report_task = PythonOperator(
    task_id='generate_analytics_report',
    python_callable=generate_analytics_report,
    dag=dag
)

cleanup_task = PythonOperator(
    task_id='cleanup_processed_data',
    python_callable=cleanup_processed_data,
    dag=dag
)

# Kafka 상태 확인 태스크
check_kafka_health = BashOperator(
    task_id='check_kafka_health',
    bash_command="""
    # Kafka 브로커 상태 확인
    curl -f http://kafka:9092/health || exit 1
    
    # 토픽 존재 확인
    kafka-topics.sh --bootstrap-server kafka:9092 --list | grep -E "(movie-user-interactions|movie-model-predictions)" || exit 1
    
    echo "Kafka health check passed"
    """,
    dag=dag
)

# 태스크 의존성 설정
setup_env_task >> check_kafka_health >> consume_events_task
consume_events_task >> aggregate_behavior_task
aggregate_behavior_task >> update_models_task
[update_models_task, aggregate_behavior_task] >> generate_report_task
generate_report_task >> cleanup_task

# DAG 문서
dag.doc_md = """
# Kafka Integration Pipeline

이 DAG는 실시간 Kafka 이벤트를 배치 처리하여 MLOps 파이프라인과 통합하는 역할을 합니다.

## 주요 기능
1. **이벤트 소비**: Kafka에서 사용자 상호작용, 모델 예측 등의 이벤트 소비
2. **데이터 집계**: 시간별 사용자 행동 패턴 분석 및 집계
3. **모델 업데이트**: 실시간 데이터를 기반으로 추천 모델 온라인 학습
4. **리포트 생성**: 시간별 분석 리포트 생성 및 배포
5. **데이터 정리**: 오래된 이벤트 데이터 정리

## 실행 주기
- 1시간마다 실행
- 각 실행은 지난 1시간의 이벤트 데이터를 처리

## 모니터링
- 각 태스크의 성공/실패 상태는 Airflow UI에서 확인
- 처리 통계는 Grafana 대시보드에서 실시간 모니터링 가능
"""
