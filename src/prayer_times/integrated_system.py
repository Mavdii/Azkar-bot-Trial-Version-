#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🕌 Integrated Prayer Times System - النظام المتكامل لمواقيت الصلاة
====================================================================
نظام متكامل يجمع جميع مكونات مواقيت الصلاة والورد القرآني

Features:
- 🔄 تكامل شامل لجميع المكونات
- 🕌 مواقيت دقيقة للقاهرة مع APIs متعددة
- 📖 ورد قرآني دقيق بعد كل صلاة بـ 30 دقيقة
- 🔔 تذكيرات الصلاة المتقدمة
- 🛡️ معالجة شاملة للأخطاء

Author: Islamic Bot Developer Team
Version: 1.0.0
License: MIT
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
import pytz

# Telegram imports
from telegram import Bot

# Local imports
from .cairo_manager import CairoPrayerTimesManager, CairoPrayerTimes
from .enhanced_api_client import EnhancedPrayerAPIClient
from .prayer_cache import PrayerTimesCache
from .precise_quran_scheduler import PreciseQuranScheduler
from .active_groups_manager import ActiveGroupsManager
from .prayer_reminders import PrayerRemindersSystem
from .error_handler import PrayerTimesErrorHandler, ErrorCategory, ErrorSeverity

# Configure logging
logger = logging.getLogger(__name__)

# Cairo timezone
CAIRO_TZ = pytz.timezone('Africa/Cairo')

