#!/usr/bin/env python3
"""
2단계 피처 스토어 핵심 기능 테스트
test_feature_store.py
"""

import sys
import os
import time
import json
import traceback
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

def test_imports():
    """필수 모듈 import 테스트"""
    print("🔍 모듈 import 테스트...")
    
    try:
        # 기본 패키지들
        import pandas as pd
        import numpy as np
        import redis
        import psycopg2
        
        # 피처 스토어 모듈들
        from features.engineering.tmdb_processor import AdvancedTMDBPreProcessor
        from features.store.feature_store import SimpleFeatureStore, FeatureStoreConfig
        from features.pipeline.feature_pipeline import FeaturePipeline
        from features.validation.feature_validator import FeatureValidator
        
        print("✅ 모든 필수 모듈 import 성공")
        return True
        
    except ImportError as e:
        print(f"❌ 모듈 import 실패: {e}")
        return False

def test_database_connections():
    """데이터베이스 연결 테스트"""
    print("🔗 데이터베이스 연결 테스트...")
    
    # Redis 연결 테스트
    try:
        import redis
        r = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)
        r.ping()
        print("✅ Redis 연결 성공")
    except Exception as e:
        print(f"❌ Redis 연결 실패: {e}")
        return False
    
    # PostgreSQL 연결 테스트
    try:
        import psycopg2
        conn = psycopg2.connect(
            host='postgres',
            database='mlops',
            user='mlops_user',
            password='mlops_password'
        )
        cursor = conn.cursor()
        cursor.execute('SELECT version();')
        version = cursor.fetchone()
        cursor.close()
        conn.close()
        print("✅ PostgreSQL 연결 성공")
    except Exception as e:
        print(f"❌ PostgreSQL 연결 실패: {e}")
        return False
    
    return True

def test_feature_engineering():
    """피처 엔지니어링 테스트"""
    print("🔬 피처 엔지니어링 테스트...")
    
    try:
        from features.engineering.tmdb_processor import AdvancedTMDBPreProcessor
        
        # 테스트 데이터 생성
        test_movies = [
            {
                'id': 1,
                'title': 'Test Movie 1',
                'release_date': '2023-06-15',
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
                'original_language': 'en'
            },
            {
                'id': 2,
                'title': 'Test Movie 2',
                'release_date': '2023-12-20',
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
                'original_language': 'en'
            }
        ]
        
        # 프로세서 초기화
        config = {
            'temporal_features': True,
            'statistical_features': True,
            'interaction_features': True
        }
        processor = AdvancedTMDBPreProcessor(config)
        
        # 피처 생성
        start_time = time.time()
        features_df = processor.process_movies(test_movies)
        processing_time = time.time() - start_time
        
        # 결과 검증
        assert len(features_df) == len(test_movies), "피처 데이터 행 수가 일치하지 않음"
        assert len(features_df.columns) > 10, "생성된 피처 수가 너무 적음"
        
        print(f"✅ 피처 엔지니어링 성공:")
        print(f"   - 처리 시간: {processing_time:.2f}초")
        print(f"   - 생성된 피처 수: {len(features_df.columns)}개")
        print(f"   - 처리량: {len(test_movies)/processing_time:.1f} movies/second")
        
        return True, features_df
        
    except Exception as e:
        print(f"❌ 피처 엔지니어링 실패: {e}")
        traceback.print_exc()
        return False, None

