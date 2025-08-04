#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🕌 Prayer Reminders System - نظام تذكيرات الصلاة
==================================================
نظام متقدم لتذكيرات الصلاة مع إنذارات قبل الوقت وتذكيرات دقيقة

Features:
- ⏰ تنبيهات قبل الصلاة بـ 5 دقائق
- 🕌 تذكيرات دقيقة عند حلول وقت الصلاة
- 📱 رسائل مخصصة لكل صلاة
- 🔄 إعادة جدولة تلقائية عند تغيير المواقيت
- 📊 إحصائيات مفصلة للتذكيرات

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
from enum import Enum

# Telegram imports
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError, Forbidden, BadRequest
from telegram.constants import ParseMode

# Local imports
from .cairo_manager import CairoPrayerTimes, CairoPrayerTimesManager
from .active_groups_manager import ActiveGroupsManager
from .error_handler import PrayerTimesErrorHandler, ErrorCategory, ErrorSeverity, error_handler_decorator

# Configure logging
logger = logging.getLogger(__name__)

# Cairo timezone
CAIRO_TZ = pytz.timezone('Africa/Cairo')

class ReminderType(Enum):
    """نوع التذكير"""
    ALERT = "alert"  # تنبيه قبل الصلاة
    REMINDER = "reminder"  # تذكير عند الصلاة

@dataclass
class PrayerReminder:
    """تذكير صلاة"""
    prayer_name: str
    prayer_time: datetime
    reminder_type: ReminderType
    send_time: datetime
    scheduled: bool = False
    sent: bool = False
    task: Optional[asyncio.Task] = None
    
    def is_due(self, current_time: Optional[datetime] = None) -> bool:
        """التحقق من حان وقت الإرسال"""
        if current_time is None:
            current_time = datetime.now(CAIRO_TZ)
        return current_time >= self.send_time
    
    def is_overdue(self, current_time: Optional[datetime] = None, grace_minutes: int = 30) -> bool:
        """التحقق من تأخر الإرسال"""
        if current_time is None:
            current_time = datetime.now(CAIRO_TZ)
        return current_time > (self.send_time + timedelta(minutes=grace_minutes))
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'prayer_name': self.prayer_name,
            'prayer_time': self.prayer_time.isoformat(),
            'reminder_type': self.reminder_type.value,
            'send_time': self.send_time.isoformat(),
            'scheduled': self.scheduled,
            'sent': self.sent
        }


class PrayerRemindersSystem:
    """نظام تذكيرات الصلاة"""
    
    def __init__(
        self,
        bot: Bot,
        prayer_manager: CairoPrayerTimesManager,
        groups_manager: ActiveGroupsManager,
        error_handler: PrayerTimesErrorHandler,
        alert_minutes_before: int = 5
    ):
        self.bot = bot
        self.prayer_manager = prayer_manager
        self.groups_manager = groups_manager
        self.error_handler = error_handler
        self.alert_minutes_before = alert_minutes_before
        
        # التذكيرات المجدولة
        self.scheduled_reminders: Dict[str, List[PrayerReminder]] = {}
        
        # إحصائيات
        self.stats = {
            'total_reminders_scheduled': 0,
            'total_alerts_sent': 0,
            'total_reminders_sent': 0,
            'successful_sends': 0,
            'failed_sends': 0,
            'last_schedule_time': None,
            'last_send_time': None,
            'groups_reached': 0
        }
    
    async def initialize(self) -> bool:
        """تهيئة نظام التذكيرات"""
        try:
            logger.info("🔄 بدء تهيئة نظام تذكيرات الصلاة...")
            
            # إضافة callback لتحديثات مواقيت الصلاة
            self.prayer_manager.add_update_callback(self._on_prayer_times_updated)
            
            # جدولة تذكيرات اليوم
            await self.schedule_today_reminders()
            
            logger.info("✅ تم تهيئة نظام تذكيرات الصلاة بنجاح")
            return True
            
        except Exception as e:
            await self.error_handler.handle_error(
                e, ErrorCategory.SYSTEM_ERROR, ErrorSeverity.HIGH,
                {'component': 'PrayerRemindersSystem', 'method': 'initialize'}
            )
            return False    
    @
