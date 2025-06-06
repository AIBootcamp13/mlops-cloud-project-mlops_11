#!/usr/bin/env python3
"""
간단한 데이터 저장소 테스트
문제 진단을 위한 최소한의 테스트
"""

import json
from pathlib import Path
from datetime import datetime
import sys

def simple_storage_test():
    """간단한 저장소 테스트"""
    print("=== 간단한 데이터 저장소 테스트 ===")
    
    # 1. 현재 디렉토리 확인
    current_dir = Path.cwd()
    print(f"현재 작업 디렉토리: {current_dir}")
    
    # 2. 테스트 데이터 생성
    test_data = {
        "test_time": datetime.now().isoformat(),
        "message": "Hello, MLOps!",
        "count": 42
    }
    print(f"테스트 데이터: {test_data}")
    
    # 3. 파일 경로 설정
    test_file = current_dir / "data" / "test" / "simple_test.json"
    print(f"저장할 파일: {test_file.absolute()}")
    
    # 4. 디렉토리 생성
    test_file.parent.mkdir(parents=True, exist_ok=True)
    print(f"디렉토리 생성: {test_file.parent.absolute()}")
    
    # 5. JSON 파일 저장
    try:
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)
        print(f"✅ 파일 저장 성공")
    except Exception as e:
        print(f"❌ 파일 저장 실패: {e}")
        return False
    
    # 6. 파일 존재 확인
    if test_file.exists():
        print(f"✅ 파일 존재 확인 - 크기: {test_file.stat().st_size} bytes")
    else:
        print(f"❌ 파일이 존재하지 않음")
        return False
    
    # 7. 파일 로드
    try:
        with open(test_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        print(f"✅ 파일 로드 성공")
        print(f"로드된 데이터: {loaded_data}")
    except Exception as e:
        print(f"❌ 파일 로드 실패: {e}")
        return False
    
    # 8. 데이터 검증
    if loaded_data.get('test_time') and loaded_data.get('message') == "Hello, MLOps!":
        print(f"✅ 데이터 검증 성공")
        return True
    else:
        print(f"❌ 데이터 검증 실패")
        return False

def check_environment():
    """환경 확인"""
    print("=== 환경 정보 ===")
    print(f"Python 버전: {sys.version}")
    print(f"현재 경로: {Path.cwd()}")
    print(f"Python 경로: {sys.path[:3]}")
    
    # 디렉토리 권한 확인
    current_dir = Path.cwd()
    try:
        test_dir = current_dir / "data" / "test"
        test_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ 디렉토리 생성 권한 확인")
        
        # 간단한 파일 쓰기 테스트
        test_file = test_dir / "permission_test.txt"
        with open(test_file, 'w') as f:
            f.write("permission test")
        
        if test_file.exists():
            print(f"✅ 파일 쓰기 권한 확인")
            test_file.unlink()  # 테스트 파일 삭제
        else:
            print(f"❌ 파일 쓰기 권한 문제")
            
    except Exception as e:
        print(f"❌ 권한 확인 실패: {e}")

def main():
    """메인 함수"""
    print("간단한 데이터 저장소 진단 테스트 시작\n")
    
    # 환경 확인
    check_environment()
    print()
    
    # 저장소 테스트
    result = simple_storage_test()
    print()
    
    if result:
        print("🎉 모든 테스트 통과!")
    else:
        print("⚠️ 테스트 실패")
    
    return result

if __name__ == "__main__":
    main()
