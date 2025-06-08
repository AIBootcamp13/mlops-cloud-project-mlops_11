#!/bin/bash
# MLflow API 테스트 - 컨테이너 내부 실행

echo "=== MLflow API 테스트 (완전 격리 환경) ==="

docker exec movie-mlops-mlflow sh -c '
echo "1. MLflow 실험 목록:"
curl -s -X POST "http://localhost:5000/api/2.0/mlflow/experiments/search" \
     -H "Content-Type: application/json" \
     -d "{\"max_results\": 10}" | jq .

echo ""
echo "2. 등록된 모델 개수:"
curl -s -X GET "http://localhost:5000/api/2.0/mlflow/registered-models/search" \
     -H "Content-Type: application/json" | jq ".registered_models | length"

echo ""
echo "3. MLflow 서비스 상태:"
curl -s -o /dev/null -w "HTTP Status: %{http_code}" http://localhost:5000
echo ""
'
