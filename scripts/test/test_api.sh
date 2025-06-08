#!/bin/bash
# ==============================================================================
# API 테스트 스크립트
# Phase 2 구현 결과 테스트
# ==============================================================================

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

API_BASE_URL="http://localhost:8000"

echo -e "${BLUE}🧪 Movie MLOps API 테스트 시작...${NC}"
echo ""

# 1. 헬스체크
echo -e "${YELLOW}1. 헬스체크 테스트${NC}"
curl -s "$API_BASE_URL/health" | jq '.' || echo "❌ 헬스체크 실패"
echo ""

# 2. 루트 엔드포인트
echo -e "${YELLOW}2. 루트 엔드포인트 테스트${NC}"
curl -s "$API_BASE_URL/" | jq '.' || echo "❌ 루트 엔드포인트 실패"
echo ""

# 3. 기본 추천 (my-mlops-web 호환)
echo -e "${YELLOW}3. 기본 추천 API 테스트 (k=5)${NC}"
curl -s "$API_BASE_URL/?k=5" | jq '.' || echo "❌ 기본 추천 실패"
echo ""

# 4. 영화 목록
echo -e "${YELLOW}4. 영화 목록 API 테스트${NC}"
curl -s "$API_BASE_URL/movies" | jq '.' || echo "❌ 영화 목록 실패"
echo ""

# 5. 모델 정보
echo -e "${YELLOW}5. 모델 정보 API 테스트${NC}"
curl -s "$API_BASE_URL/model/info" | jq '.' || echo "❌ 모델 정보 실패"
echo ""

# 6. 데이터셋 정보
echo -e "${YELLOW}6. 데이터셋 정보 API 테스트${NC}"
curl -s "$API_BASE_URL/dataset/info" | jq '.' || echo "❌ 데이터셋 정보 실패"
echo ""

# 7. API 문서 접근
echo -e "${YELLOW}7. API 문서 접근 테스트${NC}"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE_URL/docs")
if [ "$HTTP_STATUS" -eq 200 ]; then
    echo -e "${GREEN}✅ API 문서 접근 성공 (HTTP $HTTP_STATUS)${NC}"
else
    echo -e "${RED}❌ API 문서 접근 실패 (HTTP $HTTP_STATUS)${NC}"
fi
echo ""

# 8. OpenAPI 스키마
echo -e "${YELLOW}8. OpenAPI 스키마 테스트${NC}"
curl -s "$API_BASE_URL/openapi.json" | jq '.info.title' || echo "❌ OpenAPI 스키마 실패"
echo ""

echo -e "${BLUE}🎉 API 테스트 완료!${NC}"
echo ""
echo -e "${GREEN}📋 테스트 결과 요약:${NC}"
echo "  • 헬스체크: $API_BASE_URL/health"
echo "  • 기본 추천: $API_BASE_URL/?k=10"
echo "  • 영화 목록: $API_BASE_URL/movies"
echo "  • 모델 정보: $API_BASE_URL/model/info"
echo "  • API 문서: $API_BASE_URL/docs"
echo ""
echo -e "${YELLOW}💡 React 앱에서 사용할 엔드포인트:${NC}"
echo "  REACT_APP_API_ENDPOINT=$API_BASE_URL"
