"""PyTorch 모델 훈련 스크립트"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple, List
import logging
import os
import time
from datetime import datetime
import json
from tqdm import tqdm

from src.models.pytorch.movie_recommender import (
    MovieRecommenderNet, 
    CollaborativeFilteringModel,
    ContentBasedModel,
    create_model,
    save_model,
    load_model,
    count_parameters
)
from src.models.pytorch.data_loader import (
    create_data_loaders,
    prepare_data_from_watch_log
)

logger = logging.getLogger(__name__)


class ModelTrainer:
    """PyTorch 모델 훈련을 담당하는 클래스"""
    
    def __init__(
        self,
        model: nn.Module,
        device: Optional[torch.device] = None,
        experiment_name: str = "movie_recommender"
    ):
        """
        Args:
            model: 훈련할 모델
            device: 사용할 디바이스
            experiment_name: 실험 이름
        """
        self.model = model
        self.device = device or torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.experiment_name = experiment_name
        
        # 모델을 디바이스로 이동
        self.model = self.model.to(self.device)
        
        # 훈련 기록 초기화
        self.train_history = {
            'train_loss': [],
            'val_loss': [],
            'train_rmse': [],
            'val_rmse': [],
            'epochs': []
        }
        
        # TensorBoard 설정
        log_dir = f"logs/pytorch/{experiment_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.writer = SummaryWriter(log_dir)
        
        logger.info(f"모델 훈련기 초기화 완료 - 디바이스: {self.device}")
        logger.info(f"모델 파라미터 수: {count_parameters(self.model):,}")
    
    def train_epoch(
        self,
        train_loader: DataLoader,
        optimizer: optim.Optimizer,
        criterion: nn.Module,
        epoch: int
    ) -> Tuple[float, float]:
        """한 에포크 훈련"""
        self.model.train()
        total_loss = 0.0
        total_samples = 0
        predictions = []
        targets = []
        
        progress_bar = tqdm(train_loader, desc=f"Epoch {epoch+1} Training")
        
        for batch_idx, batch in enumerate(progress_bar):
            # 데이터를 디바이스로 이동
            user_ids = batch['user_id'].to(self.device)
            movie_ids = batch['movie_id'].to(self.device) 
            ratings = batch['rating'].to(self.device)
            
            # 순전파
            optimizer.zero_grad()
            outputs = self.model(user_ids, movie_ids)
            loss = criterion(outputs, ratings)
            
            # 역전파
            loss.backward()
            optimizer.step()
            
            # 통계 업데이트
            batch_size = ratings.size(0)
            total_loss += loss.item() * batch_size
            total_samples += batch_size
            
            # 예측값 저장 (RMSE 계산용)
            predictions.extend(outputs.detach().cpu().numpy())
            targets.extend(ratings.detach().cpu().numpy())
            
            # 진행률 업데이트
            progress_bar.set_postfix({
                'Loss': f"{loss.item():.4f}",
                'Avg_Loss': f"{total_loss/total_samples:.4f}"
            })
        
        # 에포크 통계 계산
        avg_loss = total_loss / total_samples
        rmse = np.sqrt(np.mean((np.array(predictions) - np.array(targets)) ** 2))
        
        return avg_loss, rmse
    
    def validate_epoch(
        self,
        val_loader: DataLoader,
        criterion: nn.Module,
        epoch: int
    ) -> Tuple[float, float]:
        """한 에포크 검증"""
        self.model.eval()
        total_loss = 0.0
        total_samples = 0
        predictions = []
        targets = []
        
        with torch.no_grad():
            for batch in tqdm(val_loader, desc=f"Epoch {epoch+1} Validation"):
                user_ids = batch['user_id'].to(self.device)
                movie_ids = batch['movie_id'].to(self.device)
                ratings = batch['rating'].to(self.device)
                
                outputs = self.model(user_ids, movie_ids)
                loss = criterion(outputs, ratings)
                
                batch_size = ratings.size(0)
                total_loss += loss.item() * batch_size
                total_samples += batch_size
                
                predictions.extend(outputs.cpu().numpy())
                targets.extend(ratings.cpu().numpy())
        
        avg_loss = total_loss / total_samples
        rmse = np.sqrt(np.mean((np.array(predictions) - np.array(targets)) ** 2))
        
        return avg_loss, rmse
    
    def train(
        self,
        train_loader: DataLoader,
        val_loader: Optional[DataLoader] = None,
        num_epochs: int = 100,
        learning_rate: float = 0.001,
        optimizer_type: str = 'adam',
        criterion_type: str = 'mse',
        scheduler_type: Optional[str] = None,
        early_stopping_patience: int = 10,
        save_best_model: bool = True,
        model_save_path: str = "models/trained/pytorch_model.pth"
    ) -> Dict[str, List[float]]:
        """
        모델 훈련
        
        Args:
            train_loader: 훈련 데이터로더
            val_loader: 검증 데이터로더
            num_epochs: 에포크 수
            learning_rate: 학습률
            optimizer_type: 옵티마이저 타입
            criterion_type: 손실함수 타입
            scheduler_type: 스케줄러 타입
            early_stopping_patience: 조기 종료 patience
            save_best_model: 최고 모델 저장 여부
            model_save_path: 모델 저장 경로
            
        Returns:
            훈련 기록 딕셔너리
        """
        logger.info("모델 훈련 시작")
        
        # 옵티마이저 설정
        if optimizer_type.lower() == 'adam':
            optimizer = optim.Adam(self.model.parameters(), lr=learning_rate)
        elif optimizer_type.lower() == 'sgd':
            optimizer = optim.SGD(self.model.parameters(), lr=learning_rate, momentum=0.9)
        elif optimizer_type.lower() == 'adamw':
            optimizer = optim.AdamW(self.model.parameters(), lr=learning_rate)
        else:
            raise ValueError(f"지원하지 않는 옵티마이저: {optimizer_type}")
        
        # 손실함수 설정
        if criterion_type.lower() == 'mse':
            criterion = nn.MSELoss()
        elif criterion_type.lower() == 'mae':
            criterion = nn.L1Loss()
        elif criterion_type.lower() == 'huber':
            criterion = nn.SmoothL1Loss()
        else:
            raise ValueError(f"지원하지 않는 손실함수: {criterion_type}")
        
        # 스케줄러 설정
        scheduler = None
        if scheduler_type == 'step':
            scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=20, gamma=0.5)
        elif scheduler_type == 'cosine':
            scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=num_epochs)
        elif scheduler_type == 'reduce_on_plateau':
            scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', patience=5)
        
        # 조기 종료 설정
        best_val_loss = float('inf')
        patience_counter = 0
        
        # 훈련 루프
        start_time = time.time()
        
        for epoch in range(num_epochs):
            epoch_start_time = time.time()
            
            # 훈련
            train_loss, train_rmse = self.train_epoch(train_loader, optimizer, criterion, epoch)
            
            # 검증
            val_loss, val_rmse = None, None
            if val_loader is not None:
                val_loss, val_rmse = self.validate_epoch(val_loader, criterion, epoch)
            
            # 기록 업데이트
            self.train_history['train_loss'].append(train_loss)
            self.train_history['train_rmse'].append(train_rmse)
            self.train_history['epochs'].append(epoch + 1)
            
            if val_loss is not None:
                self.train_history['val_loss'].append(val_loss)
                self.train_history['val_rmse'].append(val_rmse)
            
            # TensorBoard 로깅
            self.writer.add_scalar('Loss/Train', train_loss, epoch)
            self.writer.add_scalar('RMSE/Train', train_rmse, epoch)
            
            if val_loss is not None:
                self.writer.add_scalar('Loss/Validation', val_loss, epoch)
                self.writer.add_scalar('RMSE/Validation', val_rmse, epoch)
            
            # 학습률 스케줄링
            if scheduler is not None:
                if scheduler_type == 'reduce_on_plateau' and val_loss is not None:
                    scheduler.step(val_loss)
                else:
                    scheduler.step()
                
                current_lr = optimizer.param_groups[0]['lr']
                self.writer.add_scalar('Learning_Rate', current_lr, epoch)
            
            # 에포크 시간 계산
            epoch_time = time.time() - epoch_start_time
            
            # 로깅
            log_msg = f"Epoch {epoch+1}/{num_epochs} - "
            log_msg += f"Train Loss: {train_loss:.4f}, Train RMSE: {train_rmse:.4f}"
            
            if val_loss is not None:
                log_msg += f", Val Loss: {val_loss:.4f}, Val RMSE: {val_rmse:.4f}"
            
            log_msg += f" - Time: {epoch_time:.2f}s"
            logger.info(log_msg)
            
            # 조기 종료 체크
            if val_loss is not None:
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    patience_counter = 0
                    
                    # 최고 모델 저장
                    if save_best_model:
                        os.makedirs(os.path.dirname(model_save_path), exist_ok=True)
                        metadata = {
                            'epoch': epoch + 1,
                            'train_loss': train_loss,
                            'val_loss': val_loss,
                            'train_rmse': train_rmse,
                            'val_rmse': val_rmse,
                            'experiment_name': self.experiment_name,
                            'model_config': {
                                'num_users': getattr(self.model, 'num_users', None),
                                'num_movies': getattr(self.model, 'num_movies', None),
                                'embedding_dim': getattr(self.model, 'embedding_dim', None)
                            }
                        }
                        save_model(self.model, model_save_path, metadata)
                        logger.info(f"최고 모델 저장: {model_save_path}")
                else:
                    patience_counter += 1
                
                if patience_counter >= early_stopping_patience:
                    logger.info(f"조기 종료 - {early_stopping_patience} 에포크 동안 개선 없음")
                    break
        
        # 훈련 완료
        total_time = time.time() - start_time
        logger.info(f"훈련 완료 - 총 시간: {total_time/60:.2f}분")
        
        # TensorBoard 정리
        self.writer.close()
        
        return self.train_history
    
    def evaluate(
        self,
        test_loader: DataLoader,
        metrics: List[str] = ['rmse', 'mae', 'mse']
    ) -> Dict[str, float]:
        """모델 평가"""
        self.model.eval()
        predictions = []
        targets = []
        
        with torch.no_grad():
            for batch in tqdm(test_loader, desc="Evaluating"):
                user_ids = batch['user_id'].to(self.device)
                movie_ids = batch['movie_id'].to(self.device)
                ratings = batch['rating'].to(self.device)
                
                outputs = self.model(user_ids, movie_ids)
                
                predictions.extend(outputs.cpu().numpy())
                targets.extend(ratings.cpu().numpy())
        
        predictions = np.array(predictions)
        targets = np.array(targets)
        
        # 메트릭 계산
        results = {}
        
        if 'rmse' in metrics:
            results['rmse'] = np.sqrt(np.mean((predictions - targets) ** 2))
        
        if 'mae' in metrics:
            results['mae'] = np.mean(np.abs(predictions - targets))
        
        if 'mse' in metrics:
            results['mse'] = np.mean((predictions - targets) ** 2)
        
        logger.info("평가 결과:")
        for metric, value in results.items():
            logger.info(f"  {metric.upper()}: {value:.4f}")
        
        return results


def train_pytorch_model(
    data_path: str = "data/processed/watch_log.csv",
    model_type: str = "neural_cf",
    model_config: Optional[Dict[str, Any]] = None,
    training_config: Optional[Dict[str, Any]] = None,
    experiment_name: str = "pytorch_movie_recommender"
) -> Tuple[nn.Module, Dict[str, List[float]]]:
    """
    PyTorch 모델 훈련 메인 함수
    
    Args:
        data_path: 데이터 파일 경로
        model_type: 모델 타입
        model_config: 모델 설정
        training_config: 훈련 설정
        experiment_name: 실험 이름
        
    Returns:
        (훈련된 모델, 훈련 기록)
    """
    logger.info(f"PyTorch 모델 훈련 시작 - {model_type}")
    
    # 기본 설정
    default_model_config = {
        'embedding_dim': 64,
        'hidden_dims': [128, 64, 32],
        'dropout_rate': 0.3
    }
    
    default_training_config = {
        'batch_size': 256,
        'num_epochs': 50,
        'learning_rate': 0.001,
        'optimizer_type': 'adam',
        'criterion_type': 'mse',
        'early_stopping_patience': 10
    }
    
    model_config = {**default_model_config, **(model_config or {})}
    training_config = {**default_training_config, **(training_config or {})}
    
    # 데이터 준비
    logger.info("데이터 준비 중...")
    train_df, val_df, test_df = prepare_data_from_watch_log(data_path)
    
    # 데이터로더 생성
    data_loaders = create_data_loaders(
        train_df=train_df,
        val_df=val_df,
        test_df=test_df,
        batch_size=training_config['batch_size']
    )
    
    # 모델 설정 업데이트
    metadata = data_loaders['metadata']
    model_config.update({
        'num_users': metadata['num_users'],
        'num_movies': metadata['num_movies']
    })
    
    # 모델 생성
    model = create_model(model_type, model_config)
    
    # 훈련기 생성
    trainer = ModelTrainer(model, experiment_name=experiment_name)
    
    # 훈련 실행
    history = trainer.train(
        train_loader=data_loaders['train'],
        val_loader=data_loaders['val'],
        **training_config
    )
    
    # 테스트 평가
    if 'test' in data_loaders:
        test_results = trainer.evaluate(data_loaders['test'])
        logger.info(f"테스트 결과: {test_results}")
    
    return model, history


if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)
    
    # 훈련 실행
    model, history = train_pytorch_model(
        model_type="neural_cf",
        experiment_name="movie_recommender_test"
    )
    
    print("훈련 완료!")
    print(f"최종 훈련 손실: {history['train_loss'][-1]:.4f}")
    if history['val_loss']:
        print(f"최종 검증 손실: {history['val_loss'][-1]:.4f}")
