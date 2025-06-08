"""PyTorch 기반 영화 추천 모델"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class MovieRecommenderNet(nn.Module):
    """PyTorch 기반 영화 추천 신경망 모델"""
    
    def __init__(
        self, 
        num_users: int,
        num_movies: int, 
        embedding_dim: int = 64,
        hidden_dims: list = [128, 64, 32],
        dropout_rate: float = 0.3,
        use_bias: bool = True
    ):
        """
        Args:
            num_users: 사용자 수
            num_movies: 영화 수
            embedding_dim: 임베딩 차원
            hidden_dims: 히든 레이어 차원들
            dropout_rate: 드롭아웃 비율
            use_bias: 바이어스 사용 여부
        """
        super(MovieRecommenderNet, self).__init__()
        
        self.num_users = num_users
        self.num_movies = num_movies
        self.embedding_dim = embedding_dim
        
        # 사용자 및 영화 임베딩
        self.user_embedding = nn.Embedding(num_users, embedding_dim)
        self.movie_embedding = nn.Embedding(num_movies, embedding_dim)
        
        # 사용자 및 영화 바이어스
        if use_bias:
            self.user_bias = nn.Embedding(num_users, 1)
            self.movie_bias = nn.Embedding(num_movies, 1)
            self.global_bias = nn.Parameter(torch.zeros(1))
        else:
            self.user_bias = None
            self.movie_bias = None
            self.global_bias = None
        
        # MLP layers for deep learning
        self.mlp_layers = nn.ModuleList()
        input_dim = embedding_dim * 2  # user + movie embeddings
        
        for hidden_dim in hidden_dims:
            self.mlp_layers.append(nn.Linear(input_dim, hidden_dim))
            self.mlp_layers.append(nn.ReLU())
            self.mlp_layers.append(nn.Dropout(dropout_rate))
            input_dim = hidden_dim
        
        # 최종 출력 레이어
        self.output_layer = nn.Linear(input_dim, 1)
        
        # 가중치 초기화
        self._init_weights()
    
    def _init_weights(self):
        """가중치 초기화"""
        nn.init.normal_(self.user_embedding.weight, std=0.01)
        nn.init.normal_(self.movie_embedding.weight, std=0.01)
        
        if self.user_bias is not None:
            nn.init.constant_(self.user_bias.weight, 0)
            nn.init.constant_(self.movie_bias.weight, 0)
        
        for layer in self.mlp_layers:
            if isinstance(layer, nn.Linear):
                nn.init.xavier_normal_(layer.weight)
                if layer.bias is not None:
                    nn.init.constant_(layer.bias, 0)
        
        nn.init.xavier_normal_(self.output_layer.weight)
        if self.output_layer.bias is not None:
            nn.init.constant_(self.output_layer.bias, 0)
    
    def forward(self, user_ids: torch.Tensor, movie_ids: torch.Tensor) -> torch.Tensor:
        """
        순전파
        
        Args:
            user_ids: 사용자 ID 텐서 (batch_size,)
            movie_ids: 영화 ID 텐서 (batch_size,)
            
        Returns:
            예측 평점 (batch_size, 1)
        """
        # 임베딩 조회
        user_emb = self.user_embedding(user_ids)  # (batch_size, embedding_dim)
        movie_emb = self.movie_embedding(movie_ids)  # (batch_size, embedding_dim)
        
        # Matrix Factorization part (bias 포함)
        mf_output = (user_emb * movie_emb).sum(dim=1, keepdim=True)  # (batch_size, 1)
        
        if self.user_bias is not None:
            user_bias = self.user_bias(user_ids)  # (batch_size, 1)
            movie_bias = self.movie_bias(movie_ids)  # (batch_size, 1)
            mf_output = mf_output + user_bias + movie_bias + self.global_bias
        
        # MLP part
        mlp_input = torch.cat([user_emb, movie_emb], dim=1)  # (batch_size, embedding_dim * 2)
        
        mlp_output = mlp_input
        for layer in self.mlp_layers:
            mlp_output = layer(mlp_output)
        
        mlp_output = self.output_layer(mlp_output)  # (batch_size, 1)
        
        # MF와 MLP 결합
        output = mf_output + mlp_output
        
        return output.squeeze()  # (batch_size,)
    
    def predict(self, user_ids: torch.Tensor, movie_ids: torch.Tensor) -> torch.Tensor:
        """예측 (평가 모드)"""
        self.eval()
        with torch.no_grad():
            return self.forward(user_ids, movie_ids)
    
    def get_user_embedding(self, user_id: int) -> torch.Tensor:
        """사용자 임베딩 반환"""
        with torch.no_grad():
            return self.user_embedding(torch.tensor([user_id]))
    
    def get_movie_embedding(self, movie_id: int) -> torch.Tensor:
        """영화 임베딩 반환"""
        with torch.no_grad():
            return self.movie_embedding(torch.tensor([movie_id]))
    
    def recommend_for_user(
        self, 
        user_id: int, 
        num_recommendations: int = 10,
        exclude_seen: bool = True,
        seen_movies: Optional[set] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        사용자에게 영화 추천
        
        Args:
            user_id: 사용자 ID
            num_recommendations: 추천할 영화 수
            exclude_seen: 이미 본 영화 제외 여부
            seen_movies: 이미 본 영화 집합
            
        Returns:
            (추천 영화 IDs, 예측 평점)
        """
        self.eval()
        with torch.no_grad():
            # 모든 영화에 대한 예측
            user_tensor = torch.tensor([user_id] * self.num_movies)
            movie_tensor = torch.arange(self.num_movies)
            
            predictions = self.forward(user_tensor, movie_tensor)
            
            # 이미 본 영화 제외
            if exclude_seen and seen_movies:
                for movie_id in seen_movies:
                    if movie_id < len(predictions):
                        predictions[movie_id] = float('-inf')
            
            # 상위 N개 추천
            top_scores, top_indices = torch.topk(predictions, num_recommendations)
            
            return top_indices, top_scores


