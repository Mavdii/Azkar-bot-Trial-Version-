#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🕌 Prayer Times Monitoring System - نظام مراقبة مواقيت الصلاة
================================================================
نظام مراقبة شامل لمتابعة أداء وصحة نظام مواقيت الصلاة

Features:
- 📊 مراقبة أداء APIs والاستجابة
- 🔍 فحص صحة جميع المكونات
- 📈 إحصائيات مفصلة ومقاييس الأداء
- 🚨 تنبيهات للمشاكل والأخطاء
- 📋 تقارير دورية للحالة

Author: Islamic Bot Developer Team
Version: 1.0.0
License: MIT
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
import pytz
from dataclasses import dataclass, field
from enum import Enum
import json
import time
import psutil
import platform

# Configure logging
logger = logging.getLogger(__name__)

# Cairo timezone
CAIRO_TZ = pytz.timezone('Africa/Cairo')

class HealthStatus(Enum):
    """حالات الصحة"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

class MetricType(Enum):
    """أنواع المقاييس"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"

@dataclass
class HealthCheck:
    """فحص صحة"""
    component: str
    status: HealthStatus
    message: str
    details: Optional[Dict[str, Any]] = None
    last_check: Optional[datetime] = None
    response_time_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'component': self.component,
            'status': self.status.value,
            'message': self.message,
            'details': self.details or {},
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'response_time_ms': self.response_time_ms
        }

@dataclass
class Metric:
    """مقياس أداء"""
    name: str
    type: MetricType
    value: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'name': self.name,
            'type': self.type.value,
            'value': self.value,
            'timestamp': self.timestamp.isoformat(),
            'labels': self.labels,
            'description': self.description
        }

@dataclass
class Alert:
    """تنبيه"""
    id: str
    severity: str
    message: str
    component: str
    timestamp: datetime
    resolved: bool = False
    resolution_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'id': self.id,
            'severity': self.severity,
            'message': self.message,
            'component': self.component,
            'timestamp': self.timestamp.isoformat(),
            'resolved': self.resolved,
            'resolution_time': self.resolution_time.isoformat() if self.resolution_time else None
        }