def test_feature_store():
    """피처 스토어 테스트"""
    print("🏪 피처 스토어 테스트...")
    
    try:
        from features.store.feature_store import SimpleFeatureStore, FeatureStoreConfig
        
        # 피처 스토어 설정
        config = FeatureStoreConfig(
            base_path='/app/data/feature_store',
            cache_enabled=True,
            compression='snappy'
        )
        
        # 피처 스토어 초기화
        store = SimpleFeatureStore(config)
        
        # 테스트 피처 데이터
        test_features = {
            'movie_id': 1,
            'title': 'Test Movie',
            'release_year': 2023,
            'genre_action': 1,
            'genre_comedy': 0,
            'vote_average': 8.5,
            'popularity_score': 45.2,
            'runtime_minutes': 120,
            'budget_millions': 50.0,
            'revenue_millions': 150.0,
            'roi': 3.0
        }
        
        feature_group = 'test_movies'
        
        # 피처 저장 테스트
        store.save_features(feature_group, test_features)
        print("✅ 피처 저장 성공")
        
        # 피처 조회 테스트
        loaded_features = store.get_features([feature_group])
        assert loaded_features is not None, "피처 조회 실패"
        print("✅ 피처 조회 성공")
        
        # 메타데이터 테스트
        metadata = store.get_feature_metadata(feature_group)
        assert metadata is not None, "메타데이터 조회 실패"
        print("✅ 메타데이터 관리 성공")
        
        # 버전 관리 테스트
        versions = store.list_feature_versions(feature_group)
        assert len(versions) > 0, "버전 관리 실패"
        print("✅ 버전 관리 성공")
        
        return True
        
    except Exception as e:
        print(f"❌ 피처 스토어 테스트 실패: {e}")
        traceback.print_exc()
        return False

def test_feature_pipeline():
    """피처 파이프라인 테스트"""
    print("🔄 피처 파이프라인 테스트...")
    
    try:
        from features.pipeline.feature_pipeline import FeaturePipeline
        
        # 파이프라인 설정
        pipeline_config = {
            'stages': [
                {
                    'name': 'data_validation',
                    'type': 'DataValidationStage',
                    'config': {}
                },
                {
                    'name': 'feature_extraction',
                    'type': 'FeatureExtractionStage',
                    'config': {}
                }
            ],
            'parallel_execution': False
        }
        
        # 파이프라인 생성
        pipeline = FeaturePipeline(pipeline_config)
        
        # 테스트 데이터
        test_data = [
            {
                'id': 1,
                'title': 'Pipeline Test Movie',
                'release_date': '2023-01-01',
                'vote_average': 8.0,
                'vote_count': 1000,
                'popularity': 40.0,
                'genres': [{'id': 28, 'name': 'Action'}],
                'runtime': 120
            }
        ]
        
        # 파이프라인 실행
        start_time = time.time()
        results = pipeline.run(test_data)
        processing_time = time.time() - start_time
        
        assert results is not None, "파이프라인 실행 결과가 None"
        
        print(f"✅ 피처 파이프라인 성공:")
        print(f"   - 처리 시간: {processing_time:.2f}초")
        print(f"   - 실행된 스테이지: {len(pipeline_config['stages'])}개")
        
        return True
        
    except Exception as e:
        print(f"❌ 피처 파이프라인 테스트 실패: {e}")
        traceback.print_exc()
        return False

def test_feature_validation():
    """피처 검증 테스트"""
    print("✅ 피처 검증 테스트...")
    
    try:
        from features.validation.feature_validator import FeatureValidator
        
        # 검증기 초기화
        validator = FeatureValidator()
        
        # 테스트 피처 데이터
        test_features = {
            'vote_average': 8.5,
            'vote_count': 1500,
            'popularity': 45.2,
            'runtime': 120,
            'budget': 50000000,
            'revenue': 150000000,
            'release_year': 2023
        }
        
        # 기본 검증
        validation_result = validator.validate_features(test_features)
        
        assert validation_result['is_valid'], f"피처 검증 실패: {validation_result['errors']}"
        
        print(f"✅ 피처 검증 성공:")
        print(f"   - 검증된 피처 수: {len(test_features)}개")
        print(f"   - 품질 점수: {validation_result.get('quality_score', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 피처 검증 테스트 실패: {e}")
        traceback.print_exc()
        return False

