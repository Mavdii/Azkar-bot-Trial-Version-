#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🕌 Precise Quran Scheduler - مجدول الورد القرآني الدقيق
=========================================================
نظام جدولة دقيق لإرسال الورد القرآني بعد كل صلاة بـ 30 دقيقة بالضبط

Features:
- ⏰ جدولة دقيقة بعد كل صلاة بـ 30 دقيقة
- 🔄 إعادة جدولة تلقائية عند تغيير مواقيت الصلاة
- 📱 إرسال 3 صفحات قرآنية لكل مجموعة نشطة
- 🛡️ معالجة الأخطاء والمهام المفقودة
- 📊 إحصائيات مفصلة للأداء

Author: Islamic Bot Developer Team
Version: 1.0.0
License: MIT
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple, Callable
import pytz
from dataclasses import dataclass
import json

# Telegram imports
from telegram import Bot, InputMediaPhoto, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError, Forbidden, BadRequest
from telegram.constants import ParseMode

# Local imports
from .cairo_manager import CairoPrayerTimes, CairoPrayerTimesManager

# Configure logging
logger = logging.getLogger(__name__)

# Cairo timezone
CAIRO_TZ = pytz.timezone('Africa/Cairo')

@dataclass
class QuranSchedule:
    """جدولة الورد القرآني"""
    prayer_name: str
    prayer_time: datetime
    send_time: datetime
    scheduled: bool = False
    sent: bool = False
    task: Optional[asyncio.Task] = None
    
    def calculate_send_time(self, delay_minutes: int = 30) -> datetime:
        """حساب وقت الإرسال"""
        return self.prayer_time + timedelta(minutes=delay_minutes)
    
    def is_due(self, current_time: Optional[datetime] = None) -> bool:
        """التحقق من حان وقت الإرسال"""
        if current_time is None:
            current_time = datetime.now(CAIRO_TZ)
        return current_time >= self.send_time
    
    def is_overdue(self, current_time: Optional[datetime] = None, grace_minutes: int = 60) -> bool:
        """التحقق من تأخر الإرسال"""
        if current_time is None:
            current_time = datetime.now(CAIRO_TZ)
        return current_time > (self.send_time + timedelta(minutes=grace_minutes))
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'prayer_name': self.prayer_name,
            'prayer_time': self.prayer_time.isoformat(),
            'send_time': self.send_time.isoformat(),
            'scheduled': self.scheduled,
            'sent': self.sent
        }

