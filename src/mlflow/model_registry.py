"""MLflow 모델 레지스트리 관리"""

import mlflow
import mlflow.pytorch
import mlflow.sklearn
from mlflow.tracking import MlflowClient
from mlflow.entities.model_registry.model_version_status import ModelVersionStatus
import torch
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List, Union, Tuple
import logging
import os
import json
import time
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MLflowModelRegistry:
    """MLflow 모델 레지스트리 관리 클래스"""
    
    def __init__(
        self,
        tracking_uri: Optional[str] = None,
        registry_uri: Optional[str] = None
    ):
        """
        Args:
            tracking_uri: MLflow 추적 서버 URI
            registry_uri: MLflow 레지스트리 서버 URI
        """
        # MLflow 클라이언트 설정
        if tracking_uri:
            mlflow.set_tracking_uri(tracking_uri)
        
        if registry_uri:
            mlflow.set_registry_uri(registry_uri)
        
        self.client = MlflowClient()
        
        logger.info("MLflow 모델 레지스트리 클라이언트 초기화 완료")
    
    def register_model(
        self,
        model_uri: str,
        model_name: str,
        description: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        await_creation: bool = True
    ) -> Dict[str, Any]:
        """
        모델을 레지스트리에 등록
        
        Args:
            model_uri: 모델 URI (runs:/<run_id>/model 형식)
            model_name: 등록할 모델 이름
            description: 모델 설명
            tags: 모델 태그
            await_creation: 등록 완료까지 대기 여부
            
        Returns:
            등록된 모델 버전 정보
        """
        try:
            # 모델 등록
            model_version = mlflow.register_model(
                model_uri=model_uri,
                name=model_name
            )
            
            # 모델 설명 업데이트
            if description:
                self.client.update_registered_model(
                    name=model_name,
                    description=description
                )
            
            # 모델 태그 설정
            if tags:
                for key, value in tags.items():
                    self.client.set_registered_model_tag(
                        name=model_name,
                        key=key,
                        value=value
                    )
            
            # 등록 완료 대기
            if await_creation:
                self._wait_for_model_ready(model_name, model_version.version)
            
            logger.info(f"모델 등록 완료: {model_name} v{model_version.version}")
            
            return {
                'name': model_version.name,
                'version': model_version.version,
                'creation_timestamp': model_version.creation_timestamp,
                'current_stage': model_version.current_stage,
                'source': model_version.source,
                'run_id': model_version.run_id
            }
            
        except Exception as e:
            logger.error(f"모델 등록 실패: {e}")
            raise
    
    def transition_model_stage(
        self,
        model_name: str,
        version: Union[int, str],
        stage: str,
        archive_existing: bool = True,
        description: Optional[str] = None
    ) -> bool:
        """
        모델 버전의 스테이지 변경
        
        Args:
            model_name: 모델 이름
            version: 모델 버전
            stage: 새로운 스테이지 ('Staging', 'Production', 'Archived')
            archive_existing: 기존 Production 모델 자동 아카이브
            description: 변경 사유
            
        Returns:
            변경 성공 여부
        """
        try:
            valid_stages = ['None', 'Staging', 'Production', 'Archived']
            if stage not in valid_stages:
                raise ValueError(f"유효하지 않은 스테이지: {stage}. 가능한 값: {valid_stages}")
            
            self.client.transition_model_version_stage(
                name=model_name,
                version=str(version),
                stage=stage,
                archive_existing_versions=archive_existing,
                description=description
            )
            
            logger.info(f"모델 스테이지 변경: {model_name} v{version} -> {stage}")
            return True
            
        except Exception as e:
            logger.error(f"모델 스테이지 변경 실패: {e}")
            return False
    
    def get_model_version(
        self,
        model_name: str,
        version: Optional[Union[int, str]] = None,
        stage: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        특정 모델 버전 정보 조회
        
        Args:
            model_name: 모델 이름
            version: 모델 버전 (지정하지 않으면 latest)
            stage: 스테이지로 조회 ('Production', 'Staging' 등)
            
        Returns:
            모델 버전 정보
        """
        try:
            if stage:
                # 스테이지로 조회
                versions = self.client.get_latest_versions(
                    name=model_name,
                    stages=[stage]
                )
                if not versions:
                    logger.warning(f"스테이지 '{stage}'에 모델이 없습니다: {model_name}")
                    return None
                model_version = versions[0]
            else:
                # 버전으로 조회
                if version is None:
                    # 최신 버전 조회
                    versions = self.client.search_model_versions(f"name='{model_name}'")
                    if not versions:
                        logger.warning(f"모델을 찾을 수 없습니다: {model_name}")
                        return None
                    model_version = max(versions, key=lambda x: int(x.version))
                else:
                    model_version = self.client.get_model_version(
                        name=model_name,
                        version=str(version)
                    )
            
            return {
                'name': model_version.name,
                'version': model_version.version,
                'creation_timestamp': model_version.creation_timestamp,
                'last_updated_timestamp': model_version.last_updated_timestamp,
                'current_stage': model_version.current_stage,
                'description': model_version.description,
                'source': model_version.source,
                'run_id': model_version.run_id,
                'status': model_version.status,
                'status_message': model_version.status_message,
                'tags': {tag.key: tag.value for tag in model_version.tags}
            }
            
        except Exception as e:
            logger.error(f"모델 버전 조회 실패: {e}")
            return None
    
    def list_models(
        self,
        max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """등록된 모델 목록 조회"""
        try:
            registered_models = self.client.list_registered_models(max_results=max_results)
            
            models_info = []
            for model in registered_models:
                # 각 모델의 최신 버전들 정보
                latest_versions = self.client.get_latest_versions(
                    name=model.name,
                    stages=['Production', 'Staging', 'None']
                )
                
                version_info = {}
                for version in latest_versions:
                    version_info[version.current_stage] = {
                        'version': version.version,
                        'creation_timestamp': version.creation_timestamp,
                        'run_id': version.run_id
                    }
                
                models_info.append({
                    'name': model.name,
                    'creation_timestamp': model.creation_timestamp,
                    'last_updated_timestamp': model.last_updated_timestamp,
                    'description': model.description,
                    'latest_versions': version_info,
                    'tags': {tag.key: tag.value for tag in model.tags}
                })
            
            logger.info(f"등록된 모델 조회: {len(models_info)}개")
            return models_info
            
        except Exception as e:
            logger.error(f"모델 목록 조회 실패: {e}")
            return []
    
    def load_model(
        self,
        model_name: str,
        version: Optional[Union[int, str]] = None,
        stage: Optional[str] = None,
        model_type: str = "pytorch"
    ) -> Any:
        """
        레지스트리에서 모델 로드
        
        Args:
            model_name: 모델 이름
            version: 모델 버전
            stage: 스테이지 ('Production', 'Staging' 등)
            model_type: 모델 타입 ('pytorch', 'sklearn', 'pyfunc')
            
        Returns:
            로드된 모델
        """
        try:
            # 모델 URI 구성
            if stage:
                model_uri = f"models:/{model_name}/{stage}"
            elif version:
                model_uri = f"models:/{model_name}/{version}"
            else:
                model_uri = f"models:/{model_name}/latest"
            
            # 모델 타입에 따라 로드
            if model_type == "pytorch":
                model = mlflow.pytorch.load_model(model_uri)
            elif model_type == "sklearn":
                model = mlflow.sklearn.load_model(model_uri)
            elif model_type == "pyfunc":
                model = mlflow.pyfunc.load_model(model_uri)
            else:
                raise ValueError(f"지원하지 않는 모델 타입: {model_type}")
            
            logger.info(f"모델 로드 완료: {model_uri}")
            return model
            
        except Exception as e:
            logger.error(f"모델 로드 실패: {e}")
            raise
    
    def delete_model_version(
        self,
        model_name: str,
        version: Union[int, str]
    ) -> bool:
        """특정 모델 버전 삭제"""
        try:
            self.client.delete_model_version(
                name=model_name,
                version=str(version)
            )
            
            logger.info(f"모델 버전 삭제: {model_name} v{version}")
            return True
            
        except Exception as e:
            logger.error(f"모델 버전 삭제 실패: {e}")
            return False
    
    def delete_registered_model(
        self,
        model_name: str
    ) -> bool:
        """등록된 모델 전체 삭제"""
        try:
            self.client.delete_registered_model(model_name)
            
            logger.info(f"등록된 모델 삭제: {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"등록된 모델 삭제 실패: {e}")
            return False
    
    def update_model_version(
        self,
        model_name: str,
        version: Union[int, str],
        description: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> bool:
        """모델 버전 정보 업데이트"""
        try:
            # 설명 업데이트
            if description is not None:
                self.client.update_model_version(
                    name=model_name,
                    version=str(version),
                    description=description
                )
            
            # 태그 업데이트
            if tags:
                for key, value in tags.items():
                    self.client.set_model_version_tag(
                        name=model_name,
                        version=str(version),
                        key=key,
                        value=value
                    )
            
            logger.info(f"모델 버전 업데이트: {model_name} v{version}")
            return True
            
        except Exception as e:
            logger.error(f"모델 버전 업데이트 실패: {e}")
            return False
    
    def get_model_metrics(
        self,
        model_name: str,
        version: Optional[Union[int, str]] = None,
        stage: Optional[str] = None
    ) -> Dict[str, float]:
        """모델의 성능 메트릭 조회"""
        try:
            # 모델 버전 정보 조회
            model_info = self.get_model_version(model_name, version, stage)
            if not model_info:
                return {}
            
            run_id = model_info['run_id']
            if not run_id:
                logger.warning(f"모델 버전에 연결된 실행이 없습니다: {model_name} v{model_info['version']}")
                return {}
            
            # 실행의 메트릭 조회
            run = self.client.get_run(run_id)
            metrics = run.data.metrics
            
            logger.info(f"모델 메트릭 조회: {model_name} v{model_info['version']} - {len(metrics)}개 메트릭")
            return metrics
            
        except Exception as e:
            logger.error(f"모델 메트릭 조회 실패: {e}")
            return {}
    
    def compare_model_versions(
        self,
        model_name: str,
        versions: List[Union[int, str]],
        metrics: List[str]
    ) -> pd.DataFrame:
        """모델 버전별 성능 비교"""
        try:
            comparison_data = []
            
            for version in versions:
                version_info = self.get_model_version(model_name, version)
                if not version_info:
                    continue
                
                row_data = {
                    'version': version_info['version'],
                    'stage': version_info['current_stage'],
                    'creation_time': version_info['creation_timestamp'],
                    'run_id': version_info['run_id']
                }
                
                # 메트릭 추가
                if version_info['run_id']:
                    run = self.client.get_run(version_info['run_id'])
                    for metric in metrics:
                        row_data[metric] = run.data.metrics.get(metric, None)
                
                comparison_data.append(row_data)
            
            comparison_df = pd.DataFrame(comparison_data)
            logger.info(f"모델 버전 비교: {model_name} - {len(versions)}개 버전")
            
            return comparison_df
            
        except Exception as e:
            logger.error(f"모델 버전 비교 실패: {e}")
            return pd.DataFrame()
    
    def get_production_model(
        self,
        model_name: str
    ) -> Optional[Any]:
        """프로덕션 스테이지 모델 로드"""
        try:
            return self.load_model(model_name, stage="Production")
        except Exception as e:
            logger.warning(f"프로덕션 모델 로드 실패: {e}")
            return None
    
    def promote_model_to_production(
        self,
        model_name: str,
        version: Union[int, str],
        description: str = "Promoted to production"
    ) -> bool:
        """모델을 프로덕션으로 승격"""
        try:
            # Staging으로 먼저 이동 (선택사항)
            current_info = self.get_model_version(model_name, version)
            if current_info and current_info['current_stage'] != 'Staging':
                self.transition_model_stage(
                    model_name=model_name,
                    version=version,
                    stage='Staging',
                    description="Moved to staging before production"
                )
                
                # Staging에서 잠시 대기
                time.sleep(2)
            
            # Production으로 승격
            return self.transition_model_stage(
                model_name=model_name,
                version=version,
                stage='Production',
                archive_existing=True,
                description=description
            )
            
        except Exception as e:
            logger.error(f"프로덕션 승격 실패: {e}")
            return False
    
    def _wait_for_model_ready(
        self,
        model_name: str,
        version: str,
        timeout: int = 60
    ):
        """모델 등록 완료까지 대기"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                model_version = self.client.get_model_version(model_name, version)
                if model_version.status == ModelVersionStatus.READY:
                    return
                elif model_version.status == ModelVersionStatus.FAILED_REGISTRATION:
                    raise Exception(f"모델 등록 실패: {model_version.status_message}")
                
                time.sleep(1)
                
            except Exception as e:
                if "RESOURCE_DOES_NOT_EXIST" not in str(e):
                    raise
                time.sleep(1)
        
        raise Exception(f"모델 등록 대기 시간 초과: {timeout}초")
    
    def get_model_lineage(
        self,
        model_name: str,
        version: Optional[Union[int, str]] = None
    ) -> Dict[str, Any]:
        """모델 계보 정보 조회"""
        try:
            version_info = self.get_model_version(model_name, version)
            if not version_info:
                return {}
            
            lineage = {
                'model_name': model_name,
                'version': version_info['version'],
                'run_id': version_info['run_id']
            }
            
            # 연결된 실행 정보
            if version_info['run_id']:
                run = self.client.get_run(version_info['run_id'])
                lineage['experiment_id'] = run.info.experiment_id
                lineage['experiment_name'] = self.client.get_experiment(run.info.experiment_id).name
                lineage['run_name'] = run.data.tags.get('mlflow.runName', 'Unknown')
                lineage['parameters'] = run.data.params
                lineage['metrics'] = run.data.metrics
                lineage['artifacts'] = [artifact.path for artifact in self.client.list_artifacts(run.info.run_id)]
            
            return lineage
            
        except Exception as e:
            logger.error(f"모델 계보 조회 실패: {e}")
            return {}


# 전역 레지스트리 인스턴스
_model_registry = None

def get_model_registry(
    tracking_uri: Optional[str] = None,
    registry_uri: Optional[str] = None
) -> MLflowModelRegistry:
    """전역 모델 레지스트리 인스턴스 반환"""
    global _model_registry
    if _model_registry is None:
        _model_registry = MLflowModelRegistry(tracking_uri, registry_uri)
    return _model_registry


# 사용 예제
if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)
    
    # 레지스트리 생성
    registry = get_model_registry()
    
    # 모델 목록 조회
    models = registry.list_models()
    print(f"등록된 모델 수: {len(models)}")
    
    for model in models:
        print(f"모델: {model['name']}")
        print(f"  설명: {model['description']}")
        print(f"  최신 버전들: {model['latest_versions']}")
        print()
