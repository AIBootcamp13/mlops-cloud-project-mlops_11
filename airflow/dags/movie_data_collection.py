"""
Movie Data Collection DAG
기존 my-mlops의 data-prepare 로직을 Airflow DAG로 구현
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta
import sys
import os
import logging

# 경로 설정
sys.path.append('/app')
sys.path.append('/app/src')

# 기본 설정
default_args = {
    'owner': 'movie-mlops-team',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# DAG 정의
dag = DAG(
    'movie_data_collection',
    default_args=default_args,
    description='영화 데이터 수집 및 처리 파이프라인 (기존 my-mlops 로직)',
    schedule_interval=timedelta(days=1),  # 매일 실행
    catchup=False,
    max_active_runs=1,
    tags=['movie', 'data-collection', 'tmdb']
)

def collect_tmdb_data(**context):
    """
    TMDB API에서 영화 데이터 수집
    기존 crawler.py 로직 사용
    """
    try:
        from src.data.collectors.tmdb_collector import TMDBCrawler
        
        # 환경 변수 확인
        api_key = os.getenv('TMDB_API_KEY')
        if not api_key:
            raise ValueError("TMDB_API_KEY 환경 변수가 설정되지 않았습니다.")
        
        # 크롤러 초기화 및 실행
        tmdb_crawler = TMDBCrawler()
        
        # 인기 영화 데이터 수집 (1-3페이지)
        result = tmdb_crawler.get_bulk_popular_movies(start_page=1, end_page=3)
        
        # 결과 저장
        output_dir = "/app/data/raw/tmdb"
        os.makedirs(output_dir, exist_ok=True)
        
        tmdb_crawler.save_movies_to_json_file(result, output_dir, "popular")
        
        logging.info(f"TMDB 데이터 수집 완료: {len(result)}개 영화")
        
        # XCom으로 다음 태스크에 데이터 전달
        return {
            "movies_count": len(result),
            "output_file": f"{output_dir}/popular.json",
            "collection_date": datetime.now().isoformat()
        }
        
    except Exception as e:
        logging.error(f"TMDB 데이터 수집 실패: {e}")
        raise

def process_tmdb_data(**context):
    """
    수집된 TMDB 데이터 전처리
    기존 preprocessing.py 로직 사용
    """
    try:
        import json
        from src.data.processors.tmdb_processor import TMDBPreProcessor
        
        # 이전 태스크에서 수집된 데이터 정보 가져오기
        ti = context['ti']
        collection_info = ti.xcom_pull(task_ids='collect_tmdb_data')
        
        if not collection_info:
            raise ValueError("이전 태스크에서 데이터 정보를 가져올 수 없습니다.")
        
        # 수집된 데이터 로드
        input_file = collection_info['output_file']
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        movies = data.get('movies', [])
        if not movies:
            raise ValueError("처리할 영화 데이터가 없습니다.")
        
        # 전처리 실행
        tmdb_preprocessor = TMDBPreProcessor(movies)
        tmdb_preprocessor.run()
        
        # 결과 저장
        output_dir = "/app/data/processed"
        os.makedirs(output_dir, exist_ok=True)
        
        tmdb_preprocessor.save("watch_log")
        
        # 시각화 (선택적)
        try:
            tmdb_preprocessor.plot()
        except Exception as plot_error:
            logging.warning(f"시각화 생성 실패 (계속 진행): {plot_error}")
        
        logging.info(f"TMDB 데이터 전처리 완료: {len(movies)}개 영화")
        
        return {
            "processed_movies": len(movies),
            "output_file": f"{output_dir}/watch_log.csv",
            "processing_date": datetime.now().isoformat()
        }
        
    except Exception as e:
        logging.error(f"TMDB 데이터 전처리 실패: {e}")
        raise

def validate_processed_data(**context):
    """
    처리된 데이터 검증
    """
    try:
        import pandas as pd
        
        # 이전 태스크에서 처리된 데이터 정보 가져오기
        ti = context['ti']
        processing_info = ti.xcom_pull(task_ids='process_tmdb_data')
        
        if not processing_info:
            raise ValueError("이전 태스크에서 처리 정보를 가져올 수 없습니다.")
        
        # 처리된 데이터 파일 확인
        output_file = processing_info['output_file']
        
        if not os.path.exists(output_file):
            raise FileNotFoundError(f"처리된 데이터 파일을 찾을 수 없습니다: {output_file}")
        
        # 데이터 로드 및 기본 검증
        df = pd.read_csv(output_file)
        
        # 기본 통계
        row_count = len(df)
        col_count = len(df.columns)
        
        if row_count == 0:
            raise ValueError("처리된 데이터가 비어있습니다.")
        
        # 필수 컬럼 확인 (실제 구조에 따라 조정 필요)
        expected_columns = ['user_id', 'content_id']  # 예상 컬럼들
        missing_columns = [col for col in expected_columns if col not in df.columns]
        
        if missing_columns:
            logging.warning(f"일부 예상 컬럼이 없습니다: {missing_columns}")
        
        logging.info(f"데이터 검증 완료: {row_count}행, {col_count}열")
        
        return {
            "validation_status": "success",
            "row_count": row_count,
            "col_count": col_count,
            "columns": list(df.columns),
            "validation_date": datetime.now().isoformat()
        }
        
    except Exception as e:
        logging.error(f"데이터 검증 실패: {e}")
        raise

# 태스크 정의
collect_task = PythonOperator(
    task_id='collect_tmdb_data',
    python_callable=collect_tmdb_data,
    dag=dag,
    doc_md="""
    ## TMDB 데이터 수집
    
    TMDB API를 사용하여 인기 영화 데이터를 수집합니다.
    
    **입력**: TMDB API
    **출력**: `/app/data/raw/tmdb/popular.json`
    **의존성**: TMDB_API_KEY 환경 변수
    """
)

process_task = PythonOperator(
    task_id='process_tmdb_data',
    python_callable=process_tmdb_data,
    dag=dag,
    doc_md="""
    ## TMDB 데이터 전처리
    
    수집된 영화 데이터를 ML 모델에서 사용할 수 있는 형태로 전처리합니다.
    
    **입력**: `/app/data/raw/tmdb/popular.json`
    **출력**: `/app/data/processed/watch_log.csv`
    """
)

validate_task = PythonOperator(
    task_id='validate_processed_data',
    python_callable=validate_processed_data,
    dag=dag,
    doc_md="""
    ## 처리된 데이터 검증
    
    전처리된 데이터의 품질을 검증합니다.
    
    **입력**: `/app/data/processed/watch_log.csv`
    **출력**: 검증 결과 로그
    """
)

# 데이터 백업 태스크 (선택적)
backup_task = BashOperator(
    task_id='backup_processed_data',
    bash_command="""
    cd /app/data/processed
    if [ -f watch_log.csv ]; then
        cp watch_log.csv watch_log_$(date +%Y%m%d_%H%M%S).csv
        echo "데이터 백업 완료: watch_log_$(date +%Y%m%d_%H%M%S).csv"
    else
        echo "백업할 파일이 없습니다."
        exit 1
    fi
    """,
    dag=dag
)

# 태스크 의존성 설정
collect_task >> process_task >> validate_task >> backup_task

# DAG 문서화
dag.doc_md = """
# Movie Data Collection Pipeline

이 DAG는 기존 my-mlops 프로젝트의 데이터 수집 로직을 Airflow로 구현한 것입니다.

## 워크플로우

1. **collect_tmdb_data**: TMDB API에서 인기 영화 데이터 수집
2. **process_tmdb_data**: 수집된 데이터를 ML용으로 전처리
3. **validate_processed_data**: 처리된 데이터 품질 검증
4. **backup_processed_data**: 처리된 데이터 백업

## 환경 변수

- `TMDB_API_KEY`: TMDB API 키 (필수)
- `TMDB_BASE_URL`: TMDB API 베이스 URL (기본값: https://api.themoviedb.org/3/movie)

## 출력 파일

- 원시 데이터: `/app/data/raw/tmdb/popular.json`
- 처리된 데이터: `/app/data/processed/watch_log.csv`
- 백업 데이터: `/app/data/processed/watch_log_YYYYMMDD_HHMMSS.csv`

## 실행 주기

매일 한 번 자동 실행됩니다.
"""
