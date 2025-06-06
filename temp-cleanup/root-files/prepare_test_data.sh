#!/bin/bash

# 2단계 피처 스토어 테스트 데이터 준비 스크립트
# prepare_test_data.sh

echo "🗃️ 2단계 피처 스토어 테스트 데이터 준비 중..."

# 테스트 데이터 디렉토리 생성
docker-compose exec dev bash -c "
mkdir -p /app/data/test
mkdir -p /app/data/test/sample_data
mkdir -p /app/data/test/integration_test
mkdir -p /app/data/test/unit_test
"

# 테스트 데이터 생성 스크립트 실행
docker-compose exec dev python -c "
import sys
sys.path.append('/app/src')

import json
import os
from pathlib import Path

# 테스트 데이터 디렉토리 확인
test_data_dir = Path('/app/data/test')
test_data_dir.mkdir(exist_ok=True)

print('📋 테스트 데이터 생성 중...')

# 기본 테스트 영화 데이터
test_movies = [
    {
        'id': 1, 
        'title': 'Test Movie 1', 
        'release_date': '2023-01-15',
        'vote_average': 8.5, 
        'vote_count': 1500, 
        'popularity': 45.2,
        'genres': [
            {'id': 28, 'name': 'Action'}, 
            {'id': 12, 'name': 'Adventure'}
        ],
        'runtime': 120, 
        'budget': 50000000, 
        'revenue': 150000000,
        'overview': 'An exciting action adventure movie.',
        'adult': False,
        'original_language': 'en',
        'production_companies': [
            {'id': 1, 'name': 'Test Studios'}
        ],
        'production_countries': [
            {'iso_3166_1': 'US', 'name': 'United States'}
        ]
    },
    {
        'id': 2, 
        'title': 'Test Movie 2', 
        'release_date': '2023-06-20',
        'vote_average': 7.2, 
        'vote_count': 800, 
        'popularity': 32.1,
        'genres': [
            {'id': 35, 'name': 'Comedy'}, 
            {'id': 10749, 'name': 'Romance'}
        ],
        'runtime': 95, 
        'budget': 20000000, 
        'revenue': 75000000,
        'overview': 'A heartwarming romantic comedy.',
        'adult': False,
        'original_language': 'en',
        'production_companies': [
            {'id': 2, 'name': 'Comedy Films Inc.'}
        ],
        'production_countries': [
            {'iso_3166_1': 'US', 'name': 'United States'}
        ]
    },
    {
        'id': 3, 
        'title': 'Test Movie 3', 
        'release_date': '2023-12-01',
        'vote_average': 9.0, 
        'vote_count': 2500, 
        'popularity': 75.8,
        'genres': [
            {'id': 878, 'name': 'Science Fiction'}, 
            {'id': 53, 'name': 'Thriller'}
        ],
        'runtime': 140, 
        'budget': 80000000, 
        'revenue': 250000000,
        'overview': 'A mind-bending sci-fi thriller.',
        'adult': False,
        'original_language': 'en',
        'production_companies': [
            {'id': 3, 'name': 'Sci-Fi Productions'}
        ],
        'production_countries': [
            {'iso_3166_1': 'US', 'name': 'United States'}
        ]
    }
]

# 기본 테스트 데이터 저장
sample_movies_path = test_data_dir / 'sample_movies.json'
with open(sample_movies_path, 'w', encoding='utf-8') as f:
    json.dump(test_movies, f, indent=2, ensure_ascii=False)

print(f'✅ 기본 테스트 데이터 저장: {sample_movies_path}')

# 성능 테스트용 대용량 데이터 생성
performance_movies = []
for i in range(1000):
    performance_movies.append({
        'id': i + 1000,
        'title': f'Performance Test Movie {i+1}',
        'release_date': f'202{(i % 4) + 1}-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}',
        'vote_average': round(5.0 + (i % 50) * 0.1, 1),
        'vote_count': 100 + i * 10,
        'popularity': round(10.0 + (i % 90), 1),
        'genres': [
            {'id': 28 + (i % 10), 'name': f'Genre{(i % 10) + 1}'}
        ],
        'runtime': 90 + (i % 60),
        'budget': 1000000 + i * 50000,
        'revenue': 2000000 + i * 100000,
        'overview': f'Performance test movie number {i+1}.',
        'adult': False,
        'original_language': 'en'
    })

performance_data_path = test_data_dir / 'performance_test_movies.json'
with open(performance_data_path, 'w', encoding='utf-8') as f:
    json.dump(performance_movies, f, indent=2)

print(f'✅ 성능 테스트 데이터 저장: {performance_data_path} ({len(performance_movies)}개)')

# 통합 테스트용 데이터
integration_data = {
    'test_scenario_1': {
        'name': 'Basic Feature Engineering',
        'movies': test_movies[:2],
        'expected_features': ['vote_average', 'popularity', 'runtime', 'budget', 'revenue']
    },
    'test_scenario_2': {
        'name': 'Genre Processing',
        'movies': test_movies,
        'expected_features': ['genre_Action', 'genre_Comedy', 'genre_Science Fiction']
    }
}

integration_data_path = test_data_dir / 'integration_test_scenarios.json'
with open(integration_data_path, 'w', encoding='utf-8') as f:
    json.dump(integration_data, f, indent=2, ensure_ascii=False)

print(f'✅ 통합 테스트 시나리오 저장: {integration_data_path}')

# 테스트 설정 파일
test_config = {
    'feature_engineering': {
        'temporal_features': True,
        'statistical_features': True,
        'interaction_features': True,
        'genre_encoding': 'one_hot'
    },
    'feature_store': {
        'base_path': '/app/data/test/feature_store',
        'cache_enabled': False,
        'compression': 'snappy'
    },
    'performance_targets': {
        'processing_speed': 10,  # records per second
        'memory_limit': 2048,    # MB
        'api_response_time': 50  # milliseconds
    }
}

test_config_path = test_data_dir / 'test_config.json'
with open(test_config_path, 'w', encoding='utf-8') as f:
    json.dump(test_config, f, indent=2)

print(f'✅ 테스트 설정 파일 저장: {test_config_path}')

# 빈 결과 디렉토리 생성
result_dirs = [
    '/app/data/test/results',
    '/app/data/test/feature_store',
    '/app/data/test/temp'
]

for result_dir in result_dirs:
    Path(result_dir).mkdir(exist_ok=True)
    print(f'✅ 결과 디렉토리 생성: {result_dir}')

print('\\n🎉 모든 테스트 데이터 준비 완료!')
print('\\n📋 생성된 파일들:')
print(f'  - {sample_movies_path}')
print(f'  - {performance_data_path}')
print(f'  - {integration_data_path}')
print(f'  - {test_config_path}')
print('\\n📁 생성된 디렉토리들:')
for result_dir in result_dirs:
    print(f'  - {result_dir}')
"

echo "✅ 테스트 데이터 준비 완료!"
echo ""
echo "📋 다음 명령어로 데이터를 확인할 수 있습니다:"
echo "docker-compose exec dev ls -la /app/data/test/"
echo "docker-compose exec dev cat /app/data/test/sample_movies.json"
