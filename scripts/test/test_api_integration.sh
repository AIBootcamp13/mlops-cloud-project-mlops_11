#!/bin/bash

echo "🧪 Movie MLOps API 통합 테스트 시작..."

API_BASE_URL="http://localhost:8000"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 테스트 결과 추적
TESTS_PASSED=0
TESTS_FAILED=0

# 테스트 함수
test_endpoint() {
    local name="$1"
    local method="$2"
    local url="$3"
    local data="$4"
    local expected_status="$5"
    
    echo -e "\n${BLUE}🔍 테스트: $name${NC}"
    echo "   URL: $method $url"
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$url")
    elif [ "$method" = "POST" ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST -H "Content-Type: application/json" -d "$data" "$url")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n -1)
    
    if [ "$http_code" = "$expected_status" ]; then
        echo -e "   ${GREEN}✅ 성공 (HTTP $http_code)${NC}"
        echo "$body" | jq . 2>/dev/null || echo "$body"
        ((TESTS_PASSED++))
    else
        echo -e "   ${RED}❌ 실패 (HTTP $http_code, 예상: $expected_status)${NC}"
        echo "$body"
        ((TESTS_FAILED++))
    fi
}

# 서버 상태 확인
echo -e "${YELLOW}📡 서버 연결 확인...${NC}"
if ! curl -s "$API_BASE_URL/health" > /dev/null; then
    echo -e "${RED}❌ 서버에 연결할 수 없습니다. 다음 명령어로 서버를 시작하세요:${NC}"
    echo "   ./run_movie_mlops.sh"
    echo "   메뉴에서 5번 선택 (API 스택)"
    exit 1
fi

echo -e "${GREEN}✅ 서버 연결 확인됨${NC}"

# ==========================================
# 기본 엔드포인트 테스트
# ==========================================

echo -e "\n${YELLOW}📋 기본 엔드포인트 테스트${NC}"

test_endpoint \
    "루트 엔드포인트" \
    "GET" \
    "$API_BASE_URL/" \
    "" \
    "200"

test_endpoint \
    "헬스체크" \
    "GET" \
    "$API_BASE_URL/health" \
    "" \
    "200"

# ==========================================
# 추천 API 테스트
# ==========================================

echo -e "\n${YELLOW}🎬 추천 API 테스트${NC}"

test_endpoint \
    "기본 추천 (레거시)" \
    "GET" \
    "$API_BASE_URL/recommendations?k=5" \
    "" \
    "200"

test_endpoint \
    "v1 추천 API" \
    "GET" \
    "$API_BASE_URL/api/v1/recommendations?k=5" \
    "" \
    "200"

test_endpoint \
    "v1 추천 API (사용자 지정)" \
    "GET" \
    "$API_BASE_URL/api/v1/recommendations?k=3&user_id=test_user" \
    "" \
    "200"

# ==========================================
# 영화 정보 API 테스트
# ==========================================

echo -e "\n${YELLOW}🎥 영화 정보 API 테스트${NC}"

test_endpoint \
    "v1 영화 목록" \
    "GET" \
    "$API_BASE_URL/api/v1/movies?limit=5" \
    "" \
    "200"

test_endpoint \
    "v1 영화 목록 (페이지네이션)" \
    "GET" \
    "$API_BASE_URL/api/v1/movies?limit=3&offset=5" \
    "" \
    "200"

# ==========================================
# 모델 정보 API 테스트
# ==========================================

echo -e "\n${YELLOW}🤖 모델 정보 API 테스트${NC}"

test_endpoint \
    "v1 모델 정보" \
    "GET" \
    "$API_BASE_URL/api/v1/model/info" \
    "" \
    "200"

# ==========================================
# 피드백 API 테스트
# ==========================================

echo -e "\n${YELLOW}💬 피드백 API 테스트${NC}"

test_endpoint \
    "피드백 제출" \
    "POST" \
    "$API_BASE_URL/api/v1/feedback" \
    '{
        "user_id": "test_user_001",
        "movie_id": 123,
        "interaction_type": "rating",
        "rating": 4.5,
        "session_id": "test_session_123"
    }' \
    "200"

test_endpoint \
    "사용자 피드백 조회" \
    "GET" \
    "$API_BASE_URL/api/v1/feedback/test_user_001?limit=10" \
    "" \
    "200"

# ==========================================
# 이벤트 API 테스트
# ==========================================

echo -e "\n${YELLOW}📊 이벤트 API 테스트${NC}"

test_endpoint \
    "사용자 상호작용 이벤트" \
    "POST" \
    "$API_BASE_URL/api/v1/events/user-interaction" \
    '{
        "user_id": "test_user_002",
        "movie_id": 456,
        "interaction_type": "view",
        "duration_seconds": 120,
        "device_type": "mobile"
    }' \
    "200"

test_endpoint \
    "시스템 이벤트" \
    "POST" \
    "$API_BASE_URL/api/v1/events/system" \
    '{
        "event_type": "api_call",
        "service_name": "movie-recommendation-api",
        "severity": "info",
        "message": "테스트 API 호출"
    }' \
    "200"

test_endpoint \
    "모델 드리프트 이벤트" \
    "POST" \
    "$API_BASE_URL/api/v1/events/model-drift" \
    '{
        "model_name": "movie_predictor",
        "model_version": "1.0.0",
        "drift_score": 0.8,
        "threshold": 0.7,
        "drift_type": "data_drift"
    }' \
    "200"

test_endpoint \
    "이벤트 통계 조회" \
    "GET" \
    "$API_BASE_URL/api/v1/events/stats" \
    "" \
    "200"

# ==========================================
# 피처 API 테스트
# ==========================================

echo -e "\n${YELLOW}🔧 피처 API 테스트${NC}"

test_endpoint \
    "피처 헬스체크" \
    "GET" \
    "$API_BASE_URL/api/v1/features/health" \
    "" \
    "200"

test_endpoint \
    "피처 뷰 목록" \
    "GET" \
    "$API_BASE_URL/api/v1/features/views" \
    "" \
    "200"

# ==========================================
# 에러 케이스 테스트
# ==========================================

echo -e "\n${YELLOW}⚠️ 에러 케이스 테스트${NC}"

test_endpoint \
    "존재하지 않는 엔드포인트" \
    "GET" \
    "$API_BASE_URL/api/v1/nonexistent" \
    "" \
    "404"

test_endpoint \
    "잘못된 매개변수" \
    "GET" \
    "$API_BASE_URL/api/v1/recommendations?k=0" \
    "" \
    "422"

# ==========================================
# 테스트 결과 요약
# ==========================================

echo -e "\n${YELLOW}📊 테스트 결과 요약${NC}"
echo "======================================"
echo -e "✅ 성공: ${GREEN}$TESTS_PASSED${NC}"
echo -e "❌ 실패: ${RED}$TESTS_FAILED${NC}"
echo -e "📊 전체: $((TESTS_PASSED + TESTS_FAILED))"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 모든 테스트가 성공했습니다!${NC}"
    exit 0
else
    echo -e "\n${RED}⚠️ 일부 테스트가 실패했습니다. 로그를 확인하세요.${NC}"
    exit 1
fi
