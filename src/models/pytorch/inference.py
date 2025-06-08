"""PyTorch 모델 추론 스크립트"""

import torch
import torch.nn as nn
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, List, Tuple
import logging
import os
from datetime import datetime

from src.models.pytorch.movie_recommender import (
    MovieRecommenderNet,
    CollaborativeFilteringModel, 
    ContentBasedModel,
    load_model
)
from src.models.pytorch.data_loader import MovieRatingDataset

logger = logging.getLogger(__name__)


class MovieRecommenderInference:
    """PyTorch 영화 추천 모델 추론 클래스"""
    
    def __init__(
        self,
        model_path: str,
        model_type: str = "neural_cf",
        device: Optional[torch.device] = None
    ):
        """
        Args:
            model_path: 훈련된 모델 경로
            model_type: 모델 타입
            device: 사용할 디바이스
        """
        self.model_path = model_path
        self.model_type = model_type
        self.device = device or torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        self.model = None
        self.metadata = None
        self.user_encoder = None
        self.movie_encoder = None
        
        self._load_model()
    
    def _load_model(self):
        """모델 로드"""
        try:
            logger.info(f"모델 로딩: {self.model_path}")
            
            # 체크포인트 로드
            checkpoint = torch.load(self.model_path, map_location=self.device)
            self.metadata = checkpoint.get('metadata', {})
            
            # 모델 설정 추출
            model_config = self.metadata.get('model_config', {})
            
            # 모델 생성
            if self.model_type == "neural_cf":
                self.model = MovieRecommenderNet(**model_config)
            elif self.model_type == "collaborative_filtering":
                self.model = CollaborativeFilteringModel(**model_config)
            elif self.model_type == "content_based":
                self.model = ContentBasedModel(**model_config)
            else:
                raise ValueError(f"지원하지 않는 모델 타입: {self.model_type}")
            
            # 가중치 로드
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.model.to(self.device)
            self.model.eval()
            
            logger.info(f"모델 로딩 완료 - 디바이스: {self.device}")
            
        except Exception as e:
            logger.error(f"모델 로딩 실패: {e}")
            raise
    
    def setup_encoders(self, data_path: str):
        """데이터에서 인코더 설정"""
        try:
            df = pd.read_csv(data_path)
            
            # 임시 데이터셋 생성하여 인코더 얻기
            temp_dataset = MovieRatingDataset(df)
            self.user_encoder = temp_dataset.user_encoder
            self.movie_encoder = temp_dataset.movie_encoder
            
            logger.info("인코더 설정 완료")
            
        except Exception as e:
            logger.error(f"인코더 설정 실패: {e}")
            raise
    
    def predict_rating(
        self,
        user_id: int,
        movie_id: int
    ) -> float:
        """단일 사용자-영화 평점 예측"""
        if self.user_encoder is None or self.movie_encoder is None:
            raise ValueError("인코더가 설정되지 않았습니다. setup_encoders()를 먼저 호출하세요.")
        
        try:
            # ID 인코딩
            user_idx = self.user_encoder.transform([user_id])[0]
            movie_idx = self.movie_encoder.transform([movie_id])[0]
            
            # 텐서 생성
            user_tensor = torch.tensor([user_idx], dtype=torch.long, device=self.device)
            movie_tensor = torch.tensor([movie_idx], dtype=torch.long, device=self.device)
            
            # 예측
            with torch.no_grad():
                prediction = self.model(user_tensor, movie_tensor)
                rating = prediction.cpu().item()
            
            return rating
            
        except ValueError as e:
            logger.warning(f"예측 실패 - 알 수 없는 ID (user: {user_id}, movie: {movie_id}): {e}")
            return 0.0
        except Exception as e:
            logger.error(f"예측 중 오류 발생: {e}")
            return 0.0
    
    def predict_batch(
        self,
        user_ids: List[int],
        movie_ids: List[int]
    ) -> List[float]:
        """배치 평점 예측"""
        if len(user_ids) != len(movie_ids):
            raise ValueError("user_ids와 movie_ids의 길이가 다릅니다.")
        
        predictions = []
        
        # 유효한 ID들만 필터링
        valid_pairs = []
        valid_indices = []
        
        for i, (user_id, movie_id) in enumerate(zip(user_ids, movie_ids)):
            try:
                user_idx = self.user_encoder.transform([user_id])[0]
                movie_idx = self.movie_encoder.transform([movie_id])[0]
                valid_pairs.append((user_idx, movie_idx))
                valid_indices.append(i)
            except ValueError:
                # 알 수 없는 ID는 건너뛰기
                continue
        
        if not valid_pairs:
            return [0.0] * len(user_ids)
        
        # 배치 예측
        user_tensors = torch.tensor([pair[0] for pair in valid_pairs], dtype=torch.long, device=self.device)
        movie_tensors = torch.tensor([pair[1] for pair in valid_pairs], dtype=torch.long, device=self.device)
        
        with torch.no_grad():
            batch_predictions = self.model(user_tensors, movie_tensors)
            batch_ratings = batch_predictions.cpu().numpy()
        
        # 결과 매핑
        result = [0.0] * len(user_ids)
        for i, valid_idx in enumerate(valid_indices):
            result[valid_idx] = float(batch_ratings[i])
        
        return result
    
    def recommend_for_user(
        self,
        user_id: int,
        num_recommendations: int = 10,
        exclude_seen: bool = True,
        seen_movies: Optional[List[int]] = None,
        min_rating_threshold: float = 0.0
    ) -> List[Tuple[int, float]]:
        """사용자에게 영화 추천"""
        if self.user_encoder is None or self.movie_encoder is None:
            raise ValueError("인코더가 설정되지 않았습니다. setup_encoders()를 먼저 호출하세요.")
        
        try:
            # 사용자 ID 인코딩
            user_idx = self.user_encoder.transform([user_id])[0]
            
            # 모든 영화에 대한 예측
            all_movie_ids = list(range(len(self.movie_encoder.classes_)))
            user_tensors = torch.tensor([user_idx] * len(all_movie_ids), dtype=torch.long, device=self.device)
            movie_tensors = torch.tensor(all_movie_ids, dtype=torch.long, device=self.device)
            
            with torch.no_grad():
                predictions = self.model(user_tensors, movie_tensors)
                ratings = predictions.cpu().numpy()
            
            # 영화 ID와 예측 평점 매핑
            movie_ratings = []
            for i, movie_idx in enumerate(all_movie_ids):
                original_movie_id = self.movie_encoder.classes_[movie_idx]
                predicted_rating = ratings[i]
                
                # 필터링 조건 확인
                if predicted_rating < min_rating_threshold:
                    continue
                
                if exclude_seen and seen_movies and original_movie_id in seen_movies:
                    continue
                
                movie_ratings.append((original_movie_id, predicted_rating))
            
            # 평점 기준 정렬
            movie_ratings.sort(key=lambda x: x[1], reverse=True)
            
            # 상위 N개 반환
            recommendations = movie_ratings[:num_recommendations]
            
            logger.info(f"사용자 {user_id}에게 {len(recommendations)}개 영화 추천")
            return recommendations
            
        except ValueError as e:
            logger.warning(f"추천 실패 - 알 수 없는 사용자 ID {user_id}: {e}")
            return []
        except Exception as e:
            logger.error(f"추천 중 오류 발생: {e}")
            return []
    
    def recommend_similar_movies(
        self,
        movie_id: int,
        num_recommendations: int = 10
    ) -> List[Tuple[int, float]]:
        """유사한 영화 추천 (영화 임베딩 기반)"""
        if not hasattr(self.model, 'movie_embedding'):
            logger.warning("모델에 영화 임베딩이 없습니다.")
            return []
        
        try:
            # 영화 ID 인코딩
            movie_idx = self.movie_encoder.transform([movie_id])[0]
            
            # 대상 영화 임베딩 얻기
            target_embedding = self.model.movie_embedding(torch.tensor([movie_idx], device=self.device))
            
            # 모든 영화 임베딩
            all_movie_indices = torch.arange(len(self.movie_encoder.classes_), device=self.device)
            all_embeddings = self.model.movie_embedding(all_movie_indices)
            
            # 코사인 유사도 계산
            target_embedding = target_embedding / target_embedding.norm(dim=1, keepdim=True)
            all_embeddings = all_embeddings / all_embeddings.norm(dim=1, keepdim=True)
            
            similarities = torch.mm(target_embedding, all_embeddings.T).squeeze()
            
            # 유사도 기준 정렬 (자기 자신 제외)
            _, sorted_indices = torch.sort(similarities, descending=True)
            
            recommendations = []
            for idx in sorted_indices[1:num_recommendations+1]:  # 자기 자신(0번째) 제외
                similar_movie_id = self.movie_encoder.classes_[idx.item()]
                similarity_score = similarities[idx].item()
                recommendations.append((similar_movie_id, similarity_score))
            
            logger.info(f"영화 {movie_id}와 유사한 {len(recommendations)}개 영화 추천")
            return recommendations
            
        except ValueError as e:
            logger.warning(f"유사 영화 추천 실패 - 알 수 없는 영화 ID {movie_id}: {e}")
            return []
        except Exception as e:
            logger.error(f"유사 영화 추천 중 오류 발생: {e}")
            return []
    
    def get_user_preferences(
        self,
        user_id: int,
        top_genres: int = 5
    ) -> Dict[str, Any]:
        """사용자 선호도 분석"""
        if not hasattr(self.model, 'user_embedding'):
            logger.warning("모델에 사용자 임베딩이 없습니다.")
            return {}
        
        try:
            # 사용자 ID 인코딩
            user_idx = self.user_encoder.transform([user_id])[0]
            
            # 사용자 임베딩 추출
            user_embedding = self.model.user_embedding(torch.tensor([user_idx], device=self.device))
            user_vector = user_embedding.squeeze().cpu().numpy()
            
            # 임베딩 차원별 중요도 분석
            embedding_stats = {
                'mean_activation': float(np.mean(user_vector)),
                'max_activation': float(np.max(user_vector)),
                'min_activation': float(np.min(user_vector)),
                'std_activation': float(np.std(user_vector)),
                'embedding_norm': float(np.linalg.norm(user_vector))
            }
            
            return {
                'user_id': user_id,
                'embedding_stats': embedding_stats,
                'embedding_dimension': len(user_vector)
            }
            
        except ValueError as e:
            logger.warning(f"사용자 선호도 분석 실패 - 알 수 없는 사용자 ID {user_id}: {e}")
            return {}
        except Exception as e:
            logger.error(f"사용자 선호도 분석 중 오류 발생: {e}")
            return {}
    
    def export_embeddings(
        self,
        output_dir: str = "embeddings"
    ) -> Dict[str, str]:
        """임베딩을 파일로 내보내기"""
        os.makedirs(output_dir, exist_ok=True)
        
        exported_files = {}
        
        try:
            # 사용자 임베딩 내보내기
            if hasattr(self.model, 'user_embedding'):
                user_embeddings = self.model.user_embedding.weight.detach().cpu().numpy()
                user_file = os.path.join(output_dir, "user_embeddings.npy")
                np.save(user_file, user_embeddings)
                exported_files['user_embeddings'] = user_file
                
                # 사용자 ID 매핑도 저장
                user_mapping = {i: user_id for i, user_id in enumerate(self.user_encoder.classes_)}
                user_mapping_file = os.path.join(output_dir, "user_id_mapping.json")
                import json
                with open(user_mapping_file, 'w') as f:
                    json.dump(user_mapping, f)
                exported_files['user_mapping'] = user_mapping_file
            
            # 영화 임베딩 내보내기
            if hasattr(self.model, 'movie_embedding'):
                movie_embeddings = self.model.movie_embedding.weight.detach().cpu().numpy()
                movie_file = os.path.join(output_dir, "movie_embeddings.npy")
                np.save(movie_file, movie_embeddings)
                exported_files['movie_embeddings'] = movie_file
                
                # 영화 ID 매핑도 저장
                movie_mapping = {i: movie_id for i, movie_id in enumerate(self.movie_encoder.classes_)}
                movie_mapping_file = os.path.join(output_dir, "movie_id_mapping.json")
                with open(movie_mapping_file, 'w') as f:
                    json.dump(movie_mapping, f)
                exported_files['movie_mapping'] = movie_mapping_file
            
            logger.info(f"임베딩 내보내기 완료: {output_dir}")
            return exported_files
            
        except Exception as e:
            logger.error(f"임베딩 내보내기 실패: {e}")
            return {}
    
    def get_model_info(self) -> Dict[str, Any]:
        """모델 정보 반환"""
        return {
            'model_type': self.model_type,
            'model_path': self.model_path,
            'device': str(self.device),
            'metadata': self.metadata,
            'num_parameters': sum(p.numel() for p in self.model.parameters()),
            'model_size_mb': sum(p.numel() * p.element_size() for p in self.model.parameters()) / (1024 * 1024)
        }