def test_end_to_end_workflow():
    """End-to-End 워크플로우 테스트"""
    print("🎭 End-to-End 워크플로우 테스트...")
    
    try:
        from features.engineering.tmdb_processor import AdvancedTMDBPreProcessor
        from features.store.feature_store import SimpleFeatureStore, FeatureStoreConfig
        from features.validation.feature_validator import FeatureValidator
        
        # 1. 원시 데이터 준비
        raw_movies = [
            {
                'id': 999,
                'title': 'E2E Test Movie',
                'release_date': '2023-12-01',
                'vote_average': 9.0,
                'vote_count': 2000,
                'popularity': 75.5,
                'genres': [
                    {'id': 28, 'name': 'Action'},
                    {'id': 878, 'name': 'Science Fiction'}
                ],
                'runtime': 150,
                'budget': 100000000,
                'revenue': 300000000,
                'overview': 'An epic sci-fi action movie.',
                'adult': False,
                'original_language': 'en'
            }
        ]
        
        # 2. 피처 엔지니어링
        processor = AdvancedTMDBPreProcessor({})
        features_df = processor.process_movies(raw_movies)
        print("✅ 1단계: 피처 엔지니어링 완료")
        
        # 3. 피처 검증
        validator = FeatureValidator()
        feature_dict = features_df.to_dict('records')[0]
        validation_result = validator.validate_features(feature_dict)
        
        if not validation_result['is_valid']:
            raise ValueError(f"피처 검증 실패: {validation_result['errors']}")
        print("✅ 2단계: 피처 검증 완료")
        
        # 4. 피처 스토어 저장
        config = FeatureStoreConfig(base_path='/app/data/feature_store')
        store = SimpleFeatureStore(config)
        
        feature_group = 'e2e_test_movies'
        store.save_features(feature_group, feature_dict)
        print("✅ 3단계: 피처 스토어 저장 완료")
        
        # 5. 피처 조회 및 검증
        loaded_features = store.get_features([feature_group])
        assert loaded_features is not None, "저장된 피처 조회 실패"
        print("✅ 4단계: 피처 조회 완료")
        
        # 6. 메타데이터 확인
        metadata = store.get_feature_metadata(feature_group)
        assert metadata is not None, "메타데이터 조회 실패"
        print("✅ 5단계: 메타데이터 확인 완료")
        
        print("🎉 End-to-End 워크플로우 테스트 성공!")
        return True
        
    except Exception as e:
        print(f"❌ End-to-End 워크플로우 테스트 실패: {e}")
        traceback.print_exc()
        return False

def test_performance_benchmark():
    """성능 벤치마크 테스트"""
    print("⚡ 성능 벤치마크 테스트...")
    
    try:
        from features.engineering.tmdb_processor import AdvancedTMDBPreProcessor
        
        # 대용량 테스트 데이터 생성 (1000개)
        test_movies = []
        for i in range(1000):
            test_movies.append({
                'id': i + 1,
                'title': f'Benchmark Movie {i+1}',
                'release_date': '2023-01-01',
                'vote_average': 7.0 + (i % 30) * 0.1,
                'vote_count': 1000 + i * 10,
                'popularity': 20.0 + (i % 80),
                'genres': [{'id': 28, 'name': 'Action'}],
                'runtime': 90 + (i % 60),
                'budget': 10000000 + i * 100000,
                'revenue': 20000000 + i * 200000,
                'overview': f'Movie description {i}',
                'adult': False,
                'original_language': 'en'
            })
        
        # 성능 측정
        processor = AdvancedTMDBPreProcessor({})
        
        start_time = time.time()
        features_df = processor.process_movies(test_movies)
        end_time = time.time()
        
        duration = end_time - start_time
        throughput = len(test_movies) / duration
        
        print(f"✅ 성능 벤치마크 결과:")
        print(f"   - 처리된 영화 수: {len(test_movies):,}개")
        print(f"   - 총 처리 시간: {duration:.2f}초")
        print(f"   - 처리량: {throughput:.1f} movies/second")
        print(f"   - 생성된 피처 수: {len(features_df.columns)}개")
        print(f"   - 메모리 사용량: ~{features_df.memory_usage(deep=True).sum() / 1024 / 1024:.1f}MB")
        
        # 성능 기준 확인 (1초에 최소 10개 처리)
        if throughput >= 10:
            print("✅ 성능 기준 충족")
            return True
        else:
            print("⚠️ 성능 기준 미달")
            return False
            
    except Exception as e:
        print(f"❌ 성능 벤치마크 테스트 실패: {e}")
        traceback.print_exc()
        return False

