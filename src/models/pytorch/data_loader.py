"""PyTorch 데이터로더 구현"""

import torch
from torch.utils.data import Dataset, DataLoader
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, Optional, List
import logging
from sklearn.preprocessing import LabelEncoder, StandardScaler

logger = logging.getLogger(__name__)


class MovieRatingDataset(Dataset):
    """영화 평점 데이터셋 클래스"""
    
    def __init__(
        self,
        ratings_df: pd.DataFrame,
        user_col: str = 'user_id',
        movie_col: str = 'content_id', 
        rating_col: str = 'rating',
        features_cols: Optional[List[str]] = None,
        normalize_ratings: bool = True,
        min_rating: float = 1.0,
        max_rating: float = 10.0
    ):
        """
        Args:
            ratings_df: 평점 데이터프레임
            user_col: 사용자 ID 컬럼명
            movie_col: 영화 ID 컬럼명  
            rating_col: 평점 컬럼명
            features_cols: 추가 피처 컬럼들
            normalize_ratings: 평점 정규화 여부
            min_rating: 최소 평점
            max_rating: 최대 평점
        """
        self.ratings_df = ratings_df.copy()
        self.user_col = user_col
        self.movie_col = movie_col
        self.rating_col = rating_col
        self.features_cols = features_cols or []
        
        # 사용자/영화 인코더 생성
        self.user_encoder = LabelEncoder()
        self.movie_encoder = LabelEncoder()
        
        # ID 인코딩
        self.ratings_df['user_idx'] = self.user_encoder.fit_transform(self.ratings_df[user_col])
        self.ratings_df['movie_idx'] = self.movie_encoder.fit_transform(self.ratings_df[movie_col])
        
        # 평점 정규화
        if normalize_ratings:
            self.ratings_df[rating_col] = (
                (self.ratings_df[rating_col] - min_rating) / (max_rating - min_rating)
            )
        
        # 추가 피처 처리
        if self.features_cols:
            self.scaler = StandardScaler()
            feature_matrix = self.ratings_df[self.features_cols].values
            self.ratings_df[self.features_cols] = self.scaler.fit_transform(feature_matrix)
        else:
            self.scaler = None
        
        # 메타데이터 저장
        self.num_users = len(self.user_encoder.classes_)
        self.num_movies = len(self.movie_encoder.classes_)
        self.min_rating = min_rating
        self.max_rating = max_rating
        
        logger.info(f"데이터셋 생성 완료 - 사용자: {self.num_users}, 영화: {self.num_movies}, 샘플: {len(self.ratings_df)}")
    
    def __len__(self) -> int:
        return len(self.ratings_df)
    
    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        """단일 샘플 반환"""
        row = self.ratings_df.iloc[idx]
        
        item = {
            'user_id': torch.tensor(row['user_idx'], dtype=torch.long),
            'movie_id': torch.tensor(row['movie_idx'], dtype=torch.long),
            'rating': torch.tensor(row[self.rating_col], dtype=torch.float32)
        }
        
        # 추가 피처가 있는 경우
        if self.features_cols:
            features = torch.tensor(row[self.features_cols].values, dtype=torch.float32)
            item['features'] = features
        
        return item
    
    def get_user_items(self, user_id: int) -> List[int]:
        """특정 사용자가 평가한 영화 목록 반환"""
        try:
            user_idx = self.user_encoder.transform([user_id])[0]
            user_movies = self.ratings_df[self.ratings_df['user_idx'] == user_idx]['movie_idx'].tolist()
            return user_movies
        except ValueError:
            return []
    
    def get_movie_users(self, movie_id: int) -> List[int]:
        """특정 영화를 평가한 사용자 목록 반환"""
        try:
            movie_idx = self.movie_encoder.transform([movie_id])[0]
            movie_users = self.ratings_df[self.ratings_df['movie_idx'] == movie_idx]['user_idx'].tolist()
            return movie_users
        except ValueError:
            return []
    
    def get_user_stats(self) -> Dict[str, float]:
        """사용자 통계 반환"""
        user_ratings = self.ratings_df.groupby('user_idx')[self.rating_col].agg(['count', 'mean', 'std']).fillna(0)
        return {
            'avg_ratings_per_user': user_ratings['count'].mean(),
            'avg_user_rating': user_ratings['mean'].mean(),
            'rating_std': user_ratings['std'].mean()
        }
    
    def get_movie_stats(self) -> Dict[str, float]:
        """영화 통계 반환"""
        movie_ratings = self.ratings_df.groupby('movie_idx')[self.rating_col].agg(['count', 'mean', 'std']).fillna(0)
        return {
            'avg_ratings_per_movie': movie_ratings['count'].mean(),
            'avg_movie_rating': movie_ratings['mean'].mean(),
            'rating_std': movie_ratings['std'].mean()
        }


