#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🕌 Data Validator - نظام التحقق من البيانات
==============================================
نظام شامل للتحقق من صحة بيانات مواقيت الصلاة والإعدادات

Features:
- ✅ التحقق من صحة مواقيت الصلاة للقاهرة
- 🔍 فحص ترتيب الصلوات وصيغة الأوقات
- ⚙️ التحقق من صحة الإعدادات
- 📊 تقارير مفصلة للأخطاء
- 🛡️ آليات الحماية من البيانات الخاطئة

Author: Islamic Bot Developer Team
Version: 1.0.0
License: MIT
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import pytz
from dataclasses import dataclass
from enum import Enum
import re

# Configure logging
logger = logging.getLogger(__name__)

# Cairo timezone
CAIRO_TZ = pytz.timezone('Africa/Cairo')

class ValidationSeverity(Enum):
    """مستويات خطورة أخطاء التحقق"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class ValidationIssue:
    """مشكلة في التحقق"""
    severity: ValidationSeverity
    message: str
    field: Optional[str] = None
    expected: Optional[Any] = None
    actual: Optional[Any] = None
    suggestion: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'severity': self.severity.value,
            'message': self.message,
            'field': self.field,
            'expected': self.expected,
            'actual': self.actual,
            'suggestion': self.suggestion
        }

@dataclass
class ValidationReport:
    """تقرير التحقق"""
    is_valid: bool
    score: float  # من 0 إلى 100
    issues: List[ValidationIssue]
    validation_time: datetime
    
    def get_issues_by_severity(self, severity: ValidationSeverity) -> List[ValidationIssue]:
        """الحصول على المشاكل حسب الخطورة"""
        return [issue for issue in self.issues if issue.severity == severity]
    
    def has_critical_issues(self) -> bool:
        """التحقق من وجود مشاكل حرجة"""
        return any(issue.severity == ValidationSeverity.CRITICAL for issue in self.issues)
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'is_valid': self.is_valid,
            'score': self.score,
            'issues': [issue.to_dict() for issue in self.issues],
            'validation_time': self.validation_time.isoformat(),
            'summary': {
                'total_issues': len(self.issues),
                'critical': len(self.get_issues_by_severity(ValidationSeverity.CRITICAL)),
                'errors': len(self.get_issues_by_severity(ValidationSeverity.ERROR)),
                'warnings': len(self.get_issues_by_severity(ValidationSeverity.WARNING)),
                'info': len(self.get_issues_by_severity(ValidationSeverity.INFO))
            }
        }

class PrayerTimesDataValidator:
    """نظام التحقق من بيانات مواقيت الصلاة"""
    
    def __init__(self):
        # نطاقات الأوقات المعقولة للقاهرة (بالساعات)
        self.cairo_time_ranges = {
            'fajr': (3, 6),      # الفجر: 3:00 - 6:00
            'dhuhr': (11, 14),   # الظهر: 11:00 - 14:00
            'asr': (14, 18),     # العصر: 14:00 - 18:00
            'maghrib': (17, 20), # المغرب: 17:00 - 20:00
            'isha': (19, 23)     # العشاء: 19:00 - 23:00
        }
        
        # الحد الأدنى والأقصى للفترات بين الصلوات (بالدقائق)
        self.prayer_intervals = {
            'fajr_to_dhuhr': (360, 600),    # 6-10 ساعات
            'dhuhr_to_asr': (180, 360),     # 3-6 ساعات
            'asr_to_maghrib': (120, 300),   # 2-5 ساعات
            'maghrib_to_isha': (60, 180)    # 1-3 ساعات
        }
        
        # أنماط صيغة الوقت المقبولة
        self.time_patterns = [
            r'^\d{1,2}:\d{2}$',           # HH:MM
            r'^\d{1,2}:\d{2}:\d{2}$',     # HH:MM:SS
            r'^\d{1,2}:\d{2}\s*[AP]M$'    # HH:MM AM/PM
        ]
    
    def validate_prayer_times(self, prayer_times_data: Dict[str, Any]) -> ValidationReport:
        """التحقق من صحة بيانات مواقيت الصلاة"""
        issues = []
        validation_start = datetime.now(CAIRO_TZ)
        
        try:
            # التحقق من البنية الأساسية
            structure_issues = self._validate_structure(prayer_times_data)
            issues.extend(structure_issues)
            
            # إذا كانت هناك مشاكل حرجة في البنية، توقف
            if any(issue.severity == ValidationSeverity.CRITICAL for issue in structure_issues):
                return ValidationReport(
                    is_valid=False,
                    score=0.0,
                    issues=issues,
                    validation_time=validation_start
                )
            
            # التحقق من صيغة الأوقات
            format_issues = self._validate_time_formats(prayer_times_data)
            issues.extend(format_issues)
            
            # التحقق من معقولية الأوقات للقاهرة
            range_issues = self._validate_time_ranges(prayer_times_data)
            issues.extend(range_issues)
            
            # التحقق من ترتيب الصلوات
            order_issues = self._validate_prayer_order(prayer_times_data)
            issues.extend(order_issues)
            
            # التحقق من الفترات بين الصلوات
            interval_issues = self._validate_prayer_intervals(prayer_times_data)
            issues.extend(interval_issues)
            
            # التحقق من البيانات الإضافية
            metadata_issues = self._validate_metadata(prayer_times_data)
            issues.extend(metadata_issues)
            
            # حساب النقاط
            score = self._calculate_validation_score(issues)
            
            # تحديد صحة البيانات
            is_valid = score >= 70 and not any(
                issue.severity == ValidationSeverity.CRITICAL for issue in issues
            )
            
            return ValidationReport(
                is_valid=is_valid,
                score=score,
                issues=issues,
                validation_time=validation_start
            )
            
        except Exception as e:
            logger.error(f"❌ خطأ في التحقق من البيانات: {e}")
            issues.append(ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                message=f"خطأ في عملية التحقق: {str(e)}",
                suggestion="تحقق من صيغة البيانات المدخلة"
            ))
            
            return ValidationReport(
                is_valid=False,
                score=0.0,
                issues=issues,
                validation_time=validation_start
            )
    
    def _validate_structure(self, data: Dict[str, Any]) -> List[ValidationIssue]:
        """التحقق من البنية الأساسية للبيانات"""
        issues = []
        
        # التحقق من وجود البيانات
        if not data:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                message="لا توجد بيانات للتحقق منها",
                suggestion="تأكد من وجود بيانات مواقيت الصلاة"
            ))
            return issues
        
        # التحقق من وجود الصلوات الأساسية
        required_prayers = ['fajr', 'dhuhr', 'asr', 'maghrib', 'isha']
        
        # البحث في مستويات مختلفة من البيانات
        prayer_data = data
        if 'timings' in data:
            prayer_data = data['timings']
        elif 'data' in data and isinstance(data['data'], dict):
            if 'timings' in data['data']:
                prayer_data = data['data']['timings']
            else:
                prayer_data = data['data']
        
        missing_prayers = []
        for prayer in required_prayers:
            if prayer not in prayer_data:
                # محاولة البحث بأسماء مختلفة
                alternative_names = {
                    'fajr': ['Fajr', 'FAJR', 'فجر'],
                    'dhuhr': ['Dhuhr', 'DHUHR', 'ظهر'],
                    'asr': ['Asr', 'ASR', 'عصر'],
                    'maghrib': ['Maghrib', 'MAGHRIB', 'مغرب'],
                    'isha': ['Isha', 'ISHA', 'عشاء']
                }
                
                found = False
                for alt_name in alternative_names.get(prayer, []):
                    if alt_name in prayer_data:
                        found = True
                        break
                
                if not found:
                    missing_prayers.append(prayer)
        
        if missing_prayers:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                message=f"صلوات مفقودة: {', '.join(missing_prayers)}",
                field="prayers",
                expected=required_prayers,
                actual=list(prayer_data.keys()),
                suggestion="تأكد من وجود جميع الصلوات الخمس في البيانات"
            ))
        
        return issues
    
    def _validate_time_formats(self, data: Dict[str, Any]) -> List[ValidationIssue]:
        """التحقق من صيغة الأوقات"""
        issues = []
        
        # الحصول على بيانات الأوقات
        prayer_data = self._extract_prayer_data(data)
        
        for prayer_name, time_value in prayer_data.items():
            if prayer_name.lower() in ['fajr', 'dhuhr', 'asr', 'maghrib', 'isha']:
                if not time_value:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        message=f"وقت صلاة {prayer_name} فارغ",
                        field=prayer_name,
                        suggestion="تأكد من وجود وقت صحيح للصلاة"
                    ))
                    continue
                
                # تنظيف الوقت من الرموز الإضافية
                clean_time = str(time_value).strip().split(' ')[0]
                
                # التحقق من صيغة الوقت
                valid_format = False
                for pattern in self.time_patterns:
                    if re.match(pattern, clean_time):
                        valid_format = True
                        break
                
                if not valid_format:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        message=f"صيغة وقت غير صحيحة لصلاة {prayer_name}",
                        field=prayer_name,
                        expected="HH:MM",
                        actual=clean_time,
                        suggestion="استخدم صيغة HH:MM للأوقات"
                    ))
                    continue
                
                # التحقق من صحة الساعة والدقيقة
                try:
                    time_parts = clean_time.split(':')
                    hour = int(time_parts[0])
                    minute = int(time_parts[1])
                    
                    if not (0 <= hour <= 23):
                        issues.append(ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            message=f"ساعة غير صحيحة لصلاة {prayer_name}: {hour}",
                            field=prayer_name,
                            expected="0-23",
                            actual=hour,
                            suggestion="الساعة يجب أن تكون بين 0 و 23"
                        ))
                    
                    if not (0 <= minute <= 59):
                        issues.append(ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            message=f"دقيقة غير صحيحة لصلاة {prayer_name}: {minute}",
                            field=prayer_name,
                            expected="0-59",
                            actual=minute,
                            suggestion="الدقيقة يجب أن تكون بين 0 و 59"
                        ))
                        
                except (ValueError, IndexError) as e:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        message=f"خطأ في تحليل وقت صلاة {prayer_name}: {clean_time}",
                        field=prayer_name,
                        actual=clean_time,
                        suggestion="تأكد من صيغة الوقت HH:MM"
                    ))
        
        return issues
    
    def _validate_time_ranges(self, data: Dict[str, Any]) -> List[ValidationIssue]:
        """التحقق من معقولية الأوقات للقاهرة"""
        issues = []
        
        prayer_data = self._extract_prayer_data(data)
        
        for prayer_name, time_value in prayer_data.items():
            prayer_key = prayer_name.lower()
            if prayer_key in self.cairo_time_ranges:
                try:
                    # تحويل الوقت إلى ساعة
                    clean_time = str(time_value).strip().split(' ')[0]
                    hour = int(clean_time.split(':')[0])
                    
                    # الحصول على النطاق المتوقع
                    min_hour, max_hour = self.cairo_time_ranges[prayer_key]
                    
                    if not (min_hour <= hour <= max_hour):
                        issues.append(ValidationIssue(
                            severity=ValidationSeverity.WARNING,
                            message=f"وقت صلاة {prayer_name} غير معتاد للقاهرة: {clean_time}",
                            field=prayer_name,
                            expected=f"{min_hour:02d}:00 - {max_hour:02d}:59",
                            actual=clean_time,
                            suggestion=f"وقت صلاة {prayer_name} عادة يكون بين {min_hour}:00 و {max_hour}:59 في القاهرة"
                        ))
                        
                except (ValueError, IndexError):
                    # تم التعامل مع هذا في _validate_time_formats
                    pass
        
        return issues
    
    def _validate_prayer_order(self, data: Dict[str, Any]) -> List[ValidationIssue]:
        """التحقق من ترتيب الصلوات"""
        issues = []
        
        prayer_data = self._extract_prayer_data(data)
        prayer_order = ['fajr', 'dhuhr', 'asr', 'maghrib', 'isha']
        
        # تحويل الأوقات إلى دقائق من بداية اليوم
        prayer_minutes = {}
        
        for prayer in prayer_order:
            if prayer in prayer_data:
                try:
                    clean_time = str(prayer_data[prayer]).strip().split(' ')[0]
                    hour, minute = map(int, clean_time.split(':'))
                    total_minutes = hour * 60 + minute
                    prayer_minutes[prayer] = total_minutes
                except (ValueError, IndexError):
                    # تم التعامل مع هذا في _validate_time_formats
                    continue
        
        # التحقق من الترتيب
        for i in range(len(prayer_order) - 1):
            current_prayer = prayer_order[i]
            next_prayer = prayer_order[i + 1]
            
            if current_prayer in prayer_minutes and next_prayer in prayer_minutes:
                current_time = prayer_minutes[current_prayer]
                next_time = prayer_minutes[next_prayer]
                
                if current_time >= next_time:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        message=f"ترتيب خاطئ: صلاة {current_prayer} ({self._minutes_to_time(current_time)}) يجب أن تكون قبل صلاة {next_prayer} ({self._minutes_to_time(next_time)})",
                        field=f"{current_prayer}_to_{next_prayer}",
                        suggestion="تأكد من ترتيب الصلوات: فجر، ظهر، عصر، مغرب، عشاء"
                    ))
        
        return issues
    
    def _validate_prayer_intervals(self, data: Dict[str, Any]) -> List[ValidationIssue]:
        """التحقق من الفترات بين الصلوات"""
        issues = []
        
        prayer_data = self._extract_prayer_data(data)
        prayer_order = ['fajr', 'dhuhr', 'asr', 'maghrib', 'isha']
        
        # تحويل الأوقات إلى دقائق
        prayer_minutes = {}
        for prayer in prayer_order:
            if prayer in prayer_data:
                try:
                    clean_time = str(prayer_data[prayer]).strip().split(' ')[0]
                    hour, minute = map(int, clean_time.split(':'))
                    total_minutes = hour * 60 + minute
                    prayer_minutes[prayer] = total_minutes
                except (ValueError, IndexError):
                    continue
        
        # التحقق من الفترات
        interval_checks = [
            ('fajr', 'dhuhr', 'fajr_to_dhuhr'),
            ('dhuhr', 'asr', 'dhuhr_to_asr'),
            ('asr', 'maghrib', 'asr_to_maghrib'),
            ('maghrib', 'isha', 'maghrib_to_isha')
        ]
        
        for first_prayer, second_prayer, interval_key in interval_checks:
            if first_prayer in prayer_minutes and second_prayer in prayer_minutes:
                interval = prayer_minutes[second_prayer] - prayer_minutes[first_prayer]
                
                if interval_key in self.prayer_intervals:
                    min_interval, max_interval = self.prayer_intervals[interval_key]
                    
                    if interval < min_interval:
                        issues.append(ValidationIssue(
                            severity=ValidationSeverity.WARNING,
                            message=f"الفترة بين صلاة {first_prayer} و {second_prayer} قصيرة جداً: {interval} دقيقة",
                            field=interval_key,
                            expected=f"{min_interval}-{max_interval} دقيقة",
                            actual=f"{interval} دقيقة",
                            suggestion=f"الفترة المعتادة بين {first_prayer} و {second_prayer} هي {min_interval}-{max_interval} دقيقة"
                        ))
                    elif interval > max_interval:
                        issues.append(ValidationIssue(
                            severity=ValidationSeverity.WARNING,
                            message=f"الفترة بين صلاة {first_prayer} و {second_prayer} طويلة جداً: {interval} دقيقة",
                            field=interval_key,
                            expected=f"{min_interval}-{max_interval} دقيقة",
                            actual=f"{interval} دقيقة",
                            suggestion=f"الفترة المعتادة بين {first_prayer} و {second_prayer} هي {min_interval}-{max_interval} دقيقة"
                        ))
        
        return issues
    
    def _validate_metadata(self, data: Dict[str, Any]) -> List[ValidationIssue]:
        """التحقق من البيانات الإضافية"""
        issues = []
        
        # التحقق من وجود معلومات المصدر
        if 'source' not in data:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                message="لا توجد معلومات عن مصدر البيانات",
                field="source",
                suggestion="إضافة معلومات المصدر يساعد في التتبع والتشخيص"
            ))
        
        # التحقق من معلومات التاريخ
        if 'date' in data:
            try:
                # محاولة التحقق من صيغة التاريخ
                date_info = data['date']
                if isinstance(date_info, dict):
                    if 'readable' not in date_info and 'gregorian' not in date_info:
                        issues.append(ValidationIssue(
                            severity=ValidationSeverity.INFO,
                            message="معلومات التاريخ غير مكتملة",
                            field="date",
                            suggestion="إضافة معلومات التاريخ الميلادي والهجري"
                        ))
            except Exception:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message="خطأ في معلومات التاريخ",
                    field="date",
                    suggestion="تحقق من صيغة معلومات التاريخ"
                ))
        
        # التحقق من معلومات الموقع
        if 'meta' in data:
            meta = data['meta']
            if isinstance(meta, dict):
                location_fields = ['city', 'country', 'latitude', 'longitude']
                missing_location = [field for field in location_fields if field not in meta]
                
                if missing_location:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.INFO,
                        message=f"معلومات موقع مفقودة: {', '.join(missing_location)}",
                        field="meta",
                        suggestion="إضافة معلومات الموقع الكاملة يحسن من دقة التحقق"
                    ))
        
        return issues
    
    def _extract_prayer_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """استخراج بيانات الأوقات من البنية المختلفة"""
        # البحث في مستويات مختلفة
        if 'timings' in data:
            return data['timings']
        elif 'data' in data and isinstance(data['data'], dict):
            if 'timings' in data['data']:
                return data['data']['timings']
            else:
                return data['data']
        else:
            # البحث عن الصلوات مباشرة في البيانات
            prayers = {}
            for key, value in data.items():
                if key.lower() in ['fajr', 'dhuhr', 'asr', 'maghrib', 'isha']:
                    prayers[key.lower()] = value
            return prayers if prayers else data
    
    def _minutes_to_time(self, minutes: int) -> str:
        """تحويل الدقائق إلى صيغة HH:MM"""
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours:02d}:{mins:02d}"
    
    def _calculate_validation_score(self, issues: List[ValidationIssue]) -> float:
        """حساب نقاط التحقق"""
        if not issues:
            return 100.0
        
        # نقاط الخصم حسب نوع المشكلة
        deduction_points = {
            ValidationSeverity.CRITICAL: 50,
            ValidationSeverity.ERROR: 20,
            ValidationSeverity.WARNING: 10,
            ValidationSeverity.INFO: 2
        }
        
        total_deduction = 0
        for issue in issues:
            total_deduction += deduction_points.get(issue.severity, 0)
        
        # النقاط النهائية (لا تقل عن 0)
        final_score = max(0, 100 - total_deduction)
        return final_score
    
    def validate_30_minute_delay_calculation(
        self,
        prayer_time: datetime,
        calculated_send_time: datetime,
        expected_delay_minutes: int = 30
    ) -> ValidationReport:
        """التحقق من صحة حساب تأخير الـ 30 دقيقة"""
        issues = []
        validation_start = datetime.now(CAIRO_TZ)
        
        try:
            # حساب الفرق الفعلي
            actual_delay = calculated_send_time - prayer_time
            actual_delay_minutes = actual_delay.total_seconds() / 60
            
            # التحقق من دقة التأخير
            if abs(actual_delay_minutes - expected_delay_minutes) > 1:  # هامش خطأ دقيقة واحدة
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"تأخير غير صحيح: {actual_delay_minutes:.1f} دقيقة بدلاً من {expected_delay_minutes}",
                    field="delay_calculation",
                    expected=f"{expected_delay_minutes} دقيقة",
                    actual=f"{actual_delay_minutes:.1f} دقيقة",
                    suggestion="تحقق من حساب التأخير"
                ))
            
            # التحقق من أن وقت الإرسال في نفس اليوم
            if prayer_time.date() != calculated_send_time.date():
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    message="وقت الإرسال في يوم مختلف عن وقت الصلاة",
                    field="date_consistency",
                    suggestion="تأكد من أن التأخير لا يتجاوز منتصف الليل"
                ))
            
            # التحقق من معقولية وقت الإرسال
            send_hour = calculated_send_time.hour
            if not (0 <= send_hour <= 23):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    message=f"ساعة إرسال غير صحيحة: {send_hour}",
                    field="send_time_hour",
                    expected="0-23",
                    actual=send_hour,
                    suggestion="تحقق من حساب وقت الإرسال"
                ))
            
            # حساب النقاط
            score = self._calculate_validation_score(issues)
            is_valid = score >= 90 and not issues
            
            return ValidationReport(
                is_valid=is_valid,
                score=score,
                issues=issues,
                validation_time=validation_start
            )
            
        except Exception as e:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                message=f"خطأ في التحقق من حساب التأخير: {str(e)}",
                suggestion="تحقق من صحة البيانات المدخلة"
            ))
            
            return ValidationReport(
                is_valid=False,
                score=0.0,
                issues=issues,
                validation_time=validation_start
            )


# Export للاستخدام في الملفات الأخرى
__all__ = [
    'PrayerTimesDataValidator',
    'ValidationReport',
    'ValidationIssue',
    'ValidationSeverity'
]