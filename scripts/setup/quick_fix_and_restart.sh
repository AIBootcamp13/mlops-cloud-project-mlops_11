#!/bin/bash
# Movie MLOps 빠른 수정 및 재시작 스크립트

echo "🛠️ 컨테이너 충돌 해결 중..."
chmod +x fix_container_conflicts.sh
./fix_container_conflicts.sh

echo ""
echo "🚀 시스템 재시작 중..."
./run_movie_mlops.sh
