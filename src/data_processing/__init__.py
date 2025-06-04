"""
MLOps Cloud Project - 데이터 처리 모듈

1.1 단계: TMDB API 연동 및 데이터 수집
"""

from .tmdb_api_connector import TMDBAPIConnector, test_tmdb_connection
from .environment_manager import EnvironmentManager, get_tmdb_config, validate_environment
from .response_parser import TMDBResponseParser, MovieData, parse_tmdb_response
from .rate_limiter import RateLimiter, RateLimitConfig, rate_limited

__version__ = "1.0.0"
__author__ = "MLOps Project Team"

# 패키지 레벨 편의 함수들
def create_tmdb_connector(**kwargs):
    """TMDB 커넥터 생성 편의 함수"""
    return TMDBAPIConnector(**kwargs)

def create_response_parser():
    """응답 파서 생성 편의 함수"""
    return TMDBResponseParser()

def create_rate_limiter(**kwargs):
    """Rate Limiter 생성 편의 함수"""
    return RateLimiter(**kwargs)

# 기본 설정으로 인스턴스 생성
default_env_manager = EnvironmentManager()
default_parser = TMDBResponseParser()

__all__ = [
    'TMDBAPIConnector',
    'test_tmdb_connection',
    'EnvironmentManager', 
    'get_tmdb_config',
    'validate_environment',
    'TMDBResponseParser',
    'MovieData',
    'parse_tmdb_response',
    'RateLimiter',
    'RateLimitConfig',
    'rate_limited',
    'create_tmdb_connector',
    'create_response_parser',
    'create_rate_limiter',
    'default_env_manager',
    'default_parser'
]
