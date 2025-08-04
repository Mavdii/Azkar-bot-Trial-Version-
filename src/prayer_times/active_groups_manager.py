#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🕌 Active Groups Manager - مدير المجموعات النشطة
==================================================
نظام إدارة المجموعات النشطة للورد القرآني والتذكيرات

Features:
- 📱 إدارة المجموعات المفعلة للورد القرآني
- ⚙️ إعدادات مخصصة لكل مجموعة
- 🔄 تحديث تلقائي للإعدادات
- 📊 إحصائيات مفصلة للمجموعات
- 🛡️ معالجة شاملة للأخطاء

Author: Islamic Bot Developer Team
Version: 1.0.0
License: MIT
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
import pytz
from dataclasses import dataclass, asdict
import json

# Configure logging
logger = logging.getLogger(__name__)

# Cairo timezone
CAIRO_TZ = pytz.timezone('Africa/Cairo')

@dataclass
class GroupSettings:
    """إعدادات المجموعة"""
    chat_id: int
    quran_daily_enabled: bool = True
    quran_send_delay_minutes: int = 30
    prayer_reminders_enabled: bool = True
    prayer_alert_minutes: int = 5
    morning_evening_dhikr: bool = True
    post_prayer_dhikr: bool = True
    timezone: str = "Africa/Cairo"
    last_updated: Optional[datetime] = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now(CAIRO_TZ)
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'chat_id': self.chat_id,
            'quran_daily_enabled': self.quran_daily_enabled,
            'quran_send_delay_minutes': self.quran_send_delay_minutes,
            'prayer_reminders_enabled': self.prayer_reminders_enabled,
            'prayer_alert_minutes': self.prayer_alert_minutes,
            'morning_evening_dhikr': self.morning_evening_dhikr,
            'post_prayer_dhikr': self.post_prayer_dhikr,
            'timezone': self.timezone,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GroupSettings':
        """إنشاء من قاموس"""
        last_updated = None
        if data.get('last_updated'):
            last_updated = datetime.fromisoformat(data['last_updated'])
        
        return cls(
            chat_id=data['chat_id'],
            quran_daily_enabled=data.get('quran_daily_enabled', True),
            quran_send_delay_minutes=data.get('quran_send_delay_minutes', 30),
            prayer_reminders_enabled=data.get('prayer_reminders_enabled', True),
            prayer_alert_minutes=data.get('prayer_alert_minutes', 5),
            morning_evening_dhikr=data.get('morning_evening_dhikr', True),
            post_prayer_dhikr=data.get('post_prayer_dhikr', True),
            timezone=data.get('timezone', 'Africa/Cairo'),
            last_updated=last_updated
        )
    
    def is_valid(self) -> bool:
        """التحقق من صحة الإعدادات"""
        try:
            # التحقق من معرف المجموعة
            if not isinstance(self.chat_id, int) or self.chat_id == 0:
                return False
            
            # التحقق من تأخير الورد القرآني
            if not (1 <= self.quran_send_delay_minutes <= 120):
                return False
            
            # التحقق من تأخير تنبيه الصلاة
            if not (1 <= self.prayer_alert_minutes <= 30):
                return False
            
            # التحقق من المنطقة الزمنية
            try:
                pytz.timezone(self.timezone)
            except pytz.exceptions.UnknownTimeZoneError:
                return False
            
            return True
            
        except Exception:
            return False