class PreciseQuranScheduler:
    """مجدول الورد القرآني الدقيق"""
    
    def __init__(
        self,
        bot: Bot,
        prayer_manager: CairoPrayerTimesManager,
        quran_page_manager,
        page_tracker,
        delay_minutes: int = 30,
        supabase_client=None
    ):
        self.bot = bot
        self.prayer_manager = prayer_manager
        self.quran_page_manager = quran_page_manager
        self.page_tracker = page_tracker
        self.delay_minutes = delay_minutes
        self.supabase_client = supabase_client
        
        # الجدولة الحالية
        self.current_schedules: Dict[str, QuranSchedule] = {}
        
        # المجموعات النشطة
        self.active_groups: Set[int] = set()
        
        # callbacks للأحداث
        self.schedule_callbacks: List[Callable[[str, QuranSchedule], None]] = []
        self.send_callbacks: List[Callable[[str, List[int]], None]] = []
        
        # إحصائيات
        self.stats = {
            'total_schedules_created': 0,
            'total_quran_sent': 0,
            'successful_sends': 0,
            'failed_sends': 0,
            'missed_schedules': 0,
            'reschedules': 0,
            'active_groups_count': 0,
            'last_schedule_time': None,
            'last_send_time': None,
            'average_send_delay': 0.0
        }
    
    async def initialize(self) -> bool:
        """تهيئة المجدول"""
        try:
            logger.info("🔄 بدء تهيئة مجدول الورد القرآني الدقيق...")
            
            # تحميل المجموعات النشطة
            await self._load_active_groups()
            
            # إضافة callback لتحديثات مواقيت الصلاة
            self.prayer_manager.add_update_callback(self._on_prayer_times_updated)
            
            # جدولة مواقيت اليوم
            await self.schedule_today_quran()
            
            logger.info("✅ تم تهيئة مجدول الورد القرآني الدقيق بنجاح")
            return True
            
        except Exception as e:
            logger.error(f"❌ فشل في تهيئة مجدول الورد القرآني: {e}")
            return False
    
    async def _load_active_groups(self) -> None:
        """تحميل المجموعات النشطة"""
        try:
            if self.supabase_client:
                result = self.supabase_client.table('group_settings').select('chat_id').eq('quran_daily_enabled', True).execute()
                if result.data:
                    self.active_groups = {row['chat_id'] for row in result.data}
                    self.stats['active_groups_count'] = len(self.active_groups)
                    logger.info(f"✅ تم تحميل {len(self.active_groups)} مجموعة نشطة للورد القرآني")
            else:
                logger.warning("⚠️ لا توجد قاعدة بيانات متاحة لتحميل المجموعات النشطة")
                
        except Exception as e:
            logger.error(f"❌ خطأ في تحميل المجموعات النشطة: {e}")
    
    async def schedule_today_quran(self) -> bool:
        """جدولة الورد القرآني لليوم الحالي"""
        try:
            logger.info("🔄 بدء جدولة الورد القرآني لليوم...")
            
            # الحصول على مواقيت اليوم
            prayer_times = await self.prayer_manager.get_today_prayer_times()
            if not prayer_times:
                logger.error("❌ لا توجد مواقيت متاحة للجدولة")
                return False
            
            # إلغاء الجدولة السابقة
            await self._cancel_all_schedules()
            
            # جدولة كل صلاة
            prayers = ['fajr', 'dhuhr', 'asr', 'maghrib', 'isha']
            scheduled_count = 0
            
            for prayer_name in prayers:
                prayer_time = prayer_times.get_prayer_time(prayer_name)
                if prayer_time:
                    success = await self._schedule_prayer_quran(prayer_name, prayer_time)
                    if success:
                        scheduled_count += 1
            
            self.stats['total_schedules_created'] += scheduled_count
            self.stats['last_schedule_time'] = datetime.now().isoformat()
            
            logger.info(f"✅ تم جدولة الورد القرآني لـ {scheduled_count} صلاة")
            return scheduled_count > 0
            
        except Exception as e:
            logger.error(f"❌ خطأ في جدولة الورد القرآني لليوم: {e}")
            return False
    
    async def _schedule_prayer_quran(self, prayer_name: str, prayer_time: datetime) -> bool:
        """جدولة الورد القرآني لصلاة محددة"""
        try:
            # حساب وقت الإرسال
            send_time = prayer_time + timedelta(minutes=self.delay_minutes)
            
            # إنشاء جدولة
            schedule = QuranSchedule(
                prayer_name=prayer_name,
                prayer_time=prayer_time,
                send_time=send_time
            )
            
            # التحقق من أن الوقت لم يفت بعد
            now = datetime.now(CAIRO_TZ)
            if schedule.is_overdue(now):
                logger.warning(f"⚠️ وقت إرسال الورد لصلاة {prayer_name} قد فات")
                return False
            
            # إذا كان الوقت قد حان، أرسل فوراً
            if schedule.is_due(now):
                logger.info(f"⏰ وقت إرسال الورد لصلاة {prayer_name} قد حان، سيتم الإرسال فوراً")
                await self._send_quran_for_prayer(prayer_name)
                schedule.sent = True
                self.current_schedules[prayer_name] = schedule
                return True
            
            # جدولة المهمة
            delay_seconds = (send_time - now).total_seconds()
            schedule.task = asyncio.create_task(
                self._delayed_send_quran(prayer_name, delay_seconds)
            )
            schedule.scheduled = True
            
            # حفظ الجدولة
            self.current_schedules[prayer_name] = schedule
            
            # إشعار المستمعين
            await self._notify_schedule_callbacks(prayer_name, schedule)
            
            logger.info(f"✅ تم جدولة الورد القرآني لصلاة {prayer_name} في {send_time.strftime('%H:%M')}")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في جدولة الورد لصلاة {prayer_name}: {e}")
            return False
    
    async def _delayed_send_quran(self, prayer_name: str, delay_seconds: float) -> None:
        """إرسال الورد القرآني بعد تأخير محدد"""
        try:
            logger.info(f"⏰ انتظار {delay_seconds/60:.1f} دقيقة لإرسال الورد بعد صلاة {prayer_name}")
            
            # انتظار الوقت المحدد
            await asyncio.sleep(delay_seconds)
            
            # إرسال الورد القرآني
            await self._send_quran_for_prayer(prayer_name)
            
            # تحديث حالة الجدولة
            if prayer_name in self.current_schedules:
                self.current_schedules[prayer_name].sent = True
            
        except asyncio.CancelledError:
            logger.info(f"🚫 تم إلغاء جدولة الورد لصلاة {prayer_name}")
            raise
        except Exception as e:
            logger.error(f"❌ خطأ في إرسال الورد المجدول لصلاة {prayer_name}: {e}")
    
    async def _send_quran_for_prayer(self, prayer_name: str) -> None:
        """إرسال الورد القرآني لجميع المجموعات النشطة"""
        try:
            start_time = datetime.now()
            logger.info(f"🕌 بدء إرسال الورد القرآني بعد صلاة {prayer_name}")
            
            if not self.active_groups:
                logger.warning("⚠️ لا توجد مجموعات نشطة لإرسال الورد القرآني")
                return
            
            successful_sends = []
            failed_sends = []
            
            # إرسال لكل مجموعة نشطة
            for chat_id in self.active_groups.copy():
                try:
                    success = await self._send_quran_to_group(chat_id)
                    if success:
                        successful_sends.append(chat_id)
                    else:
                        failed_sends.append(chat_id)
                    
                    # تأخير قصير لتجنب rate limiting
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"❌ خطأ في إرسال الورد للمجموعة {chat_id}: {e}")
                    failed_sends.append(chat_id)
                    
                    # إزالة المجموعة إذا كان البوت محظور
                    if "bot was blocked" in str(e).lower() or "chat not found" in str(e).lower():
                        self.active_groups.discard(chat_id)
            
            # تحديث الإحصائيات
            self.stats['total_quran_sent'] += 1
            self.stats['successful_sends'] += len(successful_sends)
            self.stats['failed_sends'] += len(failed_sends)
            self.stats['last_send_time'] = datetime.now().isoformat()
            
            # حساب متوسط التأخير
            actual_delay = (datetime.now() - start_time).total_seconds()
            self._update_average_send_delay(actual_delay)
            
            # إشعار المستمعين
            await self._notify_send_callbacks(prayer_name, successful_sends)
            
            logger.info(f"✅ تم إرسال الورد القرآني بعد صلاة {prayer_name} لـ {len(successful_sends)} مجموعة")
            
            if failed_sends:
                logger.warning(f"⚠️ فشل الإرسال لـ {len(failed_sends)} مجموعة")
            
        except Exception as e:
            logger.error(f"❌ خطأ في إرسال الورد القرآني بعد صلاة {prayer_name}: {e}")
    
    async def _send_quran_to_group(self, chat_id: int) -> bool:
        """إرسال الورد القرآني لمجموعة واحدة"""
        try:
            # الحصول على الصفحة الحالية للمجموعة
            current_page = await self.page_tracker.get_current_page(chat_id)
            
            # الحصول على الصفحات التالية (3 صفحات)
            pages_to_send = await self.quran_page_manager.get_next_pages(chat_id, current_page)
            
            if not pages_to_send:
                logger.warning(f"⚠️ لا توجد صفحات متاحة للإرسال للمجموعة {chat_id}")
                return False
            
            # تحضير مجموعة الوسائط
            media_group = []
            page_numbers = []
            
            for i, page_path in enumerate(pages_to_send):
                page_num = current_page + i
                if page_num > 604:
                    page_num = ((page_num - 1) % 604) + 1
                
                page_numbers.append(page_num)
                
                with open(page_path, 'rb') as photo:
                    media_group.append(InputMediaPhoto(media=photo.read()))
            
            # إرسال مجموعة الصور
            await self.bot.send_media_group(
                chat_id=chat_id,
                media=media_group
            )
            
            # إرسال رسالة نصية مع الزر
            caption = self._format_quran_message(page_numbers)
            keyboard = self._get_quran_keyboard()
            
            await self.bot.send_message(
                chat_id=chat_id,
                text=caption,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )
            
            # تحديث الصفحة الحالية
            next_page = current_page + len(pages_to_send)
            if next_page > 604:
                # تم إكمال المصحف
                await self.page_tracker.mark_completion(chat_id)
                await self._send_completion_message(chat_id)
                next_page = ((next_page - 1) % 604) + 1
            
            await self.page_tracker.update_current_page(chat_id, next_page)
            
            logger.debug(f"✅ تم إرسال الورد القرآني للمجموعة {chat_id} - الصفحات: {page_numbers}")
            return True
            
        except Forbidden:
            logger.warning(f"⚠️ البوت محظور في المجموعة {chat_id}")
            self.active_groups.discard(chat_id)
            return False
        except BadRequest as e:
            logger.error(f"❌ خطأ في الطلب للمجموعة {chat_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ خطأ في إرسال الورد للمجموعة {chat_id}: {e}")
            return False
    
    def _format_quran_message(self, page_numbers: List[int]) -> str:
        """تنسيق رسالة الورد القرآني"""
        return "**لا تنس قراءة وردك من القرآن بعد كل صلاة**"
    
    def _get_quran_keyboard(self) -> InlineKeyboardMarkup:
        """إنشاء كيبورد الورد القرآني"""
        keyboard = [
            [InlineKeyboardButton("🎵 تلاوات قرآنية - أجر 🎵", url="https://t.me/Telawat_Quran_0")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    async def _send_completion_message(self, chat_id: int) -> None:
        """إرسال رسالة إكمال المصحف"""
        try:
            stats = await self.page_tracker.get_progress_stats(chat_id)
            completion_count = stats.get('completion_count', 1)
            
            message = f"""🎉 **مبروك! لقد أتممت قراءة المصحف الشريف** 🎉

📖 تم إنهاء 604 صفحة
🏆 هذه المرة رقم {completion_count}
⭐ جعل الله هذا العمل في ميزان حسناتك

🔄 سيبدأ الورد من جديد من الصفحة الأولى

🤲 "وَمَن يَعْمَلْ مِثْقَالَ ذَرَّةٍ خَيْرًا يَرَهُ" """
            
            await self.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"❌ خطأ في إرسال رسالة الإكمال: {e}")
    
    async def _on_prayer_times_updated(self, new_times: CairoPrayerTimes, old_times: Optional[CairoPrayerTimes] = None) -> None:
        """معالج تحديث مواقيت الصلاة"""
        try:
            logger.info("🔄 تم تحديث مواقيت الصلاة، سيتم إعادة الجدولة")
            
            # إعادة جدولة الورد القرآني
            success = await self.schedule_today_quran()
            
            if success:
                self.stats['reschedules'] += 1
                logger.info("✅ تم إعادة جدولة الورد القرآني بنجاح")
            else:
                logger.error("❌ فشل في إعادة جدولة الورد القرآني")
                
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة تحديث مواقيت الصلاة: {e}")
    
    async def _cancel_all_schedules(self) -> None:
        """إلغاء جميع الجدولات الحالية"""
        try:
            cancelled_count = 0
            
            for prayer_name, schedule in self.current_schedules.items():
                if schedule.task and not schedule.task.done():
                    schedule.task.cancel()
                    try:
                        await schedule.task
                    except asyncio.CancelledError:
                        pass
                    cancelled_count += 1
            
            self.current_schedules.clear()
            
            if cancelled_count > 0:
                logger.info(f"🚫 تم إلغاء {cancelled_count} جدولة")
                
        except Exception as e:
            logger.error(f"❌ خطأ في إلغاء الجدولات: {e}")
    
    async def send_manual_quran(self, chat_id: int) -> bool:
        """إرسال الورد القرآني يدوياً لمجموعة محددة"""
        try:
            logger.info(f"📖 إرسال الورد القرآني يدوياً للمجموعة {chat_id}")
            
            success = await self._send_quran_to_group(chat_id)
            
            if success:
                logger.info(f"✅ تم إرسال الورد القرآني يدوياً للمجموعة {chat_id}")
            else:
                logger.error(f"❌ فشل في إرسال الورد القرآني يدوياً للمجموعة {chat_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ خطأ في الإرسال اليدوي للمجموعة {chat_id}: {e}")
            return False
    
    async def add_active_group(self, chat_id: int) -> None:
        """إضافة مجموعة للقائمة النشطة"""
        self.active_groups.add(chat_id)
        self.stats['active_groups_count'] = len(self.active_groups)
        logger.info(f"✅ تم إضافة المجموعة {chat_id} للورد القرآني")
    
    async def remove_active_group(self, chat_id: int) -> None:
        """إزالة مجموعة من القائمة النشطة"""
        self.active_groups.discard(chat_id)
        self.stats['active_groups_count'] = len(self.active_groups)
        logger.info(f"✅ تم إزالة المجموعة {chat_id} من الورد القرآني")
    
    def add_schedule_callback(self, callback: Callable[[str, QuranSchedule], None]) -> None:
        """إضافة callback للجدولة"""
        self.schedule_callbacks.append(callback)
    
    def add_send_callback(self, callback: Callable[[str, List[int]], None]) -> None:
        """إضافة callback للإرسال"""
        self.send_callbacks.append(callback)
    
    async def _notify_schedule_callbacks(self, prayer_name: str, schedule: QuranSchedule) -> None:
        """إشعار callbacks الجدولة"""
        for callback in self.schedule_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(prayer_name, schedule)
                else:
                    callback(prayer_name, schedule)
            except Exception as e:
                logger.error(f"❌ خطأ في callback الجدولة: {e}")
    
    async def _notify_send_callbacks(self, prayer_name: str, successful_groups: List[int]) -> None:
        """إشعار callbacks الإرسال"""
        for callback in self.send_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(prayer_name, successful_groups)
                else:
                    callback(prayer_name, successful_groups)
            except Exception as e:
                logger.error(f"❌ خطأ في callback الإرسال: {e}")
    
    def _update_average_send_delay(self, delay: float) -> None:
        """تحديث متوسط تأخير الإرسال"""
        current_avg = self.stats['average_send_delay']
        total_sends = self.stats['total_quran_sent']
        
        if total_sends == 1:
            self.stats['average_send_delay'] = delay
        else:
            self.stats['average_send_delay'] = (
                (current_avg * (total_sends - 1) + delay) / total_sends
            )
    
    def get_current_schedules(self) -> Dict[str, Dict[str, Any]]:
        """الحصول على الجدولات الحالية"""
        return {
            prayer_name: schedule.to_dict()
            for prayer_name, schedule in self.current_schedules.items()
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """الحصول على إحصائيات المجدول"""
        return {
            'scheduler_stats': self.stats.copy(),
            'current_schedules': len(self.current_schedules),
            'active_groups': len(self.active_groups),
            'pending_schedules': len([
                s for s in self.current_schedules.values()
                if s.scheduled and not s.sent
            ])
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """الحصول على حالة صحة المجدول"""
        try:
            # حساب معدل النجاح
            total_attempts = self.stats['successful_sends'] + self.stats['failed_sends']
            success_rate = (
                (self.stats['successful_sends'] / total_attempts * 100)
                if total_attempts > 0 else 100
            )
            
            # تحديد الحالة
            if success_rate >= 90:
                status = "healthy"
                message = "المجدول يعمل بشكل ممتاز"
            elif success_rate >= 70:
                status = "warning"
                message = "المجدول يعمل مع بعض المشاكل"
            else:
                status = "critical"
                message = "المجدول يواجه مشاكل كبيرة"
            
            return {
                'status': status,
                'message': message,
                'success_rate': round(success_rate, 2),
                'active_groups': len(self.active_groups),
                'pending_schedules': len([
                    s for s in self.current_schedules.values()
                    if s.scheduled and not s.sent
                ]),
                'missed_schedules': self.stats['missed_schedules']
            }
            
        except Exception as e:
            logger.error(f"❌ خطأ في فحص حالة المجدول: {e}")
            return {
                'status': 'error',
                'message': f'خطأ في فحص الحالة: {e}',
                'success_rate': 0,
                'active_groups': 0,
                'pending_schedules': 0,
                'missed_schedules': 0
            }
    
    async def cleanup(self) -> None:
        """تنظيف الموارد"""
        try:
            # إلغاء جميع المهام المجدولة
            await self._cancel_all_schedules()
            
            logger.info("✅ تم تنظيف مجدول الورد القرآني الدقيق")
            
        except Exception as e:
            logger.error(f"❌ خطأ في تنظيف مجدول الورد القرآني: {e}")
    
    def __str__(self) -> str:
        return f"PreciseQuranScheduler(schedules={len(self.current_schedules)}, groups={len(self.active_groups)})"
    
    def __repr__(self) -> str:
        return f"PreciseQuranScheduler(delay={self.delay_minutes}min, stats={self.stats['total_quran_sent']} sent)"


# Export للاستخدام في الملفات الأخرى
__all__ = ['PreciseQuranScheduler', 'QuranSchedule']