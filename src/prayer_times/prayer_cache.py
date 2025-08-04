#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🕌 Prayer Times Cache System - نظام التخزين المؤقت لمواقيت الصلاة
====================================================================
نظام تخزين مؤقت متقدم لمواقيت الصلاة مع دعم ملفات وقاعدة البيانات

Features:
- 💾 تخزين مؤقت لمدة 24 ساعة
- 🔄 تنظيف تلقائي للبيانات المنتهية الصلاحية
- 📁 دعم التخزين في الملفات وقاعدة البيانات
- 🛡️ آلية fallback للأيام السابقة
- 📊 إحصائيات مفصلة للأداء

Author: Islamic Bot Developer Team
Version: 1.0.0
License: MIT
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import pytz
from dataclasses import dataclass
import aiofiles
from pathlib import Path

# Import the CairoPrayerTimes model
from .cairo_manager import CairoPrayerTimes

# Configure logging
logger = logging.getLogger(__name__)

# Cairo timezone
CAIRO_TZ = pytz.timezone('Africa/Cairo')

@dataclass
class CacheEntry:
    """إدخال التخزين المؤقت"""
    date: str
    prayer_times: CairoPrayerTimes
    cached_at: datetime
    expires_at: datetime
    source: str
    
    def is_expired(self) -> bool:
        """التحقق من انتهاء صلاحية الإدخال"""
        return datetime.now(CAIRO_TZ) > self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'date': self.date,
            'prayer_times': self.prayer_times.to_dict(),
            'cached_at': self.cached_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'source': self.source
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheEntry':
        """إنشاء من قاموس"""
        return cls(
            date=data['date'],
            prayer_times=CairoPrayerTimes.from_dict(data['prayer_times']),
            cached_at=datetime.fromisoformat(data['cached_at']),
            expires_at=datetime.fromisoformat(data['expires_at']),
            source=data['source']
        )

