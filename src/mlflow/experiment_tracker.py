"""MLflow 실험 추적 시스템"""

import mlflow
import mlflow.pytorch
import mlflow.sklearn
import torch
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, List, Union
import logging
import os
import json
from datetime import datetime
import tempfile
import pickle

logger = logging.getLogger(__name__)


class MLflowExperimentTracker:
    """MLflow를 사용한 실험 추적 클래스"""
    
    def __init__(
        self,
        experiment_name: str,
        tracking_uri: Optional[str] = None,
        artifact_location: Optional[str] = None
    ):
        """
        Args:
            experiment_name: 실험 이름
            tracking_uri: MLflow 추적 서버 URI
            artifact_location: 아티팩트 저장 위치
        """
        self.experiment_name = experiment_name
        
        # MLflow 설정
        if tracking_uri:
            mlflow.set_tracking_uri(tracking_uri)
        
        # 실험 설정 또는 생성
        try:
            experiment = mlflow.get_experiment_by_name(experiment_name)
            if experiment is None:
                experiment_id = mlflow.create_experiment(
                    name=experiment_name,
                    artifact_location=artifact_location
                )
                logger.info(f"새 실험 생성: {experiment_name} (ID: {experiment_id})")
            else:
                experiment_id = experiment.experiment_id
                logger.info(f"기존 실험 사용: {experiment_name} (ID: {experiment_id})")
            
            mlflow.set_experiment(experiment_name)
            self.experiment_id = experiment_id
            
        except Exception as e:
            logger.error(f"MLflow 실험 설정 실패: {e}")
            raise
    
    def start_run(
        self,
        run_name: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> str:
        """새로운 실행 시작"""
        try:
            if run_name is None:
                run_name = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            run = mlflow.start_run(run_name=run_name)
            run_id = run.info.run_id
            
            # 기본 태그 설정
            default_tags = {
                "experiment": self.experiment_name,
                "timestamp": datetime.now().isoformat(),
                "user": os.getenv("USER", "unknown")
            }
            
            if tags:
                default_tags.update(tags)
            
            mlflow.set_tags(default_tags)
            
            logger.info(f"MLflow 실행 시작: {run_name} (ID: {run_id})")
            return run_id
            
        except Exception as e:
            logger.error(f"MLflow 실행 시작 실패: {e}")
            raise
    
    def log_params(self, params: Dict[str, Any]):
        """파라미터 로깅"""
        try:
            # MLflow는 string, int, float만 지원하므로 변환
            clean_params = {}
            for key, value in params.items():
                if isinstance(value, (str, int, float, bool)):
                    clean_params[key] = value
                elif isinstance(value, (list, tuple)):
                    clean_params[key] = str(value)
                elif isinstance(value, dict):
                    clean_params[key] = json.dumps(value)
                else:
                    clean_params[key] = str(value)
            
            mlflow.log_params(clean_params)
            logger.debug(f"파라미터 로깅: {len(clean_params)}개 항목")
            
        except Exception as e:
            logger.error(f"파라미터 로깅 실패: {e}")
    
    def log_metrics(
        self, 
        metrics: Dict[str, float], 
        step: Optional[int] = None
    ):
        """메트릭 로깅"""
        try:
            for key, value in metrics.items():
                if isinstance(value, (int, float, np.number)):
                    mlflow.log_metric(key, float(value), step=step)
                else:
                    logger.warning(f"메트릭 '{key}'은 숫자가 아닙니다: {type(value)}")
            
            logger.debug(f"메트릭 로깅: {len(metrics)}개 항목 (step: {step})")
            
        except Exception as e:
            logger.error(f"메트릭 로깅 실패: {e}")
    
    def log_model(
        self,
        model: Union[torch.nn.Module, object],
        model_name: str = "model",
        model_type: str = "pytorch",
        input_example: Optional[Any] = None,
        signature: Optional[Any] = None,
        **kwargs
    ):
        """모델 로깅"""
        try:
            if model_type == "pytorch" and isinstance(model, torch.nn.Module):
                mlflow.pytorch.log_model(
                    pytorch_model=model,
                    artifact_path=model_name,
                    input_example=input_example,
                    signature=signature,
                    **kwargs
                )
            elif model_type == "sklearn":
                mlflow.sklearn.log_model(
                    sk_model=model,
                    artifact_path=model_name,
                    input_example=input_example,
                    signature=signature,
                    **kwargs
                )
            else:
                # 범용 모델 로깅 (pickle 사용)
                with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as f:
                    pickle.dump(model, f)
                    temp_path = f.name
                
                mlflow.log_artifact(temp_path, f"{model_name}/model.pkl")
                os.unlink(temp_path)
            
            logger.info(f"모델 로깅 완료: {model_name} ({model_type})")
            
        except Exception as e:
            logger.error(f"모델 로깅 실패: {e}")
    
    def log_artifacts(
        self,
        artifacts: Dict[str, str],
        artifact_path: Optional[str] = None
    ):
        """아티팩트 로깅"""
        try:
            for name, file_path in artifacts.items():
                if os.path.exists(file_path):
                    if artifact_path:
                        mlflow.log_artifact(file_path, f"{artifact_path}/{name}")
                    else:
                        mlflow.log_artifact(file_path, name)
                else:
                    logger.warning(f"아티팩트 파일을 찾을 수 없습니다: {file_path}")
            
            logger.info(f"아티팩트 로깅: {len(artifacts)}개 파일")
            
        except Exception as e:
            logger.error(f"아티팩트 로깅 실패: {e}")
    
    def log_dataset_info(
        self,
        dataset_info: Dict[str, Any],
        prefix: str = "dataset"
    ):
        """데이터셋 정보 로깅"""
        try:
            # 데이터셋 정보를 파라미터와 메트릭으로 분리
            params = {}
            metrics = {}
            
            for key, value in dataset_info.items():
                param_key = f"{prefix}_{key}"
                
                if isinstance(value, (int, float, np.number)):
                    metrics[param_key] = float(value)
                else:
                    params[param_key] = str(value)
            
            if params:
                self.log_params(params)
            if metrics:
                self.log_metrics(metrics)
            
            logger.info(f"데이터셋 정보 로깅: {len(dataset_info)}개 항목")
            
        except Exception as e:
            logger.error(f"데이터셋 정보 로깅 실패: {e}")
    
    def log_training_history(
        self,
        history: Dict[str, List[float]],
        prefix: str = ""
    ):
        """훈련 기록 로깅"""
        try:
            # 각 에포크별로 메트릭 로깅
            epochs = history.get('epochs', range(len(list(history.values())[0])))
            
            for epoch in epochs:
                epoch_metrics = {}
                
                for metric_name, values in history.items():
                    if metric_name != 'epochs' and epoch - 1 < len(values):
                        key = f"{prefix}{metric_name}" if prefix else metric_name
                        epoch_metrics[key] = values[epoch - 1]
                
                if epoch_metrics:
                    self.log_metrics(epoch_metrics, step=epoch)
            
            # 최종 메트릭도 로깅
            final_metrics = {}
            for metric_name, values in history.items():
                if metric_name != 'epochs' and values:
                    key = f"final_{prefix}{metric_name}" if prefix else f"final_{metric_name}"
                    final_metrics[key] = values[-1]
            
            if final_metrics:
                self.log_metrics(final_metrics)
            
            logger.info(f"훈련 기록 로깅: {len(history)}개 메트릭, {len(epochs)}개 에포크")
            
        except Exception as e:
            logger.error(f"훈련 기록 로깅 실패: {e}")
    
    def log_predictions(
        self,
        predictions: np.ndarray,
        actuals: np.ndarray,
        sample_size: int = 1000
    ):
        """예측 결과 로깅 및 분석"""
        try:
            # 샘플링 (너무 큰 데이터는 일부만 저장)
            if len(predictions) > sample_size:
                indices = np.random.choice(len(predictions), sample_size, replace=False)
                pred_sample = predictions[indices]
                actual_sample = actuals[indices]
            else:
                pred_sample = predictions
                actual_sample = actuals
            
            # 예측 vs 실제값 데이터프레임 생성
            df = pd.DataFrame({
                'prediction': pred_sample,
                'actual': actual_sample,
                'error': pred_sample - actual_sample,
                'abs_error': np.abs(pred_sample - actual_sample)
            })
            
            # CSV로 저장 후 아티팩트로 로깅
            with tempfile.NamedTemporaryFile(suffix='.csv', delete=False, mode='w') as f:
                df.to_csv(f.name, index=False)
                mlflow.log_artifact(f.name, "predictions.csv")
                temp_path = f.name
            
            os.unlink(temp_path)
            
            # 예측 통계 로깅
            prediction_stats = {
                'pred_mean': float(np.mean(pred_sample)),
                'pred_std': float(np.std(pred_sample)),
                'actual_mean': float(np.mean(actual_sample)),
                'actual_std': float(np.std(actual_sample)),
                'mean_error': float(np.mean(pred_sample - actual_sample)),
                'mean_abs_error': float(np.mean(np.abs(pred_sample - actual_sample))),
                'correlation': float(np.corrcoef(pred_sample, actual_sample)[0, 1])
            }
            
            self.log_metrics(prediction_stats)
            
            logger.info(f"예측 결과 로깅: {len(pred_sample)}개 샘플")
            
        except Exception as e:
            logger.error(f"예측 결과 로깅 실패: {e}")
    
    def log_feature_importance(
        self,
        feature_names: List[str],
        importance_scores: List[float],
        importance_type: str = "feature_importance"
    ):
        """피처 중요도 로깅"""
        try:
            # 피처 중요도 데이터프레임 생성
            df = pd.DataFrame({
                'feature': feature_names,
                'importance': importance_scores
            }).sort_values('importance', ascending=False)
            
            # CSV로 저장 후 아티팩트로 로깅
            with tempfile.NamedTemporaryFile(suffix='.csv', delete=False, mode='w') as f:
                df.to_csv(f.name, index=False)
                mlflow.log_artifact(f.name, f"{importance_type}.csv")
                temp_path = f.name
            
            os.unlink(temp_path)
            
            # 상위 피처들을 메트릭으로 로깅
            top_features = df.head(10)
            for _, row in top_features.iterrows():
                metric_name = f"{importance_type}_{row['feature']}"
                self.log_metrics({metric_name: row['importance']})
            
            logger.info(f"피처 중요도 로깅: {len(feature_names)}개 피처")
            
        except Exception as e:
            logger.error(f"피처 중요도 로깅 실패: {e}")
    
    def end_run(self, status: str = "FINISHED"):
        """실행 종료"""
        try:
            mlflow.end_run(status=status)
            logger.info(f"MLflow 실행 종료: {status}")
            
        except Exception as e:
            logger.error(f"MLflow 실행 종료 실패: {e}")
    
    def get_best_run(
        self,
        metric_name: str,
        ascending: bool = False
    ) -> Optional[Dict[str, Any]]:
        """최고 성능 실행 조회"""
        try:
            runs = mlflow.search_runs(
                experiment_ids=[self.experiment_id],
                order_by=[f"metrics.{metric_name} {'ASC' if ascending else 'DESC'}"],
                max_results=1
            )
            
            if not runs.empty:
                best_run = runs.iloc[0].to_dict()
                logger.info(f"최고 실행 조회: {best_run['run_id']} ({metric_name}: {best_run.get(f'metrics.{metric_name}', 'N/A')})")
                return best_run
            else:
                logger.warning("실행 기록을 찾을 수 없습니다")
                return None
                
        except Exception as e:
            logger.error(f"최고 실행 조회 실패: {e}")
            return None
    
    def compare_runs(
        self,
        run_ids: List[str],
        metrics: List[str]
    ) -> pd.DataFrame:
        """실행 비교"""
        try:
            runs_data = []
            
            for run_id in run_ids:
                run = mlflow.get_run(run_id)
                run_data = {
                    'run_id': run_id,
                    'run_name': run.data.tags.get('mlflow.runName', 'Unknown'),
                    'status': run.info.status,
                    'start_time': run.info.start_time,
                    'end_time': run.info.end_time
                }
                
                # 요청된 메트릭 추가
                for metric in metrics:
                    run_data[metric] = run.data.metrics.get(metric, None)
                
                runs_data.append(run_data)
            
            comparison_df = pd.DataFrame(runs_data)
            logger.info(f"실행 비교: {len(run_ids)}개 실행, {len(metrics)}개 메트릭")
            
            return comparison_df
            
        except Exception as e:
            logger.error(f"실행 비교 실패: {e}")
            return pd.DataFrame()


# 컨텍스트 매니저를 위한 래퍼 클래스
class MLflowRunContext:
    """MLflow 실행을 위한 컨텍스트 매니저"""
    
    def __init__(
        self,
        tracker: MLflowExperimentTracker,
        run_name: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None
    ):
        self.tracker = tracker
        self.run_name = run_name
        self.tags = tags
        self.run_id = None
    
    def __enter__(self):
        self.run_id = self.tracker.start_run(self.run_name, self.tags)
        return self.tracker
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            logger.error(f"실행 중 오류 발생: {exc_type.__name__}: {exc_val}")
            self.tracker.end_run(status="FAILED")
        else:
            self.tracker.end_run(status="FINISHED")


def create_experiment_tracker(
    experiment_name: str,
    tracking_uri: Optional[str] = None
) -> MLflowExperimentTracker:
    """실험 추적기 생성 헬퍼 함수"""
    return MLflowExperimentTracker(
        experiment_name=experiment_name,
        tracking_uri=tracking_uri
    )


# 사용 예제
if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)
    
    # 실험 추적기 생성
    tracker = create_experiment_tracker("test_experiment")
    
    # 컨텍스트 매니저 사용 예제
    with MLflowRunContext(tracker, "test_run", {"model": "pytorch", "version": "1.0"}) as mlf:
        # 파라미터 로깅
        mlf.log_params({
            "learning_rate": 0.001,
            "batch_size": 32,
            "epochs": 10
        })
        
        # 가상 훈련 루프
        for epoch in range(3):
            # 가상 메트릭
            train_loss = 1.0 - epoch * 0.1
            val_loss = 1.1 - epoch * 0.08
            
            mlf.log_metrics({
                "train_loss": train_loss,
                "val_loss": val_loss
            }, step=epoch)
        
        # 가상 예측 결과
        predictions = np.random.randn(100)
        actuals = predictions + np.random.randn(100) * 0.1
        mlf.log_predictions(predictions, actuals)
    
    print("MLflow 실험 추적 테스트 완료!")