class ActiveGroupsManager:
    """مدير المجموعات النشطة"""
    
    def __init__(self, supabase_client=None, cache_file: str = "active_groups_cache.json"):
        self.supabase_client = supabase_client
        self.cache_file = cache_file
        
        # المجموعات النشطة والإعدادات
        self.active_groups: Set[int] = set()
        self.group_settings: Dict[int, GroupSettings] = {}
        
        # إحصائيات
        self.stats = {
            'total_groups': 0,
            'quran_enabled_groups': 0,
            'prayer_reminders_enabled_groups': 0,
            'last_sync_time': None,
            'database_syncs': 0,
            'cache_loads': 0,
            'settings_updates': 0
        }
    
    async def initialize(self) -> bool:
        """تهيئة مدير المجموعات"""
        try:
            logger.info("🔄 بدء تهيئة مدير المجموعات النشطة...")
            
            # تحميل من قاعدة البيانات
            await self._load_from_database()
            
            # تحميل من الملف المحلي كـ backup
            await self._load_from_cache()
            
            # تحديث الإحصائيات
            self._update_statistics()
            
            logger.info(f"✅ تم تهيئة مدير المجموعات: {len(self.active_groups)} مجموعة نشطة")
            return True
            
        except Exception as e:
            logger.error(f"❌ فشل في تهيئة مدير المجموعات: {e}")
            return False    
  
  async def _load_from_database(self) -> None:
        """تحميل المجموعات من قاعدة البيانات"""
        try:
            if not self.supabase_client:
                logger.warning("⚠️ لا توجد قاعدة بيانات متاحة")
                return
            
            # جلب المجموعات النشطة
            groups_result = self.supabase_client.table('groups').select('*').eq('is_active', True).execute()
            
            # جلب إعدادات المجموعات
            settings_result = self.supabase_client.table('group_settings').select('*').execute()
            
            # معالجة البيانات
            if groups_result.data:
                for group_data in groups_result.data:
                    chat_id = group_data['chat_id']
                    self.active_groups.add(chat_id)
            
            if settings_result.data:
                for settings_data in settings_result.data:
                    try:
                        settings = GroupSettings.from_dict(settings_data)
                        if settings.is_valid():
                            self.group_settings[settings.chat_id] = settings
                            
                            # إضافة للمجموعات النشطة إذا كان الورد القرآني مفعل
                            if settings.quran_daily_enabled:
                                self.active_groups.add(settings.chat_id)
                    except Exception as e:
                        logger.warning(f"⚠️ تخطي إعدادات تالفة للمجموعة {settings_data.get('chat_id', 'unknown')}: {e}")
            
            self.stats['database_syncs'] += 1
            self.stats['last_sync_time'] = datetime.now().isoformat()
            
            logger.info(f"📊 تم تحميل {len(self.active_groups)} مجموعة نشطة من قاعدة البيانات")
            
        except Exception as e:
            logger.error(f"❌ خطأ في تحميل المجموعات من قاعدة البيانات: {e}")
    
    async def _load_from_cache(self) -> None:
        """تحميل المجموعات من الملف المحلي"""
        try:
            import os
            if not os.path.exists(self.cache_file):
                logger.info("📁 ملف التخزين المؤقت للمجموعات غير موجود")
                return
            
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # تحميل المجموعات النشطة
            if 'active_groups' in data:
                cached_groups = set(data['active_groups'])
                # دمج مع المجموعات المحملة من قاعدة البيانات
                self.active_groups.update(cached_groups)
            
            # تحميل الإعدادات
            if 'group_settings' in data:
                for chat_id_str, settings_data in data['group_settings'].items():
                    try:
                        chat_id = int(chat_id_str)
                        if chat_id not in self.group_settings:  # لا نستبدل إعدادات قاعدة البيانات
                            settings = GroupSettings.from_dict(settings_data)
                            if settings.is_valid():
                                self.group_settings[chat_id] = settings
                    except Exception as e:
                        logger.warning(f"⚠️ تخطي إعدادات تالفة من الملف للمجموعة {chat_id_str}: {e}")
            
            self.stats['cache_loads'] += 1
            logger.info(f"📁 تم تحميل بيانات إضافية من الملف المحلي")
            
        except Exception as e:
            logger.error(f"❌ خطأ في تحميل الملف المحلي: {e}")
    
    async def _save_to_cache(self) -> None:
        """حفظ المجموعات في الملف المحلي"""
        try:
            data = {
                'active_groups': list(self.active_groups),
                'group_settings': {
                    str(chat_id): settings.to_dict()
                    for chat_id, settings in self.group_settings.items()
                },
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug("💾 تم حفظ بيانات المجموعات في الملف المحلي")
            
        except Exception as e:
            logger.error(f"❌ خطأ في حفظ الملف المحلي: {e}")
    
    async def load_active_groups(self) -> Set[int]:
        """الحصول على المجموعات النشطة للورد القرآني"""
        try:
            # تحديث من قاعدة البيانات إذا مر وقت طويل
            if self._should_refresh_from_database():
                await self._load_from_database()
                self._update_statistics()
            
            # فلترة المجموعات التي لديها الورد القرآني مفعل
            quran_enabled_groups = set()
            for chat_id in self.active_groups:
                settings = self.group_settings.get(chat_id)
                if settings and settings.quran_daily_enabled:
                    quran_enabled_groups.add(chat_id)
                elif not settings:
                    # إذا لم توجد إعدادات، افترض أن الورد القرآني مفعل
                    quran_enabled_groups.add(chat_id)
            
            return quran_enabled_groups
            
        except Exception as e:
            logger.error(f"❌ خطأ في جلب المجموعات النشطة: {e}")
            return set()
    
    def _should_refresh_from_database(self) -> bool:
        """التحقق من الحاجة لتحديث البيانات من قاعدة البيانات"""
        if not self.stats['last_sync_time']:
            return True
        
        try:
            last_sync = datetime.fromisoformat(self.stats['last_sync_time'])
            time_since_sync = datetime.now() - last_sync
            return time_since_sync > timedelta(minutes=30)  # تحديث كل 30 دقيقة
        except Exception:
            return True
    
    async def add_group(self, chat_id: int, group_name: Optional[str] = None) -> bool:
        """إضافة مجموعة جديدة"""
        try:
            # إضافة للمجموعات النشطة
            self.active_groups.add(chat_id)
            
            # إنشاء إعدادات افتراضية إذا لم توجد
            if chat_id not in self.group_settings:
                self.group_settings[chat_id] = GroupSettings(chat_id=chat_id)
            
            # حفظ في قاعدة البيانات
            if self.supabase_client:
                # إضافة/تحديث المجموعة
                group_data = {
                    'chat_id': chat_id,
                    'group_name': group_name or 'Unknown Group',
                    'is_active': True
                }
                self.supabase_client.table('groups').upsert(group_data).execute()
                
                # إضافة/تحديث الإعدادات
                settings_data = self.group_settings[chat_id].to_dict()
                self.supabase_client.table('group_settings').upsert(settings_data).execute()
            
            # حفظ في الملف المحلي
            await self._save_to_cache()
            
            # تحديث الإحصائيات
            self._update_statistics()
            
            logger.info(f"✅ تم إضافة المجموعة {chat_id} ({group_name})")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في إضافة المجموعة {chat_id}: {e}")
            return False
    
    async def remove_group(self, chat_id: int) -> bool:
        """إزالة مجموعة"""
        try:
            # إزالة من المجموعات النشطة
            self.active_groups.discard(chat_id)
            
            # حفظ الإعدادات لكن تعطيل الورد القرآني
            if chat_id in self.group_settings:
                self.group_settings[chat_id].quran_daily_enabled = False
                self.group_settings[chat_id].last_updated = datetime.now(CAIRO_TZ)
            
            # تحديث في قاعدة البيانات
            if self.supabase_client:
                # تعطيل المجموعة بدلاً من حذفها
                self.supabase_client.table('groups').update({'is_active': False}).eq('chat_id', chat_id).execute()
                
                # تحديث الإعدادات
                if chat_id in self.group_settings:
                    settings_data = self.group_settings[chat_id].to_dict()
                    self.supabase_client.table('group_settings').upsert(settings_data).execute()
            
            # حفظ في الملف المحلي
            await self._save_to_cache()
            
            # تحديث الإحصائيات
            self._update_statistics()
            
            logger.info(f"✅ تم إزالة المجموعة {chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في إزالة المجموعة {chat_id}: {e}")
            return False
    
    async def get_group_settings(self, chat_id: int) -> GroupSettings:
        """الحصول على إعدادات مجموعة"""
        try:
            # إذا كانت الإعدادات موجودة، أرجعها
            if chat_id in self.group_settings:
                return self.group_settings[chat_id]
            
            # إنشاء إعدادات افتراضية
            default_settings = GroupSettings(chat_id=chat_id)
            
            # محاولة جلب من قاعدة البيانات
            if self.supabase_client:
                try:
                    result = self.supabase_client.table('group_settings').select('*').eq('chat_id', chat_id).execute()
                    if result.data:
                        settings = GroupSettings.from_dict(result.data[0])
                        if settings.is_valid():
                            self.group_settings[chat_id] = settings
                            return settings
                except Exception as e:
                    logger.warning(f"⚠️ خطأ في جلب إعدادات المجموعة {chat_id} من قاعدة البيانات: {e}")
            
            # حفظ الإعدادات الافتراضية
            self.group_settings[chat_id] = default_settings
            await self.update_group_settings(chat_id, default_settings.to_dict())
            
            return default_settings
            
        except Exception as e:
            logger.error(f"❌ خطأ في جلب إعدادات المجموعة {chat_id}: {e}")
            return GroupSettings(chat_id=chat_id)  # إعدادات افتراضية
    
    async def update_group_settings(self, chat_id: int, settings_update: Dict[str, Any]) -> bool:
        """تحديث إعدادات مجموعة"""
        try:
            # الحصول على الإعدادات الحالية
            current_settings = await self.get_group_settings(chat_id)
            
            # تحديث الإعدادات
            for key, value in settings_update.items():
                if hasattr(current_settings, key):
                    setattr(current_settings, key, value)
            
            current_settings.last_updated = datetime.now(CAIRO_TZ)
            
            # التحقق من صحة الإعدادات
            if not current_settings.is_valid():
                logger.error(f"❌ إعدادات غير صحيحة للمجموعة {chat_id}")
                return False
            
            # حفظ في الذاكرة
            self.group_settings[chat_id] = current_settings
            
            # تحديث المجموعات النشطة
            if current_settings.quran_daily_enabled:
                self.active_groups.add(chat_id)
            else:
                self.active_groups.discard(chat_id)
            
            # حفظ في قاعدة البيانات
            if self.supabase_client:
                settings_data = current_settings.to_dict()
                self.supabase_client.table('group_settings').upsert(settings_data).execute()
            
            # حفظ في الملف المحلي
            await self._save_to_cache()
            
            # تحديث الإحصائيات
            self.stats['settings_updates'] += 1
            self._update_statistics()
            
            logger.info(f"✅ تم تحديث إعدادات المجموعة {chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في تحديث إعدادات المجموعة {chat_id}: {e}")
            return False
    
    def _update_statistics(self) -> None:
        """تحديث الإحصائيات"""
        try:
            self.stats['total_groups'] = len(self.group_settings)
            
            quran_enabled = 0
            prayer_reminders_enabled = 0
            
            for settings in self.group_settings.values():
                if settings.quran_daily_enabled:
                    quran_enabled += 1
                if settings.prayer_reminders_enabled:
                    prayer_reminders_enabled += 1
            
            self.stats['quran_enabled_groups'] = quran_enabled
            self.stats['prayer_reminders_enabled_groups'] = prayer_reminders_enabled
            
        except Exception as e:
            logger.error(f"❌ خطأ في تحديث الإحصائيات: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """الحصول على إحصائيات المجموعات"""
        return {
            'groups_stats': self.stats.copy(),
            'active_groups_count': len(self.active_groups),
            'total_settings_count': len(self.group_settings)
        }
    
    def get_groups_info(self) -> Dict[str, Any]:
        """الحصول على معلومات مفصلة عن المجموعات"""
        try:
            groups_info = []
            
            for chat_id, settings in self.group_settings.items():
                groups_info.append({
                    'chat_id': chat_id,
                    'is_active': chat_id in self.active_groups,
                    'quran_daily_enabled': settings.quran_daily_enabled,
                    'prayer_reminders_enabled': settings.prayer_reminders_enabled,
                    'quran_delay_minutes': settings.quran_send_delay_minutes,
                    'prayer_alert_minutes': settings.prayer_alert_minutes,
                    'timezone': settings.timezone,
                    'last_updated': settings.last_updated.isoformat() if settings.last_updated else None
                })
            
            return {
                'total_groups': len(groups_info),
                'active_groups': len(self.active_groups),
                'groups': groups_info
            }
            
        except Exception as e:
            logger.error(f"❌ خطأ في جلب معلومات المجموعات: {e}")
            return {'total_groups': 0, 'active_groups': 0, 'groups': []}
    
    async def sync_with_database(self) -> bool:
        """مزامنة البيانات مع قاعدة البيانات"""
        try:
            logger.info("🔄 بدء مزامنة البيانات مع قاعدة البيانات...")
            
            # إعادة تحميل من قاعدة البيانات
            await self._load_from_database()
            
            # حفظ في الملف المحلي
            await self._save_to_cache()
            
            # تحديث الإحصائيات
            self._update_statistics()
            
            logger.info("✅ تم مزامنة البيانات مع قاعدة البيانات")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في مزامنة البيانات: {e}")
            return False
    
    def get_health_status(self) -> Dict[str, Any]:
        """الحصول على حالة صحة النظام"""
        try:
            # تحديد الحالة بناءً على عدد المجموعات النشطة
            if len(self.active_groups) == 0:
                status = "warning"
                message = "لا توجد مجموعات نشطة"
            elif len(self.active_groups) < 5:
                status = "warning"
                message = f"عدد قليل من المجموعات النشطة: {len(self.active_groups)}"
            else:
                status = "healthy"
                message = f"النظام يعمل بشكل طبيعي مع {len(self.active_groups)} مجموعة نشطة"
            
            return {
                'status': status,
                'message': message,
                'active_groups': len(self.active_groups),
                'total_groups': len(self.group_settings),
                'database_available': self.supabase_client is not None,
                'last_sync': self.stats['last_sync_time']
            }
            
        except Exception as e:
            logger.error(f"❌ خطأ في فحص حالة النظام: {e}")
            return {
                'status': 'error',
                'message': f'خطأ في فحص الحالة: {e}',
                'active_groups': 0,
                'total_groups': 0,
                'database_available': False,
                'last_sync': None
            }
    
    def __str__(self) -> str:
        return f"ActiveGroupsManager(active={len(self.active_groups)}, total={len(self.group_settings)})"
    
    def __repr__(self) -> str:
        return f"ActiveGroupsManager(groups={len(self.group_settings)}, db_available={self.supabase_client is not None})"


# Export للاستخدام في الملفات الأخرى
__all__ = ['ActiveGroupsManager', 'GroupSettings']