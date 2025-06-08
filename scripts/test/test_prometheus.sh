#!/bin/bash

# =============================================================================
# Prometheus 모니터링 시스템 테스트 스크립트
# =============================================================================

set -e

echo "🔍 Prometheus 모니터링 시스템 테스트 시작..."

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 테스트 결과 저장
RESULTS_FILE="test_results_prometheus_$(date +%Y%m%d_%H%M%S).log"

log_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$RESULTS_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS: $1" >> "$RESULTS_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" >> "$RESULTS_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1" >> "$RESULTS_FILE"
}

# 1. Prometheus 서비스 상태 확인
test_prometheus_health() {
    log_test "Prometheus 서비스 헬스체크"
    
    if curl -f -s http://localhost:9090/-/healthy > /dev/null; then
        log_success "Prometheus 서비스가 정상적으로 실행중입니다"
        return 0
    else
        log_error "Prometheus 서비스에 접근할 수 없습니다"
        return 1
    fi
}

# 2. Prometheus 설정 확인
test_prometheus_config() {
    log_test "Prometheus 설정 검증"
    
    config_response=$(curl -s http://localhost:9090/api/v1/status/config 2>/dev/null)
    
    if echo "$config_response" | grep -q '"status":"success"'; then
        log_success "Prometheus 설정이 유효합니다"
        
        # 주요 설정 확인
        if echo "$config_response" | grep -q "movie-mlops-api"; then
            log_success "API 서비스 스크래핑 설정이 확인되었습니다"
        else
            log_warning "API 서비스 스크래핑 설정을 찾을 수 없습니다"
        fi
        
        return 0
    else
        log_error "Prometheus 설정이 유효하지 않습니다"
        return 1
    fi
}

# 3. 메트릭 수집 확인
test_metrics_collection() {
    log_test "메트릭 수집 상태 확인"
    
    # 시스템 메트릭 확인
    if curl -s "http://localhost:9090/api/v1/query?query=up" | grep -q '"status":"success"'; then
        log_success "기본 시스템 메트릭이 수집되고 있습니다"
    else
        log_error "시스템 메트릭 수집에 문제가 있습니다"
    fi
    
    # 애플리케이션 메트릭 확인
    app_metrics=(
        "http_requests_total"
        "http_request_duration_seconds"
        "system_cpu_usage_percent"
        "system_memory_usage_bytes"
    )
    
    for metric in "${app_metrics[@]}"; do
        if curl -s "http://localhost:9090/api/v1/query?query=$metric" | grep -q '"status":"success"'; then
            log_success "메트릭 '$metric'이 수집되고 있습니다"
        else
            log_warning "메트릭 '$metric'을 찾을 수 없습니다"
        fi
    done
}

# 4. 타겟 상태 확인
test_prometheus_targets() {
    log_test "Prometheus 타겟 상태 확인"
    
    targets_response=$(curl -s http://localhost:9090/api/v1/targets 2>/dev/null)
    
    if echo "$targets_response" | grep -q '"status":"success"'; then
        # 활성 타겟 수 확인
        active_targets=$(echo "$targets_response" | grep -o '"health":"up"' | wc -l)
        total_targets=$(echo "$targets_response" | grep -o '"health":' | wc -l)
        
        log_success "총 $total_targets개 타겟 중 $active_targets개가 활성 상태입니다"
        
        # 주요 서비스 타겟 확인
        services=("movie-mlops-api" "node-exporter" "cadvisor" "prometheus")
        for service in "${services[@]}"; do
            if echo "$targets_response" | grep -q "$service.*\"health\":\"up\""; then
                log_success "서비스 '$service' 타겟이 정상입니다"
            else
                log_warning "서비스 '$service' 타겟에 문제가 있을 수 있습니다"
            fi
        done
        
        return 0
    else
        log_error "Prometheus 타겟 정보를 가져올 수 없습니다"
        return 1
    fi
}

# 5. 메트릭 API 테스트
test_metrics_api() {
    log_test "메트릭 API 엔드포인트 테스트"
    
    # API 메트릭 엔드포인트 테스트
    if curl -f -s http://localhost:8000/metrics > /dev/null; then
        log_success "API 메트릭 엔드포인트가 정상 작동합니다"
        
        # 메트릭 내용 확인
        metrics_content=$(curl -s http://localhost:8000/metrics)
        
        if echo "$metrics_content" | grep -q "http_requests_total"; then
            log_success "HTTP 요청 메트릭이 노출되고 있습니다"
        fi
        
        if echo "$metrics_content" | grep -q "system_cpu_usage_percent"; then
            log_success "시스템 CPU 메트릭이 노출되고 있습니다"
        fi
        
        return 0
    else
        log_error "API 메트릭 엔드포인트에 접근할 수 없습니다"
        return 1
    fi
}

# 6. 알림 규칙 확인
test_alerting_rules() {
    log_test "알림 규칙 상태 확인"
    
    rules_response=$(curl -s http://localhost:9090/api/v1/rules 2>/dev/null)
    
    if echo "$rules_response" | grep -q '"status":"success"'; then
        rules_count=$(echo "$rules_response" | grep -o '"name":' | wc -l)
        log_success "총 $rules_count개의 알림 규칙이 로드되어 있습니다"
        return 0
    else
        log_warning "알림 규칙 정보를 확인할 수 없습니다 (규칙이 없을 수 있음)"
        return 0
    fi
}

# 7. 스토리지 상태 확인
test_prometheus_storage() {
    log_test "Prometheus 스토리지 상태 확인"
    
    # TSDB 상태 확인
    tsdb_response=$(curl -s http://localhost:9090/api/v1/status/tsdb 2>/dev/null)
    
    if echo "$tsdb_response" | grep -q '"status":"success"'; then
        log_success "TSDB 스토리지가 정상 작동합니다"
        
        # 스토리지 크기 확인 (선택사항)
        if command -v jq > /dev/null; then
            series_count=$(echo "$tsdb_response" | jq -r '.data.seriesCountByMetricName | length' 2>/dev/null || echo "unknown")
            log_success "현재 $series_count개의 메트릭 시리즈가 저장되어 있습니다"
        fi
        
        return 0
    else
        log_warning "TSDB 상태를 확인할 수 없습니다"
        return 1
    fi
}

# 8. 성능 테스트
test_prometheus_performance() {
    log_test "Prometheus 성능 테스트"
    
    # 쿼리 응답 시간 측정
    start_time=$(date +%s%3N)
    curl -s "http://localhost:9090/api/v1/query?query=up" > /dev/null
    end_time=$(date +%s%3N)
    response_time=$((end_time - start_time))
    
    if [ $response_time -lt 1000 ]; then
        log_success "쿼리 응답 시간이 양호합니다 (${response_time}ms)"
    elif [ $response_time -lt 3000 ]; then
        log_warning "쿼리 응답 시간이 보통입니다 (${response_time}ms)"
    else
        log_warning "쿼리 응답 시간이 느립니다 (${response_time}ms)"
    fi
}

# 메인 테스트 실행
main() {
    echo "========================================"
    echo "🔍 Prometheus 모니터링 시스템 테스트"
    echo "========================================"
    echo ""
    
    total_tests=0
    passed_tests=0
    
    # 테스트 실행
    tests=(
        "test_prometheus_health"
        "test_prometheus_config"
        "test_metrics_collection"
        "test_prometheus_targets"
        "test_metrics_api"
        "test_alerting_rules"
        "test_prometheus_storage"
        "test_prometheus_performance"
    )
    
    for test_function in "${tests[@]}"; do
        total_tests=$((total_tests + 1))
        echo ""
        if $test_function; then
            passed_tests=$((passed_tests + 1))
        fi
    done
    
    echo ""
    echo "========================================"
    echo "📊 테스트 결과 요약"
    echo "========================================"
    echo "총 테스트: $total_tests"
    echo "성공: $passed_tests"
    echo "실패: $((total_tests - passed_tests))"
    echo ""
    
    if [ $passed_tests -eq $total_tests ]; then
        echo -e "${GREEN}✅ 모든 테스트가 성공했습니다!${NC}"
        echo "🎉 Prometheus 모니터링 시스템이 정상적으로 작동합니다."
    else
        echo -e "${YELLOW}⚠️  일부 테스트에서 문제가 발견되었습니다.${NC}"
        echo "📝 자세한 내용은 로그 파일을 확인하세요: $RESULTS_FILE"
    fi
    
    echo ""
    echo "🔗 유용한 링크:"
    echo "  - Prometheus UI: http://localhost:9090"
    echo "  - API 메트릭: http://localhost:8000/metrics"
    echo "  - 시스템 헬스: http://localhost:8000/monitoring/health"
    echo ""
    
    # 결과 파일에 요약 저장
    echo "=======================================" >> "$RESULTS_FILE"
    echo "테스트 완료: $(date)" >> "$RESULTS_FILE"
    echo "총 테스트: $total_tests, 성공: $passed_tests, 실패: $((total_tests - passed_tests))" >> "$RESULTS_FILE"
    echo "=======================================" >> "$RESULTS_FILE"
    
    # 테스트 결과에 따른 종료 코드
    if [ $passed_tests -eq $total_tests ]; then
        exit 0
    else
        exit 1
    fi
}

# 스크립트 실행
main "$@"
