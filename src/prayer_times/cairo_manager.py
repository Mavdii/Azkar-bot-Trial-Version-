#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🕌 Cairo Prayer Times Manager - مدير مواقيت الصلاة للقاهرة
===========================================================
مدير متخصص لجلب وإدارة مواقيت الصلاة لمدينة القاهرة بدقة عالية

Features:
- 🕌 مواقيت دقيقة لمدينة القاهرة خصيصاً
- 🔄 تحديث تلقائي يومي في منتصف الليل
- 💾 تخزين مؤقت ذكي لمدة 24 ساعة
- 🛡️ نظام fallback متقدم عند فشل APIs
- ⏰ جدولة دقيقة للورد القرآني والتذكيرات

Author: Islamic Bot Developer Team
Version: 1.0.0
License: MIT
"""

import asyncio
import logging
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Any, Tuple, Callable
import pytz
from dataclasses import dataclass, asdict
import json

# Configure logging
logger = logging.getLogger(__name__)

# Cairo timezone
CAIRO_TZ = pytz.timezone('Africa/Cairo')

@dataclass
class CairoPrayerTimes:
    """نموذج بيانات مواقيت الصلاة للقاهرة"""
    date: datetime
    fajr: datetime
    dhuhr: datetime
    asr: datetime
    maghrib: datetime
    isha: datetime
    source: str
    cached_at: datetime
    
    def get_next_prayer(self, current_time: Optional[datetime] = None) -> Optional[Tuple[str, datetime]]:
        """الحصول على الصلاة التالية ووقتها"""
        if current_time is None:
            current_time = datetime.now(CAIRO_TZ)
        
        # قائمة الصلوات مرتبة حسب الوقت
        prayers = [
            ('fajr', self.fajr),
            ('dhuhr', self.dhuhr),
            ('asr', self.asr),
            ('maghrib', self.maghrib),
            ('isha', self.isha)
        ]
        
        # البحث عن الصلاة التالية
        for prayer_name, prayer_time in prayers:
            if current_time < prayer_time:
                return prayer_name, prayer_time
        
        # إذا انتهت صلوات اليوم، فالصلاة التالية هي فجر الغد
        tomorrow_fajr = self.fajr + timedelta(days=1)
        return 'fajr', tomorrow_fajr
    
    def get_prayer_time(self, prayer_name: str) -> Optional[datetime]:
        """الحصول على وقت صلاة محددة"""
        prayer_times = {
            'fajr': self.fajr,
            'dhuhr': self.dhuhr,
            'asr': self.asr,
            'maghrib': self.maghrib,
            'isha': self.isha
        }
        return prayer_times.get(prayer_name.lower())
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'date': self.date.isoformat(),
            'fajr': self.fajr.isoformat(),
            'dhuhr': self.dhuhr.isoformat(),
            'asr': self.asr.isoformat(),
            'maghrib': self.maghrib.isoformat(),
            'isha': self.isha.isoformat(),
            'source': self.source,
            'cached_at': self.cached_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CairoPrayerTimes':
        """إنشاء من قاموس"""
        return cls(
            date=datetime.fromisoformat(data['date']),
            fajr=datetime.fromisoformat(data['fajr']),
            dhuhr=datetime.fromisoformat(data['dhuhr']),
            asr=datetime.fromisoformat(data['asr']),
            maghrib=datetime.fromisoformat(data['maghrib']),
            isha=datetime.fromisoformat(data['isha']),
            source=data['source'],
            cached_at=datetime.fromisoformat(data['cached_at'])
        )
    
    def is_valid(self) -> bool:
        """التحقق من صحة المواقيت"""
        try:
            # التحقق من ترتيب الصلوات
            prayers = [self.fajr, self.dhuhr, self.asr, self.maghrib, self.isha]
            for i in range(len(prayers) - 1):
                if prayers[i] >= prayers[i + 1]:
                    return False
            
            # التحقق من أن الأوقات في نفس اليوم
            date_check = self.date.date()
            for prayer_time in prayers:
                if prayer_time.date() != date_check:
                    return False
            
            # التحقق من أن الأوقات معقولة للقاهرة
            # الفجر يجب أن يكون بين 3:00 و 6:00
            if not (3 <= self.fajr.hour <= 6):
                return False
            
            # الظهر يجب أن يكون بين 11:00 و 14:00
            if not (11 <= self.dhuhr.hour <= 14):
                return False
            
            # العصر يجب أن يكون بين 14:00 و 18:00
            if not (14 <= self.asr.hour <= 18):
                return False
            
            # المغرب يجب أن يكون بين 17:00 و 20:00
            if not (17 <= self.maghrib.hour <= 20):
                return False
            
            # العشاء يجب أن يكون بين 19:00 و 23:00
            if not (19 <= self.isha.hour <= 23):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في التحقق من صحة المواقيت: {e}")
            return False


class CairoPrayerTimesManager:
    """مدير مواقيت الصلاة المحسن للقاهرة"""
    
    def __init__(self, api_client=None, cache_manager=None):
        self.api_client = api_client
        self.cache_manager = cache_manager
        
        # حالة المدير
        self.current_prayer_times: Optional[CairoPrayerTimes] = None
        self.last_update: Optional[datetime] = None
        self.update_task: Optional[asyncio.Task] = None
        
        # callbacks للتحديثات
        self.update_callbacks: List[Callable[[CairoPrayerTimes], None]] = []
        
        # إحصائيات
        self.stats = {
            'total_fetches': 0,
            'cache_hits': 0,
            'api_calls': 0,
            'failed_fetches': 0,
            'last_successful_fetch': None,
            'average_response_time': 0.0
        }
    
    async def initialize(self) -> bool:
        """تهيئة المدير"""
        try:
            logger.info("🔄 بدء تهيئة مدير مواقيت الصلاة للقاهرة...")
            
            # جلب مواقيت اليوم
            prayer_times = await self.get_today_prayer_times()
            if prayer_times:
                self.current_prayer_times = prayer_times
                logger.info("✅ تم جلب مواقيت اليوم بنجاح")
            else:
                logger.warning("⚠️ فشل في جلب مواقيت اليوم، سيتم المحاولة لاحقاً")
            
            # بدء التحديث التلقائي
            await self._start_daily_update_task()
            
            logger.info("✅ تم تهيئة مدير مواقيت الصلاة للقاهرة بنجاح")
            return True
            
        except Exception as e:
            logger.error(f"❌ فشل في تهيئة مدير مواقيت الصلاة: {e}")
            return False
    
    async def get_today_prayer_times(self, force_refresh: bool = False) -> Optional[CairoPrayerTimes]:
        """جلب مواقيت اليوم"""
        start_time = datetime.now()
        self.stats['total_fetches'] += 1
        
        try:
            today = datetime.now(CAIRO_TZ).date()
            
            # محاولة الحصول من التخزين المؤقت أولاً
            if not force_refresh and self.cache_manager:
                cached_times = await self.cache_manager.get_cached_times(today.isoformat())
                if cached_times:
                    self.stats['cache_hits'] += 1
                    logger.info("📦 تم جلب مواقيت اليوم من التخزين المؤقت")
                    return cached_times
            
            # جلب من API
            fresh_times = await self.fetch_fresh_prayer_times()
            if fresh_times:
                # حفظ في التخزين المؤقت
                if self.cache_manager:
                    await self.cache_manager.set_cached_times(today.isoformat(), fresh_times)
                
                # تحديث الإحصائيات
                response_time = (datetime.now() - start_time).total_seconds()
                self._update_average_response_time(response_time)
                self.stats['last_successful_fetch'] = datetime.now().isoformat()
                
                logger.info(f"✅ تم جلب مواقيت اليوم من {fresh_times.source}")
                return fresh_times
            else:
                self.stats['failed_fetches'] += 1
                logger.error("❌ فشل في جلب مواقيت اليوم")
                return None
                
        except Exception as e:
            self.stats['failed_fetches'] += 1
            logger.error(f"❌ خطأ في جلب مواقيت اليوم: {e}")
            return None
    
    async def fetch_fresh_prayer_times(self) -> Optional[CairoPrayerTimes]:
        """جلب مواقيت جديدة من API"""
        if not self.api_client:
            logger.error("❌ لا يوجد عميل API متاح")
            return None
        
        try:
            self.stats['api_calls'] += 1
            
            # جلب من API
            api_response = await self.api_client.fetch_cairo_prayer_times()
            if api_response:
                # تحويل إلى كائن CairoPrayerTimes
                prayer_times = self._convert_api_response(api_response)
                
                # التحقق من صحة البيانات
                if prayer_times and prayer_times.is_valid():
                    return prayer_times
                else:
                    logger.error("❌ مواقيت غير صحيحة من API")
                    return None
            else:
                logger.error("❌ لا توجد بيانات من API")
                return None
                
        except Exception as e:
            logger.error(f"❌ خطأ في جلب مواقيت جديدة: {e}")
            return None
    
    def _convert_api_response(self, api_response: Dict[str, Any]) -> Optional[CairoPrayerTimes]:
        """تحويل استجابة API إلى كائن CairoPrayerTimes"""
        try:
            today = datetime.now(CAIRO_TZ).date()
            
            # استخراج الأوقات وتحويلها إلى datetime
            prayer_times = {}
            for prayer_name in ['fajr', 'dhuhr', 'asr', 'maghrib', 'isha']:
                if prayer_name in api_response:
                    time_str = api_response[prayer_name]
                    if isinstance(time_str, str):
                        # تحويل من صيغة HH:MM إلى datetime
                        hour, minute = map(int, time_str.split(':'))
                        prayer_time = CAIRO_TZ.localize(
                            datetime(today.year, today.month, today.day, hour, minute)
                        )
                        prayer_times[prayer_name] = prayer_time
                    elif isinstance(time_str, datetime):
                        # إذا كان datetime بالفعل
                        prayer_times[prayer_name] = time_str
            
            # التحقق من وجود جميع الصلوات
            required_prayers = ['fajr', 'dhuhr', 'asr', 'maghrib', 'isha']
            if not all(prayer in prayer_times for prayer in required_prayers):
                logger.error("❌ بعض الصلوات مفقودة في استجابة API")
                return None
            
            # إنشاء كائن CairoPrayerTimes
            cairo_times = CairoPrayerTimes(
                date=CAIRO_TZ.localize(datetime(today.year, today.month, today.day)),
                fajr=prayer_times['fajr'],
                dhuhr=prayer_times['dhuhr'],
                asr=prayer_times['asr'],
                maghrib=prayer_times['maghrib'],
                isha=prayer_times['isha'],
                source=api_response.get('source', 'api'),
                cached_at=datetime.now(CAIRO_TZ)
            )
            
            return cairo_times
            
        except Exception as e:
            logger.error(f"❌ خطأ في تحويل استجابة API: {e}")
            return None
    
    async def get_next_prayer_info(self) -> Optional[Tuple[str, datetime]]:
        """الحصول على معلومات الصلاة التالية"""
        try:
            # التأكد من وجود مواقيت اليوم
            if not self.current_prayer_times:
                self.current_prayer_times = await self.get_today_prayer_times()
            
            if self.current_prayer_times:
                return self.current_prayer_times.get_next_prayer()
            else:
                logger.error("❌ لا توجد مواقيت متاحة للحصول على الصلاة التالية")
                return None
                
        except Exception as e:
            logger.error(f"❌ خطأ في الحصول على الصلاة التالية: {e}")
            return None
    
    async def get_prayer_time(self, prayer_name: str) -> Optional[datetime]:
        """الحصول على وقت صلاة محددة"""
        try:
            # التأكد من وجود مواقيت اليوم
            if not self.current_prayer_times:
                self.current_prayer_times = await self.get_today_prayer_times()
            
            if self.current_prayer_times:
                return self.current_prayer_times.get_prayer_time(prayer_name)
            else:
                logger.error(f"❌ لا توجد مواقيت متاحة للحصول على وقت صلاة {prayer_name}")
                return None
                
        except Exception as e:
            logger.error(f"❌ خطأ في الحصول على وقت صلاة {prayer_name}: {e}")
            return None
    
    async def schedule_daily_update(self) -> None:
        """جدولة التحديث اليومي"""
        try:
            # حساب وقت التحديث التالي (منتصف الليل)
            now = datetime.now(CAIRO_TZ)
            next_midnight = now.replace(hour=0, minute=1, second=0, microsecond=0) + timedelta(days=1)
            
            sleep_seconds = (next_midnight - now).total_seconds()
            logger.info(f"⏰ التحديث التالي للمواقيت خلال {sleep_seconds/3600:.1f} ساعة")
            
            # انتظار حتى منتصف الليل
            await asyncio.sleep(sleep_seconds)
            
            # تحديث المواقيت
            await self._perform_daily_update()
            
        except Exception as e:
            logger.error(f"❌ خطأ في جدولة التحديث اليومي: {e}")
    
    async def _perform_daily_update(self) -> None:
        """تنفيذ التحديث اليومي"""
        try:
            logger.info("🔄 بدء التحديث اليومي لمواقيت الصلاة")
            
            # جلب مواقيت جديدة
            new_times = await self.get_today_prayer_times(force_refresh=True)
            
            if new_times:
                old_times = self.current_prayer_times
                self.current_prayer_times = new_times
                self.last_update = datetime.now(CAIRO_TZ)
                
                # إشعار المستمعين بالتحديث
                await self._notify_update_callbacks(new_times, old_times)
                
                logger.info("✅ تم التحديث اليومي لمواقيت الصلاة بنجاح")
            else:
                logger.error("❌ فشل التحديث اليومي لمواقيت الصلاة")
            
            # جدولة التحديث التالي
            await self.schedule_daily_update()
            
        except Exception as e:
            logger.error(f"❌ خطأ في التحديث اليومي: {e}")
    
    async def _start_daily_update_task(self) -> None:
        """بدء مهمة التحديث اليومي"""
        try:
            if self.update_task and not self.update_task.done():
                self.update_task.cancel()
            
            self.update_task = asyncio.create_task(self.schedule_daily_update())
            logger.info("✅ تم بدء مهمة التحديث اليومي")
            
        except Exception as e:
            logger.error(f"❌ فشل في بدء مهمة التحديث اليومي: {e}")
    
    def add_update_callback(self, callback: Callable[[CairoPrayerTimes, Optional[CairoPrayerTimes]], None]) -> None:
        """إضافة callback للتحديثات"""
        self.update_callbacks.append(callback)
    
    async def _notify_update_callbacks(self, new_times: CairoPrayerTimes, old_times: Optional[CairoPrayerTimes] = None) -> None:
        """إشعار callbacks بالتحديث"""
        for callback in self.update_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(new_times, old_times)
                else:
                    callback(new_times, old_times)
            except Exception as e:
                logger.error(f"❌ خطأ في callback التحديث: {e}")
    
    def _update_average_response_time(self, response_time: float) -> None:
        """تحديث متوسط وقت الاستجابة"""
        current_avg = self.stats['average_response_time']
        total_fetches = self.stats['total_fetches']
        
        if total_fetches == 1:
            self.stats['average_response_time'] = response_time
        else:
            # حساب المتوسط المتحرك
            self.stats['average_response_time'] = (
                (current_avg * (total_fetches - 1) + response_time) / total_fetches
            )
    
    def get_statistics(self) -> Dict[str, Any]:
        """الحصول على إحصائيات المدير"""
        return {
            'manager_stats': self.stats.copy(),
            'current_prayer_times': self.current_prayer_times.to_dict() if self.current_prayer_times else None,
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'update_task_running': self.update_task is not None and not self.update_task.done()
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """الحصول على حالة صحة النظام"""
        try:
            # تحديد الحالة العامة
            if not self.current_prayer_times:
                status = "critical"
                message = "لا توجد مواقيت متاحة"
            elif self.stats['failed_fetches'] > self.stats['total_fetches'] * 0.5:
                status = "warning"
                message = "معدل فشل عالي في جلب المواقيت"
            else:
                status = "healthy"
                message = "النظام يعمل بشكل طبيعي"
            
            return {
                'status': status,
                'message': message,
                'has_current_times': self.current_prayer_times is not None,
                'last_update_hours': (
                    (datetime.now(CAIRO_TZ) - self.last_update).total_seconds() / 3600
                    if self.last_update else None
                ),
                'success_rate': (
                    (self.stats['total_fetches'] - self.stats['failed_fetches']) / self.stats['total_fetches'] * 100
                    if self.stats['total_fetches'] > 0 else 0
                ),
                'update_task_running': self.update_task is not None and not self.update_task.done()
            }
            
        except Exception as e:
            logger.error(f"❌ خطأ في الحصول على حالة الصحة: {e}")
            return {
                'status': 'error',
                'message': f'خطأ في فحص الحالة: {e}',
                'has_current_times': False,
                'last_update_hours': None,
                'success_rate': 0,
                'update_task_running': False
            }
    
    async def cleanup(self) -> None:
        """تنظيف الموارد"""
        try:
            # إيقاف مهمة التحديث
            if self.update_task and not self.update_task.done():
                self.update_task.cancel()
                try:
                    await self.update_task
                except asyncio.CancelledError:
                    pass
            
            logger.info("✅ تم تنظيف مدير مواقيت الصلاة للقاهرة")
            
        except Exception as e:
            logger.error(f"❌ خطأ في تنظيف مدير مواقيت الصلاة: {e}")
    
    def __str__(self) -> str:
        return f"CairoPrayerTimesManager(has_times={self.current_prayer_times is not None})"
    
    def __repr__(self) -> str:
        return f"CairoPrayerTimesManager(last_update={self.last_update}, stats={self.stats})"


# Export للاستخدام في الملفات الأخرى
__all__ = ['CairoPrayerTimesManager', 'CairoPrayerTimes']