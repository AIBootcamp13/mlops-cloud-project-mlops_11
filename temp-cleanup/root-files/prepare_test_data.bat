@echo off
REM 2단계 피처 스토어 테스트 데이터 준비 스크립트 (Windows)
REM prepare_test_data.bat

echo 🗃️ 2단계 피처 스토어 테스트 데이터 준비 중...

REM 테스트 데이터 디렉토리 생성
docker-compose exec dev bash -c "mkdir -p /app/data/test /app/data/test/sample_data /app/data/test/integration_test /app/data/test/unit_test"

REM 테스트 데이터 생성
docker-compose exec dev python -c "import sys; sys.path.append('/app/src'); import json; from pathlib import Path; test_data_dir = Path('/app/data/test'); test_data_dir.mkdir(exist_ok=True); test_movies = [{'id': 1, 'title': 'Test Movie 1', 'release_date': '2023-01-15', 'vote_average': 8.5, 'vote_count': 1500, 'popularity': 45.2, 'genres': [{'id': 28, 'name': 'Action'}, {'id': 12, 'name': 'Adventure'}], 'runtime': 120, 'budget': 50000000, 'revenue': 150000000}, {'id': 2, 'title': 'Test Movie 2', 'release_date': '2023-06-20', 'vote_average': 7.2, 'vote_count': 800, 'popularity': 32.1, 'genres': [{'id': 35, 'name': 'Comedy'}, {'id': 10749, 'name': 'Romance'}], 'runtime': 95, 'budget': 20000000, 'revenue': 75000000}]; sample_path = test_data_dir / 'sample_movies.json'; json.dump(test_movies, open(sample_path, 'w'), indent=2); print(f'✅ 테스트 데이터 생성: {sample_path}')"

echo ✅ 테스트 데이터 준비 완료!
echo.
echo 📋 다음 명령어로 데이터를 확인할 수 있습니다:
echo docker-compose exec dev ls -la /app/data/test/
echo docker-compose exec dev cat /app/data/test/sample_movies.json
echo.
pause