def generate_test_report(test_results):
    """테스트 결과 리포트 생성"""
    print("📊 테스트 리포트 생성 중...")
    
    # reports 디렉토리 생성
    reports_dir = Path('reports')
    reports_dir.mkdir(exist_ok=True)
    
    # 테스트 결과 요약
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result)
    failed_tests = total_tests - passed_tests
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    # JSON 리포트
    report_data = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'summary': {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': round(success_rate, 2)
        },
        'test_results': test_results,
        'environment': {
            'python_version': sys.version,
            'platform': sys.platform,
            'working_directory': str(Path.cwd())
        }
    }
    
    # JSON 파일 저장
    json_report_path = reports_dir / 'feature_store_test_results.json'
    with open(json_report_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    
    # 텍스트 리포트 생성
    text_report_path = reports_dir / 'feature_store_test_report.txt'
    with open(text_report_path, 'w', encoding='utf-8') as f:
        f.write("🧪 2단계 피처 스토어 테스트 리포트\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"실행 시간: {report_data['timestamp']}\n\n")
        
        f.write("📊 테스트 결과 요약\n")
        f.write("-" * 20 + "\n")
        f.write(f"총 테스트: {total_tests}개\n")
        f.write(f"성공: {passed_tests}개\n")
        f.write(f"실패: {failed_tests}개\n")
        f.write(f"성공률: {success_rate:.1f}%\n\n")
        
        f.write("📋 상세 결과\n")
        f.write("-" * 20 + "\n")
        for test_name, result in test_results.items():
            status = "✅ 통과" if result else "❌ 실패"
            f.write(f"{status} {test_name}\n")
        
        f.write(f"\n🎯 전체 결과: {'🎉 성공' if failed_tests == 0 else '⚠️ 일부 실패'}\n")
    
    print(f"✅ 테스트 리포트 생성 완료:")
    print(f"   - JSON: {json_report_path}")
    print(f"   - 텍스트: {text_report_path}")

def main():
    """메인 테스트 실행 함수"""
    print("🚀 2단계 피처 스토어 핵심 기능 테스트 시작")
    print("=" * 60)
    
    start_time = time.time()
    test_results = {}
    
    # 테스트 실행
    tests = [
        ("모듈 Import", test_imports),
        ("데이터베이스 연결", test_database_connections),
        ("피처 엔지니어링", lambda: test_feature_engineering()[0]),
        ("피처 스토어", test_feature_store),
        ("피처 파이프라인", test_feature_pipeline),
        ("피처 검증", test_feature_validation),
        ("End-to-End 워크플로우", test_end_to_end_workflow),
        ("성능 벤치마크", test_performance_benchmark)
    ]
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name} 테스트 실행 중...")
        try:
            result = test_func()
            test_results[test_name] = result
            if result:
                print(f"✅ {test_name} 테스트 성공")
            else:
                print(f"❌ {test_name} 테스트 실패")
        except Exception as e:
            print(f"❌ {test_name} 테스트 오류: {e}")
            test_results[test_name] = False
    
    # 결과 요약
    total_time = time.time() - start_time
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result)
    failed_tests = total_tests - passed_tests
    
    print("\n" + "=" * 60)
    print(f"🎯 테스트 완료 - 총 소요시간: {total_time:.2f}초")
    print(f"📊 결과: {passed_tests}/{total_tests} 성공 ({passed_tests/total_tests*100:.1f}%)")
    
    if failed_tests == 0:
        print("🎉 모든 테스트가 성공했습니다!")
    else:
        print(f"⚠️ {failed_tests}개의 테스트가 실패했습니다.")
        print("\n실패한 테스트:")
        for test_name, result in test_results.items():
            if not result:
                print(f"  - {test_name}")
    
    # 리포트 생성
    generate_test_report(test_results)
    
    print(f"\n📋 다음 단계:")
    print(f"  1. API 서버 시작: docker-compose --profile api up -d")
    print(f"  2. 모니터링 시작: docker-compose --profile monitoring up -d")
    print(f"  3. 전체 테스트: ./run_all_feature_store_tests.sh")
    
    return failed_tests == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
