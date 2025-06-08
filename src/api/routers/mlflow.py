"""MLflow API 라우터"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
import logging
from pydantic import BaseModel
import pandas as pd

from src.mlflow.experiment_tracker import create_experiment_tracker
from src.mlflow.model_registry import get_model_registry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mlflow", tags=["mlflow"])


class ExperimentCreateRequest(BaseModel):
    """실험 생성 요청 모델"""
    name: str
    description: Optional[str] = None


class RunCreateRequest(BaseModel):
    """실행 생성 요청 모델"""
    experiment_name: str
    run_name: Optional[str] = None
    tags: Optional[Dict[str, str]] = None


class MetricsLogRequest(BaseModel):
    """메트릭 로깅 요청 모델"""
    run_id: str
    metrics: Dict[str, float]
    step: Optional[int] = None


class ParamsLogRequest(BaseModel):
    """파라미터 로깅 요청 모델"""
    run_id: str
    params: Dict[str, Any]


class ModelRegisterRequest(BaseModel):
    """모델 등록 요청 모델"""
    model_uri: str
    model_name: str
    description: Optional[str] = None
    tags: Optional[Dict[str, str]] = None


class ModelStageTransitionRequest(BaseModel):
    """모델 스테이지 변경 요청 모델"""
    model_name: str
    version: str
    stage: str
    description: Optional[str] = None


@router.get("/health")
async def mlflow_health_check():
    """MLflow 서비스 상태 확인"""
    try:
        # MLflow 서버 연결 테스트
        registry = get_model_registry()
        models = registry.list_models(max_results=1)
        
        return {
            "status": "healthy",
            "mlflow_server": "connected",
            "registry_accessible": True,
            "timestamp": pd.Timestamp.now().isoformat()
        }
    except Exception as e:
        logger.error(f"MLflow 상태 확인 실패: {e}")
        raise HTTPException(status_code=500, detail=f"MLflow 서비스 상태 확인 실패: {str(e)}")


@router.get("/experiments")
async def list_experiments(max_results: int = Query(100, description="최대 결과 수")):
    """실험 목록 조회"""
    try:
        import mlflow
        from mlflow.tracking import MlflowClient
        
        client = MlflowClient()
        experiments = client.list_experiments(max_results=max_results)
        
        experiments_data = []
        for exp in experiments:
            experiments_data.append({
                "experiment_id": exp.experiment_id,
                "name": exp.name,
                "artifact_location": exp.artifact_location,
                "lifecycle_stage": exp.lifecycle_stage,
                "creation_time": exp.creation_time,
                "last_update_time": exp.last_update_time,
                "tags": {tag.key: tag.value for tag in exp.tags}
            })
        
        return {
            "experiments": experiments_data,
            "count": len(experiments_data)
        }
        
    except Exception as e:
        logger.error(f"실험 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"실험 목록 조회 실패: {str(e)}")


@router.post("/experiments")
async def create_experiment(request: ExperimentCreateRequest):
    """새 실험 생성"""
    try:
        tracker = create_experiment_tracker(request.name)
        
        return {
            "experiment_id": tracker.experiment_id,
            "experiment_name": request.name,
            "description": request.description,
            "message": "실험이 성공적으로 생성되었습니다"
        }
        
    except Exception as e:
        logger.error(f"실험 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=f"실험 생성 실패: {str(e)}")


@router.get("/experiments/{experiment_name}/runs")
async def list_runs(
    experiment_name: str,
    max_results: int = Query(50, description="최대 결과 수"),
    order_by: str = Query("start_time DESC", description="정렬 기준")
):
    """특정 실험의 실행 목록 조회"""
    try:
        import mlflow
        
        # 실험 ID 조회
        experiment = mlflow.get_experiment_by_name(experiment_name)
        if not experiment:
            raise HTTPException(status_code=404, detail=f"실험을 찾을 수 없습니다: {experiment_name}")
        
        runs = mlflow.search_runs(
            experiment_ids=[experiment.experiment_id],
            max_results=max_results,
            order_by=[order_by]
        )
        
        if runs.empty:
            return {"runs": [], "count": 0}
        
        # DataFrame을 딕셔너리 형태로 변환
        runs_data = []
        for _, run in runs.iterrows():
            run_data = {
                "run_id": run["run_id"],
                "run_name": run.get("tags.mlflow.runName", "Unnamed"),
                "status": run["status"],
                "start_time": run["start_time"],
                "end_time": run["end_time"],
                "metrics": {k.replace("metrics.", ""): v for k, v in run.items() if k.startswith("metrics.")},
                "params": {k.replace("params.", ""): v for k, v in run.items() if k.startswith("params.")},
                "tags": {k.replace("tags.", ""): v for k, v in run.items() if k.startswith("tags.")}
            }
            runs_data.append(run_data)
        
        return {
            "runs": runs_data,
            "count": len(runs_data),
            "experiment_name": experiment_name
        }
        
    except Exception as e:
        logger.error(f"실행 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"실행 목록 조회 실패: {str(e)}")


@router.get("/runs/{run_id}")
async def get_run_details(run_id: str):
    """특정 실행의 상세 정보 조회"""
    try:
        from mlflow.tracking import MlflowClient
        
        client = MlflowClient()
        run = client.get_run(run_id)
        
        return {
            "run_id": run.info.run_id,
            "experiment_id": run.info.experiment_id,
            "status": run.info.status,
            "start_time": run.info.start_time,
            "end_time": run.info.end_time,
            "artifact_uri": run.info.artifact_uri,
            "lifecycle_stage": run.info.lifecycle_stage,
            "metrics": run.data.metrics,
            "params": run.data.params,
            "tags": run.data.tags
        }
        
    except Exception as e:
        logger.error(f"실행 상세 정보 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"실행 정보 조회 실패: {str(e)}")


@router.get("/models")
async def list_registered_models(max_results: int = Query(100, description="최대 결과 수")):
    """등록된 모델 목록 조회"""
    try:
        registry = get_model_registry()
        models = registry.list_models(max_results=max_results)
        
        return {
            "models": models,
            "count": len(models)
        }
        
    except Exception as e:
        logger.error(f"등록된 모델 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"모델 목록 조회 실패: {str(e)}")


@router.get("/models/{model_name}")
async def get_model_details(model_name: str):
    """특정 모델의 상세 정보 조회"""
    try:
        registry = get_model_registry()
        
        # 모델의 모든 버전 조회
        from mlflow.tracking import MlflowClient
        client = MlflowClient()
        
        versions = client.search_model_versions(f"name='{model_name}'")
        
        if not versions:
            raise HTTPException(status_code=404, detail=f"모델을 찾을 수 없습니다: {model_name}")
        
        # 각 스테이지별 최신 버전
        stage_versions = {}
        all_versions = []
        
        for version in versions:
            stage = version.current_stage
            if stage not in stage_versions:
                stage_versions[stage] = version
            
            all_versions.append({
                "version": version.version,
                "stage": version.current_stage,
                "status": version.status,
                "creation_timestamp": version.creation_timestamp,
                "last_updated_timestamp": version.last_updated_timestamp,
                "description": version.description,
                "run_id": version.run_id,
                "source": version.source
            })
        
        # 모델 메트릭 조회 (최신 Production 버전)
        production_metrics = {}
        if "Production" in stage_versions:
            production_metrics = registry.get_model_metrics(
                model_name, 
                version=stage_versions["Production"].version
            )
        
        return {
            "model_name": model_name,
            "versions": all_versions,
            "current_stages": {stage: v.version for stage, v in stage_versions.items()},
            "production_metrics": production_metrics,
            "total_versions": len(all_versions)
        }
        
    except Exception as e:
        logger.error(f"모델 상세 정보 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"모델 정보 조회 실패: {str(e)}")


@router.post("/models/register")
async def register_model(request: ModelRegisterRequest):
    """모델을 레지스트리에 등록"""
    try:
        registry = get_model_registry()
        
        model_version = registry.register_model(
            model_uri=request.model_uri,
            model_name=request.model_name,
            description=request.description,
            tags=request.tags
        )
        
        return {
            "message": "모델이 성공적으로 등록되었습니다",
            "model_version": model_version
        }
        
    except Exception as e:
        logger.error(f"모델 등록 실패: {e}")
        raise HTTPException(status_code=500, detail=f"모델 등록 실패: {str(e)}")


@router.post("/models/stage-transition")
async def transition_model_stage(request: ModelStageTransitionRequest):
    """모델 스테이지 변경"""
    try:
        registry = get_model_registry()
        
        success = registry.transition_model_stage(
            model_name=request.model_name,
            version=request.version,
            stage=request.stage,
            description=request.description
        )
        
        if success:
            return {
                "message": f"모델 스테이지가 성공적으로 변경되었습니다",
                "model_name": request.model_name,
                "version": request.version,
                "new_stage": request.stage
            }
        else:
            raise HTTPException(status_code=500, detail="모델 스테이지 변경에 실패했습니다")
        
    except Exception as e:
        logger.error(f"모델 스테이지 변경 실패: {e}")
        raise HTTPException(status_code=500, detail=f"스테이지 변경 실패: {str(e)}")


@router.post("/models/{model_name}/promote-to-production")
async def promote_to_production(
    model_name: str,
    version: str,
    description: str = "API를 통한 프로덕션 승격"
):
    """모델을 프로덕션으로 승격"""
    try:
        registry = get_model_registry()
        
        success = registry.promote_model_to_production(
            model_name=model_name,
            version=version,
            description=description
        )
        
        if success:
            return {
                "message": f"모델이 프로덕션으로 승격되었습니다",
                "model_name": model_name,
                "version": version
            }
        else:
            raise HTTPException(status_code=500, detail="프로덕션 승격에 실패했습니다")
        
    except Exception as e:
        logger.error(f"프로덕션 승격 실패: {e}")
        raise HTTPException(status_code=500, detail=f"프로덕션 승격 실패: {str(e)}")


@router.get("/models/{model_name}/versions/{version}/metrics")
async def get_model_version_metrics(model_name: str, version: str):
    """특정 모델 버전의 메트릭 조회"""
    try:
        registry = get_model_registry()
        metrics = registry.get_model_metrics(model_name, version=version)
        
        return {
            "model_name": model_name,
            "version": version,
            "metrics": metrics
        }
        
    except Exception as e:
        logger.error(f"모델 메트릭 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"메트릭 조회 실패: {str(e)}")


@router.get("/models/{model_name}/compare")
async def compare_model_versions(
    model_name: str,
    versions: List[str] = Query(..., description="비교할 버전들"),
    metrics: List[str] = Query(["rmse", "mae", "accuracy"], description="비교할 메트릭들")
):
    """모델 버전별 성능 비교"""
    try:
        registry = get_model_registry()
        comparison_df = registry.compare_model_versions(model_name, versions, metrics)
        
        if comparison_df.empty:
            return {
                "model_name": model_name,
                "comparison": [],
                "message": "비교할 데이터가 없습니다"
            }
        
        # DataFrame을 딕셔너리로 변환
        comparison_data = comparison_df.to_dict('records')
        
        return {
            "model_name": model_name,
            "compared_versions": versions,
            "compared_metrics": metrics,
            "comparison": comparison_data
        }
        
    except Exception as e:
        logger.error(f"모델 버전 비교 실패: {e}")
        raise HTTPException(status_code=500, detail=f"모델 비교 실패: {str(e)}")


@router.get("/models/{model_name}/lineage")
async def get_model_lineage(model_name: str, version: Optional[str] = None):
    """모델 계보 정보 조회"""
    try:
        registry = get_model_registry()
        lineage = registry.get_model_lineage(model_name, version)
        
        return {
            "model_name": model_name,
            "lineage": lineage
        }
        
    except Exception as e:
        logger.error(f"모델 계보 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"모델 계보 조회 실패: {str(e)}")


@router.get("/dashboard/summary")
async def get_dashboard_summary():
    """MLflow 대시보드 요약 정보"""
    try:
        import mlflow
        from mlflow.tracking import MlflowClient
        
        client = MlflowClient()
        registry = get_model_registry()
        
        # 실험 통계
        experiments = client.list_experiments()
        active_experiments = [exp for exp in experiments if exp.lifecycle_stage == 'active']
        
        # 모델 통계
        models = registry.list_models()
        
        # 스테이지별 모델 수 계산
        stage_counts = {"Production": 0, "Staging": 0, "None": 0, "Archived": 0}
        for model in models:
            for stage, version_info in model.get('latest_versions', {}).items():
                if stage in stage_counts:
                    stage_counts[stage] += 1
        
        # 최근 실행 수 (최근 7일)
        from datetime import datetime, timedelta
        recent_cutoff = (datetime.now() - timedelta(days=7)).timestamp() * 1000
        
        recent_runs_count = 0
        for exp in active_experiments[:5]:  # 상위 5개 실험만 확인
            try:
                runs = mlflow.search_runs(
                    experiment_ids=[exp.experiment_id],
                    filter_string=f"attributes.start_time > {recent_cutoff}",
                    max_results=1000
                )
                recent_runs_count += len(runs)
            except:
                pass
        
        return {
            "summary": {
                "total_experiments": len(experiments),
                "active_experiments": len(active_experiments),
                "total_models": len(models),
                "models_by_stage": stage_counts,
                "recent_runs_7days": recent_runs_count
            },
            "timestamp": pd.Timestamp.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"대시보드 요약 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"대시보드 요약 조회 실패: {str(e)}")


@router.delete("/models/{model_name}/versions/{version}")
async def delete_model_version(model_name: str, version: str):
    """모델 버전 삭제"""
    try:
        registry = get_model_registry()
        success = registry.delete_model_version(model_name, version)
        
        if success:
            return {
                "message": f"모델 버전이 삭제되었습니다",
                "model_name": model_name,
                "version": version
            }
        else:
            raise HTTPException(status_code=500, detail="모델 버전 삭제에 실패했습니다")
        
    except Exception as e:
        logger.error(f"모델 버전 삭제 실패: {e}")
        raise HTTPException(status_code=500, detail=f"모델 버전 삭제 실패: {str(e)}")
