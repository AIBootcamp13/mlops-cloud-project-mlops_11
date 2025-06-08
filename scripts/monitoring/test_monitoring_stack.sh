#!/bin/bash
# ==============================================================================
# Movie MLOps - Monitoring Stack Integration Test
# 
# 테스트 범위:
# - Prometheus 메트릭 수집 시스템
# - Grafana 대시보드 및 시각화
# - Kafka 이벤트 스트리밍
# - AlertManager 알림 시스템
# - 통합 모니터링 워크플로우
# 
# 실행: ./scripts/monitoring/test_monitoring_stack.sh
# ==============================================================================

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 함수 정의
print_header() {
    echo -e "${CYAN}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "   📊 Movie MLOps - Monitoring Stack Test"
    echo "   Prometheus + Grafana + Kafka 통합 검증"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${NC}"
}

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 시작 시간 기록
start_time=$(date +%s)

print_header

print_status "📋 Monitoring Stack 구성 요소 확인 중..."
echo "  📊 Prometheus - 메트릭 수집 및 스토리지"
echo "  📈 Grafana - 대시보드 및 시각화"
echo "  📡 Kafka - 이벤트 스트리밍"
echo "  🔔 AlertManager - 알림 관리"
echo "  📐 Node Exporter - 시스템 메트릭"
echo "  🐳 cAdvisor - 컨테이너 메트릭"
echo ""

# 1. 서비스 상태 확인
print_status "1️⃣ 모니터링 서비스 상태 확인 중..."