class PrayerTimesCache:
    """نظام التخزين المؤقت لمواقيت الصلاة"""
    
    def __init__(
        self,
        cache_file: str = "prayer_times_cache.json",
        cache_duration_hours: int = 24,
        max_entries: int = 100,
        cleanup_interval_hours: int = 6,
        supabase_client=None
    ):
        self.cache_file = Path(cache_file)
        self.cache_duration_hours = cache_duration_hours
        self.max_entries = max_entries
        self.cleanup_interval_hours = cleanup_interval_hours
        self.supabase_client = supabase_client
        
        # التخزين المؤقت في الذاكرة
        self.memory_cache: Dict[str, CacheEntry] = {}
        
        # مهمة التنظيف التلقائي
        self.cleanup_task: Optional[asyncio.Task] = None
        
        # إحصائيات
        self.stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'file_reads': 0,
            'file_writes': 0,
            'db_reads': 0,
            'db_writes': 0,
            'cleanup_runs': 0,
            'entries_cleaned': 0,
            'last_cleanup': None
        }
    
    async def initialize(self) -> bool:
        """تهيئة نظام التخزين المؤقت"""
        try:
            logger.info("🔄 بدء تهيئة نظام التخزين المؤقت...")
            
            # إنشاء مجلد التخزين المؤقت إذا لم يكن موجوداً
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            
            # تحميل البيانات المحفوظة
            await self._load_from_file()
            
            # بدء مهمة التنظيف التلقائي
            await self._start_cleanup_task()
            
            logger.info("✅ تم تهيئة نظام التخزين المؤقت بنجاح")
            return True
            
        except Exception as e:
            logger.error(f"❌ فشل في تهيئة نظام التخزين المؤقت: {e}")
            return False
    
    async def get_cached_times(self, date: str) -> Optional[CairoPrayerTimes]:
        """الحصول على مواقيت محفوظة لتاريخ محدد"""
        self.stats['total_requests'] += 1
        
        try:
            # البحث في الذاكرة أولاً
            if date in self.memory_cache:
                entry = self.memory_cache[date]
                if not entry.is_expired():
                    self.stats['cache_hits'] += 1
                    logger.debug(f"📦 تم العثور على مواقيت {date} في الذاكرة")
                    return entry.prayer_times
                else:
                    # إزالة الإدخال المنتهي الصلاحية
                    del self.memory_cache[date]
                    logger.debug(f"🗑️ تم حذف إدخال منتهي الصلاحية: {date}")
            
            # البحث في قاعدة البيانات
            if self.supabase_client:
                db_entry = await self._get_from_database(date)
                if db_entry and not db_entry.is_expired():
                    # إضافة إلى الذاكرة
                    self.memory_cache[date] = db_entry
                    self.stats['cache_hits'] += 1
                    self.stats['db_reads'] += 1
                    logger.debug(f"📦 تم العثور على مواقيت {date} في قاعدة البيانات")
                    return db_entry.prayer_times
            
            # البحث في الملف
            file_entry = await self._get_from_file(date)
            if file_entry and not file_entry.is_expired():
                # إضافة إلى الذاكرة
                self.memory_cache[date] = file_entry
                self.stats['cache_hits'] += 1
                self.stats['file_reads'] += 1
                logger.debug(f"📦 تم العثور على مواقيت {date} في الملف")
                return file_entry.prayer_times
            
            # لم يتم العثور على بيانات صالحة
            self.stats['cache_misses'] += 1
            logger.debug(f"❌ لم يتم العثور على مواقيت صالحة لـ {date}")
            return None
            
        except Exception as e:
            self.stats['cache_misses'] += 1
            logger.error(f"❌ خطأ في جلب مواقيت {date} من التخزين المؤقت: {e}")
            return None
    
    async def set_cached_times(self, date: str, prayer_times: CairoPrayerTimes) -> bool:
        """حفظ مواقيت في التخزين المؤقت"""
        try:
            now = datetime.now(CAIRO_TZ)
            expires_at = now + timedelta(hours=self.cache_duration_hours)
            
            # إنشاء إدخال جديد
            entry = CacheEntry(
                date=date,
                prayer_times=prayer_times,
                cached_at=now,
                expires_at=expires_at,
                source=prayer_times.source
            )
            
            # حفظ في الذاكرة
            self.memory_cache[date] = entry
            
            # حفظ في قاعدة البيانات
            if self.supabase_client:
                await self._save_to_database(entry)
                self.stats['db_writes'] += 1
            
            # حفظ في الملف
            await self._save_to_file()
            self.stats['file_writes'] += 1
            
            # تنظيف الذاكرة إذا تجاوزت الحد الأقصى
            if len(self.memory_cache) > self.max_entries:
                await self._cleanup_memory_cache()
            
            logger.debug(f"✅ تم حفظ مواقيت {date} في التخزين المؤقت")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في حفظ مواقيت {date}: {e}")
            return False
    
    async def get_last_valid_times(self, days_back: int = 7) -> Optional[CairoPrayerTimes]:
        """الحصول على آخر مواقيت صالحة من الأيام السابقة"""
        try:
            today = datetime.now(CAIRO_TZ).date()
            
            # البحث في الأيام السابقة
            for i in range(1, days_back + 1):
                check_date = (today - timedelta(days=i)).isoformat()
                cached_times = await self.get_cached_times(check_date)
                
                if cached_times and cached_times.is_valid():
                    logger.info(f"📦 تم العثور على مواقيت صالحة من {check_date}")
                    return cached_times
            
            logger.warning(f"⚠️ لم يتم العثور على مواقيت صالحة في آخر {days_back} أيام")
            return None
            
        except Exception as e:
            logger.error(f"❌ خطأ في البحث عن آخر مواقيت صالحة: {e}")
            return None
    
    async def _get_from_file(self, date: str) -> Optional[CacheEntry]:
        """الحصول على إدخال من الملف"""
        try:
            if not self.cache_file.exists():
                return None
            
            async with aiofiles.open(self.cache_file, 'r', encoding='utf-8') as f:
                content = await f.read()
                if not content.strip():
                    return None
                
                data = json.loads(content)
                
                if date in data:
                    return CacheEntry.from_dict(data[date])
                
                return None
                
        except Exception as e:
            logger.error(f"❌ خطأ في قراءة الملف للتاريخ {date}: {e}")
            return None
    
    async def _save_to_file(self) -> bool:
        """حفظ جميع الإدخالات في الملف"""
        try:
            # تحويل الذاكرة إلى قاموس
            data = {}
            for date, entry in self.memory_cache.items():
                if not entry.is_expired():
                    data[date] = entry.to_dict()
            
            # حفظ في الملف
            async with aiofiles.open(self.cache_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(data, indent=2, ensure_ascii=False))
            
            logger.debug(f"✅ تم حفظ {len(data)} إدخال في الملف")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في حفظ الملف: {e}")
            return False
    
    async def _load_from_file(self) -> bool:
        """تحميل البيانات من الملف"""
        try:
            if not self.cache_file.exists():
                logger.info("📁 ملف التخزين المؤقت غير موجود، سيتم إنشاؤه")
                return True
            
            async with aiofiles.open(self.cache_file, 'r', encoding='utf-8') as f:
                content = await f.read()
                if not content.strip():
                    return True
                
                data = json.loads(content)
                
                # تحميل الإدخالات الصالحة فقط
                loaded_count = 0
                for date, entry_data in data.items():
                    try:
                        entry = CacheEntry.from_dict(entry_data)
                        if not entry.is_expired():
                            self.memory_cache[date] = entry
                            loaded_count += 1
                    except Exception as e:
                        logger.warning(f"⚠️ تخطي إدخال تالف للتاريخ {date}: {e}")
                
                logger.info(f"📁 تم تحميل {loaded_count} إدخال من الملف")
                return True
                
        except Exception as e:
            logger.error(f"❌ خطأ في تحميل الملف: {e}")
            return False
    
    async def _get_from_database(self, date: str) -> Optional[CacheEntry]:
        """الحصول على إدخال من قاعدة البيانات"""
        try:
            if not self.supabase_client:
                return None
            
            result = self.supabase_client.table('prayer_times_cache').select('*').eq('date', date).execute()
            
            if result.data:
                db_data = result.data[0]
                
                # تحويل البيانات إلى CacheEntry
                prayer_times_data = db_data['prayer_times']
                prayer_times = CairoPrayerTimes.from_dict(prayer_times_data)
                
                entry = CacheEntry(
                    date=db_data['date'],
                    prayer_times=prayer_times,
                    cached_at=datetime.fromisoformat(db_data['created_at']),
                    expires_at=datetime.fromisoformat(db_data['expires_at']),
                    source=db_data['source']
                )
                
                return entry
            
            return None
            
        except Exception as e:
            logger.error(f"❌ خطأ في قراءة قاعدة البيانات للتاريخ {date}: {e}")
            return None
    
    async def _save_to_database(self, entry: CacheEntry) -> bool:
        """حفظ إدخال في قاعدة البيانات"""
        try:
            if not self.supabase_client:
                return False
            
            # تحضير البيانات
            data = {
                'date': entry.date,
                'prayer_times': entry.prayer_times.to_dict(),
                'source': entry.source,
                'created_at': entry.cached_at.isoformat(),
                'expires_at': entry.expires_at.isoformat()
            }
            
            # محاولة التحديث أولاً، ثم الإدراج
            result = self.supabase_client.table('prayer_times_cache').upsert(data).execute()
            
            if result.data:
                logger.debug(f"✅ تم حفظ مواقيت {entry.date} في قاعدة البيانات")
                return True
            else:
                logger.error(f"❌ فشل في حفظ مواقيت {entry.date} في قاعدة البيانات")
                return False
                
        except Exception as e:
            logger.error(f"❌ خطأ في حفظ قاعدة البيانات للتاريخ {entry.date}: {e}")
            return False
    
    async def _cleanup_memory_cache(self) -> None:
        """تنظيف الذاكرة من الإدخالات القديمة"""
        try:
            # إزالة الإدخالات المنتهية الصلاحية
            expired_dates = [
                date for date, entry in self.memory_cache.items()
                if entry.is_expired()
            ]
            
            for date in expired_dates:
                del self.memory_cache[date]
            
            # إذا كان العدد لا يزال كبيراً، احتفظ بالأحدث فقط
            if len(self.memory_cache) > self.max_entries:
                # ترتيب حسب تاريخ التخزين المؤقت
                sorted_entries = sorted(
                    self.memory_cache.items(),
                    key=lambda x: x[1].cached_at,
                    reverse=True
                )
                
                # الاحتفاظ بالأحدث فقط
                self.memory_cache = dict(sorted_entries[:self.max_entries])
            
            cleaned_count = len(expired_dates)
            if cleaned_count > 0:
                self.stats['entries_cleaned'] += cleaned_count
                logger.debug(f"🗑️ تم تنظيف {cleaned_count} إدخال من الذاكرة")
                
        except Exception as e:
            logger.error(f"❌ خطأ في تنظيف الذاكرة: {e}")
    
    async def cleanup_expired(self) -> int:
        """تنظيف جميع الإدخالات المنتهية الصلاحية"""
        try:
            self.stats['cleanup_runs'] += 1
            self.stats['last_cleanup'] = datetime.now().isoformat()
            
            cleaned_count = 0
            
            # تنظيف الذاكرة
            await self._cleanup_memory_cache()
            
            # تنظيف قاعدة البيانات
            if self.supabase_client:
                try:
                    now = datetime.now(CAIRO_TZ).isoformat()
                    result = self.supabase_client.table('prayer_times_cache').delete().lt('expires_at', now).execute()
                    if result.data:
                        db_cleaned = len(result.data)
                        cleaned_count += db_cleaned
                        logger.debug(f"🗑️ تم تنظيف {db_cleaned} إدخال من قاعدة البيانات")
                except Exception as e:
                    logger.error(f"❌ خطأ في تنظيف قاعدة البيانات: {e}")
            
            # حفظ الملف بعد التنظيف
            await self._save_to_file()
            
            logger.info(f"🗑️ تم تنظيف {cleaned_count} إدخال منتهي الصلاحية")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"❌ خطأ في تنظيف الإدخالات المنتهية الصلاحية: {e}")
            return 0
    
    async def _start_cleanup_task(self) -> None:
        """بدء مهمة التنظيف التلقائي"""
        try:
            async def cleanup_loop():
                while True:
                    try:
                        # انتظار فترة التنظيف
                        await asyncio.sleep(self.cleanup_interval_hours * 3600)
                        
                        # تنفيذ التنظيف
                        await self.cleanup_expired()
                        
                    except Exception as e:
                        logger.error(f"❌ خطأ في مهمة التنظيف التلقائي: {e}")
                        await asyncio.sleep(3600)  # انتظار ساعة قبل المحاولة مرة أخرى
            
            self.cleanup_task = asyncio.create_task(cleanup_loop())
            logger.info(f"✅ تم بدء مهمة التنظيف التلقائي (كل {self.cleanup_interval_hours} ساعات)")
            
        except Exception as e:
            logger.error(f"❌ فشل في بدء مهمة التنظيف التلقائي: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """الحصول على إحصائيات التخزين المؤقت"""
        try:
            # حساب معدل النجاح
            hit_rate = (
                (self.stats['cache_hits'] / self.stats['total_requests'] * 100)
                if self.stats['total_requests'] > 0 else 0
            )
            
            return {
                'cache_stats': {
                    'total_requests': self.stats['total_requests'],
                    'cache_hits': self.stats['cache_hits'],
                    'cache_misses': self.stats['cache_misses'],
                    'hit_rate_percentage': round(hit_rate, 2),
                    'memory_entries': len(self.memory_cache),
                    'max_entries': self.max_entries
                },
                'storage_stats': {
                    'file_reads': self.stats['file_reads'],
                    'file_writes': self.stats['file_writes'],
                    'db_reads': self.stats['db_reads'],
                    'db_writes': self.stats['db_writes']
                },
                'cleanup_stats': {
                    'cleanup_runs': self.stats['cleanup_runs'],
                    'entries_cleaned': self.stats['entries_cleaned'],
                    'last_cleanup': self.stats['last_cleanup'],
                    'cleanup_task_running': self.cleanup_task is not None and not self.cleanup_task.done()
                }
            }
            
        except Exception as e:
            logger.error(f"❌ خطأ في الحصول على إحصائيات التخزين المؤقت: {e}")
            return {}
    
    def get_cache_info(self) -> Dict[str, Any]:
        """الحصول على معلومات التخزين المؤقت"""
        try:
            # معلومات الإدخالات الحالية
            entries_info = []
            for date, entry in self.memory_cache.items():
                entries_info.append({
                    'date': date,
                    'source': entry.source,
                    'cached_at': entry.cached_at.isoformat(),
                    'expires_at': entry.expires_at.isoformat(),
                    'is_expired': entry.is_expired(),
                    'hours_until_expiry': (
                        (entry.expires_at - datetime.now(CAIRO_TZ)).total_seconds() / 3600
                        if not entry.is_expired() else 0
                    )
                })
            
            return {
                'cache_file': str(self.cache_file),
                'cache_duration_hours': self.cache_duration_hours,
                'entries': entries_info,
                'total_entries': len(entries_info),
                'expired_entries': len([e for e in entries_info if e['is_expired']])
            }
            
        except Exception as e:
            logger.error(f"❌ خطأ في الحصول على معلومات التخزين المؤقت: {e}")
            return {}
    
    async def clear_cache(self) -> bool:
        """مسح جميع بيانات التخزين المؤقت"""
        try:
            # مسح الذاكرة
            self.memory_cache.clear()
            
            # مسح الملف
            if self.cache_file.exists():
                self.cache_file.unlink()
            
            # مسح قاعدة البيانات
            if self.supabase_client:
                self.supabase_client.table('prayer_times_cache').delete().neq('id', 0).execute()
            
            logger.info("🗑️ تم مسح جميع بيانات التخزين المؤقت")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في مسح التخزين المؤقت: {e}")
            return False
    
    async def cleanup(self) -> None:
        """تنظيف الموارد"""
        try:
            # إيقاف مهمة التنظيف
            if self.cleanup_task and not self.cleanup_task.done():
                self.cleanup_task.cancel()
                try:
                    await self.cleanup_task
                except asyncio.CancelledError:
                    pass
            
            # حفظ البيانات الأخيرة
            await self._save_to_file()
            
            logger.info("✅ تم تنظيف نظام التخزين المؤقت")
            
        except Exception as e:
            logger.error(f"❌ خطأ في تنظيف نظام التخزين المؤقت: {e}")
    
    def __str__(self) -> str:
        return f"PrayerTimesCache(entries={len(self.memory_cache)}, hit_rate={self.stats['cache_hits']}/{self.stats['total_requests']})"
    
    def __repr__(self) -> str:
        return f"PrayerTimesCache(file={self.cache_file}, duration={self.cache_duration_hours}h, max_entries={self.max_entries})"


# Export للاستخدام في الملفات الأخرى
__all__ = ['PrayerTimesCache', 'CacheEntry']