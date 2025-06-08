"""
모니터링 API 라우터
통합 모니터링 시스템의 REST API 엔드포인트
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel

from ..monitoring.health_checker import integrated_health_checker, ServiceStatus
from ..monitoring.alerting import alert_manager, AlertRule, NotificationTarget, NotificationChannel, AlertLevel
from ..events.stream_processor import realtime_analyzer

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/monitoring", tags=["monitoring"])

# Pydantic 모델들
class HealthCheckResponse(BaseModel):
    """헬스체크 응답 모델"""
    service_name: str
    status: str
    response_time_ms: float
    message: str
    checked_at: str
    endpoint: Optional[str] = None

class OverallHealthResponse(BaseModel):
    """전체 헬스 응답 모델"""
    overall_status: str
    overall_message: str
    services: Dict[str, HealthCheckResponse]
    last_check_time: Optional[str]

class AlertRuleRequest(BaseModel):
    """알림 규칙 요청 모델"""
    name: str
    condition: str
    severity: str
    channels: List[str]
    cooldown_minutes: int = 5
    enabled: bool = True
    description: str = ""

class NotificationTargetRequest(BaseModel):
    """알림 대상 요청 모델"""
    channel: str
    address: str
    config: Dict[str, Any] = {}

@router.get("/health", response_model=OverallHealthResponse)
async def get_overall_health():
    """
    전체 시스템 헬스 상태 조회
    """
    try:
        # 모든 서비스 헬스체크 실행
        results = await integrated_health_checker.check_all_services()
        
        # 전체 상태 계산
        overall_status, overall_message = integrated_health_checker.get_overall_health(results)
        
        # 응답 데이터 변환
        services = {}
        for service_name, result in results.items():
            services[service_name] = HealthCheckResponse(
                service_name=result.service_name,
                status=result.status.value,
                response_time_ms=result.response_time_ms,
                message=result.message,
                checked_at=result.checked_at.isoformat(),
                endpoint=result.endpoint
            )
        
        return OverallHealthResponse(
            overall_status=overall_status.value,
            overall_message=overall_message,
            services=services,
            last_check_time=results[list(results.keys())[0]].checked_at.isoformat() if results else None
        )
        
    except Exception as e:
        logger.error(f"Error getting overall health: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get health status: {str(e)}")

@router.get("/health/{service_name}")
async def get_service_health(service_name: str):
    """
    특정 서비스 헬스 상태 조회
    """
    try:
        # 모든 서비스 체크
        results = await integrated_health_checker.check_all_services()
        
        if service_name not in results:
            raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")
        
        result = results[service_name]
        
        # 가용률 정보 추가
        availability_24h = integrated_health_checker.get_service_availability(
            service_name, timedelta(hours=24)
        )
        availability_1h = integrated_health_checker.get_service_availability(
            service_name, timedelta(hours=1)
        )
        
        return {
            "service_name": result.service_name,
            "status": result.status.value,
            "response_time_ms": result.response_time_ms,
            "message": result.message,
            "details": result.details,
            "checked_at": result.checked_at.isoformat(),
            "endpoint": result.endpoint,
            "availability_24h": availability_24h,
            "availability_1h": availability_1h
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting service health for {service_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get service health: {str(e)}")

@router.get("/stats")
async def get_monitoring_stats():
    """
    모니터링 통계 정보 조회
    """
    try:
        health_stats = integrated_health_checker.get_stats()
        alert_stats = alert_manager.get_alert_stats()
        
        return {
            "health_monitoring": health_stats,
            "alert_system": alert_stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting monitoring stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get monitoring stats: {str(e)}")

@router.get("/availability")
async def get_service_availability(
    service_name: Optional[str] = Query(None, description="특정 서비스 이름"),
    hours: int = Query(24, description="조회할 시간 범위 (시간)")
):
    """
    서비스 가용률 조회
    """
    try:
        time_window = timedelta(hours=hours)
        
        if service_name:
            # 특정 서비스 가용률
            availability = integrated_health_checker.get_service_availability(service_name, time_window)
            if availability is None:
                raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")
            
            return {
                "service_name": service_name,
                "availability": availability,
                "time_window_hours": hours,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            # 모든 서비스 가용률
            results = await integrated_health_checker.check_all_services()
            availability_data = {}
            
            for svc_name in results.keys():
                availability = integrated_health_checker.get_service_availability(svc_name, time_window)
                availability_data[svc_name] = availability
            
            return {
                "all_services": availability_data,
                "time_window_hours": hours,
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting availability: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get availability: {str(e)}")

@router.post("/health/check")
async def trigger_health_check(background_tasks: BackgroundTasks):
    """
    수동으로 헬스체크 실행
    """
    try:
        # 백그라운드에서 헬스체크 실행
        background_tasks.add_task(integrated_health_checker.check_all_services)
        
        return {
            "message": "Health check triggered",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error triggering health check: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger health check: {str(e)}")

# 알림 관리 엔드포인트들
@router.get("/alerts/rules")
async def get_alert_rules():
    """
    모든 알림 규칙 조회
    """
    try:
        rules = {}
        for rule_name, rule in alert_manager.rules.items():
            rules[rule_name] = {
                "name": rule.name,
                "condition": rule.condition,
                "severity": rule.severity.value,
                "channels": [ch.value for ch in rule.channels],
                "cooldown_minutes": rule.cooldown_minutes,
                "enabled": rule.enabled,
                "description": rule.description
            }
        
        return {
            "rules": rules,
            "total_rules": len(rules),
            "enabled_rules": sum(1 for rule in alert_manager.rules.values() if rule.enabled)
        }
        
    except Exception as e:
        logger.error(f"Error getting alert rules: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get alert rules: {str(e)}")

@router.post("/alerts/rules")
async def create_alert_rule(rule_request: AlertRuleRequest):
    """
    새 알림 규칙 생성
    """
    try:
        # 채널 변환
        channels = []
        for ch_str in rule_request.channels:
            try:
                channels.append(NotificationChannel(ch_str))
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid channel: {ch_str}")
        
        # 심각도 변환
        try:
            severity = AlertLevel(rule_request.severity)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid severity: {rule_request.severity}")
        
        # 규칙 생성
        rule = AlertRule(
            name=rule_request.name,
            condition=rule_request.condition,
            severity=severity,
            channels=channels,
            cooldown_minutes=rule_request.cooldown_minutes,
            enabled=rule_request.enabled,
            description=rule_request.description
        )
        
        # 규칙 추가
        alert_manager.add_rule(rule)
        
        return {
            "message": f"Alert rule '{rule_request.name}' created successfully",
            "rule_name": rule_request.name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating alert rule: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create alert rule: {str(e)}")

@router.put("/alerts/rules/{rule_name}/enable")
async def enable_alert_rule(rule_name: str):
    """
    알림 규칙 활성화
    """
    try:
        if rule_name not in alert_manager.rules:
            raise HTTPException(status_code=404, detail=f"Rule '{rule_name}' not found")
        
        alert_manager.rules[rule_name].enabled = True
        
        return {
            "message": f"Alert rule '{rule_name}' enabled",
            "rule_name": rule_name,
            "enabled": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enabling alert rule: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to enable alert rule: {str(e)}")

@router.put("/alerts/rules/{rule_name}/disable")
async def disable_alert_rule(rule_name: str):
    """
    알림 규칙 비활성화
    """
    try:
        if rule_name not in alert_manager.rules:
            raise HTTPException(status_code=404, detail=f"Rule '{rule_name}' not found")
        
        alert_manager.rules[rule_name].enabled = False
        
        return {
            "message": f"Alert rule '{rule_name}' disabled",
            "rule_name": rule_name,
            "enabled": False
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disabling alert rule: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to disable alert rule: {str(e)}")

@router.delete("/alerts/rules/{rule_name}")
async def delete_alert_rule(rule_name: str):
    """
    알림 규칙 삭제
    """
    try:
        if rule_name not in alert_manager.rules:
            raise HTTPException(status_code=404, detail=f"Rule '{rule_name}' not found")
        
        alert_manager.remove_rule(rule_name)
        
        return {
            "message": f"Alert rule '{rule_name}' deleted",
            "rule_name": rule_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting alert rule: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete alert rule: {str(e)}")

@router.get("/alerts/history")
async def get_alert_history(
    limit: int = Query(100, description="조회할 알림 수"),
    severity: Optional[str] = Query(None, description="심각도 필터"),
    service: Optional[str] = Query(None, description="서비스 필터"),
    hours: int = Query(24, description="조회할 시간 범위 (시간)")
):
    """
    알림 히스토리 조회
    """
    try:
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # 필터링된 알림 히스토리
        filtered_alerts = []
        for alert in alert_manager.alert_history:
            if alert.timestamp < cutoff_time:
                continue
            
            if severity and alert.level.value != severity:
                continue
            
            if service and alert.service != service:
                continue
            
            filtered_alerts.append({
                "event_id": alert.event_id,
                "service": alert.service,
                "level": alert.level.value,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "alert_code": getattr(alert, 'alert_code', None),
                "details": alert.details
            })
        
        # 최신순 정렬 및 제한
        filtered_alerts.sort(key=lambda x: x['timestamp'], reverse=True)
        filtered_alerts = filtered_alerts[:limit]
        
        return {
            "alerts": filtered_alerts,
            "total_count": len(filtered_alerts),
            "time_window_hours": hours,
            "filters": {
                "severity": severity,
                "service": service
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting alert history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get alert history: {str(e)}")

@router.get("/alerts/targets")
async def get_notification_targets():
    """
    알림 대상 조회
    """
    try:
        targets = {}
        for channel, target_list in alert_manager.targets.items():
            targets[channel.value] = [
                {
                    "address": target.address,
                    "config": {k: "***" if "password" in k.lower() else v 
                              for k, v in (target.config or {}).items()}
                }
                for target in target_list
            ]
        
        return {
            "targets": targets,
            "total_targets": sum(len(target_list) for target_list in alert_manager.targets.values())
        }
        
    except Exception as e:
        logger.error(f"Error getting notification targets: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get notification targets: {str(e)}")

@router.post("/alerts/targets")
async def create_notification_target(target_request: NotificationTargetRequest):
    """
    알림 대상 추가
    """
    try:
        # 채널 변환
        try:
            channel = NotificationChannel(target_request.channel)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid channel: {target_request.channel}")
        
        # 대상 생성
        target = NotificationTarget(
            channel=channel,
            address=target_request.address,
            config=target_request.config
        )
        
        # 대상 추가
        alert_manager.add_target(target)
        
        return {
            "message": f"Notification target added: {target_request.channel} -> {target_request.address}",
            "channel": target_request.channel,
            "address": target_request.address
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating notification target: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create notification target: {str(e)}")

@router.delete("/alerts/targets/{channel}/{address}")
async def delete_notification_target(channel: str, address: str):
    """
    알림 대상 삭제
    """
    try:
        # 채널 변환
        try:
            channel_enum = NotificationChannel(channel)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid channel: {channel}")
        
        # 대상 제거
        alert_manager.remove_target(channel_enum, address)
        
        return {
            "message": f"Notification target removed: {channel} -> {address}",
            "channel": channel,
            "address": address
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting notification target: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete notification target: {str(e)}")

# 실시간 분석 엔드포인트들
@router.get("/realtime/analytics")
async def get_realtime_analytics():
    """
    실시간 분석 데이터 조회
    """
    try:
        # 실시간 집계 데이터 가져오기
        aggregations = realtime_analyzer.stream_processor.get_current_aggregations()
        
        # 응답 데이터 구성
        analytics = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_activity": aggregations.get('user_activity_rate', {}),
            "recommendation_performance": aggregations.get('recommendation_performance', {}),
            "model_predictions": aggregations.get('model_prediction_rate', {}),
            "system_health": aggregations.get('system_health', {}),
            "content_popularity": aggregations.get('content_popularity', {})
        }
        
        return analytics
        
    except Exception as e:
        logger.error(f"Error getting realtime analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get realtime analytics: {str(e)}")

@router.get("/realtime/metrics")
async def get_realtime_metrics():
    """
    실시간 메트릭 요약 조회
    """
    try:
        # 핸들러 통계
        handler_stats = realtime_analyzer.get_stats()
        
        # 최근 시스템 상태
        health_results = await integrated_health_checker.check_all_services()
        overall_status, overall_message = integrated_health_checker.get_overall_health(health_results)
        
        # 활성 사용자 수 (예시)
        aggregations = realtime_analyzer.stream_processor.get_current_aggregations()
        active_users = 0
        if 'user_activity_rate' in aggregations:
            active_users = len(aggregations['user_activity_rate'].get('unique_users', set()))
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_system_status": overall_status.value,
            "overall_message": overall_message,
            "active_users_5min": active_users,
            "realtime_analyzer_stats": handler_stats,
            "services_count": {
                "healthy": sum(1 for r in health_results.values() if r.status == ServiceStatus.HEALTHY),
                "degraded": sum(1 for r in health_results.values() if r.status == ServiceStatus.DEGRADED),
                "unhealthy": sum(1 for r in health_results.values() if r.status == ServiceStatus.UNHEALTHY),
                "unknown": sum(1 for r in health_results.values() if r.status == ServiceStatus.UNKNOWN)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting realtime metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get realtime metrics: {str(e)}")

@router.post("/test/alert")
async def test_alert(
    service: str = Query("test-service", description="테스트 서비스 이름"),
    level: str = Query("warning", description="알림 레벨"),
    message: str = Query("This is a test alert", description="테스트 메시지")
):
    """
    테스트 알림 전송
    """
    try:
        # 알림 레벨 변환
        try:
            alert_level = AlertLevel(level)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid alert level: {level}")
        
        # 테스트 알림 이벤트 생성
        from ..events.event_schemas import EventFactory
        
        alert_event = EventFactory.create_system_alert(
            service=service,
            level=alert_level,
            message=message,
            alert_code="test_alert",
            details={"test": True, "timestamp": datetime.utcnow().isoformat()}
        )
        
        # 알림 처리
        await alert_manager.process_alert(alert_event)
        
        return {
            "message": "Test alert sent",
            "alert_details": {
                "service": service,
                "level": level,
                "message": message,
                "event_id": alert_event.event_id
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending test alert: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send test alert: {str(e)}")
