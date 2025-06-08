"""
Movie Training Pipeline DAG
기존 my-mlops의 모델 훈련 로직을 Airflow DAG로 구현
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta
import sys
import os
import logging
import pickle

# 경로 설정
sys.path.append('/app')
sys.path.append('/app/src')

# 기본 설정
default_args = {
    'owner': 'movie-mlops-team',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# DAG 정의
dag = DAG(
    'movie_training_pipeline',
    default_args=default_args,
    description='영화 추천 모델 훈련 파이프라인 (기존 my-mlops 로직)',
    schedule_interval=timedelta(weeks=1),  # 주 1회 실행
    catchup=False,
    max_active_runs=1,
    tags=['movie', 'training', 'ml', 'model']
)

def prepare_training_data(**context):
    """
    훈련용 데이터셋 준비
    기존 dataset 로직 사용
    """
    try:
        from src.dataset.watch_log import get_datasets
        from src.utils.utils import init_seed
        
        # 시드 초기화
        init_seed()
        
        # 데이터셋 로딩
        train_dataset, val_dataset, test_dataset = get_datasets()
        
        logging.info(f"데이터셋 준비 완료:")
        logging.info(f"  훈련 데이터: {len(train_dataset.features)}개")
        logging.info(f"  검증 데이터: {len(val_dataset.features)}개")
        logging.info(f"  테스트 데이터: {len(test_dataset.features)}개")
        logging.info(f"  피처 차원: {train_dataset.features_dim}")
        logging.info(f"  클래스 수: {train_dataset.num_classes}")
        
        # 데이터셋 정보를 다음 태스크로 전달
        return {
            "train_size": len(train_dataset.features),
            "val_size": len(val_dataset.features),
            "test_size": len(test_dataset.features),
            "features_dim": train_dataset.features_dim,
            "num_classes": train_dataset.num_classes,
            "preparation_date": datetime.now().isoformat()
        }
        
    except Exception as e:
        logging.error(f"데이터셋 준비 실패: {e}")
        raise

def train_movie_model(**context):
    """
    영화 추천 모델 훈련
    기존 main.py의 훈련 로직 사용
    """
    try:
        from src.dataset.watch_log import get_datasets
        from src.dataset.data_loader import SimpleDataLoader
        from src.models.legacy.movie_predictor import MoviePredictor
        from src.training.train import train
        from src.evaluation.evaluate import evaluate
        from src.utils.utils import init_seed
        
        # 시드 초기화
        init_seed()
        
        # 이전 태스크에서 데이터셋 정보 가져오기
        ti = context['ti']
        dataset_info = ti.xcom_pull(task_ids='prepare_training_data')
        
        if not dataset_info:
            raise ValueError("이전 태스크에서 데이터셋 정보를 가져올 수 없습니다.")
        
        # 데이터셋 로딩
        train_dataset, val_dataset, test_dataset = get_datasets()
        
        # 데이터 로더 생성
        train_loader = SimpleDataLoader(
            train_dataset.features, 
            train_dataset.labels, 
            batch_size=64, 
            shuffle=True
        )
        val_loader = SimpleDataLoader(
            val_dataset.features, 
            val_dataset.labels, 
            batch_size=64, 
            shuffle=False
        )
        
        # 모델 초기화
        model_params = {
            "input_dim": train_dataset.features_dim,
            "num_classes": train_dataset.num_classes,
            "hidden_dim": 64
        }
        model = MoviePredictor(**model_params)
        
        logging.info(f"모델 훈련 시작: {model_params}")
        
        # 훈련 루프
        num_epochs = 20
        best_val_loss = float('inf')
        training_history = []
        
        for epoch in range(num_epochs):
            # 훈련
            train_loss = train(model, train_loader)
            
            # 검증
            val_loss, _ = evaluate(model, val_loader)
            
            # 로그 기록
            epoch_info = {
                "epoch": epoch + 1,
                "train_loss": float(train_loss),
                "val_loss": float(val_loss),
                "val_train_diff": float(val_loss - train_loss)
            }
            training_history.append(epoch_info)
            
            # 최적 모델 체크
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                best_epoch = epoch + 1
            
            if (epoch + 1) % 5 == 0 or epoch == 0:
                logging.info(
                    f"Epoch {epoch + 1}/{num_epochs}: "
                    f"Train Loss: {train_loss:.4f}, "
                    f"Val Loss: {val_loss:.4f}, "
                    f"Diff: {val_loss - train_loss:.4f}"
                )
        
        logging.info(f"훈련 완료! 최적 검증 손실: {best_val_loss:.4f} (Epoch {best_epoch})")
        
        # 모델 저장
        model_dir = "/app/models/trained"
        os.makedirs(model_dir, exist_ok=True)
        
        model_filename = f"movie_predictor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
        model_path = os.path.join(model_dir, model_filename)
        
        # NumPy 모델 저장 (가중치 저장)
        model_state = {
            "weights1": model.weights1,
            "bias1": model.bias1,
            "weights2": model.weights2,
            "bias2": model.bias2,
            "model_params": model_params,
            "training_history": training_history,
            "best_val_loss": best_val_loss,
            "best_epoch": best_epoch,
            "training_date": datetime.now().isoformat()
        }
        
        with open(model_path, 'wb') as f:
            pickle.dump(model_state, f)
        
        logging.info(f"모델 저장 완료: {model_path}")
        
        return {
            "model_path": model_path,
            "best_val_loss": best_val_loss,
            "best_epoch": best_epoch,
            "total_epochs": num_epochs,
            "final_train_loss": float(training_history[-1]["train_loss"]),
            "final_val_loss": float(training_history[-1]["val_loss"]),
            "training_history": training_history,
            "training_date": datetime.now().isoformat()
        }
        
    except Exception as e:
        logging.error(f"모델 훈련 실패: {e}")
        raise

def evaluate_trained_model(**context):
    """
    훈련된 모델 평가
    """
    try:
        from src.dataset.watch_log import get_datasets
        from src.dataset.data_loader import SimpleDataLoader
        from src.models.legacy.movie_predictor import MoviePredictor
        from src.evaluation.evaluate import evaluate
        import pickle
        
        # 이전 태스크에서 훈련 정보 가져오기
        ti = context['ti']
        training_info = ti.xcom_pull(task_ids='train_movie_model')
        
        if not training_info:
            raise ValueError("이전 태스크에서 훈련 정보를 가져올 수 없습니다.")
        
        # 훈련된 모델 로드
        model_path = training_info['model_path']
        with open(model_path, 'rb') as f:
            model_state = pickle.load(f)
        
        # 모델 재구성
        model_params = model_state['model_params']
        model = MoviePredictor(**model_params)
        
        # 가중치 복원
        model.weights1 = model_state['weights1']
        model.bias1 = model_state['bias1']
        model.weights2 = model_state['weights2']
        model.bias2 = model_state['bias2']
        
        # 테스트 데이터셋 로딩
        train_dataset, val_dataset, test_dataset = get_datasets()
        test_loader = SimpleDataLoader(
            test_dataset.features, 
            test_dataset.labels, 
            batch_size=64, 
            shuffle=False
        )
        
        # 테스트 평가
        test_loss, predictions = evaluate(model, test_loader)
        
        # 추천 결과 샘플 생성
        sample_predictions = predictions[:10]  # 상위 10개
        sample_content_ids = [train_dataset.decode_content_id(idx) for idx in sample_predictions]
        
        logging.info(f"모델 평가 완료: 테스트 손실 {test_loss:.4f}")
        logging.info(f"샘플 추천 결과: {sample_content_ids}")
        
        return {
            "test_loss": float(test_loss),
            "sample_predictions": sample_content_ids,
            "total_predictions": len(predictions),
            "model_path": model_path,
            "evaluation_date": datetime.now().isoformat()
        }
        
    except Exception as e:
        logging.error(f"모델 평가 실패: {e}")
        raise

def register_model_to_mlflow(**context):
    """
    훈련된 모델을 MLflow에 등록 (향후 구현)
    현재는 로그만 기록
    """
    try:
        # 이전 태스크에서 정보 가져오기
        ti = context['ti']
        training_info = ti.xcom_pull(task_ids='train_movie_model')
        evaluation_info = ti.xcom_pull(task_ids='evaluate_trained_model')
        
        if not training_info or not evaluation_info:
            raise ValueError("이전 태스크에서 정보를 가져올 수 없습니다.")
        
        # MLflow 등록 로직 (향후 구현)
        # 현재는 로그만 기록
        model_info = {
            "model_name": "movie_predictor",
            "model_version": datetime.now().strftime('%Y%m%d_%H%M%S'),
            "framework": "numpy",
            "best_val_loss": training_info['best_val_loss'],
            "test_loss": evaluation_info['test_loss'],
            "model_path": training_info['model_path'],
            "registration_date": datetime.now().isoformat()
        }
        
        logging.info(f"모델 등록 정보: {model_info}")
        
        # 향후 MLflow 연동 시 실제 등록 로직 추가
        # mlflow.log_model(model, "model")
        # mlflow.log_metrics({"val_loss": best_val_loss, "test_loss": test_loss})
        
        return model_info
        
    except Exception as e:
        logging.error(f"모델 등록 실패: {e}")
        raise

# 태스크 정의
prepare_data_task = PythonOperator(
    task_id='prepare_training_data',
    python_callable=prepare_training_data,
    dag=dag,
    doc_md="""
    ## 훈련 데이터 준비
    
    기존 watch_log 데이터를 로드하고 훈련/검증/테스트 셋으로 분할합니다.
    
    **출력**: 데이터셋 통계 정보
    """
)

train_model_task = PythonOperator(
    task_id='train_movie_model',
    python_callable=train_movie_model,
    dag=dag,
    doc_md="""
    ## 영화 추천 모델 훈련
    
    NumPy 기반 신경망 모델을 훈련합니다.
    
    **입력**: 준비된 데이터셋
    **출력**: 훈련된 모델 파일 (.pkl)
    """
)

evaluate_model_task = PythonOperator(
    task_id='evaluate_trained_model',
    python_callable=evaluate_trained_model,
    dag=dag,
    doc_md="""
    ## 훈련된 모델 평가
    
    테스트 데이터셋으로 모델 성능을 평가합니다.
    
    **입력**: 훈련된 모델
    **출력**: 테스트 성능 지표
    """
)

register_model_task = PythonOperator(
    task_id='register_model_to_mlflow',
    python_callable=register_model_to_mlflow,
    dag=dag,
    doc_md="""
    ## 모델 등록
    
    훈련된 모델을 MLflow에 등록합니다 (향후 구현).
    
    **입력**: 훈련 및 평가 결과
    **출력**: 모델 등록 정보
    """
)

# 태스크 의존성 설정
prepare_data_task >> train_model_task >> evaluate_model_task >> register_model_task

# DAG 문서화
dag.doc_md = """
# Movie Training Pipeline

이 DAG는 기존 my-mlops 프로젝트의 모델 훈련 로직을 Airflow로 구현한 것입니다.

## 워크플로우

1. **prepare_training_data**: 훈련용 데이터셋 준비
2. **train_movie_model**: NumPy 기반 신경망 모델 훈련
3. **evaluate_trained_model**: 훈련된 모델 성능 평가
4. **register_model_to_mlflow**: MLflow에 모델 등록 (향후 구현)

## 모델 정보

- **프레임워크**: NumPy 기반 신경망
- **입력 차원**: 데이터셋에 따라 자동 결정
- **은닉층**: 64개 뉴런
- **출력**: 영화 클래스 확률

## 출력 파일

- 훈련된 모델: `/app/models/trained/movie_predictor_YYYYMMDD_HHMMSS.pkl`

## 실행 주기

주 1회 자동 실행됩니다.

## 의존성

이 DAG는 `movie_data_collection` DAG가 성공적으로 완료된 후에 실행되어야 합니다.
"""
