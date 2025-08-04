#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🕌 Quran Scheduler - مجدول الورد اليومي من القرآن الكريم
=====================================================================
مجدول متقدم لإرسال صفحات القرآن الكريم في الأوقات المحددة

Features:
- ⏰ جدولة تلقائية بعد كل صلاة بـ 30 دقيقة
- 🔄 إعادة جدولة تلقائية عند إعادة التشغيل
- 📱 إرسال منسق وجميل للصفحات
- ⚙️ تكامل مع إعدادات المجموعات
- 🛡️ معالجة شاملة للأخطاء

Author: Islamic Bot Developer Team
Version: 1.0.0
License: MIT
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
import pytz
import aiocron

# Telegram imports
from telegram import Bot, InputMediaPhoto, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError, Forbidden, BadRequest
from telegram.constants import ParseMode

# Local imports
from quran_manager import QuranPageManager, PageTracker

# Configure logging
logger = logging.getLogger(__name__)

# Constants
CAIRO_TZ = pytz.timezone('Africa/Cairo')
POST_PRAYER_DELAY_MINUTES = 30

class QuranScheduler:
    """مجدول الورد اليومي من القرآن الكريم"""
    
    def __init__(self, bot: Bot, prayer_times_manager, supabase_client=None):
        self.bot = bot
        self.prayer_times = prayer_times_manager
        self.db = supabase_client
        self.delay_minutes = POST_PRAYER_DELAY_MINUTES
        self.scheduled_jobs: Dict[str, Any] = {}
        
        # Initialize managers
        self.page_manager = QuranPageManager()
        self.page_tracker = PageTracker(supabase_client)
        
        # Active groups cache
        self._active_groups: set = set()
    
    async def initialize(self) -> None:
        """تهيئة المجدول"""
        try:
            # Check available pages
            missing_pages = await self.page_manager.get_missing_pages()
            available_count = await self.page_manager.get_available_pages_count()
            
            if missing_pages:
                logger.warning(f"⚠️ يوجد {len(missing_pages)} صفحة مفقودة من أصل 604")
                if len(missing_pages) > 100:
                    logger.error("❌ عدد كبير من الصفحات مفقود، يُنصح بإضافة الصور قبل التشغيل")
            
            logger.info(f"✅ تم العثور على {available_count} صفحة من أصل 604")
            
            # Load active groups
            await self._load_active_groups()
            
            # Schedule daily quran sending
            await self.schedule_daily_quran()
            
            logger.info("✅ تم تهيئة مجدول الورد القرآني بنجاح")
            
        except Exception as e:
            logger.error(f"❌ خطأ في تهيئة مجدول الورد القرآني: {e}")
    
    async def _load_active_groups(self) -> None:
        """تحميل المجموعات النشطة"""
        if self.db:
            try:
                result = self.db.table('group_settings').select('chat_id').eq('quran_daily_enabled', True).execute()
                if result.data:
                    self._active_groups = {row['chat_id'] for row in result.data}
                    logger.info(f"✅ تم تحميل {len(self._active_groups)} مجموعة نشطة للورد القرآني")
            except Exception as e:
                logger.error(f"❌ خطأ في تحميل المجموعات النشطة: {e}")
    
    async def schedule_daily_quran(self) -> None:
        """جدولة الورد اليومي باستخدام مواقيت الصلاة الدقيقة"""
        try:
            logger.info("🔄 جدولة الورد اليومي باستخدام مواقيت الصلاة الدقيقة...")
            
            # استخدام النظام المتكامل للحصول على مواقيت دقيقة
            from prayer_times_api import get_integrated_system
            integrated_system = get_integrated_system()
            
            if integrated_system and integrated_system.is_initialized:
                # استخدام النظام المتكامل
                logger.info("✅ استخدام النظام المتكامل للجدولة")
                # النظام المتكامل سيتولى الجدولة تلقائياً
                return
            
            # Fallback: استخدام مواقيت ثابتة
            logger.warning("⚠️ استخدام مواقيت ثابتة كـ fallback")
            prayer_schedules = {
                'fajr': (4, 53),    # 4:23 + 30 minutes = 4:53
                'dhuhr': (13, 31),  # 13:01 + 30 minutes = 13:31
                'asr': (17, 8),     # 16:38 + 30 minutes = 17:08
                'maghrib': (20, 27), # 19:57 + 30 minutes = 20:27
                'isha': (21, 57)    # 21:27 + 30 minutes = 21:57
            }
            
            for prayer, (hour, minute) in prayer_schedules.items():
                # Create cron job for this prayer
                cron_time = f"{minute} {hour} * * *"
                job_name = f"quran_{prayer}"
                
                # Remove existing job if any
                if job_name in self.scheduled_jobs:
                    self.scheduled_jobs[job_name].stop()
                
                # Create new job
                self.scheduled_jobs[job_name] = aiocron.crontab(
                    cron_time,
                    func=lambda p=prayer: self._send_quran_for_prayer(p),
                    start=True
                )
                
                logger.info(f"✅ تم جدولة الورد القرآني بعد صلاة {prayer} في {hour:02d}:{minute:02d}")
            
        except Exception as e:
            logger.error(f"❌ خطأ في جدولة الورد اليومي: {e}")
    
    async def calculate_next_send_time(self, prayer_name: str) -> Optional[datetime]:
        """حساب وقت الإرسال التالي"""
        try:
            # Get today's prayer times
            if hasattr(self.prayer_times, 'fetch_cairo_prayer_times'):
                prayer_times = await self.prayer_times.fetch_cairo_prayer_times()
            else:
                # Fallback to static times if dynamic not available
                prayer_times = {
                    'fajr': datetime.now(CAIRO_TZ).replace(hour=4, minute=23, second=0, microsecond=0),
                    'dhuhr': datetime.now(CAIRO_TZ).replace(hour=13, minute=1, second=0, microsecond=0),
                    'asr': datetime.now(CAIRO_TZ).replace(hour=16, minute=38, second=0, microsecond=0),
                    'maghrib': datetime.now(CAIRO_TZ).replace(hour=19, minute=57, second=0, microsecond=0),
                    'isha': datetime.now(CAIRO_TZ).replace(hour=21, minute=27, second=0, microsecond=0)
                }
            
            if prayer_name in prayer_times:
                prayer_time = prayer_times[prayer_name]
                send_time = prayer_time + timedelta(minutes=self.delay_minutes)
                return send_time
            
        except Exception as e:
            logger.error(f"❌ خطأ في حساب وقت الإرسال لصلاة {prayer_name}: {e}")
        
        return None
    
    async def _send_quran_for_prayer(self, prayer_name: str) -> None:
        """إرسال الورد القرآني بعد صلاة معينة"""
        try:
            logger.info(f"🕌 بدء إرسال الورد القرآني بعد صلاة {prayer_name}")
            
            # Get active groups
            await self._load_active_groups()
            
            if not self._active_groups:
                logger.info("ℹ️ لا توجد مجموعات نشطة للورد القرآني")
                return
            
            # Send to each active group
            for chat_id in self._active_groups.copy():  # Use copy to avoid modification during iteration
                try:
                    await self.send_quran_pages(chat_id)
                    await asyncio.sleep(1)  # Rate limiting
                except Exception as e:
                    logger.error(f"❌ خطأ في إرسال الورد للمجموعة {chat_id}: {e}")
                    if "bot was blocked" in str(e).lower() or "chat not found" in str(e).lower():
                        self._active_groups.discard(chat_id)
            
            logger.info(f"✅ تم إرسال الورد القرآني بعد صلاة {prayer_name} لـ {len(self._active_groups)} مجموعة")
            
        except Exception as e:
            logger.error(f"❌ خطأ في إرسال الورد القرآني بعد صلاة {prayer_name}: {e}")
    
    async def send_quran_pages(self, chat_id: int) -> bool:
        """إرسال صفحات القرآن لمجموعة معينة في رسالة واحدة"""
        try:
            # Get current page for this group
            current_page = await self.page_tracker.get_current_page(chat_id)
            
            # Get next pages to send
            pages_to_send = await self.page_manager.get_next_pages(chat_id, current_page)
            
            if not pages_to_send:
                logger.warning(f"⚠️ لا توجد صفحات متاحة للإرسال للمجموعة {chat_id}")
                return False
            
            # Prepare media group with all 3 pages
            media_group = []
            page_numbers = []
            
            for i, page_path in enumerate(pages_to_send):
                page_num = current_page + i
                if page_num > 604:
                    page_num = ((page_num - 1) % 604) + 1
                
                page_numbers.append(page_num)
                
                with open(page_path, 'rb') as photo:
                    media_group.append(InputMediaPhoto(media=photo.read()))
            
            # Send media group first (without caption)
            await self.bot.send_media_group(
                chat_id=chat_id,
                media=media_group
            )
            
            # Send the text message with button immediately after
            caption = await self._format_quran_message(page_numbers, chat_id)
            keyboard = self._get_quran_keyboard()
            
            await self.bot.send_message(
                chat_id=chat_id,
                text=caption,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )
            
            # Update current page
            next_page = current_page + len(pages_to_send)
            if next_page > 604:
                # Completed the Quran
                await self.page_tracker.mark_completion(chat_id)
                await self._send_completion_message(chat_id)
                next_page = ((next_page - 1) % 604) + 1
            
            await self.page_tracker.update_current_page(chat_id, next_page)
            
            logger.info(f"✅ تم إرسال الورد القرآني للمجموعة {chat_id} - الصفحات: {page_numbers}")
            return True
            
        except Forbidden:
            logger.warning(f"⚠️ البوت محظور في المجموعة {chat_id}")
            self._active_groups.discard(chat_id)
            return False
        except BadRequest as e:
            logger.error(f"❌ خطأ في الطلب للمجموعة {chat_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ خطأ في إرسال الورد القرآني للمجموعة {chat_id}: {e}")
            return False
    
    async def _format_quran_message(self, page_numbers: List[int], chat_id: int) -> str:
        """تنسيق رسالة الورد القرآني"""
        try:
            message = "**لا تنس قراءة وردك من القرآن بعد كل صلاة**"
            return message
            
        except Exception as e:
            logger.error(f"❌ خطأ في تنسيق رسالة الورد القرآني: {e}")
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
    
    async def add_active_group(self, chat_id: int) -> None:
        """إضافة مجموعة للقائمة النشطة"""
        self._active_groups.add(chat_id)
        logger.info(f"✅ تم إضافة المجموعة {chat_id} للورد القرآني")
    
    async def remove_active_group(self, chat_id: int) -> None:
        """إزالة مجموعة من القائمة النشطة"""
        self._active_groups.discard(chat_id)
        logger.info(f"✅ تم إزالة المجموعة {chat_id} من الورد القرآني")
    
    async def send_manual_quran(self, chat_id: int) -> bool:
        """إرسال الورد القرآني يدوياً"""
        return await self.send_quran_pages(chat_id)
    
    def stop_all_jobs(self) -> None:
        """إيقاف جميع المهام المجدولة"""
        for job_name, job in self.scheduled_jobs.items():
            job.stop()
            logger.info(f"✅ تم إيقاف مهمة {job_name}")
        self.scheduled_jobs.clear()


# Export class for use in main bot
__all__ = ['QuranScheduler']