#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة الجدولة للبوت الإسلامي
تتعامل مع جدولة الأذكار والورد القرآني
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Set, Dict, Any
import aiocron
import pytz

from services.dhikr_service import DhikrService
from handlers.dhikr_handler import DhikrHandler

logger = logging.getLogger(__name__)

class SchedulerService:
    """خدمة الجدولة للأذكار والورد القرآني"""
    
    def __init__(self, dhikr_handler: DhikrHandler, bot):
        self.dhikr_handler = dhikr_handler
        self.bot = bot
        self.active_groups: Set[int] = set()
        self.scheduled_jobs: Dict[str, Any] = {}
        self.cairo_tz = pytz.timezone('Africa/Cairo')
        
        # إعدادات الجدولة
        self.dhikr_interval_minutes = 5
        self.morning_time = "05:30"
        self.evening_time = "19:30"
    
    def add_active_group(self, chat_id: int):
        """إضافة مجموعة للقائمة النشطة"""
        self.active_groups.add(chat_id)
        logger.info(f"✅ تم إضافة المجموعة {chat_id} للقائمة النشطة")
    
    def remove_active_group(self, chat_id: int):
        """إزالة مجموعة من القائمة النشطة"""
        self.active_groups.discard(chat_id)
        logger.info(f"✅ تم إزالة المجموعة {chat_id} من القائمة النشطة")
    
    async def setup_dhikr_schedule(self):
        """إعداد جدولة الأذكار العشوائية"""
        try:
            # جدولة الأذكار العشوائية كل 5 دقائق
            job_name = "random_dhikr"
            if job_name in self.scheduled_jobs:
                self.scheduled_jobs[job_name].stop()
            
            self.scheduled_jobs[job_name] = aiocron.crontab(
                f'*/{self.dhikr_interval_minutes} * * * *',
                func=self._send_random_dhikr,
                start=True
            )
            
            logger.info(f"✅ تم جدولة الأذكار العشوائية كل {self.dhikr_interval_minutes} دقائق")
            
        except Exception as e:
            logger.error(f"❌ خطأ في جدولة الأذكار العشوائية: {e}")
    
    async def setup_morning_evening_schedule(self):
        """إعداد جدولة أذكار الصباح والمساء"""
        try:
            # جدولة أذكار الصباح
            morning_hour, morning_minute = map(int, self.morning_time.split(':'))
            morning_job_name = "morning_dhikr"
            if morning_job_name in self.scheduled_jobs:
                self.scheduled_jobs[morning_job_name].stop()
            
            self.scheduled_jobs[morning_job_name] = aiocron.crontab(
                f'{morning_minute} {morning_hour} * * *',
                func=self._send_morning_dhikr,
                start=True
            )
            
            # جدولة أذكار المساء
            evening_hour, evening_minute = map(int, self.evening_time.split(':'))
            evening_job_name = "evening_dhikr"
            if evening_job_name in self.scheduled_jobs:
                self.scheduled_jobs[evening_job_name].stop()
            
            self.scheduled_jobs[evening_job_name] = aiocron.crontab(
                f'{evening_minute} {evening_hour} * * *',
                func=self._send_evening_dhikr,
                start=True
            )
            
            logger.info(f"✅ تم جدولة أذكار الصباح في {self.morning_time}")
            logger.info(f"✅ تم جدولة أذكار المساء في {self.evening_time}")
            
        except Exception as e:
            logger.error(f"❌ خطأ في جدولة أذكار الصباح والمساء: {e}")
    
    async def _send_random_dhikr(self):
        """إرسال ذكر عشوائي لجميع المجموعات النشطة"""
        try:
            if not self.active_groups:
                return
            
            # الحصول على ذكر عشوائي
            dhikr = self.dhikr_handler.dhikr_service.get_random_dhikr()
            message = self.dhikr_handler.dhikr_service.format_dhikr_message(dhikr)
            keyboard = self.dhikr_handler._create_dhikr_keyboard()
            
            # إرسال للمجموعات النشطة
            groups_to_remove = set()
            for chat_id in self.active_groups.copy():
                try:
                    await self.bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        parse_mode='Markdown',
                        reply_markup=keyboard
                    )
                    await asyncio.sleep(0.5)  # تجنب الحد الأقصى للرسائل
                    
                except Exception as e:
                    error_msg = str(e).lower()
                    if any(phrase in error_msg for phrase in ['bot was blocked', 'chat not found', 'forbidden']):
                        groups_to_remove.add(chat_id)
                        logger.warning(f"⚠️ تم حظر البوت أو حذف المجموعة {chat_id}")
                    else:
                        logger.error(f"❌ خطأ في إرسال الذكر للمجموعة {chat_id}: {e}")
            
            # إزالة المجموعات المحظورة
            for chat_id in groups_to_remove:
                self.remove_active_group(chat_id)
            
            if self.active_groups:
                logger.info(f"✅ تم إرسال ذكر عشوائي لـ {len(self.active_groups)} مجموعة")
            
        except Exception as e:
            logger.error(f"❌ خطأ في إرسال الأذكار العشوائية: {e}")
    
    async def _send_morning_dhikr(self):
        """إرسال أذكار الصباح لجميع المجموعات النشطة"""
        try:
            if not self.active_groups:
                return
            
            logger.info("🌅 بدء إرسال أذكار الصباح للمجموعات النشطة")
            
            groups_to_remove = set()
            for chat_id in self.active_groups.copy():
                try:
                    success = await self.dhikr_handler.send_morning_dhikr_images(chat_id, self.bot)
                    if success:
                        await asyncio.sleep(2)  # توقف بين المجموعات
                    
                except Exception as e:
                    error_msg = str(e).lower()
                    if any(phrase in error_msg for phrase in ['bot was blocked', 'chat not found', 'forbidden']):
                        groups_to_remove.add(chat_id)
                        logger.warning(f"⚠️ تم حظر البوت أو حذف المجموعة {chat_id}")
                    else:
                        logger.error(f"❌ خطأ في إرسال أذكار الصباح للمجموعة {chat_id}: {e}")
            
            # إزالة المجموعات المحظورة
            for chat_id in groups_to_remove:
                self.remove_active_group(chat_id)
            
            if self.active_groups:
                logger.info(f"✅ تم إرسال أذكار الصباح لـ {len(self.active_groups)} مجموعة")
            
        except Exception as e:
            logger.error(f"❌ خطأ في إرسال أذكار الصباح: {e}")
    
    async def _send_evening_dhikr(self):
        """إرسال أذكار المساء لجميع المجموعات النشطة"""
        try:
            if not self.active_groups:
                return
            
            logger.info("🌆 بدء إرسال أذكار المساء للمجموعات النشطة")
            
            groups_to_remove = set()
            for chat_id in self.active_groups.copy():
                try:
                    success = await self.dhikr_handler.send_evening_dhikr_images(chat_id, self.bot)
                    if success:
                        await asyncio.sleep(2)  # توقف بين المجموعات
                    
                except Exception as e:
                    error_msg = str(e).lower()
                    if any(phrase in error_msg for phrase in ['bot was blocked', 'chat not found', 'forbidden']):
                        groups_to_remove.add(chat_id)
                        logger.warning(f"⚠️ تم حظر البوت أو حذف المجموعة {chat_id}")
                    else:
                        logger.error(f"❌ خطأ في إرسال أذكار المساء للمجموعة {chat_id}: {e}")
            
            # إزالة المجموعات المحظورة
            for chat_id in groups_to_remove:
                self.remove_active_group(chat_id)
            
            if self.active_groups:
                logger.info(f"✅ تم إرسال أذكار المساء لـ {len(self.active_groups)} مجموعة")
            
        except Exception as e:
            logger.error(f"❌ خطأ في إرسال أذكار المساء: {e}")
    
    def stop_all_jobs(self):
        """إيقاف جميع المهام المجدولة"""
        try:
            for job_name, job in self.scheduled_jobs.items():
                job.stop()
                logger.info(f"✅ تم إيقاف مهمة {job_name}")
            self.scheduled_jobs.clear()
            
        except Exception as e:
            logger.error(f"❌ خطأ في إيقاف المهام المجدولة: {e}")
    
    def get_schedule_info(self) -> Dict[str, Any]:
        """الحصول على معلومات الجدولة"""
        return {
            'active_groups': len(self.active_groups),
            'scheduled_jobs': list(self.scheduled_jobs.keys()),
            'dhikr_interval_minutes': self.dhikr_interval_minutes,
            'morning_time': self.morning_time,
            'evening_time': self.evening_time
        }