error_handler_decorator(ErrorCategory.SCHEDULING_ERROR, ErrorSeverity.MEDIUM, fallback_return=False)
    async def schedule_today_reminders(self) -> bool:
        """جدولة تذكيرات اليوم"""
        logger.info("🔄 بدء جدولة تذكيرات الصلاة لليوم...")
        
        # الحصول على مواقيت اليوم
        prayer_times = await self.prayer_manager.get_today_prayer_times()
        if not prayer_times:
            logger.error("❌ لا توجد مواقيت متاحة للجدولة")
            return False
        
        # إلغاء الجدولة السابقة
        await self._cancel_all_reminders()
        
        # جدولة كل صلاة
        prayers = ['fajr', 'dhuhr', 'asr', 'maghrib', 'isha']
        scheduled_count = 0
        
        for prayer_name in prayers:
            prayer_time = prayer_times.get_prayer_time(prayer_name)
            if prayer_time:
                # جدولة التنبيه (5 دقائق قبل الصلاة)
                alert_success = await self._schedule_prayer_alert(prayer_name, prayer_time)
                
                # جدولة التذكير (عند وقت الصلاة)
                reminder_success = await self._schedule_prayer_reminder(prayer_name, prayer_time)
                
                if alert_success or reminder_success:
                    scheduled_count += 1
        
        self.stats['total_reminders_scheduled'] += scheduled_count * 2  # تنبيه + تذكير
        self.stats['last_schedule_time'] = datetime.now().isoformat()
        
        logger.info(f"✅ تم جدولة تذكيرات {scheduled_count} صلاة")
        return scheduled_count > 0
    
    @error_handler_decorator(ErrorCategory.SCHEDULING_ERROR, ErrorSeverity.MEDIUM, fallback_return=False)
    async def _schedule_prayer_alert(self, prayer_name: str, prayer_time: datetime) -> bool:
        """جدولة تنبيه الصلاة (5 دقائق قبل الوقت)"""
        alert_time = prayer_time - timedelta(minutes=self.alert_minutes_before)
        
        # إنشاء تذكير التنبيه
        alert_reminder = PrayerReminder(
            prayer_name=prayer_name,
            prayer_time=prayer_time,
            reminder_type=ReminderType.ALERT,
            send_time=alert_time
        )
        
        return await self._schedule_reminder(alert_reminder)
    
    @error_handler_decorator(ErrorCategory.SCHEDULING_ERROR, ErrorSeverity.MEDIUM, fallback_return=False)
    async def _schedule_prayer_reminder(self, prayer_name: str, prayer_time: datetime) -> bool:
        """جدولة تذكير الصلاة (عند الوقت)"""
        # إنشاء تذكير الصلاة
        prayer_reminder = PrayerReminder(
            prayer_name=prayer_name,
            prayer_time=prayer_time,
            reminder_type=ReminderType.REMINDER,
            send_time=prayer_time
        )
        
        return await self._schedule_reminder(prayer_reminder)
    
    async def _schedule_reminder(self, reminder: PrayerReminder) -> bool:
        """جدولة تذكير محدد"""
        try:
            now = datetime.now(CAIRO_TZ)
            
            # التحقق من أن الوقت لم يفت بعد
            if reminder.is_overdue(now):
                logger.warning(f"⚠️ وقت {reminder.reminder_type.value} لصلاة {reminder.prayer_name} قد فات")
                return False
            
            # إذا كان الوقت قد حان، أرسل فوراً
            if reminder.is_due(now):
                logger.info(f"⏰ وقت {reminder.reminder_type.value} لصلاة {reminder.prayer_name} قد حان، سيتم الإرسال فوراً")
                await self._send_reminder(reminder)
                reminder.sent = True
                self._add_reminder_to_schedule(reminder)
                return True
            
            # جدولة المهمة
            delay_seconds = (reminder.send_time - now).total_seconds()
            reminder.task = asyncio.create_task(
                self._delayed_send_reminder(reminder, delay_seconds)
            )
            reminder.scheduled = True
            
            # حفظ في الجدولة
            self._add_reminder_to_schedule(reminder)
            
            reminder_type_ar = "تنبيه" if reminder.reminder_type == ReminderType.ALERT else "تذكير"
            logger.info(f"✅ تم جدولة {reminder_type_ar} صلاة {reminder.prayer_name} في {reminder.send_time.strftime('%H:%M')}")
            return True
            
        except Exception as e:
            await self.error_handler.handle_error(
                e, ErrorCategory.SCHEDULING_ERROR, ErrorSeverity.MEDIUM,
                {'prayer': reminder.prayer_name, 'type': reminder.reminder_type.value}
            )
            return False
    
    def _add_reminder_to_schedule(self, reminder: PrayerReminder) -> None:
        """إضافة تذكير للجدولة"""
        if reminder.prayer_name not in self.scheduled_reminders:
            self.scheduled_reminders[reminder.prayer_name] = []
        self.scheduled_reminders[reminder.prayer_name].append(reminder)
    
    async def _delayed_send_reminder(self, reminder: PrayerReminder, delay_seconds: float) -> None:
        """إرسال تذكير بعد تأخير محدد"""
        try:
            reminder_type_ar = "تنبيه" if reminder.reminder_type == ReminderType.ALERT else "تذكير"
            logger.info(f"⏰ انتظار {delay_seconds/60:.1f} دقيقة لإرسال {reminder_type_ar} صلاة {reminder.prayer_name}")
            
            # انتظار الوقت المحدد
            await asyncio.sleep(delay_seconds)
            
            # إرسال التذكير
            await self._send_reminder(reminder)
            
            # تحديث حالة التذكير
            reminder.sent = True
            
        except asyncio.CancelledError:
            logger.info(f"🚫 تم إلغاء {reminder.reminder_type.value} صلاة {reminder.prayer_name}")
            raise
        except Exception as e:
            await self.error_handler.handle_error(
                e, ErrorCategory.SCHEDULING_ERROR, ErrorSeverity.MEDIUM,
                {'prayer': reminder.prayer_name, 'type': reminder.reminder_type.value}
            )
    
    @error_handler_decorator(ErrorCategory.SYSTEM_ERROR, ErrorSeverity.MEDIUM)
    async def _send_reminder(self, reminder: PrayerReminder) -> None:
        """إرسال تذكير لجميع المجموعات النشطة"""
        start_time = datetime.now()
        reminder_type_ar = "تنبيه" if reminder.reminder_type == ReminderType.ALERT else "تذكير"
        
        logger.info(f"🕌 بدء إرسال {reminder_type_ar} صلاة {reminder.prayer_name}")
        
        # الحصول على المجموعات التي لديها تذكيرات الصلاة مفعلة
        active_groups = await self._get_reminder_enabled_groups()
        
        if not active_groups:
            logger.warning("⚠️ لا توجد مجموعات مفعلة لتذكيرات الصلاة")
            return
        
        successful_sends = []
        failed_sends = []
        
        # إرسال لكل مجموعة
        for chat_id in active_groups:
            try:
                success = await self._send_reminder_to_group(chat_id, reminder)
                if success:
                    successful_sends.append(chat_id)
                else:
                    failed_sends.append(chat_id)
                
                # تأخير قصير لتجنب rate limiting
                await asyncio.sleep(0.3)
                
            except Exception as e:
                await self.error_handler.handle_error(
                    e, ErrorCategory.NETWORK_ERROR, ErrorSeverity.LOW,
                    {'chat_id': chat_id, 'prayer': reminder.prayer_name, 'type': reminder.reminder_type.value}
                )
                failed_sends.append(chat_id)
        
        # تحديث الإحصائيات
        if reminder.reminder_type == ReminderType.ALERT:
            self.stats['total_alerts_sent'] += 1
        else:
            self.stats['total_reminders_sent'] += 1
        
        self.stats['successful_sends'] += len(successful_sends)
        self.stats['failed_sends'] += len(failed_sends)
        self.stats['groups_reached'] = len(successful_sends)
        self.stats['last_send_time'] = datetime.now().isoformat()
        
        logger.info(f"✅ تم إرسال {reminder_type_ar} صلاة {reminder.prayer_name} لـ {len(successful_sends)} مجموعة")
        
        if failed_sends:
            logger.warning(f"⚠️ فشل الإرسال لـ {len(failed_sends)} مجموعة")
    
    async def _get_reminder_enabled_groups(self) -> Set[int]:
        """الحصول على المجموعات التي لديها تذكيرات الصلاة مفعلة"""
        try:
            all_groups = await self.groups_manager.load_active_groups()
            reminder_enabled_groups = set()
            
            for chat_id in all_groups:
                settings = await self.groups_manager.get_group_settings(chat_id)
                if settings.prayer_reminders_enabled:
                    reminder_enabled_groups.add(chat_id)
            
            return reminder_enabled_groups
            
        except Exception as e:
            await self.error_handler.handle_error(
                e, ErrorCategory.DATABASE_ERROR, ErrorSeverity.MEDIUM,
                {'component': 'get_reminder_enabled_groups'}
            )
            return set()
    
    @error_handler_decorator(ErrorCategory.NETWORK_ERROR, ErrorSeverity.LOW, fallback_return=False)
    async def _send_reminder_to_group(self, chat_id: int, reminder: PrayerReminder) -> bool:
        """إرسال تذكير لمجموعة واحدة"""
        # تنسيق الرسالة
        if reminder.reminder_type == ReminderType.ALERT:
            message = self._format_prayer_alert(reminder.prayer_name)
        else:
            message = self._format_prayer_reminder(reminder.prayer_name)
        
        # إنشاء الكيبورد
        keyboard = self._get_prayer_keyboard()
        
        # إرسال الرسالة
        await self.bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )
        
        return True
    
    def _format_prayer_alert(self, prayer_name: str) -> str:
        """تنسيق رسالة تنبيه الصلاة (5 دقائق قبل الوقت)"""
        messages = {
            'fajr': """🌅 **يا جماعة الخير** 🌅

⏰ **باقي 5 دقايق على صلاة الفجر** ⏰

🌟 _يلا بقى قوموا من النوم.. ده وقت الفجر جاي_
💫 _الدنيا لسه بدري والملايكة بتدعيلكم_
🤲 _اللي يصلي الفجر في وقته ربنا يحفظه طول اليوم_

**يا رب اصحينا على طاعتك واجعلنا من أهل الفجر**

⏰ **استعدوا.. الفجر على الأبواب** ⏰""",

            'dhuhr': """☀️ **يا أهل الخير** ☀️

⏰ **باقي 5 دقايق على صلاة الظهر** ⏰

🏢 _سيبوا الشغل شوية وفكروا في ربنا_
🌟 _وسط زحمة اليوم ده وقت تاخدوا فيه نفس_
💫 _الصلاة دي هتريحكم من تعب النهار_

🤲 **يا رب اجعل صلاتنا راحة لقلوبنا**

⏰ **جهزوا نفسكم.. الظهر قرب** ⏰""",

            'asr': """🌤️ **يا حبايب** 🌤️

⏰ **باقي 5 دقايق على صلاة العصر** ⏰

⚠️ _دي الصلاة اللي ربنا حذرنا منها.. ماتفوتوهاش_
🌟 _اللي يفوت العصر كإنه خسر كل حاجة_
💫 _النهار بيخلص والأعمال بتتحاسب_

🤲 **يا رب لا تجعلنا من الغافلين**

⏰ **بسرعة.. العصر مايستناش** ⏰""",

            'maghrib': """🌅 **يا أحباب الله** 🌅

⏰ **باقي 5 دقايق على صلاة المغرب** ⏰

🌇 _الشمس بتغرب والدعوة مستجابة_
🌟 _ده وقت الدعاء اللي ربنا بيسمعه_
💫 _اطلبوا من ربنا كل اللي في قلوبكم_

🤲 **يا رب استجب دعاءنا في الوقت ده**

⏰ **يلا بينا.. المغرب على الأبواب** ⏰""",

            'isha': """🌙 **يا أهلنا الغاليين** 🌙

⏰ **باقي 5 دقايق على صلاة العشاء** ⏰

🌃 _اليوم بيخلص وعايزين نختمه بالصلاة_
🌟 _دي آخر صلاة في اليوم.. خلوها حلوة_
💫 _اللي يصلي العشاء في جماعة كإنه قام نص الليل_

🤲 **يا رب اختم يومنا بالخير والطاعة**

⏰ **استعدوا.. العشاء جاي** ⏰"""
        }
        
        return messages.get(prayer_name, f"🕌 **باقي 5 دقايق على صلاة {prayer_name}** 🕌")
    
    def _format_prayer_reminder(self, prayer_name: str) -> str:
        """تنسيق رسالة تذكير الصلاة (عند الوقت)"""
        messages = {
            'fajr': """🌅 **بسم الله الرحمن الرحيم** 🌅

✨ **حان الآن موعد صلاة الفجر** ✨

🕌 _استيقظوا يا أحباب الله، فقد أشرق نور الفجر_
🌟 _هذا وقت تتنزل فيه الرحمات والبركات_
💫 _من صلى الفجر في جماعة فكأنما قام الليل كله_

🤲 **اللهم بارك لنا في صلاتنا واجعلنا من المحافظين عليها**

⏰ **الآن وقت صلاة الفجر** ⏰""",

            'dhuhr': """☀️ **بسم الله الرحمن الرحيم** ☀️

✨ **حان الآن موعد صلاة الظهر** ✨

🕌 _توقفوا عن أعمالكم وتوجهوا إلى الله_
🌟 _هذا وقت في وسط النهار للقاء مع الخالق_
💫 _الصلاة خير من العمل، والذكر خير من المال_

🤲 **اللهم اجعل صلاتنا نوراً وبرهاناً وشفاعة**

⏰ **الآن وقت صلاة الظهر** ⏰""",

            'asr': """🌤️ **بسم الله الرحمن الرحيم** 🌤️

✨ **حان الآن موعد صلاة العصر** ✨

🕌 _هذا هو الوقت الأوسط، الصلاة الوسطى_
🌟 _من فاتته صلاة العصر فكأنما وتر أهله وماله_
💫 _بادروا إلى الصلاة قبل انشغال آخر النهار_

🤲 **اللهم أعنا على ذكرك وشكرك وحسن عبادتك**

⏰ **الآن وقت صلاة العصر** ⏰""",

            'maghrib': """🌅 **بسم الله الرحمن الرحيم** 🌅

✨ **حان الآن موعد صلاة المغرب** ✨

🕌 _مع غروب الشمس، يحين وقت لقاء مع الله_
🌟 _هذا وقت استجابة الدعاء، فأكثروا من الدعاء_
💫 _بين المغرب والعشاء ساعة مستجابة_

⏰ **الآن وقت صلاة المغرب** ⏰""",

            'isha': """🌙 **بسم الله الرحمن الرحيم** 🌙

✨ **حان الآن موعد صلاة العشاء** ✨

🕌 _مع دخول الليل، اختتموا يومكم بالصلاة_
🌟 _من صلى العشاء في جماعة فكأنما قام نصف الليل_
💫 _هذا وقت السكينة والطمأنينة مع الله_

🤲 **اللهم اجعل خير أعمالنا خواتيمها وخير أيامنا يوم نلقاك**

⏰ **الآن وقت صلاة العشاء** ⏰"""
        }
        
        return messages.get(prayer_name, f"🕌 **حان وقت صلاة {prayer_name}** 🕌")
    
    def _get_prayer_keyboard(self) -> InlineKeyboardMarkup:
        """إنشاء كيبورد تذكيرات الصلاة"""
        keyboard = [
            [InlineKeyboardButton("🎵 تلاوات قرآنية - أجر 🎵", url="https://t.me/Telawat_Quran_0")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    async def _on_prayer_times_updated(self, new_times: CairoPrayerTimes, old_times: Optional[CairoPrayerTimes] = None) -> None:
        """معالج تحديث مواقيت الصلاة"""
        try:
            logger.info("🔄 تم تحديث مواقيت الصلاة، سيتم إعادة جدولة التذكيرات")
            
            # إعادة جدولة التذكيرات
            success = await self.schedule_today_reminders()
            
            if success:
                logger.info("✅ تم إعادة جدولة تذكيرات الصلاة بنجاح")
            else:
                logger.error("❌ فشل في إعادة جدولة تذكيرات الصلاة")
                
        except Exception as e:
            await self.error_handler.handle_error(
                e, ErrorCategory.SCHEDULING_ERROR, ErrorSeverity.HIGH,
                {'component': 'prayer_times_updated_callback'}
            )
    
    async def _cancel_all_reminders(self) -> None:
        """إلغاء جميع التذكيرات المجدولة"""
        try:
            cancelled_count = 0
            
            for prayer_name, reminders in self.scheduled_reminders.items():
                for reminder in reminders:
                    if reminder.task and not reminder.task.done():
                        reminder.task.cancel()
                        try:
                            await reminder.task
                        except asyncio.CancelledError:
                            pass
                        cancelled_count += 1
            
            self.scheduled_reminders.clear()
            
            if cancelled_count > 0:
                logger.info(f"🚫 تم إلغاء {cancelled_count} تذكير")
                
        except Exception as e:
            await self.error_handler.handle_error(
                e, ErrorCategory.SYSTEM_ERROR, ErrorSeverity.MEDIUM,
                {'component': 'cancel_all_reminders'}
            )
    
    def get_current_reminders(self) -> Dict[str, List[Dict[str, Any]]]:
        """الحصول على التذكيرات المجدولة حالياً"""
        return {
            prayer_name: [reminder.to_dict() for reminder in reminders]
            for prayer_name, reminders in self.scheduled_reminders.items()
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """الحصول على إحصائيات التذكيرات"""
        return {
            'reminder_stats': self.stats.copy(),
            'scheduled_reminders_count': sum(len(reminders) for reminders in self.scheduled_reminders.values()),
            'pending_reminders': sum(
                len([r for r in reminders if r.scheduled and not r.sent])
                for reminders in self.scheduled_reminders.values()
            )
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """الحصول على حالة صحة نظام التذكيرات"""
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
                message = "نظام التذكيرات يعمل بشكل ممتاز"
            elif success_rate >= 70:
                status = "warning"
                message = "نظام التذكيرات يعمل مع بعض المشاكل"
            else:
                status = "critical"
                message = "نظام التذكيرات يواجه مشاكل كبيرة"
            
            return {
                'status': status,
                'message': message,
                'success_rate': round(success_rate, 2),
                'scheduled_reminders': sum(len(reminders) for reminders in self.scheduled_reminders.values()),
                'groups_reached': self.stats['groups_reached']
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'خطأ في فحص الحالة: {e}',
                'success_rate': 0,
                'scheduled_reminders': 0,
                'groups_reached': 0
            }
    
    async def cleanup(self) -> None:
        """تنظيف الموارد"""
        try:
            # إلغاء جميع التذكيرات المجدولة
            await self._cancel_all_reminders()
            
            logger.info("✅ تم تنظيف نظام تذكيرات الصلاة")
            
        except Exception as e:
            await self.error_handler.handle_error(
                e, ErrorCategory.SYSTEM_ERROR, ErrorSeverity.MEDIUM,
                {'component': 'cleanup'}
            )
    
    def __str__(self) -> str:
        total_reminders = sum(len(reminders) for reminders in self.scheduled_reminders.values())
        return f"PrayerRemindersSystem(reminders={total_reminders}, groups={self.stats['groups_reached']})"
    
    def __repr__(self) -> str:
        return f"PrayerRemindersSystem(alert_minutes={self.alert_minutes_before}, stats={self.stats['total_reminders_sent']} sent)"


# Export للاستخدام في الملفات الأخرى
__all__ = ['PrayerRemindersSystem', 'PrayerReminder', 'ReminderType']