cla
ss PrayerTimesMonitor:
    """نظام مراقبة مواقيت الصلاة"""
    
    def __init__(self, integrated_system=None, check_interval_minutes: int = 5):
        self.integrated_system = integrated_system
        self.check_interval_minutes = check_interval_minutes
        
        # بيانات المراقبة
        self.health_checks: Dict[str, HealthCheck] = {}
        self.metrics: List[Metric] = []
        self.alerts: Dict[str, Alert] = {}
        
        # مهام المراقبة
        self.monitoring_task: Optional[asyncio.Task] = None
        self.is_monitoring = False
        
        # إعدادات التنبيهات
        self.alert_thresholds = {
            'api_response_time_ms': 5000,      # 5 ثوان
            'cache_hit_rate_percent': 50,      # 50%
            'failed_requests_percent': 20,     # 20%
            'system_memory_percent': 85,       # 85%
            'system_cpu_percent': 80           # 80%
        }
        
        # callbacks للتنبيهات
        self.alert_callbacks: List[Callable[[Alert], None]] = []
        
        # إحصائيات المراقبة
        self.monitoring_stats = {
            'total_checks': 0,
            'healthy_checks': 0,
            'warning_checks': 0,
            'critical_checks': 0,
            'total_alerts': 0,
            'active_alerts': 0,
            'monitoring_start_time': None,
            'last_check_time': None
        }
    
    async def start_monitoring(self) -> bool:
        """بدء المراقبة"""
        try:
            if self.is_monitoring:
                logger.warning("⚠️ المراقبة تعمل بالفعل")
                return True
            
            logger.info("🔄 بدء نظام مراقبة مواقيت الصلاة...")
            
            self.is_monitoring = True
            self.monitoring_stats['monitoring_start_time'] = datetime.now(CAIRO_TZ).isoformat()
            
            # بدء مهمة المراقبة الدورية
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            
            # إجراء فحص أولي
            await self.perform_health_checks()
            
            logger.info(f"✅ تم بدء المراقبة بفترة {self.check_interval_minutes} دقائق")
            return True
            
        except Exception as e:
            logger.error(f"❌ فشل في بدء المراقبة: {e}")
            self.is_monitoring = False
            return False
    
    async def stop_monitoring(self) -> None:
        """إيقاف المراقبة"""
        try:
            logger.info("🔄 إيقاف نظام المراقبة...")
            
            self.is_monitoring = False
            
            if self.monitoring_task and not self.monitoring_task.done():
                self.monitoring_task.cancel()
                try:
                    await self.monitoring_task
                except asyncio.CancelledError:
                    pass
            
            logger.info("✅ تم إيقاف نظام المراقبة")
            
        except Exception as e:
            logger.error(f"❌ خطأ في إيقاف المراقبة: {e}")
    
    async def _monitoring_loop(self) -> None:
        """حلقة المراقبة الدورية"""
        while self.is_monitoring:
            try:
                # إجراء فحوصات الصحة
                await self.perform_health_checks()
                
                # جمع المقاييس
                await self.collect_metrics()
                
                # فحص التنبيهات
                await self.check_alerts()
                
                # تنظيف البيانات القديمة
                await self._cleanup_old_data()
                
                # انتظار الفترة التالية
                await asyncio.sleep(self.check_interval_minutes * 60)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ خطأ في حلقة المراقبة: {e}")
                await asyncio.sleep(60)  # انتظار دقيقة قبل المحاولة مرة أخرى
    
    async def perform_health_checks(self) -> Dict[str, HealthCheck]:
        """إجراء فحوصات الصحة"""
        try:
            logger.debug("🔍 بدء فحوصات الصحة...")
            
            check_start = time.time()
            
            # فحص النظام المتكامل
            if self.integrated_system:
                await self._check_integrated_system()
            
            # فحص النظام العام
            await self._check_system_resources()
            
            # تحديث الإحصائيات
            self.monitoring_stats['total_checks'] += 1
            self.monitoring_stats['last_check_time'] = datetime.now(CAIRO_TZ).isoformat()
            
            # حساب إحصائيات الحالة
            self._update_health_stats()
            
            check_duration = (time.time() - check_start) * 1000
            logger.debug(f"✅ اكتملت فحوصات الصحة في {check_duration:.1f}ms")
            
            return self.health_checks.copy()
            
        except Exception as e:
            logger.error(f"❌ خطأ في فحوصات الصحة: {e}")
            return {}
    
    async def _check_integrated_system(self) -> None:
        """فحص النظام المتكامل"""
        try:
            start_time = time.time()
            
            if not self.integrated_system.is_initialized:
                self.health_checks['integrated_system'] = HealthCheck(
                    component='integrated_system',
                    status=HealthStatus.CRITICAL,
                    message='النظام المتكامل غير مهيأ',
                    last_check=datetime.now(CAIRO_TZ),
                    response_time_ms=0
                )
                return
            
            # الحصول على حالة صحة النظام
            system_health = self.integrated_system.get_system_health()
            response_time = (time.time() - start_time) * 1000
            
            # تحديد الحالة العامة
            overall_status = system_health.get('overall_status', 'unknown')
            status_map = {
                'healthy': HealthStatus.HEALTHY,
                'warning': HealthStatus.WARNING,
                'critical': HealthStatus.CRITICAL
            }
            
            self.health_checks['integrated_system'] = HealthCheck(
                component='integrated_system',
                status=status_map.get(overall_status, HealthStatus.UNKNOWN),
                message=system_health.get('overall_message', 'حالة غير معروفة'),
                details=system_health,
                last_check=datetime.now(CAIRO_TZ),
                response_time_ms=response_time
            )
            
            # فحص المكونات الفردية
            components_health = system_health.get('components_health', {})
            for component_name, component_health in components_health.items():
                component_status = component_health.get('status', 'unknown')
                
                self.health_checks[component_name] = HealthCheck(
                    component=component_name,
                    status=status_map.get(component_status, HealthStatus.UNKNOWN),
                    message=component_health.get('message', 'لا توجد رسالة'),
                    details=component_health,
                    last_check=datetime.now(CAIRO_TZ),
                    response_time_ms=response_time
                )
            
        except Exception as e:
            logger.error(f"❌ خطأ في فحص النظام المتكامل: {e}")
            self.health_checks['integrated_system'] = HealthCheck(
                component='integrated_system',
                status=HealthStatus.CRITICAL,
                message=f'خطأ في الفحص: {str(e)}',
                last_check=datetime.now(CAIRO_TZ),
                response_time_ms=0
            )
    
    async def _check_system_resources(self) -> None:
        """فحص موارد النظام"""
        try:
            start_time = time.time()
            
            # فحص الذاكرة
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            memory_status = HealthStatus.HEALTHY
            memory_message = f"استخدام الذاكرة: {memory_percent:.1f}%"
            
            if memory_percent > 90:
                memory_status = HealthStatus.CRITICAL
                memory_message += " - استخدام عالي جداً"
            elif memory_percent > 80:
                memory_status = HealthStatus.WARNING
                memory_message += " - استخدام عالي"
            
            # فحص المعالج
            cpu_percent = psutil.cpu_percent(interval=1)
            
            cpu_status = HealthStatus.HEALTHY
            cpu_message = f"استخدام المعالج: {cpu_percent:.1f}%"
            
            if cpu_percent > 90:
                cpu_status = HealthStatus.CRITICAL
                cpu_message += " - استخدام عالي جداً"
            elif cpu_percent > 80:
                cpu_status = HealthStatus.WARNING
                cpu_message += " - استخدام عالي"
            
            # فحص مساحة القرص
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            disk_status = HealthStatus.HEALTHY
            disk_message = f"استخدام القرص: {disk_percent:.1f}%"
            
            if disk_percent > 95:
                disk_status = HealthStatus.CRITICAL
                disk_message += " - مساحة قليلة جداً"
            elif disk_percent > 85:
                disk_status = HealthStatus.WARNING
                disk_message += " - مساحة قليلة"
            
            response_time = (time.time() - start_time) * 1000
            
            # حفظ نتائج الفحص
            self.health_checks['system_memory'] = HealthCheck(
                component='system_memory',
                status=memory_status,
                message=memory_message,
                details={
                    'total_gb': round(memory.total / (1024**3), 2),
                    'used_gb': round(memory.used / (1024**3), 2),
                    'available_gb': round(memory.available / (1024**3), 2),
                    'percent': memory_percent
                },
                last_check=datetime.now(CAIRO_TZ),
                response_time_ms=response_time
            )
            
            self.health_checks['system_cpu'] = HealthCheck(
                component='system_cpu',
                status=cpu_status,
                message=cpu_message,
                details={
                    'percent': cpu_percent,
                    'count': psutil.cpu_count(),
                    'count_logical': psutil.cpu_count(logical=True)
                },
                last_check=datetime.now(CAIRO_TZ),
                response_time_ms=response_time
            )
            
            self.health_checks['system_disk'] = HealthCheck(
                component='system_disk',
                status=disk_status,
                message=disk_message,
                details={
                    'total_gb': round(disk.total / (1024**3), 2),
                    'used_gb': round(disk.used / (1024**3), 2),
                    'free_gb': round(disk.free / (1024**3), 2),
                    'percent': disk_percent
                },
                last_check=datetime.now(CAIRO_TZ),
                response_time_ms=response_time
            )
            
        except Exception as e:
            logger.error(f"❌ خطأ في فحص موارد النظام: {e}")
            self.health_checks['system_resources'] = HealthCheck(
                component='system_resources',
                status=HealthStatus.CRITICAL,
                message=f'خطأ في فحص الموارد: {str(e)}',
                last_check=datetime.now(CAIRO_TZ),
                response_time_ms=0
            )
    
    async def collect_metrics(self) -> List[Metric]:
        """جمع مقاييس الأداء"""
        try:
            current_time = datetime.now(CAIRO_TZ)
            new_metrics = []
            
            # مقاييس النظام المتكامل
            if self.integrated_system and self.integrated_system.is_initialized:
                stats = self.integrated_system.get_comprehensive_statistics()
                
                # مقاييس مدير مواقيت الصلاة
                if 'prayer_manager' in stats:
                    prayer_stats = stats['prayer_manager']['manager_stats']
                    
                    new_metrics.extend([
                        Metric('prayer_total_requests', MetricType.COUNTER, 
                              prayer_stats.get('total_requests', 0), current_time),
                        Metric('prayer_cache_hits', MetricType.COUNTER, 
                              prayer_stats.get('cache_hits', 0), current_time),
                        Metric('prayer_api_calls', MetricType.COUNTER, 
                              prayer_stats.get('api_calls', 0), current_time),
                        Metric('prayer_failed_fetches', MetricType.COUNTER, 
                              prayer_stats.get('failed_fetches', 0), current_time),
                        Metric('prayer_average_response_time', MetricType.GAUGE, 
                              prayer_stats.get('average_response_time', 0), current_time)
                    ])
                
                # مقاييس التخزين المؤقت
                if 'cache_manager' in stats:
                    cache_stats = stats['cache_manager']['cache_stats']
                    
                    total_requests = cache_stats.get('total_requests', 1)
                    cache_hits = cache_stats.get('cache_hits', 0)
                    hit_rate = (cache_hits / total_requests) * 100 if total_requests > 0 else 0
                    
                    new_metrics.extend([
                        Metric('cache_hit_rate_percent', MetricType.GAUGE, hit_rate, current_time),
                        Metric('cache_memory_entries', MetricType.GAUGE, 
                              cache_stats.get('memory_entries', 0), current_time)
                    ])
                
                # مقاييس مجدول الورد القرآني
                if 'quran_scheduler' in stats:
                    quran_stats = stats['quran_scheduler']['scheduler_stats']
                    
                    new_metrics.extend([
                        Metric('quran_total_sent', MetricType.COUNTER, 
                              quran_stats.get('total_quran_sent', 0), current_time),
                        Metric('quran_successful_sends', MetricType.COUNTER, 
                              quran_stats.get('successful_sends', 0), current_time),
                        Metric('quran_failed_sends', MetricType.COUNTER, 
                              quran_stats.get('failed_sends', 0), current_time),
                        Metric('quran_active_groups', MetricType.GAUGE, 
                              quran_stats.get('active_groups_count', 0), current_time)
                    ])
                
                # مقاييس نظام التذكيرات
                if 'reminders_system' in stats:
                    reminder_stats = stats['reminders_system']['reminder_stats']
                    
                    new_metrics.extend([
                        Metric('reminders_total_sent', MetricType.COUNTER, 
                              reminder_stats.get('total_alerts_sent', 0) + 
                              reminder_stats.get('total_reminders_sent', 0), current_time),
                        Metric('reminders_successful_sends', MetricType.COUNTER, 
                              reminder_stats.get('successful_sends', 0), current_time),
                        Metric('reminders_groups_reached', MetricType.GAUGE, 
                              reminder_stats.get('groups_reached', 0), current_time)
                    ])
            
            # مقاييس موارد النظام
            if 'system_memory' in self.health_checks:
                memory_details = self.health_checks['system_memory'].details or {}
                new_metrics.append(
                    Metric('system_memory_percent', MetricType.GAUGE, 
                          memory_details.get('percent', 0), current_time)
                )
            
            if 'system_cpu' in self.health_checks:
                cpu_details = self.health_checks['system_cpu'].details or {}
                new_metrics.append(
                    Metric('system_cpu_percent', MetricType.GAUGE, 
                          cpu_details.get('percent', 0), current_time)
                )
            
            # إضافة المقاييس الجديدة
            self.metrics.extend(new_metrics)
            
            # الاحتفاظ بآخر 1000 مقياس فقط
            if len(self.metrics) > 1000:
                self.metrics = self.metrics[-1000:]
            
            return new_metrics
            
        except Exception as e:
            logger.error(f"❌ خطأ في جمع المقاييس: {e}")
            return []
    
    async def check_alerts(self) -> List[Alert]:
        """فحص التنبيهات"""
        try:
            new_alerts = []
            current_time = datetime.now(CAIRO_TZ)
            
            # فحص تنبيهات الصحة
            for component, health_check in self.health_checks.items():
                alert_id = f"health_{component}"
                
                if health_check.status in [HealthStatus.CRITICAL, HealthStatus.WARNING]:
                    severity = "critical" if health_check.status == HealthStatus.CRITICAL else "warning"
                    
                    if alert_id not in self.alerts or self.alerts[alert_id].resolved:
                        # تنبيه جديد
                        alert = Alert(
                            id=alert_id,
                            severity=severity,
                            message=f"مشكلة في {component}: {health_check.message}",
                            component=component,
                            timestamp=current_time
                        )
                        
                        self.alerts[alert_id] = alert
                        new_alerts.append(alert)
                        await self._trigger_alert(alert)
                
                elif alert_id in self.alerts and not self.alerts[alert_id].resolved:
                    # حل التنبيه
                    self.alerts[alert_id].resolved = True
                    self.alerts[alert_id].resolution_time = current_time
            
            # فحص تنبيهات المقاييس
            await self._check_metric_alerts(new_alerts, current_time)
            
            # تحديث إحصائيات التنبيهات
            self.monitoring_stats['total_alerts'] = len(self.alerts)
            self.monitoring_stats['active_alerts'] = len([a for a in self.alerts.values() if not a.resolved])
            
            return new_alerts
            
        except Exception as e:
            logger.error(f"❌ خطأ في فحص التنبيهات: {e}")
            return []
    
    async def _check_metric_alerts(self, new_alerts: List[Alert], current_time: datetime) -> None:
        """فحص تنبيهات المقاييس"""
        try:
            # الحصول على آخر المقاييس
            recent_metrics = [m for m in self.metrics if (current_time - m.timestamp).total_seconds() < 300]
            
            for metric in recent_metrics:
                alert_id = f"metric_{metric.name}"
                threshold_key = metric.name
                
                if threshold_key in self.alert_thresholds:
                    threshold = self.alert_thresholds[threshold_key]
                    
                    # تحديد نوع التحقق
                    should_alert = False
                    if 'percent' in metric.name and metric.value > threshold:
                        should_alert = True
                    elif 'response_time' in metric.name and metric.value > threshold:
                        should_alert = True
                    elif 'failed' in metric.name and metric.value > threshold:
                        should_alert = True
                    
                    if should_alert:
                        if alert_id not in self.alerts or self.alerts[alert_id].resolved:
                            severity = "critical" if metric.value > threshold * 1.2 else "warning"
                            
                            alert = Alert(
                                id=alert_id,
                                severity=severity,
                                message=f"مقياس {metric.name} تجاوز الحد المسموح: {metric.value:.1f} > {threshold}",
                                component=metric.name,
                                timestamp=current_time
                            )
                            
                            self.alerts[alert_id] = alert
                            new_alerts.append(alert)
                            await self._trigger_alert(alert)
                    
                    elif alert_id in self.alerts and not self.alerts[alert_id].resolved:
                        # حل التنبيه
                        self.alerts[alert_id].resolved = True
                        self.alerts[alert_id].resolution_time = current_time
            
        except Exception as e:
            logger.error(f"❌ خطأ في فحص تنبيهات المقاييس: {e}")
    
    async def _trigger_alert(self, alert: Alert) -> None:
        """تفعيل تنبيه"""
        try:
            logger.warning(f"🚨 تنبيه {alert.severity}: {alert.message}")
            
            # إشعار callbacks
            for callback in self.alert_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(alert)
                    else:
                        callback(alert)
                except Exception as e:
                    logger.error(f"❌ خطأ في callback التنبيه: {e}")
            
        except Exception as e:
            logger.error(f"❌ خطأ في تفعيل التنبيه: {e}")
    
    def _update_health_stats(self) -> None:
        """تحديث إحصائيات الصحة"""
        try:
            healthy_count = 0
            warning_count = 0
            critical_count = 0
            
            for health_check in self.health_checks.values():
                if health_check.status == HealthStatus.HEALTHY:
                    healthy_count += 1
                elif health_check.status == HealthStatus.WARNING:
                    warning_count += 1
                elif health_check.status == HealthStatus.CRITICAL:
                    critical_count += 1
            
            self.monitoring_stats['healthy_checks'] = healthy_count
            self.monitoring_stats['warning_checks'] = warning_count
            self.monitoring_stats['critical_checks'] = critical_count
            
        except Exception as e:
            logger.error(f"❌ خطأ في تحديث إحصائيات الصحة: {e}")
    
    async def _cleanup_old_data(self) -> None:
        """تنظيف البيانات القديمة"""
        try:
            current_time = datetime.now(CAIRO_TZ)
            
            # تنظيف المقاييس القديمة (أكثر من 24 ساعة)
            cutoff_time = current_time - timedelta(hours=24)
            self.metrics = [m for m in self.metrics if m.timestamp > cutoff_time]
            
            # تنظيف التنبيهات المحلولة القديمة (أكثر من 7 أيام)
            old_alert_cutoff = current_time - timedelta(days=7)
            old_alerts = [
                alert_id for alert_id, alert in self.alerts.items()
                if alert.resolved and alert.resolution_time and alert.resolution_time < old_alert_cutoff
            ]
            
            for alert_id in old_alerts:
                del self.alerts[alert_id]
            
            if old_alerts:
                logger.debug(f"🗑️ تم تنظيف {len(old_alerts)} تنبيه قديم")
            
        except Exception as e:
            logger.error(f"❌ خطأ في تنظيف البيانات القديمة: {e}")
    
    def add_alert_callback(self, callback: Callable[[Alert], None]) -> None:
        """إضافة callback للتنبيهات"""
        self.alert_callbacks.append(callback)
    
    def get_monitoring_dashboard(self) -> Dict[str, Any]:
        """الحصول على لوحة معلومات المراقبة"""
        try:
            current_time = datetime.now(CAIRO_TZ)
            
            # إحصائيات عامة
            uptime_hours = 0
            if self.monitoring_stats['monitoring_start_time']:
                start_time = datetime.fromisoformat(self.monitoring_stats['monitoring_start_time'])
                uptime_hours = (current_time - start_time).total_seconds() / 3600
            
            # أحدث المقاييس
            recent_metrics = {}
            for metric in reversed(self.metrics[-20:]):  # آخر 20 مقياس
                if metric.name not in recent_metrics:
                    recent_metrics[metric.name] = metric.to_dict()
            
            # التنبيهات النشطة
            active_alerts = [alert.to_dict() for alert in self.alerts.values() if not alert.resolved]
            
            # فحوصات الصحة
            health_summary = {}
            for component, health_check in self.health_checks.items():
                health_summary[component] = health_check.to_dict()
            
            return {
                'monitoring_info': {
                    'is_monitoring': self.is_monitoring,
                    'uptime_hours': round(uptime_hours, 2),
                    'check_interval_minutes': self.check_interval_minutes,
                    'last_check': self.monitoring_stats['last_check_time']
                },
                'statistics': self.monitoring_stats.copy(),
                'health_checks': health_summary,
                'recent_metrics': recent_metrics,
                'active_alerts': active_alerts,
                'system_info': {
                    'platform': platform.system(),
                    'python_version': platform.python_version(),
                    'hostname': platform.node()
                }
            }
            
        except Exception as e:
            logger.error(f"❌ خطأ في إنشاء لوحة المعلومات: {e}")
            return {'error': str(e)}
    
    def export_monitoring_data(self, file_path: str) -> bool:
        """تصدير بيانات المراقبة"""
        try:
            dashboard_data = self.get_monitoring_dashboard()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(dashboard_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ تم تصدير بيانات المراقبة إلى {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في تصدير بيانات المراقبة: {e}")
            return False
    
    async def cleanup(self) -> None:
        """تنظيف موارد المراقبة"""
        try:
            await self.stop_monitoring()
            logger.info("✅ تم تنظيف نظام المراقبة")
            
        except Exception as e:
            logger.error(f"❌ خطأ في تنظيف نظام المراقبة: {e}")
    
    def __str__(self) -> str:
        status = "running" if self.is_monitoring else "stopped"
        return f"PrayerTimesMonitor({status}, {len(self.health_checks)} checks, {len(self.alerts)} alerts)"
    
    def __repr__(self) -> str:
        return f"PrayerTimesMonitor(monitoring={self.is_monitoring}, interval={self.check_interval_minutes}min)"


# Export للاستخدام في الملفات الأخرى
__all__ = [
    'PrayerTimesMonitor',
    'HealthCheck',
    'Metric',
    'Alert',
    'HealthStatus',
    'MetricType'
]