class NegativeSamplingDataset(Dataset):
    """네거티브 샘플링을 포함한 데이터셋"""
    
    def __init__(
        self,
        positive_interactions: pd.DataFrame,
        num_negatives: int = 4,
        user_col: str = 'user_id',
        movie_col: str = 'content_id',
        rating_col: str = 'rating'
    ):
        """
        Args:
            positive_interactions: 긍정적 상호작용 데이터
            num_negatives: 긍정 샘플당 네거티브 샘플 수
            user_col: 사용자 ID 컬럼
            movie_col: 영화 ID 컬럼
            rating_col: 평점 컬럼
        """
        self.positive_df = positive_interactions.copy()
        self.num_negatives = num_negatives
        self.user_col = user_col
        self.movie_col = movie_col
        self.rating_col = rating_col
        
        # 인코더 생성
        self.user_encoder = LabelEncoder()
        self.movie_encoder = LabelEncoder()
        
        # 전체 사용자/영화 집합
        all_users = positive_interactions[user_col].unique()
        all_movies = positive_interactions[movie_col].unique()
        
        self.user_encoder.fit(all_users)
        self.movie_encoder.fit(all_movies)
        
        self.num_users = len(all_users)
        self.num_movies = len(all_movies)
        
        # 긍정적 상호작용 매트릭스 생성
        self.user_items = self.positive_df.groupby(user_col)[movie_col].apply(set).to_dict()
        
        # 네거티브 샘플 생성
        self._generate_samples()
    
    def _generate_samples(self):
        """긍정/네거티브 샘플 생성"""
        samples = []
        
        for _, row in self.positive_df.iterrows():
            user_id = row[self.user_col]
            movie_id = row[self.movie_col]
            rating = row[self.rating_col]
            
            # 긍정 샘플 추가
            user_idx = self.user_encoder.transform([user_id])[0]
            movie_idx = self.movie_encoder.transform([movie_id])[0]
            
            samples.append({
                'user_idx': user_idx,
                'movie_idx': movie_idx,
                'rating': rating,
                'label': 1.0  # 긍정
            })
            
            # 네거티브 샘플 생성
            user_seen_movies = self.user_items.get(user_id, set())
            all_movies = set(self.movie_encoder.classes_)
            unseen_movies = list(all_movies - user_seen_movies)
            
            # 랜덤하게 네거티브 샘플 선택
            if len(unseen_movies) >= self.num_negatives:
                neg_movies = np.random.choice(unseen_movies, self.num_negatives, replace=False)
            else:
                neg_movies = unseen_movies + list(np.random.choice(
                    unseen_movies, self.num_negatives - len(unseen_movies), replace=True
                ))
            
            for neg_movie in neg_movies:
                neg_movie_idx = self.movie_encoder.transform([neg_movie])[0]
                samples.append({
                    'user_idx': user_idx,
                    'movie_idx': neg_movie_idx,
                    'rating': 0.0,  # 네거티브 샘플의 가상 평점
                    'label': 0.0  # 네거티브
                })
        
        self.samples = samples
        logger.info(f"샘플 생성 완료 - 총 {len(samples)}개 (긍정: {len(self.positive_df)}, 네거티브: {len(samples) - len(self.positive_df)})")
    
    def __len__(self) -> int:
        return len(self.samples)
    
    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        sample = self.samples[idx]
        return {
            'user_id': torch.tensor(sample['user_idx'], dtype=torch.long),
            'movie_id': torch.tensor(sample['movie_idx'], dtype=torch.long),
            'rating': torch.tensor(sample['rating'], dtype=torch.float32),
            'label': torch.tensor(sample['label'], dtype=torch.float32)
        }


