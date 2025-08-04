#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🕌 Islamic Bot Configuration Manager
====================================
Professional configuration management with environment variables support.
Handles all bot settings, database connections, and feature flags.

Author: Islamic Bot Developer Team
Version: 3.0.0
License: MIT
"""

import os
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import pytz

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    ENV_LOADED = True
except ImportError:
    ENV_LOADED = False
    print("⚠️ python-dotenv not installed. Using system environment variables only.")

@dataclass
class BotConfig:
    """Bot configuration class with environment variable support"""
    
    # ==================== Bot Settings ====================
    BOT_TOKEN: str = os.getenv('BOT_TOKEN', '')
    DEVELOPER_ID: int = int(os.getenv('DEVELOPER_ID', '0'))
    DEVELOPER_USERNAME: str = os.getenv('DEVELOPER_USERNAME', '@IslamicBotDev')
    BOT_VERSION: str = os.getenv('BOT_VERSION', '3.0.0')
    
    # ==================== Database Settings ====================
    SUPABASE_URL: str = os.getenv('SUPABASE_URL', '')
    SUPABASE_KEY: str = os.getenv('SUPABASE_KEY', '')
    SUPABASE_SERVICE_KEY: str = os.getenv('SUPABASE_SERVICE_KEY', '')
    
    # ==================== Timezone & Location ====================
    DEFAULT_TIMEZONE: str = os.getenv('DEFAULT_TIMEZONE', 'Africa/Cairo')
    DEFAULT_CITY: str = os.getenv('DEFAULT_CITY', 'Cairo')
    DEFAULT_COUNTRY: str = os.getenv('DEFAULT_COUNTRY', 'Egypt')
    
    # ==================== Prayer Times ====================
    PRAYER_API_URL: str = os.getenv('PRAYER_API_URL', 'https://api.aladhan.com/v1/timingsByCity')
    PRAYER_CALCULATION_METHOD: int = int(os.getenv('PRAYER_CALCULATION_METHOD', '5'))
    PRAYER_SCHOOL: int = int(os.getenv('PRAYER_SCHOOL', '0'))
    
    # ==================== Cairo-Specific Prayer Settings ====================
    PRAYER_CITY: str = os.getenv('PRAYER_CITY', 'Cairo')
    PRAYER_COUNTRY: str = os.getenv('PRAYER_COUNTRY', 'Egypt')
    PRAYER_LATITUDE: Optional[float] = float(os.getenv('PRAYER_LATITUDE')) if os.getenv('PRAYER_LATITUDE') else None
    PRAYER_LONGITUDE: Optional[float] = float(os.getenv('PRAYER_LONGITUDE')) if os.getenv('PRAYER_LONGITUDE') else None
    
    # ==================== Enhanced API Configuration ====================
    PRAYER_PRIMARY_API: str = os.getenv('PRAYER_PRIMARY_API', 'aladhan')
    PRAYER_BACKUP_APIS: str = os.getenv('PRAYER_BACKUP_APIS', 'islamicfinder,prayertimes')
    PRAYER_API_TIMEOUT: int = int(os.getenv('PRAYER_API_TIMEOUT', '30'))
    PRAYER_API_RETRIES: int = int(os.getenv('PRAYER_API_RETRIES', '3'))
    PRAYER_API_RETRY_DELAY: float = float(os.getenv('PRAYER_API_RETRY_DELAY', '1.0'))
    
    # ==================== Prayer Cache Configuration ====================
    PRAYER_CACHE_ENABLED: bool = os.getenv('PRAYER_CACHE_ENABLED', 'true').lower() == 'true'
    PRAYER_CACHE_DURATION_HOURS: int = int(os.getenv('PRAYER_CACHE_DURATION_HOURS', '24'))
    PRAYER_CACHE_FILE: str = os.getenv('PRAYER_CACHE_FILE', 'prayer_times_cache.json')
    PRAYER_CACHE_MAX_ENTRIES: int = int(os.getenv('PRAYER_CACHE_MAX_ENTRIES', '100'))
    PRAYER_CACHE_CLEANUP_HOURS: int = int(os.getenv('PRAYER_CACHE_CLEANUP_HOURS', '6'))
    
    # ==================== Prayer Reminders Configuration ====================
    PRAYER_REMINDERS_ENABLED: bool = os.getenv('PRAYER_REMINDERS_ENABLED', 'true').lower() == 'true'
    PRAYER_ALERT_MINUTES_BEFORE: int = int(os.getenv('PRAYER_ALERT_MINUTES_BEFORE', '5'))
    PRAYER_REMINDER_AT_TIME: bool = os.getenv('PRAYER_REMINDER_AT_TIME', 'true').lower() == 'true'
    
    # ==================== Dhikr Scheduling ====================
    MORNING_DHIKR_TIME: str = os.getenv('MORNING_DHIKR_TIME', '05:30')
    EVENING_DHIKR_TIME: str = os.getenv('EVENING_DHIKR_TIME', '19:30')
    DHIKR_INTERVAL_MINUTES: int = int(os.getenv('DHIKR_INTERVAL_MINUTES', '5'))
    POST_PRAYER_DELAY_MINUTES: int = int(os.getenv('POST_PRAYER_DELAY_MINUTES', '25'))
    DHIKR_PER_PAGE: int = int(os.getenv('DHIKR_PER_PAGE', '10'))
    
    # ==================== Quran Configuration ====================
    QURAN_PAGES_PER_SESSION: int = int(os.getenv('QURAN_PAGES_PER_SESSION', '3'))
    QURAN_SEND_DELAY_MINUTES: int = int(os.getenv('QURAN_SEND_DELAY_MINUTES', '30'))
    TOTAL_QURAN_PAGES: int = int(os.getenv('TOTAL_QURAN_PAGES', '604'))
    
    # ==================== Logging Configuration ====================
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE: str = os.getenv('LOG_FILE', 'islamic_bot.log')
    LOG_MAX_SIZE: int = int(os.getenv('LOG_MAX_SIZE', '10485760'))  # 10MB
    LOG_BACKUP_COUNT: int = int(os.getenv('LOG_BACKUP_COUNT', '5'))
    
    # ==================== Advanced Settings ====================
    MAX_RETRIES: int = int(os.getenv('MAX_RETRIES', '3'))
    REQUEST_TIMEOUT: int = int(os.getenv('REQUEST_TIMEOUT', '30'))
    RATE_LIMIT_ENABLED: bool = os.getenv('RATE_LIMIT_ENABLED', 'true').lower() == 'true'
    RATE_LIMIT_CALLS: int = int(os.getenv('RATE_LIMIT_CALLS', '30'))
    RATE_LIMIT_PERIOD: int = int(os.getenv('RATE_LIMIT_PERIOD', '60'))
    
    # ==================== UI Configuration ====================
    LANGUAGE: str = os.getenv('LANGUAGE', 'ar')
    RTL_SUPPORT: bool = os.getenv('RTL_SUPPORT', 'true').lower() == 'true'
    EMOJI_ENABLED: bool = os.getenv('EMOJI_ENABLED', 'true').lower() == 'true'
    
    # ==================== Analytics & Monitoring ====================
    ANALYTICS_ENABLED: bool = os.getenv('ANALYTICS_ENABLED', 'true').lower() == 'true'
    ERROR_REPORTING_ENABLED: bool = os.getenv('ERROR_REPORTING_ENABLED', 'true').lower() == 'true'
    PERFORMANCE_MONITORING: bool = os.getenv('PERFORMANCE_MONITORING', 'true').lower() == 'true'
    
    # ==================== Security Settings ====================
    ENCRYPTION_KEY: str = os.getenv('ENCRYPTION_KEY', '')
    JWT_SECRET: str = os.getenv('JWT_SECRET', '')
    from dataclasses import field
    ALLOWED_UPDATES: list = field(default_factory=lambda: os.getenv('ALLOWED_UPDATES', 'message,callback_query,chat_member').split(','))
    
    # ==================== External APIs ====================
    WEATHER_API_KEY: str = os.getenv('WEATHER_API_KEY', '')
    HADITH_API_URL: str = os.getenv('HADITH_API_URL', 'https://api.hadith.gading.dev')
    QURAN_API_URL: str = os.getenv('QURAN_API_URL', 'https://api.quran.com')
    
    # ==================== Notification Settings ====================
    PUSH_NOTIFICATIONS_ENABLED: bool = os.getenv('PUSH_NOTIFICATIONS_ENABLED', 'true').lower() == 'true'
    EMAIL_NOTIFICATIONS_ENABLED: bool = os.getenv('EMAIL_NOTIFICATIONS_ENABLED', 'false').lower() == 'true'
    SMTP_HOST: str = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    SMTP_PORT: int = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USERNAME: str = os.getenv('SMTP_USERNAME', '')
    SMTP_PASSWORD: str = os.getenv('SMTP_PASSWORD', '')
    
    # ==================== Performance Settings ====================
    WORKER_THREADS: int = int(os.getenv('WORKER_THREADS', '4'))
    MAX_CONCURRENT_REQUESTS: int = int(os.getenv('MAX_CONCURRENT_REQUESTS', '100'))
    CACHE_TTL: int = int(os.getenv('CACHE_TTL', '3600'))
    DATABASE_POOL_SIZE: int = int(os.getenv('DATABASE_POOL_SIZE', '10'))
    
    # ==================== Backup & Recovery ====================
    BACKUP_ENABLED: bool = os.getenv('BACKUP_ENABLED', 'true').lower() == 'true'
    BACKUP_INTERVAL_HOURS: int = int(os.getenv('BACKUP_INTERVAL_HOURS', '24'))
    BACKUP_RETENTION_DAYS: int = int(os.getenv('BACKUP_RETENTION_DAYS', '30'))
    BACKUP_STORAGE_PATH: str = os.getenv('BACKUP_STORAGE_PATH', './backups')
    
    # ==================== Feature Flags ====================
    FEATURE_RANDOM_DHIKR: bool = os.getenv('FEATURE_RANDOM_DHIKR', 'true').lower() == 'true'
    FEATURE_PRAYER_REMINDERS: bool = os.getenv('FEATURE_PRAYER_REMINDERS', 'true').lower() == 'true'
    FEATURE_QURAN_DAILY: bool = os.getenv('FEATURE_QURAN_DAILY', 'true').lower() == 'true'
    FEATURE_MORNING_EVENING_DHIKR: bool = os.getenv('FEATURE_MORNING_EVENING_DHIKR', 'true').lower() == 'true'
    FEATURE_POST_PRAYER_DHIKR: bool = os.getenv('FEATURE_POST_PRAYER_DHIKR', 'true').lower() == 'true'
    FEATURE_STATISTICS: bool = os.getenv('FEATURE_STATISTICS', 'true').lower() == 'true'
    FEATURE_ADMIN_PANEL: bool = os.getenv('FEATURE_ADMIN_PANEL', 'false').lower() == 'true'
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        self.validate_config()
        self.setup_timezone()
    
    def validate_config(self) -> None:
        """Validate critical configuration values"""
        if not self.BOT_TOKEN:
            raise ValueError("❌ BOT_TOKEN is required! Please set it in your .env file.")
        
        if not self.SUPABASE_URL or not self.SUPABASE_KEY:
            print("⚠️ Supabase configuration missing. Bot will run in local mode.")
        
        if self.DEVELOPER_ID == 0:
            print("⚠️ DEVELOPER_ID not set. Some admin features may not work.")
        
        # Validate time formats
        try:
            from datetime import datetime
            datetime.strptime(self.MORNING_DHIKR_TIME, '%H:%M')
            datetime.strptime(self.EVENING_DHIKR_TIME, '%H:%M')
        except ValueError:
            raise ValueError("❌ Invalid time format in MORNING_DHIKR_TIME or EVENING_DHIKR_TIME. Use HH:MM format.")
        
        # Validate numeric ranges
        if not (1 <= self.DHIKR_INTERVAL_MINUTES <= 60):
            raise ValueError("❌ DHIKR_INTERVAL_MINUTES must be between 1 and 60.")
        
        if not (1 <= self.QURAN_PAGES_PER_SESSION <= 10):
            raise ValueError("❌ QURAN_PAGES_PER_SESSION must be between 1 and 10.")
    
    def setup_timezone(self) -> None:
        """Setup timezone configuration"""
        try:
            self.TIMEZONE = pytz.timezone(self.DEFAULT_TIMEZONE)
        except pytz.exceptions.UnknownTimeZoneError:
            print(f"⚠️ Unknown timezone: {self.DEFAULT_TIMEZONE}. Using UTC.")
            self.TIMEZONE = pytz.UTC
    
    def get_database_config(self) -> Dict[str, str]:
        """Get database configuration dictionary"""
        return {
            'url': self.SUPABASE_URL,
            'key': self.SUPABASE_KEY,
            'service_key': self.SUPABASE_SERVICE_KEY
        }
    
    def get_prayer_api_config(self) -> Dict[str, Any]:
        """Get prayer times API configuration"""
        return {
            'url': self.PRAYER_API_URL,
            'city': self.PRAYER_CITY,
            'country': self.PRAYER_COUNTRY,
            'method': self.PRAYER_CALCULATION_METHOD,
            'school': self.PRAYER_SCHOOL,
            'latitude': self.PRAYER_LATITUDE,
            'longitude': self.PRAYER_LONGITUDE
        }
    
    def get_enhanced_prayer_config(self) -> Dict[str, Any]:
        """Get enhanced prayer times configuration"""
        return {
            'primary_api': self.PRAYER_PRIMARY_API,
            'backup_apis': self.PRAYER_BACKUP_APIS.split(',') if self.PRAYER_BACKUP_APIS else [],
            'api_timeout': self.PRAYER_API_TIMEOUT,
            'api_retries': self.PRAYER_API_RETRIES,
            'api_retry_delay': self.PRAYER_API_RETRY_DELAY,
            'cache_enabled': self.PRAYER_CACHE_ENABLED,
            'cache_duration_hours': self.PRAYER_CACHE_DURATION_HOURS,
            'cache_file': self.PRAYER_CACHE_FILE,
            'cache_max_entries': self.PRAYER_CACHE_MAX_ENTRIES,
            'cache_cleanup_hours': self.PRAYER_CACHE_CLEANUP_HOURS,
            'reminders_enabled': self.PRAYER_REMINDERS_ENABLED,
            'alert_minutes_before': self.PRAYER_ALERT_MINUTES_BEFORE,
            'reminder_at_time': self.PRAYER_REMINDER_AT_TIME
        }
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration dictionary"""
        return {
            'level': getattr(logging, self.LOG_LEVEL.upper()),
            'filename': self.LOG_FILE,
            'max_size': self.LOG_MAX_SIZE,
            'backup_count': self.LOG_BACKUP_COUNT
        }
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if a specific feature is enabled"""
        feature_attr = f'FEATURE_{feature_name.upper()}'
        return getattr(self, feature_attr, False)
    
    def get_dhikr_schedule_config(self) -> Dict[str, Any]:
        """Get dhikr scheduling configuration"""
        return {
            'morning_time': self.MORNING_DHIKR_TIME,
            'evening_time': self.EVENING_DHIKR_TIME,
            'interval_minutes': self.DHIKR_INTERVAL_MINUTES,
            'post_prayer_delay': self.POST_PRAYER_DELAY_MINUTES,
            'per_page': self.DHIKR_PER_PAGE
        }
    
    def get_quran_config(self) -> Dict[str, Any]:
        """Get Quran configuration"""
        return {
            'pages_per_session': self.QURAN_PAGES_PER_SESSION,
            'send_delay_minutes': self.QURAN_SEND_DELAY_MINUTES,
            'total_pages': self.TOTAL_QURAN_PAGES
        }
    
    def print_config_summary(self) -> None:
        """Print configuration summary for debugging"""
        print("\n" + "="*50)
        print("🕌 Islamic Bot Configuration Summary")
        print("="*50)
        print(f"📱 Bot Version: {self.BOT_VERSION}")
        print(f"🌍 Timezone: {self.DEFAULT_TIMEZONE}")
        print(f"🕌 Prayer Location: {self.PRAYER_CITY}, {self.PRAYER_COUNTRY}")
        print(f"📐 Prayer Method: {self.PRAYER_CALCULATION_METHOD} (Egyptian General Authority)")
        print(f"🔗 Primary API: {self.PRAYER_PRIMARY_API}")
        print(f"💾 Prayer Cache: {'✅ Enabled' if self.PRAYER_CACHE_ENABLED else '❌ Disabled'}")
        print(f"🔔 Prayer Reminders: {'✅ Enabled' if self.PRAYER_REMINDERS_ENABLED else '❌ Disabled'}")
        print(f"⏰ Alert Before Prayer: {self.PRAYER_ALERT_MINUTES_BEFORE} minutes")
        print(f"🕐 Morning Dhikr: {self.MORNING_DHIKR_TIME}")
        print(f"🌆 Evening Dhikr: {self.EVENING_DHIKR_TIME}")
        print(f"📖 Quran Pages/Session: {self.QURAN_PAGES_PER_SESSION}")
        print(f"⏳ Quran Delay: {self.QURAN_SEND_DELAY_MINUTES} minutes after prayer")
        print(f"🗄️ Database: {'✅ Configured' if self.SUPABASE_URL else '❌ Not configured'}")
        print(f"📝 Logging Level: {self.LOG_LEVEL}")
        print(f"🔧 Environment: {'✅ .env loaded' if ENV_LOADED else '⚠️ System env only'}")
        print("="*50 + "\n")

# Create global configuration instance
config = BotConfig()

# Timezone shortcuts
CAIRO_TZ = config.TIMEZONE
UTC_TZ = pytz.UTC

# Export commonly used values
BOT_TOKEN = config.BOT_TOKEN
DEVELOPER_ID = config.DEVELOPER_ID
DEVELOPER_USERNAME = config.DEVELOPER_USERNAME
BOT_VERSION = config.BOT_VERSION

SUPABASE_URL = config.SUPABASE_URL
SUPABASE_KEY = config.SUPABASE_KEY

MORNING_DHIKR_TIME = config.MORNING_DHIKR_TIME
EVENING_DHIKR_TIME = config.EVENING_DHIKR_TIME
DHIKR_INTERVAL_MINUTES = config.DHIKR_INTERVAL_MINUTES
POST_PRAYER_DELAY_MINUTES = config.POST_PRAYER_DELAY_MINUTES

# Print configuration summary if running directly
if __name__ == "__main__":
    config.print_config_summary()