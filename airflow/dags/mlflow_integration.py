"""Airflow DAG with MLflow integration for movie recommendation pipeline"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago
import logging
import os
import sys

# 프로젝트 경로를 Python path에 추가
sys.path.append('/app')
sys.path.append('/app/src')

logger = logging.getLogger(__name__)

# 기본 DAG 설정
default_args = {
    'owner': 'movie-mlops',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# DAG 정의
dag = DAG(
    'mlflow_integration_pipeline',
    default_args=default_args,
    description='Movie recommendation pipeline with MLflow integration',
    schedule_interval=timedelta(days=1),  # 매일 실행
    catchup=False,
    tags=['mlflow', 'pytorch', 'movie-recommendation'],
)


def setup_mlflow_experiment(**context):
    """MLflow 실험 설정"""
    try:
        from src.mlflow.experiment_tracker import create_experiment_tracker
        
        # 실험 추적기 생성
        experiment_name = "movie_recommendation_pipeline"
        tracker = create_experiment_tracker(experiment_name)
        
        logger.info(f"MLflow 실험 설정 완료: {experiment_name}")
        
        # 실험 ID를 XCom에 저장하여 다른 태스크에서 사용
        context['task_instance'].xcom_push(
            key='experiment_name', 
            value=experiment_name
        )
        
        return experiment_name
        
    except Exception as e:
        logger.error(f"MLflow 실험 설정 실패: {e}")
        raise


def train_pytorch_model_with_mlflow(**context):
    """PyTorch 모델 훈련 및 MLflow 로깅"""
    try:
        from src.mlflow.experiment_tracker import create_experiment_tracker, MLflowRunContext
        from src.models.pytorch.training import train_pytorch_model
        import torch
        
        # 실험 이름 가져오기
        experiment_name = context['task_instance'].xcom_pull(
            task_ids='setup_mlflow_experiment',
            key='experiment_name'
        )
        
        if not experiment_name:
            experiment_name = "movie_recommendation_pipeline"
        
        # 실험 추적기 생성
        tracker = create_experiment_tracker(experiment_name)
        
        # 훈련 설정
        training_config = {
            'batch_size': 256,
            'num_epochs': 20,
            'learning_rate': 0.001,
            'optimizer_type': 'adam',
            'early_stopping_patience': 5
        }
        
        model_config = {
            'embedding_dim': 64,
            'hidden_dims': [128, 64, 32],
            'dropout_rate': 0.3
        }
        
        # MLflow 실행 시작
        run_name = f"pytorch_training_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        tags = {
            'model_type': 'pytorch',
            'pipeline': 'airflow',
            'environment': 'production'
        }
        
        with MLflowRunContext(tracker, run_name, tags) as mlf:
            # 훈련 파라미터 로깅
            all_params = {**training_config, **model_config}
            mlf.log_params(all_params)
            
            # 시스템 정보 로깅
            system_info = {
                'pytorch_version': torch.__version__,
                'cuda_available': torch.cuda.is_available(),
                'device_count': torch.cuda.device_count() if torch.cuda.is_available() else 0
            }
            mlf.log_params(system_info)
            
            # 모델 훈련
            model, history = train_pytorch_model(
                data_path="data/processed/watch_log.csv",
                model_type="neural_cf",
                model_config=model_config,
                training_config=training_config,
                experiment_name=f"airflow_{experiment_name}"
            )
            
            # 훈련 기록 로깅
            mlf.log_training_history(history)
            
            # 모델 로깅
            mlf.log_model(
                model=model,
                model_name="pytorch_movie_recommender",
                model_type="pytorch"
            )
            
            # 최종 성능 메트릭
            final_metrics = {
                'final_train_loss': history['train_loss'][-1],
                'best_train_loss': min(history['train_loss']),
                'total_epochs': len(history['train_loss'])
            }
            
            if history['val_loss']:
                final_metrics.update({
                    'final_val_loss': history['val_loss'][-1],
                    'best_val_loss': min(history['val_loss'])
                })
            
            mlf.log_metrics(final_metrics)
            
            # 모델 URI를 XCom에 저장
            run_id = mlf._tracker.client.get_run(mlf._tracker.client.get_experiment_by_name(experiment_name).experiment_id).info.run_id
            model_uri = f"runs:/{run_id}/pytorch_movie_recommender"
            
            context['task_instance'].xcom_push(
                key='model_uri',
                value=model_uri
            )
            context['task_instance'].xcom_push(
                key='run_id',
                value=run_id
            )
            
            logger.info(f"PyTorch 모델 훈련 완료: {model_uri}")
            
            return {
                'model_uri': model_uri,
                'run_id': run_id,
                'final_metrics': final_metrics
            }
        
    except Exception as e:
        logger.error(f"PyTorch 모델 훈련 실패: {e}")
        raise


def register_model_to_registry(**context):
    """훈련된 모델을 MLflow 레지스트리에 등록"""
    try:
        from src.mlflow.model_registry import get_model_registry
        
        # 모델 URI 가져오기
        model_uri = context['task_instance'].xcom_pull(
            task_ids='train_pytorch_model',
            key='model_uri'
        )
        
        run_id = context['task_instance'].xcom_pull(
            task_ids='train_pytorch_model',
            key='run_id'
        )
        
        if not model_uri:
            raise ValueError("모델 URI를 찾을 수 없습니다")
        
        # 모델 레지스트리 생성
        registry = get_model_registry()
        
        # 모델 등록
        model_name = "movie_recommender_pytorch"
        description = f"PyTorch 영화 추천 모델 - Airflow 파이프라인 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"
        
        tags = {
            'pipeline': 'airflow',
            'model_framework': 'pytorch',
            'training_date': datetime.now().strftime('%Y-%m-%d'),
            'run_id': run_id
        }
        
        model_version_info = registry.register_model(
            model_uri=model_uri,
            model_name=model_name,
            description=description,
            tags=tags
        )
        
        logger.info(f"모델 레지스트리 등록 완료: {model_name} v{model_version_info['version']}")
        
        # 모델 버전 정보를 XCom에 저장
        context['task_instance'].xcom_push(
            key='registered_model_name',
            value=model_name
        )
        context['task_instance'].xcom_push(
            key='registered_model_version',
            value=model_version_info['version']
        )
        
        return model_version_info
        
    except Exception as e:
        logger.error(f"모델 레지스트리 등록 실패: {e}")
        raise


def evaluate_model_performance(**context):
    """등록된 모델 성능 평가"""
    try:
        from src.mlflow.model_registry import get_model_registry
        from src.models.pytorch.data_loader import prepare_data_from_watch_log, create_data_loaders
        from src.models.pytorch.inference import MovieRecommenderInference
        import torch
        import numpy as np
        from sklearn.metrics import mean_squared_error, mean_absolute_error
        
        # 등록된 모델 정보 가져오기
        model_name = context['task_instance'].xcom_pull(
            task_ids='register_model',
            key='registered_model_name'
        )
        
        model_version = context['task_instance'].xcom_pull(
            task_ids='register_model', 
            key='registered_model_version'
        )
        
        if not model_name or not model_version:
            raise ValueError("등록된 모델 정보를 찾을 수 없습니다")
        
        # 레지스트리에서 모델 로드
        registry = get_model_registry()
        model = registry.load_model(model_name, version=model_version)
        
        # 테스트 데이터 준비
        train_df, val_df, test_df = prepare_data_from_watch_log(
            "data/processed/watch_log.csv"
        )
        
        data_loaders = create_data_loaders(
            train_df=train_df,
            test_df=test_df,
            batch_size=256
        )
        
        # 모델 평가
        model.eval()
        predictions = []
        actuals = []
        
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        model.to(device)
        
        with torch.no_grad():
            for batch in data_loaders['test']:
                user_ids = batch['user_id'].to(device)
                movie_ids = batch['movie_id'].to(device)
                ratings = batch['rating'].to(device)
                
                outputs = model(user_ids, movie_ids)
                
                predictions.extend(outputs.cpu().numpy())
                actuals.extend(ratings.cpu().numpy())
        
        predictions = np.array(predictions)
        actuals = np.array(actuals)
        
        # 성능 메트릭 계산
        rmse = np.sqrt(mean_squared_error(actuals, predictions))
        mae = mean_absolute_error(actuals, predictions)
        mse = mean_squared_error(actuals, predictions)
        
        evaluation_metrics = {
            'test_rmse': rmse,
            'test_mae': mae,
            'test_mse': mse,
            'test_samples': len(predictions)
        }
        
        # MLflow에 평가 결과 로깅
        from src.mlflow.experiment_tracker import create_experiment_tracker
        
        experiment_name = context['task_instance'].xcom_pull(
            task_ids='setup_mlflow_experiment',
            key='experiment_name'
        )
        
        tracker = create_experiment_tracker(experiment_name)
        
        # 평가 실행 시작
        run_name = f"model_evaluation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        tags = {
            'stage': 'evaluation',
            'model_name': model_name,
            'model_version': str(model_version)
        }
        
        with tracker.start_run(run_name, tags):
            tracker.log_metrics(evaluation_metrics)
            tracker.log_predictions(predictions, actuals)
        
        logger.info(f"모델 평가 완료 - RMSE: {rmse:.4f}, MAE: {mae:.4f}")
        
        # 성능 기준 확인 (예: RMSE < 1.0)
        performance_threshold = 1.0
        
        context['task_instance'].xcom_push(
            key='evaluation_metrics',
            value=evaluation_metrics
        )
        context['task_instance'].xcom_push(
            key='performance_passed',
            value=rmse < performance_threshold
        )
        
        return evaluation_metrics
        
    except Exception as e:
        logger.error(f"모델 평가 실패: {e}")
        raise


def decide_model_promotion(**context):
    """모델 프로덕션 승격 여부 결정"""
    try:
        from src.mlflow.model_registry import get_model_registry
        
        # 평가 결과 가져오기
        performance_passed = context['task_instance'].xcom_pull(
            task_ids='evaluate_model',
            key='performance_passed'
        )
        
        evaluation_metrics = context['task_instance'].xcom_pull(
            task_ids='evaluate_model',
            key='evaluation_metrics'
        )
        
        model_name = context['task_instance'].xcom_pull(
            task_ids='register_model',
            key='registered_model_name'
        )
        
        model_version = context['task_instance'].xcom_pull(
            task_ids='register_model',
            key='registered_model_version'
        )
        
        registry = get_model_registry()
        
        if performance_passed:
            # 성능 기준을 통과한 경우 Staging으로 승격
            success = registry.transition_model_stage(
                model_name=model_name,
                version=model_version,
                stage='Staging',
                description=f"자동 승격 - 성능 기준 통과 (RMSE: {evaluation_metrics['test_rmse']:.4f})"
            )
            
            if success:
                logger.info(f"모델 Staging 승격 완료: {model_name} v{model_version}")
                
                # 추가 검증 로직이 있다면 여기에 추가
                # 예: A/B 테스트, 추가 검증 등
                
                # 모든 검증을 통과하면 Production으로 승격
                prod_success = registry.promote_model_to_production(
                    model_name=model_name,
                    version=model_version,
                    description="자동 프로덕션 승격 - 모든 검증 통과"
                )
                
                if prod_success:
                    logger.info(f"모델 Production 승격 완료: {model_name} v{model_version}")
                    promotion_status = "production"
                else:
                    logger.warning(f"모델 Production 승격 실패: {model_name} v{model_version}")
                    promotion_status = "staging"
            else:
                logger.warning(f"모델 Staging 승격 실패: {model_name} v{model_version}")
                promotion_status = "none"
        else:
            logger.info(f"모델 성능 기준 미달: {model_name} v{model_version}")
            promotion_status = "none"
        
        context['task_instance'].xcom_push(
            key='promotion_status',
            value=promotion_status
        )
        
        return {
            'model_name': model_name,
            'model_version': model_version,
            'promotion_status': promotion_status,
            'performance_passed': performance_passed
        }
        
    except Exception as e:
        logger.error(f"모델 승격 결정 실패: {e}")
        raise


def cleanup_old_models(**context):
    """오래된 모델 버전 정리"""
    try:
        from src.mlflow.model_registry import get_model_registry
        
        registry = get_model_registry()
        
        # 등록된 모든 모델 조회
        models = registry.list_models()
        
        for model in models:
            model_name = model['name']
            
            # 각 모델의 모든 버전 조회
            versions = registry.client.search_model_versions(f"name='{model_name}'")
            
            # 버전을 생성 시간 기준으로 정렬 (최신 -> 오래된 순)
            versions_sorted = sorted(
                versions, 
                key=lambda x: x.creation_timestamp, 
                reverse=True
            )
            
            # Production, Staging 단계가 아닌 오래된 버전들 (5개 초과) 아카이브
            keep_count = 5
            archived_count = 0
            
            for i, version in enumerate(versions_sorted):
                if (i >= keep_count and 
                    version.current_stage in ['None'] and
                    version.creation_timestamp < (datetime.now() - timedelta(days=7)).timestamp() * 1000):
                    
                    # 아카이브로 이동
                    registry.transition_model_stage(
                        model_name=model_name,
                        version=version.version,
                        stage='Archived',
                        description="자동 아카이브 - 오래된 버전"
                    )
                    archived_count += 1
            
            if archived_count > 0:
                logger.info(f"모델 {model_name}: {archived_count}개 버전 아카이브")
        
        logger.info("오래된 모델 정리 완료")
        
    except Exception as e:
        logger.error(f"모델 정리 실패: {e}")
        # 정리 실패는 치명적이지 않으므로 예외를 발생시키지 않음
        pass


def send_notification(**context):
    """파이프라인 완료 알림"""
    try:
        promotion_status = context['task_instance'].xcom_pull(
            task_ids='decide_promotion',
            key='promotion_status'
        )
        
        evaluation_metrics = context['task_instance'].xcom_pull(
            task_ids='evaluate_model',
            key='evaluation_metrics'
        )
        
        model_name = context['task_instance'].xcom_pull(
            task_ids='register_model',
            key='registered_model_name'
        )
        
        model_version = context['task_instance'].xcom_pull(
            task_ids='register_model',
            key='registered_model_version'
        )
        
        # 간단한 로그 기반 알림 (실제 환경에서는 슬랙, 이메일 등 사용)
        message = f"""
