#!/usr/bin/env python3
"""
간단한 스케줄러 테스트 스크립트
"""

import sys
from pathlib import Path

# 프로젝트 루트 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

def test_scheduler_basic():
    """기본 스케줄러 테스트"""
    try:
        from data_processing.scheduler import TMDBDataScheduler
        print("✅ TMDBDataScheduler import 성공")
        
        scheduler = TMDBDataScheduler()
        print("✅ TMDBDataScheduler 초기화 성공")
        
        # 스케줄 설정 테스트
        scheduler.setup_jobs()
        print("✅ 스케줄 작업 설정 성공")
        
        # 스케줄된 작업 확인
        import schedule
        print(f"등록된 작업 수: {len(schedule.jobs)}개")
        
        for i, job in enumerate(schedule.jobs):
            print(f"{i+1}. {job}")
        
        return True
        
    except Exception as e:
        print(f"❌ 스케줄러 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_daily_collection():
    """일일 수집 테스트"""
    try:
        from data_processing.scheduler import TMDBDataScheduler
        scheduler = TMDBDataScheduler()
        
        print("=== 일일 수집 테스트 시작 ===")
        result = scheduler.daily_collection()
        
        if result:
            print(f"✅ 일일 수집 성공: {result.get('total_valid')}개 영화")
            print(f"품질률: {result.get('quality_rate', 0):.1f}%")
        else:
            print("❌ 일일 수집 결과 없음")
        
        return True
        
    except Exception as e:
        print(f"❌ 일일 수집 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== 스케줄러 테스트 시작 ===")
    
    # 기본 테스트
    success1 = test_scheduler_basic()
    
    if success1:
        print("\n=== 일일 수집 테스트 ===")
        success2 = test_daily_collection()
    
    print("\n=== 테스트 완료 ===")
