"""
알림 시스템
시스템 상태 변화 및 이상 상황에 대한 알림 처리
"""

import asyncio
import logging
import smtplib
import json
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass
from enum import Enum
import aiohttp

from .health_checker import ServiceStatus, HealthCheckResult
from ..events.event_schemas import SystemAlertEvent, AlertLevel
from ..events.kafka_producer import get_event_producer

logger = logging.getLogger(__name__)

class NotificationChannel(Enum):
    """알림 채널"""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    SMS = "sms"
    CONSOLE = "console"

@dataclass
class AlertRule:
    """알림 규칙"""
    name: str
    condition: str  # 조건식
    severity: AlertLevel
    channels: List[NotificationChannel]
    cooldown_minutes: int = 5
    enabled: bool = True
    description: str = ""

@dataclass
class NotificationTarget:
    """알림 대상"""
    channel: NotificationChannel
    address: str  # 이메일, 슬랙 채널, 웹훅 URL 등
    config: Dict[str, Any] = None

class AlertManager:
    """알림 매니저"""
    
    def __init__(self):
        """알림 매니저 초기화"""
        self.rules: Dict[str, AlertRule] = {}
        self.targets: Dict[NotificationChannel, List[NotificationTarget]] = {}
        self.alert_history: List[SystemAlertEvent] = []
        self.last_alerts: Dict[str, datetime] = {}
        self.max_history = 1000
        
        # 기본 규칙 등록
        self._register_default_rules()
        
        # 기본 알림 대상 설정
        self._setup_default_targets()
        
        # 이벤트 프로듀서
        self.event_producer = get_event_producer()
    
    def _register_default_rules(self):
        """기본 알림 규칙 등록"""
        default_rules = [
            AlertRule(
                name="service_down",
                condition="service.status == 'unhealthy'",
                severity=AlertLevel.CRITICAL,
                channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK],
                cooldown_minutes=5,
                description="서비스가 다운된 경우"
            ),
            AlertRule(
                name="high_cpu_usage",
                condition="system.cpu_percent > 90",
                severity=AlertLevel.WARNING,
                channels=[NotificationChannel.SLACK],
                cooldown_minutes=10,
                description="CPU 사용률이 90% 이상인 경우"
            ),
            AlertRule(
                name="high_memory_usage",
                condition="system.memory_percent > 90",
                severity=AlertLevel.WARNING,
                channels=[NotificationChannel.SLACK],
                cooldown_minutes=10,
                description="메모리 사용률이 90% 이상인 경우"
            ),
            AlertRule(
                name="disk_space_low",
                condition="system.disk_percent > 95",
                severity=AlertLevel.CRITICAL,
                channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK],
                cooldown_minutes=15,
                description="디스크 사용률이 95% 이상인 경우"
            ),
            AlertRule(
                name="high_error_rate",
                condition="api.error_rate > 0.1",
                severity=AlertLevel.ERROR,
                channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK],
                cooldown_minutes=5,
                description="API 에러율이 10% 이상인 경우"
            ),
            AlertRule(
                name="slow_response_time",
                condition="api.response_time_ms > 5000",
                severity=AlertLevel.WARNING,
                channels=[NotificationChannel.SLACK],
                cooldown_minutes=10,
                description="API 응답시간이 5초 이상인 경우"
            ),
            AlertRule(
                name="model_accuracy_drop",
                condition="model.accuracy < 0.8",
                severity=AlertLevel.WARNING,
                channels=[NotificationChannel.SLACK],
                cooldown_minutes=30,
                description="모델 정확도가 80% 미만인 경우"
            ),
            AlertRule(
                name="training_failure",
                condition="training.status == 'failed'",
                severity=AlertLevel.ERROR,
                channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK],
                cooldown_minutes=0,
                description="모델 훈련이 실패한 경우"
            )
        ]
        
        for rule in default_rules:
            self.rules[rule.name] = rule
        
        logger.info(f"Registered {len(default_rules)} default alert rules")
    
    def _setup_default_targets(self):
        """기본 알림 대상 설정"""
        # 환경변수에서 설정 읽기
        import os
        
        # 이메일 설정
        email_targets = []
        admin_email = os.getenv('ADMIN_EMAIL')
        if admin_email:
            email_targets.append(NotificationTarget(
                channel=NotificationChannel.EMAIL,
                address=admin_email,
                config={
                    'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
                    'smtp_port': int(os.getenv('SMTP_PORT', '587')),
                    'smtp_username': os.getenv('SMTP_USERNAME'),
                    'smtp_password': os.getenv('SMTP_PASSWORD'),
                    'use_tls': os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
                }
            ))
        
        # 슬랙 설정
        slack_targets = []
        slack_webhook = os.getenv('SLACK_WEBHOOK_URL')
        if slack_webhook:
            slack_targets.append(NotificationTarget(
                channel=NotificationChannel.SLACK,
                address=slack_webhook,
                config={
                    'channel': os.getenv('SLACK_CHANNEL', '#alerts'),
                    'username': os.getenv('SLACK_USERNAME', 'MovieMLOps Bot'),
                    'icon_emoji': os.getenv('SLACK_ICON_EMOJI', ':warning:')
                }
            ))
        
        # 웹훅 설정
        webhook_targets = []
        webhook_url = os.getenv('WEBHOOK_URL')
        if webhook_url:
            webhook_targets.append(NotificationTarget(
                channel=NotificationChannel.WEBHOOK,
                address=webhook_url,
                config={
                    'timeout': int(os.getenv('WEBHOOK_TIMEOUT', '30')),
                    'headers': json.loads(os.getenv('WEBHOOK_HEADERS', '{}'))
                }
            ))
        
        # 콘솔 로깅 (항상 활성화)
        console_targets = [NotificationTarget(
            channel=NotificationChannel.CONSOLE,
            address="console",
            config={}
        )]
        
        # 대상 등록
        self.targets = {
            NotificationChannel.EMAIL: email_targets,
            NotificationChannel.SLACK: slack_targets,
            NotificationChannel.WEBHOOK: webhook_targets,
            NotificationChannel.CONSOLE: console_targets
        }
        
        total_targets = sum(len(targets) for targets in self.targets.values())
        logger.info(f"Configured {total_targets} notification targets")
    
    def add_rule(self, rule: AlertRule):
        """알림 규칙 추가"""
        self.rules[rule.name] = rule
        logger.info(f"Added alert rule: {rule.name}")
    
    def remove_rule(self, rule_name: str):
        """알림 규칙 제거"""
        if rule_name in self.rules:
            del self.rules[rule_name]
            logger.info(f"Removed alert rule: {rule_name}")
    
    def add_target(self, target: NotificationTarget):
        """알림 대상 추가"""
        if target.channel not in self.targets:
            self.targets[target.channel] = []
        self.targets[target.channel].append(target)
        logger.info(f"Added notification target: {target.channel.value} -> {target.address}")
    
    def remove_target(self, channel: NotificationChannel, address: str):
        """알림 대상 제거"""
        if channel in self.targets:
            self.targets[channel] = [
                target for target in self.targets[channel] 
                if target.address != address
            ]
            logger.info(f"Removed notification target: {channel.value} -> {address}")
    
    async def process_alert(self, alert_event: SystemAlertEvent):
        """알림 이벤트 처리"""
        try:
            # 알림 히스토리에 추가
            self.alert_history.append(alert_event)
            if len(self.alert_history) > self.max_history:
                self.alert_history.pop(0)
            
            # 규칙 매칭 및 알림 전송
            await self._evaluate_and_send_alerts(alert_event)
            
        except Exception as e:
            logger.error(f"Error processing alert: {e}")
    
    async def _evaluate_and_send_alerts(self, alert_event: SystemAlertEvent):
        """규칙 평가 및 알림 전송"""
        current_time = datetime.utcnow()
        
        # 쿨다운 체크
        alert_key = f"{alert_event.service}_{alert_event.level.value}"
        last_alert_time = self.last_alerts.get(alert_key)
        
        # 활성화된 규칙들을 순회하며 조건 확인
        for rule_name, rule in self.rules.items():
            if not rule.enabled:
                continue
            
            # 쿨다운 체크
            if last_alert_time:
                cooldown = timedelta(minutes=rule.cooldown_minutes)
                if current_time - last_alert_time < cooldown:
                    continue
            
            # 규칙 조건 평가
            if self._evaluate_rule_condition(rule, alert_event):
                # 알림 전송
                await self._send_notifications(rule, alert_event)
                self.last_alerts[alert_key] = current_time
                break  # 첫 번째 매칭 규칙만 처리
    
    def _evaluate_rule_condition(self, rule: AlertRule, alert_event: SystemAlertEvent) -> bool:
        """규칙 조건 평가"""
        try:
            # 간단한 조건 평가 (실제로는 더 복잡한 규칙 엔진 필요)
            condition = rule.condition.lower()
            
            # 서비스 상태 조건
            if "service.status" in condition:
                if "== 'unhealthy'" in condition and alert_event.level in [AlertLevel.ERROR, AlertLevel.CRITICAL]:
                    return True
                if "== 'degraded'" in condition and alert_event.level == AlertLevel.WARNING:
                    return True
            
            # 심각도 조건
            if "severity" in condition:
                if rule.severity == alert_event.level:
                    return True
            
            # 서비스 이름 조건
            if alert_event.service in condition:
                return True
            
            # 기본적으로 심각도가 같거나 높으면 알림
            severity_order = [AlertLevel.INFO, AlertLevel.WARNING, AlertLevel.ERROR, AlertLevel.CRITICAL]
            rule_severity_index = severity_order.index(rule.severity)
            alert_severity_index = severity_order.index(alert_event.level)
            
            return alert_severity_index >= rule_severity_index
            
        except Exception as e:
            logger.error(f"Error evaluating rule condition for {rule.name}: {e}")
            return False
    
    async def _send_notifications(self, rule: AlertRule, alert_event: SystemAlertEvent):
        """알림 전송"""
        tasks = []
        
        for channel in rule.channels:
            if channel in self.targets:
                for target in self.targets[channel]:
                    task = asyncio.create_task(
                        self._send_single_notification(channel, target, rule, alert_event)
                    )
                    tasks.append(task)
        
        # 모든 알림 전송 완료 대기
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            success_count = sum(1 for result in results if result is True)
            error_count = len(results) - success_count
            
            if error_count > 0:
                logger.warning(f"Alert sent: {success_count} successful, {error_count} failed")
            else:
                logger.info(f"Alert sent successfully to {success_count} targets")
    
    async def _send_single_notification(self, channel: NotificationChannel, 
                                      target: NotificationTarget, rule: AlertRule, 
                                      alert_event: SystemAlertEvent) -> bool:
        """단일 알림 전송"""
        try:
            if channel == NotificationChannel.EMAIL:
                return await self._send_email_notification(target, rule, alert_event)
            elif channel == NotificationChannel.SLACK:
                return await self._send_slack_notification(target, rule, alert_event)
            elif channel == NotificationChannel.WEBHOOK:
                return await self._send_webhook_notification(target, rule, alert_event)
            elif channel == NotificationChannel.CONSOLE:
                return self._send_console_notification(target, rule, alert_event)
            else:
                logger.warning(f"Unsupported notification channel: {channel.value}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending {channel.value} notification: {e}")
            return False
    
    async def _send_email_notification(self, target: NotificationTarget, 
                                     rule: AlertRule, alert_event: SystemAlertEvent) -> bool:
        """이메일 알림 전송"""
        try:
            config = target.config or {}
            
            # 이메일 내용 생성
            subject = f"[{alert_event.level.value.upper()}] {alert_event.service}: {rule.name}"
            
            body = f"""
            Alert Rule: {rule.name}
            Service: {alert_event.service}
            Severity: {alert_event.level.value.upper()}
            Time: {alert_event.timestamp.isoformat()}
            
            Message: {alert_event.message}
            
            Details: {json.dumps(alert_event.details, indent=2) if alert_event.details else 'No additional details'}
            
            Rule Description: {rule.description}
            """
            
            # 이메일 메시지 생성
            msg = MIMEMultipart()
            msg['From'] = config.get('smtp_username', 'noreply@moviemlops.com')
            msg['To'] = target.address
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            # SMTP 서버를 통해 전송
            smtp_server = config.get('smtp_server', 'smtp.gmail.com')
            smtp_port = config.get('smtp_port', 587)
            smtp_username = config.get('smtp_username')
            smtp_password = config.get('smtp_password')
            use_tls = config.get('use_tls', True)
            
            if not smtp_username or not smtp_password:
                logger.warning("SMTP credentials not configured")
                return False
            
            # 비동기 이메일 전송을 위해 별도 스레드에서 실행
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._send_smtp_email, 
                                     smtp_server, smtp_port, smtp_username, 
                                     smtp_password, use_tls, msg)
            
            logger.info(f"Email alert sent to {target.address}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return False
    
    def _send_smtp_email(self, smtp_server: str, smtp_port: int, 
                        username: str, password: str, use_tls: bool, msg: MIMEMultipart):
        """SMTP 이메일 전송 (동기)"""
        server = smtplib.SMTP(smtp_server, smtp_port)
        
        if use_tls:
            server.starttls()
        
        server.login(username, password)
        server.sendmail(msg['From'], msg['To'], msg.as_string())
        server.quit()
    
    async def _send_slack_notification(self, target: NotificationTarget, 
                                     rule: AlertRule, alert_event: SystemAlertEvent) -> bool:
        """슬랙 알림 전송"""
        try:
            config = target.config or {}
            webhook_url = target.address
            
            # 심각도에 따른 색상
            color_map = {
                AlertLevel.INFO: "#36a64f",      # 녹색
                AlertLevel.WARNING: "#ff9500",   # 주황색
                AlertLevel.ERROR: "#ff0000",     # 빨간색
                AlertLevel.CRITICAL: "#8b0000"   # 진빨간색
            }
            
            # 슬랙 메시지 페이로드
            payload = {
                "channel": config.get('channel', '#alerts'),
                "username": config.get('username', 'MovieMLOps Bot'),
                "icon_emoji": config.get('icon_emoji', ':warning:'),
                "attachments": [{
                    "color": color_map.get(alert_event.level, "#808080"),
                    "title": f"{alert_event.level.value.upper()}: {rule.name}",
                    "text": alert_event.message,
                    "fields": [
                        {
                            "title": "Service",
                            "value": alert_event.service,
                            "short": True
                        },
                        {
                            "title": "Time",
                            "value": alert_event.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"),
                            "short": True
                        },
                        {
                            "title": "Rule",
                            "value": rule.description or rule.name,
                            "short": False
                        }
                    ],
                    "footer": "MovieMLOps Monitoring",
                    "ts": int(alert_event.timestamp.timestamp())
                }]
            }
            
            # 웹훅으로 전송
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status == 200:
                        logger.info(f"Slack alert sent to {config.get('channel', '#alerts')}")
                        return True
                    else:
                        logger.error(f"Slack notification failed: HTTP {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False
    
    async def _send_webhook_notification(self, target: NotificationTarget, 
                                       rule: AlertRule, alert_event: SystemAlertEvent) -> bool:
        """웹훅 알림 전송"""
        try:
            config = target.config or {}
            webhook_url = target.address
            timeout = config.get('timeout', 30)
            headers = config.get('headers', {})
            
            # 웹훅 페이로드
            payload = {
                "event_type": "system_alert",
                "rule_name": rule.name,
                "service": alert_event.service,
                "severity": alert_event.level.value,
                "message": alert_event.message,
                "timestamp": alert_event.timestamp.isoformat(),
                "details": alert_event.details,
                "rule_description": rule.description
            }
            
            # 웹훅 전송
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.post(webhook_url, json=payload, headers=headers) as response:
                    if 200 <= response.status < 300:
                        logger.info(f"Webhook alert sent to {webhook_url}")
                        return True
                    else:
                        logger.error(f"Webhook notification failed: HTTP {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Failed to send webhook notification: {e}")
            return False
    
    def _send_console_notification(self, target: NotificationTarget, 
                                 rule: AlertRule, alert_event: SystemAlertEvent) -> bool:
        """콘솔 알림 출력"""
        try:
            timestamp = alert_event.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            message = (f"[{timestamp}] {alert_event.level.value.upper()} ALERT: "
                      f"{alert_event.service} - {alert_event.message}")
            
            if alert_event.level == AlertLevel.CRITICAL:
                logger.critical(message)
            elif alert_event.level == AlertLevel.ERROR:
                logger.error(message)
            elif alert_event.level == AlertLevel.WARNING:
                logger.warning(message)
            else:
                logger.info(message)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send console notification: {e}")
            return False
    
    def get_alert_stats(self) -> Dict[str, Any]:
        """알림 통계 반환"""
        if not self.alert_history:
            return {"message": "No alert history available"}
        
        # 최근 24시간 알림 분석
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        recent_alerts = [alert for alert in self.alert_history if alert.timestamp >= cutoff_time]
        
        # 심각도별 집계
        severity_counts = {}
        for level in AlertLevel:
            severity_counts[level.value] = sum(1 for alert in recent_alerts if alert.level == level)
        
        # 서비스별 집계
        service_counts = {}
        for alert in recent_alerts:
            if alert.service not in service_counts:
                service_counts[alert.service] = 0
            service_counts[alert.service] += 1
        
        # 규칙별 집계
        rule_stats = {}
        for rule_name, rule in self.rules.items():
            rule_stats[rule_name] = {
                "enabled": rule.enabled,
                "severity": rule.severity.value,
                "channels": [ch.value for ch in rule.channels],
                "cooldown_minutes": rule.cooldown_minutes,
                "description": rule.description
            }
        
        return {
            "total_alerts_24h": len(recent_alerts),
            "total_alerts_all_time": len(self.alert_history),
            "alerts_by_severity_24h": severity_counts,
            "alerts_by_service_24h": service_counts,
            "configured_rules": len(self.rules),
            "enabled_rules": sum(1 for rule in self.rules.values() if rule.enabled),
            "notification_channels": list(self.targets.keys()),
            "rules": rule_stats
        }

# 글로벌 알림 매니저 인스턴스
alert_manager = AlertManager()