class IntegratedPrayerTimesSystem:
    """النظام المتكامل لمواقيت الصلاة"""
    
    def __init__(
        self,
        bot: Bot,
        supabase_client=None,
        quran_page_manager=None,
        page_tracker=None
    ):
        self.bot = bot
        self.supabase_client = supabase_client
        self.quran_page_manager = quran_page_manager
        self.page_tracker = page_tracker
        
        # تهيئة معالج الأخطاء
        self.error_handler = PrayerTimesErrorHandler(
            admin_notification_callback=self._admin_notification_callback
        )
        
        # تهيئة عميل API
        self.api_client = EnhancedPrayerAPIClient()
        
        # تهيئة نظام التخزين المؤقت
        self.cache_manager = PrayerTimesCache(
            supabase_client=supabase_client
        )
        
        # تهيئة مدير مواقيت الصلاة
        self.prayer_manager = CairoPrayerTimesManager(
            api_client=self.api_client,
            cache_manager=self.cache_manager
        )
        self.prayer_manager.error_handler = self.error_handler
        
        # تهيئة مدير المجموعات النشطة
        self.groups_manager = ActiveGroupsManager(
            supabase_client=supabase_client
        )
        
        # تهيئة نظام تذكيرات الصلاة
        self.reminders_system = PrayerRemindersSystem(
            bot=bot,
            prayer_manager=self.prayer_manager,
            groups_manager=self.groups_manager,
            error_handler=self.error_handler
        )
        
        # تهيئة مجدول الورد القرآني
        self.quran_scheduler = None
        if quran_page_manager and page_tracker:
            self.quran_scheduler = PreciseQuranScheduler(
                bot=bot,
                prayer_manager=self.prayer_manager,
                quran_page_manager=quran_page_manager,
                page_tracker=page_tracker,
                supabase_client=supabase_client
            )
        
        # حالة النظام
        self.is_initialized = False
        self.initialization_time: Optional[datetime] = None
        
        # إحصائيات عامة
        self.system_stats = {
            'initialization_time': None,
            'total_uptime_hours': 0,
            'components_initialized': 0,
            'total_components': 6,
            'last_health_check': None,
            'system_restarts': 0
        }
    
    async def initialize(self) -> bool:
        """تهيئة النظام المتكامل"""
        try:
            logger.info("🔄 بدء تهيئة النظام المتكامل لمواقيت الصلاة...")
            
            initialization_start = datetime.now(CAIRO_TZ)
            components_initialized = 0
            
            # 1. تهيئة معالج الأخطاء (مهيأ بالفعل)
            components_initialized += 1
            logger.info("✅ معالج الأخطاء جاهز")
            
            # 2. تهيئة نظام التخزين المؤقت
            if await self.cache_manager.initialize():
                components_initialized += 1
                logger.info("✅ نظام التخزين المؤقت جاهز")
            else:
                logger.error("❌ فشل في تهيئة نظام التخزين المؤقت")
            
            # 3. تهيئة مدير مواقيت الصلاة
            if await self.prayer_manager.initialize():
                components_initialized += 1
                logger.info("✅ مدير مواقيت الصلاة جاهز")
            else:
                logger.error("❌ فشل في تهيئة مدير مواقيت الصلاة")
            
            # 4. تهيئة مدير المجموعات النشطة
            if await self.groups_manager.initialize():
                components_initialized += 1
                logger.info("✅ مدير المجموعات النشطة جاهز")
            else:
                logger.error("❌ فشل في تهيئة مدير المجموعات النشطة")
            
            # 5. تهيئة نظام تذكيرات الصلاة
            if await self.reminders_system.initialize():
                components_initialized += 1
                logger.info("✅ نظام تذكيرات الصلاة جاهز")
            else:
                logger.error("❌ فشل في تهيئة نظام تذكيرات الصلاة")
            
            # 6. تهيئة مجدول الورد القرآني
            if self.quran_scheduler:
                if await self.quran_scheduler.initialize():
                    components_initialized += 1
                    logger.info("✅ مجدول الورد القرآني جاهز")
                else:
                    logger.error("❌ فشل في تهيئة مجدول الورد القرآني")
            else:
                logger.warning("⚠️ مجدول الورد القرآني غير متاح")
            
            # تحديث الإحصائيات
            self.system_stats['components_initialized'] = components_initialized
            self.system_stats['initialization_time'] = initialization_start.isoformat()
            self.initialization_time = initialization_start
            
            # تحديد حالة النظام
            if components_initialized >= 4:  # الحد الأدنى للعمل
                self.is_initialized = True
                logger.info(f"✅ تم تهيئة النظام المتكامل بنجاح ({components_initialized}/{self.system_stats['total_components']} مكونات)")
                return True
            else:
                logger.error(f"❌ فشل في تهيئة النظام المتكامل ({components_initialized}/{self.system_stats['total_components']} مكونات)")
                return False
                
        except Exception as e:
            await self.error_handler.handle_error(
                e, ErrorCategory.SYSTEM_ERROR, ErrorSeverity.CRITICAL,
                {'component': 'IntegratedPrayerTimesSystem', 'method': 'initialize'}
            )
            return False
    
    async def _admin_notification_callback(self, message: str, error_record) -> None:
        """callback لإشعار الإدارة بالأخطاء الحرجة"""
        try:
            # يمكن إضافة إرسال رسالة للمطور هنا
            logger.critical(f"🚨 إشعار إداري: {message}")
            
            # إذا كان هناك معرف مطور، أرسل له رسالة
            # if DEVELOPER_ID:
            #     await self.bot.send_message(DEVELOPER_ID, message, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            logger.error(f"❌ خطأ في إرسال إشعار إداري: {e}")
    
    async def get_today_prayer_times(self, force_refresh: bool = False) -> Optional[CairoPrayerTimes]:
        """الحصول على مواقيت اليوم"""
        try:
            if not self.is_initialized:
                logger.error("❌ النظام غير مهيأ")
                return None
            
            return await self.prayer_manager.get_today_prayer_times(force_refresh=force_refresh)
            
        except Exception as e:
            await self.error_handler.handle_error(
                e, ErrorCategory.API_ERROR, ErrorSeverity.MEDIUM,
                {'method': 'get_today_prayer_times', 'force_refresh': force_refresh}
            )
            return None
    
    async def get_next_prayer_info(self) -> Optional[tuple]:
        """الحصول على معلومات الصلاة التالية"""
        try:
            if not self.is_initialized:
                logger.error("❌ النظام غير مهيأ")
                return None
            
            return await self.prayer_manager.get_next_prayer_info()
            
        except Exception as e:
            await self.error_handler.handle_error(
                e, ErrorCategory.SYSTEM_ERROR, ErrorSeverity.LOW,
                {'method': 'get_next_prayer_info'}
            )
            return None
    
    async def send_manual_quran(self, chat_id: int) -> bool:
        """إرسال الورد القرآني يدوياً"""
        try:
            if not self.is_initialized or not self.quran_scheduler:
                logger.error("❌ النظام أو مجدول الورد القرآني غير مهيأ")
                return False
            
            return await self.quran_scheduler.send_manual_quran(chat_id)
            
        except Exception as e:
            await self.error_handler.handle_error(
                e, ErrorCategory.SYSTEM_ERROR, ErrorSeverity.MEDIUM,
                {'method': 'send_manual_quran', 'chat_id': chat_id}
            )
            return False
    
    async def add_group(self, chat_id: int, group_name: Optional[str] = None) -> bool:
        """إضافة مجموعة جديدة"""
        try:
            if not self.is_initialized:
                logger.error("❌ النظام غير مهيأ")
                return False
            
            # إضافة للمجموعات النشطة
            success = await self.groups_manager.add_group(chat_id, group_name)
            
            # إضافة لمجدول الورد القرآني إذا كان متاحاً
            if success and self.quran_scheduler:
                await self.quran_scheduler.add_active_group(chat_id)
            
            return success
            
        except Exception as e:
            await self.error_handler.handle_error(
                e, ErrorCategory.DATABASE_ERROR, ErrorSeverity.MEDIUM,
                {'method': 'add_group', 'chat_id': chat_id, 'group_name': group_name}
            )
            return False
    
    async def remove_group(self, chat_id: int) -> bool:
        """إزالة مجموعة"""
        try:
            if not self.is_initialized:
                logger.error("❌ النظام غير مهيأ")
                return False
            
            # إزالة من المجموعات النشطة
            success = await self.groups_manager.remove_group(chat_id)
            
            # إزالة من مجدول الورد القرآني إذا كان متاحاً
            if success and self.quran_scheduler:
                await self.quran_scheduler.remove_active_group(chat_id)
            
            return success
            
        except Exception as e:
            await self.error_handler.handle_error(
                e, ErrorCategory.DATABASE_ERROR, ErrorSeverity.MEDIUM,
                {'method': 'remove_group', 'chat_id': chat_id}
            )
            return False
    
    async def update_group_settings(self, chat_id: int, settings: Dict[str, Any]) -> bool:
        """تحديث إعدادات مجموعة"""
        try:
            if not self.is_initialized:
                logger.error("❌ النظام غير مهيأ")
                return False
            
            return await self.groups_manager.update_group_settings(chat_id, settings)
            
        except Exception as e:
            await self.error_handler.handle_error(
                e, ErrorCategory.DATABASE_ERROR, ErrorSeverity.MEDIUM,
                {'method': 'update_group_settings', 'chat_id': chat_id}
            )
            return False
    
    async def get_group_settings(self, chat_id: int):
        """الحصول على إعدادات مجموعة"""
        try:
            if not self.is_initialized:
                logger.error("❌ النظام غير مهيأ")
                return None
            
            return await self.groups_manager.get_group_settings(chat_id)
            
        except Exception as e:
            await self.error_handler.handle_error(
                e, ErrorCategory.DATABASE_ERROR, ErrorSeverity.LOW,
                {'method': 'get_group_settings', 'chat_id': chat_id}
            )
            return None
    
    def get_comprehensive_statistics(self) -> Dict[str, Any]:
        """الحصول على إحصائيات شاملة للنظام"""
        try:
            # حساب وقت التشغيل
            if self.initialization_time:
                uptime = datetime.now(CAIRO_TZ) - self.initialization_time
                self.system_stats['total_uptime_hours'] = uptime.total_seconds() / 3600
            
            stats = {
                'system_stats': self.system_stats.copy(),
                'is_initialized': self.is_initialized
            }
            
            # إضافة إحصائيات المكونات
            if self.is_initialized:
                stats['prayer_manager'] = self.prayer_manager.get_statistics()
                stats['cache_manager'] = self.cache_manager.get_statistics()
                stats['groups_manager'] = self.groups_manager.get_statistics()
                stats['reminders_system'] = self.reminders_system.get_statistics()
                stats['api_client'] = self.api_client.get_statistics()
                stats['error_handler'] = self.error_handler.get_error_statistics()
                
                if self.quran_scheduler:
                    stats['quran_scheduler'] = self.quran_scheduler.get_statistics()
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ خطأ في جلب الإحصائيات الشاملة: {e}")
            return {'error': str(e)}
    
    def get_system_health(self) -> Dict[str, Any]:
        """الحصول على حالة صحة النظام الشاملة"""
        try:
            self.system_stats['last_health_check'] = datetime.now(CAIRO_TZ).isoformat()
            
            health_status = {
                'overall_status': 'healthy',
                'overall_message': 'النظام يعمل بشكل طبيعي',
                'components_health': {},
                'system_info': {
                    'initialized': self.is_initialized,
                    'uptime_hours': self.system_stats['total_uptime_hours'],
                    'components_count': self.system_stats['components_initialized'],
                    'total_components': self.system_stats['total_components']
                }
            }
            
            if not self.is_initialized:
                health_status['overall_status'] = 'critical'
                health_status['overall_message'] = 'النظام غير مهيأ'
                return health_status
            
            # فحص صحة المكونات
            components_health = {}
            critical_issues = 0
            warning_issues = 0
            
            # فحص مدير مواقيت الصلاة
            prayer_health = self.prayer_manager.get_health_status()
            components_health['prayer_manager'] = prayer_health
            if prayer_health['status'] == 'critical':
                critical_issues += 1
            elif prayer_health['status'] == 'warning':
                warning_issues += 1
            
            # فحص مدير المجموعات
            groups_health = self.groups_manager.get_health_status()
            components_health['groups_manager'] = groups_health
            if groups_health['status'] == 'critical':
                critical_issues += 1
            elif groups_health['status'] == 'warning':
                warning_issues += 1
            
            # فحص نظام التذكيرات
            reminders_health = self.reminders_system.get_health_status()
            components_health['reminders_system'] = reminders_health
            if reminders_health['status'] == 'critical':
                critical_issues += 1
            elif reminders_health['status'] == 'warning':
                warning_issues += 1
            
            # فحص عميل API
            api_health = self.api_client.get_health_status()
            components_health['api_client'] = api_health
            if api_health['status'] == 'critical':
                critical_issues += 1
            elif api_health['status'] == 'warning':
                warning_issues += 1
            
            # فحص مجدول الورد القرآني
            if self.quran_scheduler:
                quran_health = self.quran_scheduler.get_health_status()
                components_health['quran_scheduler'] = quran_health
                if quran_health['status'] == 'critical':
                    critical_issues += 1
                elif quran_health['status'] == 'warning':
                    warning_issues += 1
            
            health_status['components_health'] = components_health
            
            # تحديد الحالة العامة
            if critical_issues > 0:
                health_status['overall_status'] = 'critical'
                health_status['overall_message'] = f'يوجد {critical_issues} مشكلة حرجة في النظام'
            elif warning_issues > 0:
                health_status['overall_status'] = 'warning'
                health_status['overall_message'] = f'يوجد {warning_issues} تحذير في النظام'
            
            return health_status
            
        except Exception as e:
            logger.error(f"❌ خطأ في فحص صحة النظام: {e}")
            return {
                'overall_status': 'error',
                'overall_message': f'خطأ في فحص الحالة: {e}',
                'components_health': {},
                'system_info': {'initialized': False}
            }
    
    async def restart_system(self) -> bool:
        """إعادة تشغيل النظام"""
        try:
            logger.info("🔄 بدء إعادة تشغيل النظام المتكامل...")
            
            # تنظيف الموارد الحالية
            await self.cleanup()
            
            # إعادة التهيئة
            success = await self.initialize()
            
            if success:
                self.system_stats['system_restarts'] += 1
                logger.info("✅ تم إعادة تشغيل النظام بنجاح")
            else:
                logger.error("❌ فشل في إعادة تشغيل النظام")
            
            return success
            
        except Exception as e:
            await self.error_handler.handle_error(
                e, ErrorCategory.SYSTEM_ERROR, ErrorSeverity.CRITICAL,
                {'method': 'restart_system'}
            )
            return False
    
    async def cleanup(self) -> None:
        """تنظيف جميع موارد النظام"""
        try:
            logger.info("🔄 بدء تنظيف موارد النظام المتكامل...")
            
            # تنظيف المكونات بالترتيب العكسي للتهيئة
            if self.quran_scheduler:
                await self.quran_scheduler.cleanup()
            
            if self.reminders_system:
                await self.reminders_system.cleanup()
            
            if self.prayer_manager:
                await self.prayer_manager.cleanup()
            
            if self.cache_manager:
                await self.cache_manager.cleanup()
            
            self.is_initialized = False
            logger.info("✅ تم تنظيف موارد النظام المتكامل")
            
        except Exception as e:
            logger.error(f"❌ خطأ في تنظيف موارد النظام: {e}")
    
    def __str__(self) -> str:
        status = "initialized" if self.is_initialized else "not_initialized"
        components = self.system_stats['components_initialized']
        total = self.system_stats['total_components']
        return f"IntegratedPrayerTimesSystem({status}, {components}/{total} components)"
    
    def __repr__(self) -> str:
        return f"IntegratedPrayerTimesSystem(initialized={self.is_initialized}, uptime={self.system_stats['total_uptime_hours']:.1f}h)"


# Export للاستخدام في الملفات الأخرى
__all__ = ['IntegratedPrayerTimesSystem']