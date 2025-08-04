#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🕌 Prayer Times Package
=======================
حزمة شاملة لإدارة مواقيت الصلاة مع دعم APIs متعددة

Modules:
- config: إعدادات مواقيت الصلاة
- models: نماذج البيانات
- api_client: عميل API الأساسي
- aladhan_api: عميل Aladhan API
- cache: إدارة التخزين المؤقت
- validator: التحقق من صحة البيانات
- manager: المدير الرئيسي

Author: Islamic Bot Developer Team
Version: 1.0.0
License: MIT
"""

from .models import (
    PrayerTimes,
    PrayerTime,
    PrayerName,
    GregorianDate,
    HijriDate,
    LocationInfo,
    ValidationResult
)

from .config import (
    PrayerConfig,
    LocationConfig,
    APIConfig,
    CacheConfig,
    SchedulingConfig,
    CalculationMethod,
    MadhabSchool,
    APIProvider,
    get_prayer_config,
    reload_prayer_config
)

from .api_client import (
    BaseAPIClient,
    APIClientManager,
    APIResponse,
    APIHealthCheck,
    APIStatus,
    PrayerTimesAPIError,
    APIConnectionError,
    APITimeoutError,
    APIRateLimitError,
    APIValidationError
)

from .aladhan_api import AladhanAPIClient

from .cache import (
    PrayerCacheManager,
    CacheEntry
)

from .validator import (
    PrayerTimesValidator,
    ValidationReport,
    ValidationIssue,
    ValidationSeverity
)

__version__ = "1.0.0"
__author__ = "Islamic Bot Developer Team"

__all__ = [
    # Models
    'PrayerTimes',
    'PrayerTime',
    'PrayerName',
    'GregorianDate',
    'HijriDate',
    'LocationInfo',
    'ValidationResult',
    
    # Config
    'PrayerConfig',
    'LocationConfig',
    'APIConfig',
    'CacheConfig',
    'SchedulingConfig',
    'CalculationMethod',
    'MadhabSchool',
    'APIProvider',
    'get_prayer_config',
    'reload_prayer_config',
    
    # API Client
    'BaseAPIClient',
    'APIClientManager',
    'APIResponse',
    'APIHealthCheck',
    'APIStatus',
    'PrayerTimesAPIError',
    'APIConnectionError',
    'APITimeoutError',
    'APIRateLimitError',
    'APIValidationError',
    
    # Specific APIs
    'AladhanAPIClient',
    
    # Cache
    'PrayerCacheManager',
    'CacheEntry',
    
    # Validator
    'PrayerTimesValidator',
    'ValidationReport',
    'ValidationIssue',
    'ValidationSeverity'
]