class SequentialDataset(Dataset):
    """시퀀셜 추천을 위한 데이터셋"""
    
    def __init__(
        self,
        interactions_df: pd.DataFrame,
        sequence_length: int = 10,
        user_col: str = 'user_id',
        movie_col: str = 'content_id',
        timestamp_col: str = 'timestamp',
        rating_col: str = 'rating'
    ):
        """
        Args:
            interactions_df: 상호작용 데이터
            sequence_length: 시퀀스 길이
            user_col: 사용자 ID 컬럼
            movie_col: 영화 ID 컬럼
            timestamp_col: 타임스탬프 컬럼
            rating_col: 평점 컬럼
        """
        self.sequence_length = sequence_length
        self.movie_encoder = LabelEncoder()
        
        # 영화 ID 인코딩
        all_movies = interactions_df[movie_col].unique()
        self.movie_encoder.fit(all_movies)
        self.num_movies = len(all_movies)
        
        # 사용자별로 시간순 정렬된 시퀀스 생성
        sequences = []
        
        for user_id in interactions_df[user_col].unique():
            user_data = interactions_df[interactions_df[user_col] == user_id].copy()
            
            if timestamp_col in user_data.columns:
                user_data = user_data.sort_values(timestamp_col)
            
            user_movies = self.movie_encoder.transform(user_data[movie_col])
            user_ratings = user_data[rating_col].values
            
            # 시퀀스 생성 (슬라이딩 윈도우)
            for i in range(len(user_movies) - sequence_length):
                seq_movies = user_movies[i:i+sequence_length]
                seq_ratings = user_ratings[i:i+sequence_length] 
                target_movie = user_movies[i+sequence_length]
                target_rating = user_ratings[i+sequence_length]
                
                sequences.append({
                    'sequence': seq_movies,
                    'ratings': seq_ratings,
                    'target_movie': target_movie,
                    'target_rating': target_rating,
                    'user_id': user_id
                })
        
        self.sequences = sequences
        logger.info(f"시퀀셜 데이터셋 생성 완료 - {len(sequences)}개 시퀀스")
    
    def __len__(self) -> int:
        return len(self.sequences)
    
    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        seq = self.sequences[idx]
        return {
            'sequence': torch.tensor(seq['sequence'], dtype=torch.long),
            'ratings': torch.tensor(seq['ratings'], dtype=torch.float32),
            'target_movie': torch.tensor(seq['target_movie'], dtype=torch.long),
            'target_rating': torch.tensor(seq['target_rating'], dtype=torch.float32)
        }


def create_data_loaders(
    train_df: pd.DataFrame,
    val_df: Optional[pd.DataFrame] = None,
    test_df: Optional[pd.DataFrame] = None,
    dataset_type: str = 'rating',
    batch_size: int = 256,
    num_workers: int = 4,
    **dataset_kwargs
) -> Dict[str, DataLoader]:
    """
    데이터로더 생성 함수
    
    Args:
        train_df: 훈련 데이터
        val_df: 검증 데이터
        test_df: 테스트 데이터
        dataset_type: 데이터셋 타입 ('rating', 'negative_sampling', 'sequential')
        batch_size: 배치 크기
        num_workers: 워커 수
        **dataset_kwargs: 데이터셋별 추가 인자
        
    Returns:
        데이터로더 딕셔너리
    """
    loaders = {}
    
    # 데이터셋 클래스 선택
    if dataset_type == 'rating':
        DatasetClass = MovieRatingDataset
    elif dataset_type == 'negative_sampling':
        DatasetClass = NegativeSamplingDataset
    elif dataset_type == 'sequential':
        DatasetClass = SequentialDataset
    else:
        raise ValueError(f"지원하지 않는 데이터셋 타입: {dataset_type}")
    
    # 훈련 데이터로더
    train_dataset = DatasetClass(train_df, **dataset_kwargs)
    loaders['train'] = DataLoader(
        train_dataset, 
        batch_size=batch_size, 
        shuffle=True, 
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available()
    )
    
    # 검증 데이터로더
    if val_df is not None:
        val_dataset = DatasetClass(val_df, **dataset_kwargs)
        loaders['val'] = DataLoader(
            val_dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers,
            pin_memory=torch.cuda.is_available()
        )
    
    # 테스트 데이터로더
    if test_df is not None:
        test_dataset = DatasetClass(test_df, **dataset_kwargs)
        loaders['test'] = DataLoader(
            test_dataset,
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers,
            pin_memory=torch.cuda.is_available()
        )
    
    # 메타데이터 저장
    loaders['metadata'] = {
        'num_users': train_dataset.num_users,
        'num_movies': train_dataset.num_movies,
        'train_size': len(train_dataset),
        'val_size': len(val_dataset) if val_df is not None else 0,
        'test_size': len(test_dataset) if test_df is not None else 0
    }
    
    logger.info(f"데이터로더 생성 완료 - {dataset_type} 타입")
    return loaders


