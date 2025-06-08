#!/bin/bash
# MLflow API 테스트 스크립트

echo "=== MLflow 실험 목록 조회 ==="
curl -s -X POST 'http://localhost:5000/api/2.0/mlflow/experiments/search' \
     -H 'Content-Type: application/json' \
     -d '{"max_results": 10}' | jq .

echo ""
echo "=== MLflow 서버 상태 ==="
curl -s 'http://localhost:5000/health' | jq . || echo "Health endpoint not available"

echo ""
echo "=== MLflow 버전 정보 ==="
curl -s 'http://localhost:5000/version' | jq . || echo "Version endpoint not available"