def create_inference_from_checkpoint(
    model_path: str,
    data_path: str,
    model_type: str = "neural_cf"
) -> MovieRecommenderInference:
    """체크포인트에서 추론 객체 생성"""
    inference = MovieRecommenderInference(model_path, model_type)
    inference.setup_encoders(data_path)
    return inference


# 사용 예제
if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)
    
    # 추론 객체 생성 (예제)
    model_path = "models/trained/pytorch_model.pth"
    data_path = "data/processed/watch_log.csv"
    
    if os.path.exists(model_path) and os.path.exists(data_path):
        # 추론 객체 생성
        inference = create_inference_from_checkpoint(model_path, data_path)
        
        # 모델 정보 출력
        info = inference.get_model_info()
        print(f"모델 정보: {info}")
        
        # 사용자 1에게 추천
        recommendations = inference.recommend_for_user(user_id=1, num_recommendations=5)
        print(f"사용자 1 추천: {recommendations}")
        
        # 평점 예측
        rating = inference.predict_rating(user_id=1, movie_id=100)
        print(f"사용자 1, 영화 100 예측 평점: {rating:.2f}")
        
    else:
        print("모델 파일 또는 데이터 파일을 찾을 수 없습니다.")
        print("먼저 모델을 훈련하세요: python src/models/pytorch/training.py")