=== 영화 추천 모델 파이프라인 완료 ===
모델: {model_name} v{model_version}
승격 상태: {promotion_status}
성능 메트릭:
- RMSE: {evaluation_metrics['test_rmse']:.4f}
- MAE: {evaluation_metrics['test_mae']:.4f}
- 테스트 샘플: {evaluation_metrics['test_samples']}
실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        logger.info(message)
        
        # 성능이 좋고 프로덕션에 배포된 경우 특별 알림
        if promotion_status == "production":
            logger.info("🎉 새로운 모델이 프로덕션에 배포되었습니다!")
        
        return message
        
    except Exception as e:
        logger.error(f"알림 전송 실패: {e}")
        pass


# 태스크 정의
setup_experiment_task = PythonOperator(
    task_id='setup_mlflow_experiment',
    python_callable=setup_mlflow_experiment,
    dag=dag,
)

train_model_task = PythonOperator(
    task_id='train_pytorch_model',
    python_callable=train_pytorch_model_with_mlflow,
    dag=dag,
)

register_model_task = PythonOperator(
    task_id='register_model',
    python_callable=register_model_to_registry,
    dag=dag,
)

evaluate_model_task = PythonOperator(
    task_id='evaluate_model',
    python_callable=evaluate_model_performance,
    dag=dag,
)

decide_promotion_task = PythonOperator(
    task_id='decide_promotion',
    python_callable=decide_model_promotion,
    dag=dag,
)

cleanup_models_task = PythonOperator(
    task_id='cleanup_old_models',
    python_callable=cleanup_old_models,
    dag=dag,
)

notification_task = PythonOperator(
    task_id='send_notification',
    python_callable=send_notification,
    dag=dag,
)

# 추가 유틸리티 태스크들
check_data_quality_task = BashOperator(
    task_id='check_data_quality',
    bash_command='python -c "import pandas as pd; df=pd.read_csv(\\"data/processed/watch_log.csv\\"); print(f\\"Data quality check: {len(df)} rows, {df.isnull().sum().sum()} nulls\\")"',
    dag=dag,
)

# 태스크 의존성 설정
setup_experiment_task >> check_data_quality_task >> train_model_task
train_model_task >> register_model_task >> evaluate_model_task
evaluate_model_task >> decide_promotion_task
decide_promotion_task >> [cleanup_models_task, notification_task]
