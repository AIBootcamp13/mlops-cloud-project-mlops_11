"""Feast 레포지토리 초기화 및 설정"""

import os
import sys
import pandas as pd
from datetime import datetime, timedelta

# 프로젝트 루트를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.features.feast_client import FeastClient


def create_sample_data():
    """샘플 피처 데이터 생성"""
    print("샘플 피처 데이터 생성 중...")
    
    # 현재 watch_log.csv 읽기
    watch_log_path = os.path.join(project_root, "data", "processed", "watch_log.csv")
    
    if not os.path.exists(watch_log_path):
        print(f"오류: {watch_log_path} 파일을 찾을 수 없습니다.")
        return False
    
    df = pd.read_csv(watch_log_path)
    print(f"원시 데이터 로드 완료: {len(df)} 행")
    
    # Feast 클라이언트 생성
    feast_client = FeastClient()
    
    # 피처 계산
    features = feast_client.compute_features_from_raw_data(df)
    
    if not features:
        print("피처 계산 실패")
        return False
    
    # Feast 데이터 디렉토리 생성
    feast_data_dir = os.path.join(project_root, "data", "feast")
    os.makedirs(feast_data_dir, exist_ok=True)
    
    # 계산된 피처를 파일로 저장
    movie_features_path = os.path.join(feast_data_dir, "movie_features.parquet")
    user_features_path = os.path.join(feast_data_dir, "user_features.parquet")
    
    features['movie_features'].to_parquet(movie_features_path, index=False)
    features['user_features'].to_parquet(user_features_path, index=False)
    
    print(f"영화 피처 저장: {movie_features_path}")
    print(f"사용자 피처 저장: {user_features_path}")
    
    return True


def init_feast_repo():
    """Feast 레포지토리 초기화"""
    print("Feast 레포지토리 초기화 중...")
    
    feast_repo_path = os.path.join(project_root, "feast_repo")
    
    # Feast 레포지토리로 이동
    original_cwd = os.getcwd()
    os.chdir(feast_repo_path)
    
    try:
        # Feast apply 실행
        os.system("feast apply")
        print("Feast 피처 정의가 적용되었습니다.")
        
        # 샘플 데이터 생성
        os.chdir(project_root)
        if create_sample_data():
            print("샘플 데이터 생성 완료")
        
        # 다시 feast_repo로 이동하여 materialize 실행
        os.chdir(feast_repo_path)
        
        # 과거 7일간의 데이터를 실체화
        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)
        
        feast_client = FeastClient()
        feast_client.materialize_features(start_time, end_time)
        
        print("Feast 초기화가 완료되었습니다!")
        return True
        
    except Exception as e:
        print(f"Feast 초기화 실패: {e}")
        return False
        
    finally:
        os.chdir(original_cwd)


if __name__ == "__main__":
    init_feast_repo()