def prepare_data_from_watch_log(
    csv_path: str,
    test_ratio: float = 0.2,
    val_ratio: float = 0.1,
    min_interactions: int = 5
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    watch_log.csv에서 훈련/검증/테스트 데이터 준비
    
    Args:
        csv_path: CSV 파일 경로
        test_ratio: 테스트 데이터 비율
        val_ratio: 검증 데이터 비율
        min_interactions: 사용자/영화별 최소 상호작용 수
        
    Returns:
        (train_df, val_df, test_df)
    """
    logger.info(f"데이터 로딩: {csv_path}")
    df = pd.read_csv(csv_path)
    
    # 데이터 전처리
    logger.info(f"원시 데이터 크기: {len(df)}")
    
    # 최소 상호작용 필터링
    user_counts = df['user_id'].value_counts()
    movie_counts = df['content_id'].value_counts()
    
    valid_users = user_counts[user_counts >= min_interactions].index
    valid_movies = movie_counts[movie_counts >= min_interactions].index
    
    df_filtered = df[
        (df['user_id'].isin(valid_users)) & 
        (df['content_id'].isin(valid_movies))
    ].copy()
    
    logger.info(f"필터링 후 데이터 크기: {len(df_filtered)}")
    logger.info(f"사용자 수: {df_filtered['user_id'].nunique()}")
    logger.info(f"영화 수: {df_filtered['content_id'].nunique()}")
    
    # 데이터 분할 (시간 기반 또는 랜덤)
    if 'timestamp' in df_filtered.columns:
        # 시간 기반 분할
        df_sorted = df_filtered.sort_values('timestamp')
        n_total = len(df_sorted)
        
        train_end = int(n_total * (1 - test_ratio - val_ratio))
        val_end = int(n_total * (1 - test_ratio))
        
        train_df = df_sorted.iloc[:train_end].copy()
        val_df = df_sorted.iloc[train_end:val_end].copy()
        test_df = df_sorted.iloc[val_end:].copy()
    else:
        # 랜덤 분할
        df_shuffled = df_filtered.sample(frac=1, random_state=42).reset_index(drop=True)
        n_total = len(df_shuffled)
        
        train_end = int(n_total * (1 - test_ratio - val_ratio))
        val_end = int(n_total * (1 - test_ratio))
        
        train_df = df_shuffled.iloc[:train_end].copy()
        val_df = df_shuffled.iloc[train_end:val_end].copy()
        test_df = df_shuffled.iloc[val_end:].copy()
    
    logger.info(f"데이터 분할 완료 - 훈련: {len(train_df)}, 검증: {len(val_df)}, 테스트: {len(test_df)}")
    
    return train_df, val_df, test_df


# 유틸리티 함수들
def collate_fn_rating(batch: List[Dict[str, torch.Tensor]]) -> Dict[str, torch.Tensor]:
    """평점 예측용 배치 collate 함수"""
    return {
        'user_id': torch.stack([item['user_id'] for item in batch]),
        'movie_id': torch.stack([item['movie_id'] for item in batch]),
        'rating': torch.stack([item['rating'] for item in batch])
    }


def collate_fn_sequence(batch: List[Dict[str, torch.Tensor]]) -> Dict[str, torch.Tensor]:
    """시퀀셜 추천용 배치 collate 함수"""
    return {
        'sequence': torch.stack([item['sequence'] for item in batch]),
        'ratings': torch.stack([item['ratings'] for item in batch]),
        'target_movie': torch.stack([item['target_movie'] for item in batch]),
        'target_rating': torch.stack([item['target_rating'] for item in batch])
    }