class CollaborativeFilteringModel(nn.Module):
    """간단한 Collaborative Filtering 모델"""
    
    def __init__(self, num_users: int, num_movies: int, embedding_dim: int = 50):
        super(CollaborativeFilteringModel, self).__init__()
        
        self.user_embedding = nn.Embedding(num_users, embedding_dim)
        self.movie_embedding = nn.Embedding(num_movies, embedding_dim)
        self.user_bias = nn.Embedding(num_users, 1)
        self.movie_bias = nn.Embedding(num_movies, 1)
        self.global_bias = nn.Parameter(torch.zeros(1))
        
        # 가중치 초기화
        nn.init.normal_(self.user_embedding.weight, std=0.01)
        nn.init.normal_(self.movie_embedding.weight, std=0.01)
        nn.init.constant_(self.user_bias.weight, 0)
        nn.init.constant_(self.movie_bias.weight, 0)
    
    def forward(self, user_ids: torch.Tensor, movie_ids: torch.Tensor) -> torch.Tensor:
        user_emb = self.user_embedding(user_ids)
        movie_emb = self.movie_embedding(movie_ids)
        user_bias = self.user_bias(user_ids).squeeze()
        movie_bias = self.movie_bias(movie_ids).squeeze()
        
        # Dot product + biases
        output = (user_emb * movie_emb).sum(dim=1) + user_bias + movie_bias + self.global_bias
        return output


class ContentBasedModel(nn.Module):
    """Content-based 추천 모델"""
    
    def __init__(
        self, 
        movie_feature_dim: int,
        user_feature_dim: int,
        hidden_dims: list = [128, 64, 32]
    ):
        super(ContentBasedModel, self).__init__()
        
        self.movie_feature_dim = movie_feature_dim
        self.user_feature_dim = user_feature_dim
        
        # Feature processing layers
        self.movie_processor = nn.Sequential(
            nn.Linear(movie_feature_dim, hidden_dims[0]),
            nn.ReLU(),
            nn.Dropout(0.3)
        )
        
        self.user_processor = nn.Sequential(
            nn.Linear(user_feature_dim, hidden_dims[0]),
            nn.ReLU(),
            nn.Dropout(0.3)
        )
        
        # Interaction layers
        input_dim = hidden_dims[0] * 2
        layers = []
        
        for i, hidden_dim in enumerate(hidden_dims[1:], 1):
            layers.extend([
                nn.Linear(input_dim, hidden_dim),
                nn.ReLU(),
                nn.Dropout(0.3)
            ])
            input_dim = hidden_dim
        
        layers.append(nn.Linear(input_dim, 1))
        self.interaction_layers = nn.Sequential(*layers)
    
    def forward(
        self, 
        movie_features: torch.Tensor, 
        user_features: torch.Tensor
    ) -> torch.Tensor:
        """
        Args:
            movie_features: (batch_size, movie_feature_dim)
            user_features: (batch_size, user_feature_dim)
        """
        movie_processed = self.movie_processor(movie_features)
        user_processed = self.user_processor(user_features)
        
        # Concatenate and predict
        combined = torch.cat([movie_processed, user_processed], dim=1)
        output = self.interaction_layers(combined)
        
        return output.squeeze()


def create_model(
    model_type: str,
    model_config: Dict[str, Any],
    device: Optional[torch.device] = None
) -> nn.Module:
    """
    모델 팩토리 함수
    
    Args:
        model_type: 모델 타입 ('neural_cf', 'collaborative_filtering', 'content_based')
        model_config: 모델 설정
        device: 사용할 디바이스
        
    Returns:
        생성된 모델
    """
    if device is None:
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    if model_type == 'neural_cf':
        model = MovieRecommenderNet(**model_config)
    elif model_type == 'collaborative_filtering':
        model = CollaborativeFilteringModel(**model_config)
    elif model_type == 'content_based':
        model = ContentBasedModel(**model_config)
    else:
        raise ValueError(f"지원하지 않는 모델 타입: {model_type}")
    
    model = model.to(device)
    logger.info(f"{model_type} 모델이 {device}에 생성되었습니다")
    
    return model


def count_parameters(model: nn.Module) -> int:
    """모델의 파라미터 수 계산"""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def save_model(model: nn.Module, path: str, metadata: Optional[Dict] = None):
    """모델 저장"""
    save_dict = {
        'model_state_dict': model.state_dict(),
        'model_class': model.__class__.__name__,
        'metadata': metadata or {}
    }
    torch.save(save_dict, path)
    logger.info(f"모델이 저장되었습니다: {path}")


def load_model(model: nn.Module, path: str, device: Optional[torch.device] = None):
    """모델 로드"""
    if device is None:
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    checkpoint = torch.load(path, map_location=device)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.to(device)
    
    logger.info(f"모델이 로드되었습니다: {path}")
    return model, checkpoint.get('metadata', {})
