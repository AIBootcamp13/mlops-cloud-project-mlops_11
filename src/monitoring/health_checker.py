"""
통합 헬스체커
모든 MLOps 서비스의 상태를 통합적으로 모니터링
"""

import asyncio
import aiohttp
import psutil
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import subprocess
import json

from .prometheus_metrics import get_metrics
from ..events.kafka_producer import get_event_producer
from ..events.event_schemas import EventFactory, AlertLevel

logger = logging.getLogger(__name__)

class ServiceStatus(Enum):
    """서비스 상태"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"  
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class HealthCheckResult:
    """헬스체크 결과"""
    service_name: str
    status: ServiceStatus
    response_time_ms: float
    message: str
    details: Dict[str, Any]
    checked_at: datetime
    endpoint: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        result = asdict(self)
        result['status'] = self.status.value
        result['checked_at'] = self.checked_at.isoformat()
        return result

class ServiceHealthChecker:
    """개별 서비스 헬스체커"""
    
    def __init__(self, service_name: str, endpoint: str, 
                 timeout: int = 5, healthy_status_codes: List[int] = None):
        """
        서비스 헬스체커 초기화
        
        Args:
            service_name: 서비스 이름
            endpoint: 헬스체크 엔드포인트
            timeout: 타임아웃 (초)
            healthy_status_codes: 정상 상태 코드 리스트
        """
        self.service_name = service_name
        self.endpoint = endpoint
        self.timeout = timeout
        self.healthy_status_codes = healthy_status_codes or [200, 201, 204]
        self.last_check_time = None
        self.consecutive_failures = 0
        self.check_history: List[HealthCheckResult] = []
        self.max_history = 100
    
    async def check_health(self) -> HealthCheckResult:
        """헬스체크 수행"""
        start_time = time.time()
        checked_at = datetime.utcnow()
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(self.endpoint) as response:
                    response_time_ms = (time.time() - start_time) * 1000
                    
                    # 응답 내용 읽기
                    try:
                        response_text = await response.text()
                        response_data = json.loads(response_text) if response_text else {}
                    except:
                        response_data = {"raw_response": response_text[:500] if 'response_text' in locals() else ""}
                    
                    # 상태 결정
                    if response.status in self.healthy_status_codes:
                        status = ServiceStatus.HEALTHY
                        message = "Service is healthy"
                        self.consecutive_failures = 0
                    else:
                        status = ServiceStatus.UNHEALTHY
                        message = f"HTTP {response.status}: {response.reason}"
                        self.consecutive_failures += 1
                    
                    details = {
                        "status_code": response.status,
                        "response_data": response_data,
                        "headers": dict(response.headers),
                        "consecutive_failures": self.consecutive_failures
                    }
                    
        except asyncio.TimeoutError:
            response_time_ms = self.timeout * 1000
            status = ServiceStatus.UNHEALTHY
            message = f"Timeout after {self.timeout}s"
            details = {"error": "timeout", "consecutive_failures": self.consecutive_failures}
            self.consecutive_failures += 1
            
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            status = ServiceStatus.UNHEALTHY
            message = f"Connection error: {str(e)}"
            details = {"error": str(e), "consecutive_failures": self.consecutive_failures}
            self.consecutive_failures += 1
        
        # 결과 생성
        result = HealthCheckResult(
            service_name=self.service_name,
            status=status,
            response_time_ms=response_time_ms,
            message=message,
            details=details,
            checked_at=checked_at,
            endpoint=self.endpoint
        )
        
        # 히스토리 업데이트
        self.check_history.append(result)
        if len(self.check_history) > self.max_history:
            self.check_history.pop(0)
        
        self.last_check_time = checked_at
        return result
    
    def get_availability(self, time_window: timedelta = timedelta(hours=1)) -> float:
        """가용률 계산"""
        cutoff_time = datetime.utcnow() - time_window
        recent_checks = [check for check in self.check_history if check.checked_at >= cutoff_time]
        
        if not recent_checks:
            return 0.0
        
        healthy_checks = sum(1 for check in recent_checks if check.status == ServiceStatus.HEALTHY)
        return healthy_checks / len(recent_checks)

class SystemResourceChecker:
    """시스템 리소스 체커"""
    
    def __init__(self):
        self.warning_thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'disk_percent': 90.0,
            'load_average': 2.0
        }
        
        self.critical_thresholds = {
            'cpu_percent': 95.0,
            'memory_percent': 95.0,
            'disk_percent': 95.0,
            'load_average': 5.0
        }
    
    async def check_system_resources(self) -> HealthCheckResult:
        """시스템 리소스 체크"""
        start_time = time.time()
        checked_at = datetime.utcnow()
        
        try:
            # CPU 사용률
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 메모리 사용률
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # 디스크 사용률
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # 로드 평균 (Linux/Unix만)
            try:
                load_avg = psutil.getloadavg()[0]  # 1분 평균
            except:
                load_avg = 0.0
            
            # 네트워크 I/O
            net_io = psutil.net_io_counters()
            
            # 디스크 I/O
            disk_io = psutil.disk_io_counters()
            
            details = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "memory_total_gb": memory.total / (1024**3),
                "memory_available_gb": memory.available / (1024**3),
                "disk_percent": disk_percent,
                "disk_total_gb": disk.total / (1024**3),
                "disk_free_gb": disk.free / (1024**3),
                "load_average_1min": load_avg,
                "network_bytes_sent": net_io.bytes_sent,
                "network_bytes_recv": net_io.bytes_recv,
                "disk_read_bytes": disk_io.read_bytes if disk_io else 0,
                "disk_write_bytes": disk_io.write_bytes if disk_io else 0
            }
            
            # 상태 결정
            status = ServiceStatus.HEALTHY
            messages = []
            
            # Critical 체크
            if cpu_percent >= self.critical_thresholds['cpu_percent']:
                status = ServiceStatus.UNHEALTHY
                messages.append(f"Critical CPU usage: {cpu_percent:.1f}%")
            elif memory_percent >= self.critical_thresholds['memory_percent']:
                status = ServiceStatus.UNHEALTHY
                messages.append(f"Critical memory usage: {memory_percent:.1f}%")
            elif disk_percent >= self.critical_thresholds['disk_percent']:
                status = ServiceStatus.UNHEALTHY
                messages.append(f"Critical disk usage: {disk_percent:.1f}%")
            elif load_avg >= self.critical_thresholds['load_average']:
                status = ServiceStatus.UNHEALTHY
                messages.append(f"Critical load average: {load_avg:.2f}")
            
            # Warning 체크
            elif cpu_percent >= self.warning_thresholds['cpu_percent']:
                status = ServiceStatus.DEGRADED
                messages.append(f"High CPU usage: {cpu_percent:.1f}%")
            elif memory_percent >= self.warning_thresholds['memory_percent']:
                status = ServiceStatus.DEGRADED
                messages.append(f"High memory usage: {memory_percent:.1f}%")
            elif disk_percent >= self.warning_thresholds['disk_percent']:
                status = ServiceStatus.DEGRADED
                messages.append(f"High disk usage: {disk_percent:.1f}%")
            elif load_avg >= self.warning_thresholds['load_average']:
                status = ServiceStatus.DEGRADED
                messages.append(f"High load average: {load_avg:.2f}")
            
            message = "; ".join(messages) if messages else "System resources are healthy"
            
            response_time_ms = (time.time() - start_time) * 1000
            
            return HealthCheckResult(
                service_name="system_resources",
                status=status,
                response_time_ms=response_time_ms,
                message=message,
                details=details,
                checked_at=checked_at
            )
            
        except Exception as e:
            logger.error(f"Error checking system resources: {e}")
            return HealthCheckResult(
                service_name="system_resources",
                status=ServiceStatus.UNKNOWN,
                response_time_ms=(time.time() - start_time) * 1000,
                message=f"Error checking system resources: {str(e)}",
                details={"error": str(e)},
                checked_at=checked_at
            )

class IntegratedHealthChecker:
    """통합 헬스체커"""
    
    def __init__(self):
        """통합 헬스체커 초기화"""
        self.service_checkers: Dict[str, ServiceHealthChecker] = {}
        self.system_checker = SystemResourceChecker()
        self.metrics = get_metrics()
        self.event_producer = get_event_producer()
        
        # 기본 서비스들 등록
        self._register_default_services()
        
        # 체크 결과 히스토리
        self.check_history: List[Dict[str, HealthCheckResult]] = []
        self.max_history = 1000
        
        # 알림 설정
        self.alert_cooldown = timedelta(minutes=5)  # 5분 쿨다운
        self.last_alerts: Dict[str, datetime] = {}
    
    def _register_default_services(self):
        """기본 서비스들 등록"""
        services = {
            'postgres': 'http://postgres:5432',
            'redis': 'http://redis:6379',
            'mlflow': 'http://mlflow:5000/health',
            'feast': 'http://feast:6566/health',
            'airflow': 'http://airflow-webserver:8080/health',
            'api': 'http://api:8000/health',
            'prometheus': 'http://prometheus:9090/-/healthy',
            'grafana': 'http://grafana:3000/api/health'
        }
        
        for service_name, endpoint in services.items():
            self.add_service(service_name, endpoint)
    
    def add_service(self, service_name: str, endpoint: str, **kwargs):
        """서비스 추가"""
        self.service_checkers[service_name] = ServiceHealthChecker(
            service_name=service_name,
            endpoint=endpoint,
            **kwargs
        )
        logger.info(f"Added health check for service: {service_name}")
    
    def remove_service(self, service_name: str):
        """서비스 제거"""
        if service_name in self.service_checkers:
            del self.service_checkers[service_name]
            logger.info(f"Removed health check for service: {service_name}")
    
    async def check_all_services(self) -> Dict[str, HealthCheckResult]:
        """모든 서비스 헬스체크"""
        results = {}
        
        # 시스템 리소스 체크
        system_result = await self.system_checker.check_system_resources()
        results['system_resources'] = system_result
        
        # 서비스별 헬스체크 (병렬 실행)
        service_tasks = []
        for service_name, checker in self.service_checkers.items():
            task = asyncio.create_task(checker.check_health())
            service_tasks.append((service_name, task))
        
        # 모든 태스크 완료 대기
        for service_name, task in service_tasks:
            try:
                result = await task
                results[service_name] = result
            except Exception as e:
                logger.error(f"Error checking {service_name}: {e}")
                results[service_name] = HealthCheckResult(
                    service_name=service_name,
                    status=ServiceStatus.UNKNOWN,
                    response_time_ms=0,
                    message=f"Check failed: {str(e)}",
                    details={"error": str(e)},
                    checked_at=datetime.utcnow()
                )
        
        # 히스토리 업데이트
        self.check_history.append(results)
        if len(self.check_history) > self.max_history:
            self.check_history.pop(0)
        
        # 메트릭 업데이트
        self._update_metrics(results)
        
        # 알림 체크
        await self._check_alerts(results)
        
        return results
    
    def _update_metrics(self, results: Dict[str, HealthCheckResult]):
        """메트릭 업데이트"""
        for service_name, result in results.items():
            # 서비스 헬스 메트릭 (0=unhealthy, 1=healthy)
            health_value = 1 if result.status == ServiceStatus.HEALTHY else 0
            
            # Prometheus 게이지 업데이트
            try:
                from prometheus_client import Gauge
                health_gauge = Gauge(
                    f'{service_name}_service_healthy',
                    f'{service_name} service health status',
                    registry=self.metrics.registry
                )
                health_gauge.set(health_value)
                
                # 응답시간 메트릭
                response_time_gauge = Gauge(
                    f'{service_name}_response_time_ms',
                    f'{service_name} response time in milliseconds',
                    registry=self.metrics.registry
                )
                response_time_gauge.set(result.response_time_ms)
                
            except Exception as e:
                logger.error(f"Error updating metrics for {service_name}: {e}")
    
    async def _check_alerts(self, results: Dict[str, HealthCheckResult]):
        """알림 체크 및 전송"""
        current_time = datetime.utcnow()
        
        for service_name, result in results.items():
            # 쿨다운 체크
            last_alert_time = self.last_alerts.get(service_name)
            if last_alert_time and current_time - last_alert_time < self.alert_cooldown:
                continue
            
            # 알림 조건 체크
            should_alert = False
            alert_level = AlertLevel.INFO
            alert_message = ""
            
            if result.status == ServiceStatus.UNHEALTHY:
                should_alert = True
                alert_level = AlertLevel.ERROR
                alert_message = f"Service {service_name} is unhealthy: {result.message}"
            elif result.status == ServiceStatus.DEGRADED:
                should_alert = True
                alert_level = AlertLevel.WARNING
                alert_message = f"Service {service_name} is degraded: {result.message}"
            elif result.response_time_ms > 5000:  # 5초 이상
                should_alert = True
                alert_level = AlertLevel.WARNING
                alert_message = f"Service {service_name} has high response time: {result.response_time_ms:.0f}ms"
            
            # 알림 전송
            if should_alert:
                await self._send_alert(service_name, alert_level, alert_message, result.details)
                self.last_alerts[service_name] = current_time
    
    async def _send_alert(self, service_name: str, level: AlertLevel, message: str, details: Dict[str, Any]):
        """알림 전송"""
        try:
            # 이벤트 생성 및 전송
            alert_event = EventFactory.create_system_alert(
                service=service_name,
                level=level,
                message=message,
                details=details
            )
            
            # Kafka로 알림 이벤트 전송
            self.event_producer.send_event(alert_event)
            
            # 로깅
            if level == AlertLevel.CRITICAL:
                logger.critical(f"CRITICAL ALERT: {message}")
            elif level == AlertLevel.ERROR:
                logger.error(f"ERROR ALERT: {message}")
            elif level == AlertLevel.WARNING:
                logger.warning(f"WARNING ALERT: {message}")
            else:
                logger.info(f"INFO ALERT: {message}")
            
        except Exception as e:
            logger.error(f"Error sending alert for {service_name}: {e}")
    
    def get_overall_health(self, results: Dict[str, HealthCheckResult] = None) -> Tuple[ServiceStatus, str]:
        """전체 시스템 헬스 상태 반환"""
        if results is None:
            if not self.check_history:
                return ServiceStatus.UNKNOWN, "No health check data available"
            results = self.check_history[-1]
        
        # 서비스별 상태 집계
        healthy_count = sum(1 for r in results.values() if r.status == ServiceStatus.HEALTHY)
        degraded_count = sum(1 for r in results.values() if r.status == ServiceStatus.DEGRADED)
        unhealthy_count = sum(1 for r in results.values() if r.status == ServiceStatus.UNHEALTHY)
        unknown_count = sum(1 for r in results.values() if r.status == ServiceStatus.UNKNOWN)
        
        total_services = len(results)
        
        # 전체 상태 결정
        if unhealthy_count > 0:
            status = ServiceStatus.UNHEALTHY
            message = f"{unhealthy_count} services unhealthy, {degraded_count} degraded, {healthy_count} healthy"
        elif degraded_count > total_services // 2:  # 절반 이상이 degraded
            status = ServiceStatus.DEGRADED
            message = f"{degraded_count} services degraded, {healthy_count} healthy"
        elif healthy_count == total_services:
            status = ServiceStatus.HEALTHY
            message = "All services healthy"
        elif healthy_count >= total_services * 0.8:  # 80% 이상 정상
            status = ServiceStatus.HEALTHY
            message = f"{healthy_count}/{total_services} services healthy"
        else:
            status = ServiceStatus.DEGRADED
            message = f"Mixed service health: {healthy_count} healthy, {degraded_count} degraded, {unhealthy_count} unhealthy"
        
        return status, message
    
    def get_service_availability(self, service_name: str, time_window: timedelta = timedelta(hours=24)) -> Optional[float]:
        """서비스 가용률 반환"""
        if service_name == 'system_resources':
            # 시스템 리소스는 히스토리에서 계산
            cutoff_time = datetime.utcnow() - time_window
            recent_checks = [
                check_result[service_name] 
                for check_result in self.check_history 
                if service_name in check_result and check_result[service_name].checked_at >= cutoff_time
            ]
            
            if not recent_checks:
                return None
            
            healthy_checks = sum(1 for check in recent_checks if check.status == ServiceStatus.HEALTHY)
            return healthy_checks / len(recent_checks)
        
        # 서비스별 체커에서 가용률 가져오기
        if service_name in self.service_checkers:
            return self.service_checkers[service_name].get_availability(time_window)
        
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """통계 정보 반환"""
        if not self.check_history:
            return {"message": "No health check data available"}
        
        latest_results = self.check_history[-1]
        overall_status, overall_message = self.get_overall_health(latest_results)
        
        # 서비스별 통계
        service_stats = {}
        for service_name in latest_results.keys():
            availability_24h = self.get_service_availability(service_name, timedelta(hours=24))
            availability_1h = self.get_service_availability(service_name, timedelta(hours=1))
            
            latest_result = latest_results[service_name]
            service_stats[service_name] = {
                "status": latest_result.status.value,
                "message": latest_result.message,
                "response_time_ms": latest_result.response_time_ms,
                "availability_24h": availability_24h,
                "availability_1h": availability_1h,
                "last_checked": latest_result.checked_at.isoformat()
            }
        
        return {
            "overall_status": overall_status.value,
            "overall_message": overall_message,
            "services": service_stats,
            "total_checks_performed": len(self.check_history),
            "last_check_time": latest_results[list(latest_results.keys())[0]].checked_at.isoformat() if latest_results else None
        }

# 글로벌 헬스체커 인스턴스
integrated_health_checker = IntegratedHealthChecker()
