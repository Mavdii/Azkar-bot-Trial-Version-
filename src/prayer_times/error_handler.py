#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🕌 Error Handler & Logging System - نظام معالجة الأخطاء والتسجيل
====================================================================
نظام شامل لمعالجة الأخطاء والتسجيل المفصل لمواقيت الصلاة

Features:
- 🛡️ معالجة شاملة للأخطاء مع آليات fallback
- 📝 تسجيل مفصل لجميع العمليات
- 🚨 إشعارات إدارية للأخطاء الحرجة
- 📊 إحصائيات الأخطاء والأداء
- 🔄 آليات إعادة المحاولة الذكية

Author: Islamic Bot Developer Team
Version: 1.0.0
License: MIT
"""

import asyncio
import logging
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
import pytz
from dataclasses import dataclass, field
from enum import Enum
import json
import functools
import sys
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

# Cairo timezone
CAIRO_TZ = pytz.timezone('Africa/Cairo')

class ErrorSeverity(Enum):
    """مستويات خطورة الأخطاء"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """فئات الأخطاء"""
    API_ERROR = "api_error"
    DATABASE_ERROR = "database_error"
    CACHE_ERROR = "cache_error"
    SCHEDULING_ERROR = "scheduling_error"
    NETWORK_ERROR = "network_error"
    VALIDATION_ERROR = "validation_error"
    SYSTEM_ERROR = "system_error"

@dataclass
class ErrorRecord:
    """سجل خطأ"""
    timestamp: datetime
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    details: Optional[str] = None
    traceback_info: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    resolved: bool = False
    resolution_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'category': self.category.value,
            'severity': self.severity.value,
            'message': self.message,
            'details': self.details,
            'traceback_info': self.traceback_info,
            'context': self.context,
            'resolved': self.resolved,
            'resolution_time': self.resolution_time.isoformat() if self.resolution_time else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ErrorRecord':
        """إنشاء من قاموس"""
        return cls(
            timestamp=datetime.fromisoformat(data['timestamp']),
            category=ErrorCategory(data['category']),
            severity=ErrorSeverity(data['severity']),
            message=data['message'],
            details=data.get('details'),
            traceback_info=data.get('traceback_info'),
            context=data.get('context'),
            resolved=data.get('resolved', False),
            resolution_time=datetime.fromisoformat(data['resolution_time']) if data.get('resolution_time') else None
        )

class PrayerTimesErrorHandler:
    """معالج أخطاء مواقيت الصلاة"""
    
    def __init__(
        self,
        log_file: str = "prayer_times_errors.log",
        max_error_records: int = 1000,
        admin_notification_callback: Optional[Callable] = None
    ):
        self.log_file = Path(log_file)
        self.max_error_records = max_error_records
        self.admin_notification_callback = admin_notification_callback
        
        # سجلات الأخطاء
        self.error_records: List[ErrorRecord] = []
        
        # إحصائيات الأخطاء
        self.stats = {
            'total_errors': 0,
            'errors_by_category': {category.value: 0 for category in ErrorCategory},
            'errors_by_severity': {severity.value: 0 for severity in ErrorSeverity},
            'resolved_errors': 0,
            'unresolved_errors': 0,
            'last_error_time': None,
            'last_critical_error_time': None,
            'average_resolution_time': 0.0
        }
        
        # إعداد نظام التسجيل المخصص
        self._setup_custom_logger()
    
    def _setup_custom_logger(self) -> None:
        """إعداد نظام التسجيل المخصص"""
        try:
            # إنشاء مجلد السجلات
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            
            # إعداد formatter مخصص
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            # إعداد file handler
            file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            file_handler.setLevel(logging.DEBUG)
            
            # إضافة handler للـ logger الرئيسي
            prayer_logger = logging.getLogger('prayer_times')
            prayer_logger.addHandler(file_handler)
            prayer_logger.setLevel(logging.DEBUG)
            
            logger.info("✅ تم إعداد نظام التسجيل المخصص")
            
        except Exception as e:
            logger.error(f"❌ فشل في إعداد نظام التسجيل: {e}")
    
    async def handle_error(
        self,
        error: Exception,
        category: ErrorCategory,
        severity: ErrorSeverity,
        context: Optional[Dict[str, Any]] = None,
        custom_message: Optional[str] = None
    ) -> ErrorRecord:
        """معالجة خطأ وتسجيله"""
        try:
            # إنشاء سجل الخطأ
            error_record = ErrorRecord(
                timestamp=datetime.now(CAIRO_TZ),
                category=category,
                severity=severity,
                message=custom_message or str(error),
                details=f"{type(error).__name__}: {str(error)}",
                traceback_info=traceback.format_exc(),
                context=context or {}
            )
            
            # إضافة إلى السجلات
            self.error_records.append(error_record)
            
            # تحديث الإحصائيات
            self._update_error_stats(error_record)
            
            # تسجيل الخطأ
            await self._log_error(error_record)
            
            # إشعار الإدارة للأخطاء الحرجة
            if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
                await self._notify_admin(error_record)
            
            # تنظيف السجلات القديمة
            await self._cleanup_old_records()
            
            return error_record
            
        except Exception as e:
            # خطأ في معالج الأخطاء نفسه!
            logger.critical(f"❌ خطأ حرج في معالج الأخطاء: {e}")
            return ErrorRecord(
                timestamp=datetime.now(CAIRO_TZ),
                category=ErrorCategory.SYSTEM_ERROR,
                severity=ErrorSeverity.CRITICAL,
                message="خطأ في معالج الأخطاء",
                details=str(e)
            )
    
    async def _log_error(self, error_record: ErrorRecord) -> None:
        """تسجيل الخطأ في السجلات"""
        try:
            # تحديد مستوى التسجيل
            log_level_map = {
                ErrorSeverity.LOW: logging.INFO,
                ErrorSeverity.MEDIUM: logging.WARNING,
                ErrorSeverity.HIGH: logging.ERROR,
                ErrorSeverity.CRITICAL: logging.CRITICAL
            }
            
            log_level = log_level_map.get(error_record.severity, logging.ERROR)
            
            # تنسيق الرسالة
            log_message = f"[{error_record.category.value.upper()}] {error_record.message}"
            if error_record.details:
                log_message += f" | Details: {error_record.details}"
            if error_record.context:
                log_message += f" | Context: {json.dumps(error_record.context, ensure_ascii=False)}"
            
            # تسجيل الخطأ
            prayer_logger = logging.getLogger('prayer_times')
            prayer_logger.log(log_level, log_message)
            
            # تسجيل traceback للأخطاء الحرجة
            if error_record.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL] and error_record.traceback_info:
                prayer_logger.log(log_level, f"Traceback:\n{error_record.traceback_info}")
            
        except Exception as e:
            logger.error(f"❌ خطأ في تسجيل الخطأ: {e}")
    
    async def _notify_admin(self, error_record: ErrorRecord) -> None:
        """إشعار الإدارة بالأخطاء الحرجة"""
        try:
            if self.admin_notification_callback:
                notification_message = self._format_admin_notification(error_record)
                await self.admin_notification_callback(notification_message, error_record)
            
        except Exception as e:
            logger.error(f"❌ خطأ في إشعار الإدارة: {e}")
    
    def _format_admin_notification(self, error_record: ErrorRecord) -> str:
        """تنسيق رسالة إشعار الإدارة"""
        severity_emoji = {
            ErrorSeverity.LOW: "ℹ️",
            ErrorSeverity.MEDIUM: "⚠️",
            ErrorSeverity.HIGH: "❌",
            ErrorSeverity.CRITICAL: "🚨"
        }
        
        emoji = severity_emoji.get(error_record.severity, "❌")
        
        message = f"""{emoji} **خطأ في نظام مواقيت الصلاة**