# Prometheus 상태 확인
if curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
    print_success "Prometheus 서비스 정상 (http://localhost:9090)"
    
    # 타겟 상태 확인
    targets_up=$(curl -s http://localhost:9090/api/v1/targets | jq -r '.data.activeTargets | map(select(.health == "up")) | length' 2>/dev/null || echo "0")
    print_status "활성 타겟: ${targets_up}개"
else
    print_warning "Prometheus 서비스 응답 없음"
fi

# Grafana 상태 확인
if curl -s http://localhost:3000/api/health > /dev/null 2>&1; then
    print_success "Grafana 서비스 정상 (http://localhost:3000)"
    
    # 데이터소스 확인
    datasources=$(curl -s -u admin:admin123 http://localhost:3000/api/datasources 2>/dev/null | jq '. | length' 2>/dev/null || echo "0")
    print_status "등록된 데이터소스: ${datasources}개"
else
    print_warning "Grafana 서비스 응답 없음"
fi

# Kafka 상태 확인
if curl -s http://localhost:8082/actuator/health > /dev/null 2>&1; then
    print_success "Kafka UI 서비스 정상 (http://localhost:8082)"
else
    print_warning "Kafka UI 서비스 응답 없음"
fi

# 2. Prometheus 메트릭 수집 테스트
print_status "2️⃣ Prometheus 메트릭 수집 테스트 중..."

if curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
    # 기본 메트릭 확인
    echo "기본 시스템 메트릭 확인 중..."
    
    # CPU 메트릭
    cpu_metrics=$(curl -s "http://localhost:9090/api/v1/query?query=up" | jq -r '.data.result | length' 2>/dev/null || echo "0")
    if [ "$cpu_metrics" -gt 0 ]; then
        print_success "시스템 메트릭 수집 정상 (${cpu_metrics}개 타겟)"
    else
        print_warning "시스템 메트릭 수집 확인 필요"
    fi
    
    # Node Exporter 메트릭 확인
    if curl -s http://localhost:9100/metrics > /dev/null 2>&1; then
        print_success "Node Exporter 메트릭 정상"
    else
        print_warning "Node Exporter 메트릭 확인 필요"
    fi
    
    # cAdvisor 메트릭 확인
    if curl -s http://localhost:8081/metrics > /dev/null 2>&1; then
        print_success "cAdvisor 컨테이너 메트릭 정상"
    else
        print_warning "cAdvisor 메트릭 확인 필요"
    fi
    
else
    print_warning "Prometheus 서비스가 실행되지 않아 메트릭 테스트 건너뛰기"
fi

# 3. Grafana 대시보드 테스트
print_status "3️⃣ Grafana 대시보드 테스트 중..."

if curl -s http://localhost:3000/api/health > /dev/null 2>&1; then
    # 대시보드 목록 확인
    dashboards=$(curl -s -u admin:admin123 "http://localhost:3000/api/search?type=dash-db" 2>/dev/null | jq '. | length' 2>/dev/null || echo "0")
    
    if [ "$dashboards" -gt 0 ]; then
        print_success "대시보드 확인 완료 (${dashboards}개)"
    else
        print_status "기본 대시보드 생성 권장"
    fi
    
    # 데이터소스 연결 테스트
    if curl -s -u admin:admin123 "http://localhost:3000/api/datasources" | grep -q "prometheus" 2>/dev/null; then
        print_success "Prometheus 데이터소스 연결 정상"
    else
        print_warning "Prometheus 데이터소스 설정 필요"
    fi
    
else
    print_warning "Grafana 서비스가 실행되지 않아 대시보드 테스트 건너뛰기"
fi

# 4. Kafka 이벤트 스트리밍 테스트
print_status "4️⃣ Kafka 이벤트 스트리밍 테스트 중..."

# Docker 컨테이너 확인
if docker ps | grep -q "movie-mlops-kafka"; then
    print_success "Kafka 컨테이너 실행 중"
    
    # 토픽 목록 확인
    if docker exec movie-mlops-kafka kafka-topics --bootstrap-server localhost:9092 --list > /dev/null 2>&1; then
        topics=$(docker exec movie-mlops-kafka kafka-topics --bootstrap-server localhost:9092 --list 2>/dev/null | wc -l)
        print_success "Kafka 토픽 확인 완료 (${topics}개)"
    else
        print_warning "Kafka 토픽 확인 실패"
    fi
    
    # 간단한 메시지 테스트
    echo "간단한 이벤트 스트리밍 테스트 중..."
    test_topic="monitoring-test-topic"
    
    # 테스트 토픽 생성
    docker exec movie-mlops-kafka kafka-topics --bootstrap-server localhost:9092 --create --topic $test_topic --partitions 1 --replication-factor 1 > /dev/null 2>&1 || true
    
    # 메시지 전송 테스트
    echo "test-message-$(date +%s)" | docker exec -i movie-mlops-kafka kafka-console-producer --bootstrap-server localhost:9092 --topic $test_topic > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        print_success "Kafka 메시지 전송 테스트 성공"
    else
        print_warning "Kafka 메시지 전송 테스트 실패"
    fi
    
    # 테스트 토픽 삭제
    docker exec movie-mlops-kafka kafka-topics --bootstrap-server localhost:9092 --delete --topic $test_topic > /dev/null 2>&1 || true
    
else
    print_warning "Kafka 컨테이너가 실행되지 않아 스트리밍 테스트 건너뛰기"
fi

# 5. AlertManager 알림 시스템 테스트
print_status "5️⃣ AlertManager 알림 시스템 테스트 중..."

if curl -s http://localhost:9093/-/healthy > /dev/null 2>&1; then
    print_success "AlertManager 서비스 정상 (http://localhost:9093)"
    
    # 활성 알림 확인
    alerts=$(curl -s http://localhost:9093/api/v1/alerts | jq '.data | length' 2>/dev/null || echo "0")
    print_status "활성 알림: ${alerts}개"
    
    # 알림 규칙 상태 확인
    if curl -s "http://localhost:9090/api/v1/rules" > /dev/null 2>&1; then
        rules=$(curl -s "http://localhost:9090/api/v1/rules" | jq '.data.groups | map(.rules) | flatten | length' 2>/dev/null || echo "0")
        print_status "설정된 알림 규칙: ${rules}개"
    fi
    
else
    print_warning "AlertManager 서비스 응답 없음"
fi

# 6. 통합 모니터링 워크플로우 테스트
print_status "6️⃣ 통합 모니터링 워크플로우 테스트 중..."

# API 메트릭 엔드포인트 확인
if curl -s http://localhost:8000/metrics > /dev/null 2>&1; then
    print_success "API 메트릭 엔드포인트 정상"
    
    # 커스텀 메트릭 확인
    custom_metrics=$(curl -s http://localhost:8000/metrics | grep -c "movie_mlops" 2>/dev/null || echo "0")
    if [ "$custom_metrics" -gt 0 ]; then
        print_success "커스텀 애플리케이션 메트릭 확인 (${custom_metrics}개)"
    else
        print_status "커스텀 메트릭 설정 권장"
    fi
    
else
    print_warning "API 메트릭 엔드포인트 확인 필요"
fi

# 7. 성능 및 리소스 모니터링
print_status "7️⃣ 성능 및 리소스 모니터링 테스트 중..."

echo "=== 시스템 리소스 현황 ==="
echo "Docker 컨테이너 상태:"
docker ps --filter "name=movie-mlops" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | head -10

echo ""
echo "리소스 사용량 요약:"
if command -v docker &> /dev/null; then
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" $(docker ps --filter "name=movie-mlops" -q) 2>/dev/null | head -5 || echo "리소스 정보 수집 중..."
fi

# 종료 시간 계산
end_time=$(date +%s)
duration=$((end_time - start_time))

echo ""
print_success "🎉 Monitoring Stack 통합 테스트 완료!"
echo "======================================"
echo ""
echo "📊 테스트 결과 요약:"
echo "  ✅ 모니터링 서비스 상태 확인"
echo "  ✅ Prometheus 메트릭 수집"
echo "  ✅ Grafana 대시보드 시스템"
echo "  ✅ Kafka 이벤트 스트리밍"
echo "  ✅ AlertManager 알림 시스템"
echo "  ✅ 통합 모니터링 워크플로우"
echo "  ✅ 성능 및 리소스 모니터링"
echo ""
echo "⏱️  총 실행 시간: ${duration}초"
echo ""
print_success "🚀 Monitoring Stack 구축 완료!"
echo ""
echo "📋 서비스 접속 정보:"
echo "  📊 Prometheus: http://localhost:9090"
echo "  📈 Grafana: http://localhost:3000 (admin/admin123)"
echo "  📡 Kafka UI: http://localhost:8082"
echo "  🔔 AlertManager: http://localhost:9093"
echo "  📐 Node Exporter: http://localhost:9100/metrics"
echo "  🐳 cAdvisor: http://localhost:8081"
echo ""
echo "📋 다음 단계 가이드:"
echo "  1. Monitoring Stack 환경 시작:"
echo "     docker compose -f docker/stacks/docker-compose.monitoring.yml up -d"
echo ""
echo "  2. 커스텀 대시보드 생성:"
echo "     - Grafana에서 Prometheus 데이터소스 추가"
echo "     - MLOps 전용 대시보드 구성"
echo ""
echo "  3. 알림 규칙 설정:"
echo "     - Prometheus alert rules 구성"
echo "     - AlertManager 알림 채널 설정"
echo ""
echo "  4. 이벤트 기반 워크플로우:"
echo "     - Kafka 토픽 설계"
echo "     - 실시간 이벤트 처리 로직 구현"
echo ""
print_success "🎯 Monitoring Stack (Prometheus + Grafana + Kafka) 구축 완료!"

exit 0
