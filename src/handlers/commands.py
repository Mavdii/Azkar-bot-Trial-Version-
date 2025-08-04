#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
معالجات الأوامر الأساسية للبوت الإسلامي
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

logger = logging.getLogger(__name__)

class CommandsHandler:
    """معالج الأوامر الأساسية"""
    
    def __init__(self, scheduler_service=None):
        self.scheduler_service = scheduler_service
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """معالج أمر /start"""
        try:
            chat_id = update.effective_chat.id
            user = update.effective_user
            
            # إضافة المجموعة للقائمة النشطة إذا كانت مجموعة
            if update.effective_chat.type in ['group', 'supergroup']:
                if self.scheduler_service:
                    self.scheduler_service.add_active_group(chat_id)
            
            welcome_message = f"""🕌 **أهلاً وسهلاً بك في البوت الإسلامي الشامل** 🕌

🌟 **المميزات المتاحة:**
• 📿 أذكار عشوائية كل 5 دقائق
• 🌅 أذكار الصباح كصور في 5:30 ص
• 🌆 أذكار المساء كصور في 7:30 م
• 📖 ورد يومي من القرآن الكريم
• 🕐 تذكير بأوقات الصلاة

🎯 **الأوامر المتاحة:**
/dhikr - ذكر عشوائي
/morning - أذكار الصباح (صور)
/evening - أذكار المساء (صور)
/quran_progress - تقدم الورد القرآني
/quran_manual - إرسال الورد يدوياً
/help - المساعدة

📱 **ملاحظة مهمة:**
• أذكار الصباح والمساء ترسل كصور
• ضع الصور في المجلدات المخصصة لها

🤲 **بارك الله فيك وجعل هذا العمل في ميزان حسناتك**"""

            await update.message.reply_text(
                welcome_message,
                parse_mode=ParseMode.MARKDOWN
            )
            
            logger.info(f"✅ تم إرسال رسالة الترحيب للمستخدم {user.id if user else 'Unknown'}")
            
        except Exception as e:
            logger.error(f"❌ خطأ في معالج أمر البداية: {e}")
            await update.message.reply_text("❌ حدث خطأ، حاول مرة أخرى")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """معالج أمر /help"""
        try:
            help_message = """🕌 **دليل استخدام البوت الإسلامي** 🕌

📿 **الأذكار التلقائية:**
• يرسل البوت أذكار عشوائية كل 5 دقائق
• أذكار الصباح تُرسل كصور في 5:30 صباحاً
• أذكار المساء تُرسل كصور في 7:30 مساءً

📖 **الورد القرآني:**
• يرسل البوت 3 صفحات من القرآن بعد كل صلاة بـ 30 دقيقة
• يتتبع تقدمك في قراءة المصحف
• يعيد البدء تلقائياً بعد إنهاء المصحف

🎯 **الأوامر:**
/dhikr - للحصول على ذكر عشوائي
/morning - لأذكار الصباح (صور)
/evening - لأذكار المساء (صور)
/quran_progress - لمعرفة تقدمك في الورد
/quran_manual - لإرسال الورد يدوياً

📁 **إعداد الصور:**
• ضع صور أذكار الصباح في مجلد: morning_dhikr_images
• ضع صور أذكار المساء في مجلد: evening_dhikr_images
• استخدم أسماء مرقمة: 01.jpg, 02.jpg, إلخ

👨‍💻 **المطور:** @Mavdiii
🔗 **قناة التلاوات:** @Telawat_Quran_0

🤲 **جعل الله هذا العمل في ميزان حسناتنا جميعاً**"""

            await update.message.reply_text(
                help_message,
                parse_mode=ParseMode.MARKDOWN
            )
            
            logger.info(f"✅ تم إرسال رسالة المساعدة للمستخدم {update.effective_user.id if update.effective_user else 'Unknown'}")
            
        except Exception as e:
            logger.error(f"❌ خطأ في معالج أمر المساعدة: {e}")
            await update.message.reply_text("❌ حدث خطأ، حاول مرة أخرى")
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """معالج الأخطاء العام"""
        try:
            logger.error(f"❌ خطأ في البوت: {context.error}")
            
            # إذا كان هناك update، نحاول إرسال رسالة خطأ
            if update and hasattr(update, 'effective_chat') and update.effective_chat:
                try:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="❌ حدث خطأ مؤقت، يرجى المحاولة مرة أخرى"
                    )
                except Exception:
                    pass  # تجاهل أخطاء إرسال رسالة الخطأ
            
        except Exception as e:
            logger.error(f"❌ خطأ في معالج الأخطاء نفسه: {e}")
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """معالج أمر الإحصائيات (للمطور فقط)"""
        try:
            # التحقق من أن المستخدم هو المطور
            if update.effective_user.id != 7089656746:  # DEVELOPER_ID
                await update.message.reply_text("❌ هذا الأمر متاح للمطور فقط")
                return
            
            stats_message = "📊 **إحصائيات البوت** 📊\n\n"
            
            if self.scheduler_service:
                schedule_info = self.scheduler_service.get_schedule_info()
                stats_message += f"👥 **المجموعات النشطة:** {schedule_info['active_groups']}\n"
                stats_message += f"⏰ **المهام المجدولة:** {len(schedule_info['scheduled_jobs'])}\n"
                stats_message += f"🔄 **فترة الأذكار:** كل {schedule_info['dhikr_interval_minutes']} دقائق\n"
                stats_message += f"🌅 **وقت أذكار الصباح:** {schedule_info['morning_time']}\n"
                stats_message += f"🌆 **وقت أذكار المساء:** {schedule_info['evening_time']}\n"
            
            stats_message += "\n✅ **البوت يعمل بشكل طبيعي**"
            
            await update.message.reply_text(
                stats_message,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"❌ خطأ في معالج أمر الإحصائيات: {e}")
            await update.message.reply_text("❌ حدث خطأ في جلب الإحصائيات")