**الفئة:** {error_record.category.value}
**الخطورة:** {error_record.severity.value}
**الوقت:** {error_record.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

**الرسالة:** {error_record.message}"""

        if error_record.details:
            message += f"\n**التفاصيل:** {error_record.details}"
        
        if error_record.context:
            message += f"\n**السياق:** {json.dumps(error_record.context, ensure_ascii=False, indent=2)}"
        
        return message
    
    def _update_error_stats(self, error_record: ErrorRecord) -> None:
        """تحديث إحصائيات الأخطاء"""
        try:
            self.stats['total_errors'] += 1
            self.stats['errors_by_category'][error_record.category.value] += 1
            self.stats['errors_by_severity'][error_record.severity.value] += 1
            self.stats['last_error_time'] = error_record.timestamp.isoformat()
            
            if error_record.severity == ErrorSeverity.CRITICAL:
                self.stats['last_critical_error_time'] = error_record.timestamp.isoformat()
            
            # حساب الأخطاء المحلولة وغير المحلولة
            resolved_count = len([r for r in self.error_records if r.resolved])
            self.stats['resolved_errors'] = resolved_count
            self.stats['unresolved_errors'] = len(self.error_records) - resolved_count
            
            # حساب متوسط وقت الحل
            resolved_records = [r for r in self.error_records if r.resolved and r.resolution_time]
            if resolved_records:
                total_resolution_time = sum(
                    (r.resolution_time - r.timestamp).total_seconds()
                    for r in resolved_records
                )
                self.stats['average_resolution_time'] = total_resolution_time / len(resolved_records)
            
        except Exception as e:
            logger.error(f"❌ خطأ في تحديث إحصائيات الأخطاء: {e}")
    
    async def _cleanup_old_records(self) -> None:
        """تنظيف السجلات القديمة"""
        try:
            if len(self.error_records) > self.max_error_records:
                # الاحتفاظ بالأحدث فقط
                self.error_records = self.error_records[-self.max_error_records:]
                logger.debug(f"🗑️ تم تنظيف السجلات القديمة، المتبقي: {len(self.error_records)}")
            
        except Exception as e:
            logger.error(f"❌ خطأ في تنظيف السجلات: {e}")
    
    async def resolve_error(self, error_index: int, resolution_note: Optional[str] = None) -> bool:
        """وضع علامة حل على خطأ"""
        try:
            if 0 <= error_index < len(self.error_records):
                error_record = self.error_records[error_index]
                error_record.resolved = True
                error_record.resolution_time = datetime.now(CAIRO_TZ)
                
                if resolution_note:
                    if not error_record.context:
                        error_record.context = {}
                    error_record.context['resolution_note'] = resolution_note
                
                # تحديث الإحصائيات
                self._update_error_stats(error_record)
                
                logger.info(f"✅ تم وضع علامة حل على الخطأ {error_index}")
                return True
            else:
                logger.error(f"❌ فهرس خطأ غير صحيح: {error_index}")
                return False
                
        except Exception as e:
            logger.error(f"❌ خطأ في وضع علامة الحل: {e}")
            return False
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """الحصول على إحصائيات الأخطاء"""
        return {
            'error_stats': self.stats.copy(),
            'recent_errors': [
                {
                    'timestamp': record.timestamp.isoformat(),
                    'category': record.category.value,
                    'severity': record.severity.value,
                    'message': record.message,
                    'resolved': record.resolved
                }
                for record in self.error_records[-10:]  # آخر 10 أخطاء
            ]
        }
    
    def get_unresolved_errors(self) -> List[ErrorRecord]:
        """الحصول على الأخطاء غير المحلولة"""
        return [record for record in self.error_records if not record.resolved]
    
    def get_critical_errors(self, hours_back: int = 24) -> List[ErrorRecord]:
        """الحصول على الأخطاء الحرجة في فترة زمنية"""
        try:
            cutoff_time = datetime.now(CAIRO_TZ) - timedelta(hours=hours_back)
            return [
                record for record in self.error_records
                if record.severity == ErrorSeverity.CRITICAL and record.timestamp > cutoff_time
            ]
        except Exception as e:
            logger.error(f"❌ خطأ في جلب الأخطاء الحرجة: {e}")
            return []
    
    def export_error_log(self, file_path: str) -> bool:
        """تصدير سجل الأخطاء"""
        try:
            export_data = {
                'export_timestamp': datetime.now(CAIRO_TZ).isoformat(),
                'statistics': self.stats,
                'error_records': [record.to_dict() for record in self.error_records]
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ تم تصدير سجل الأخطاء إلى {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في تصدير سجل الأخطاء: {e}")
            return False


def error_handler_decorator(
    category: ErrorCategory,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    fallback_return=None,
    retry_count: int = 0,
    retry_delay: float = 1.0
):
    """ديكوريتر لمعالجة الأخطاء تلقائياً"""
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            error_handler = getattr(args[0], 'error_handler', None) if args else None
            
            for attempt in range(retry_count + 1):
                try:
                    if asyncio.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    else:
                        return func(*args, **kwargs)
                        
                except Exception as e:
                    if error_handler:
                        context = {
                            'function': func.__name__,
                            'attempt': attempt + 1,
                            'max_attempts': retry_count + 1,
                            'args_count': len(args),
                            'kwargs_keys': list(kwargs.keys())
                        }
                        await error_handler.handle_error(e, category, severity, context)
                    
                    # إعادة المحاولة أو إرجاع fallback
                    if attempt < retry_count:
                        await asyncio.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                        continue
                    else:
                        if fallback_return is not None:
                            return fallback_return
                        raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            error_handler = getattr(args[0], 'error_handler', None) if args else None
            
            for attempt in range(retry_count + 1):
                try:
                    return func(*args, **kwargs)
                        
                except Exception as e:
                    if error_handler:
                        context = {
                            'function': func.__name__,
                            'attempt': attempt + 1,
                            'max_attempts': retry_count + 1,
                            'args_count': len(args),
                            'kwargs_keys': list(kwargs.keys())
                        }
                        # للدوال المتزامنة، نحتاج لتشغيل معالج الأخطاء في loop
                        try:
                            loop = asyncio.get_event_loop()
                            loop.create_task(error_handler.handle_error(e, category, severity, context))
                        except RuntimeError:
                            # إذا لم يكن هناك loop، نسجل الخطأ فقط
                            logger.error(f"Error in {func.__name__}: {e}")
                    
                    # إعادة المحاولة أو إرجاع fallback
                    if attempt < retry_count:
                        import time
                        time.sleep(retry_delay * (2 ** attempt))
                        continue
                    else:
                        if fallback_return is not None:
                            return fallback_return
                        raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


# Export للاستخدام في الملفات الأخرى
__all__ = [
    'PrayerTimesErrorHandler',
    'ErrorRecord',
    'ErrorSeverity',
    'ErrorCategory',
    'error_handler_decorator'
]