#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
معالج أوامر الأذكار للبوت الإسلامي
يتعامل مع جميع أوامر الأذكار والصور
"""

import asyncio
import logging
import random
from typing import List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.error import TelegramError

from services.dhikr_service import DhikrService

logger = logging.getLogger(__name__)

class DhikrHandler:
    """معالج أوامر الأذكار"""
    
    def __init__(self, dhikr_service: DhikrService):
        self.dhikr_service = dhikr_service
    
    async def handle_dhikr_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """معالج أمر /dhikr للحصول على ذكر عشوائي"""
        try:
            # الحصول على ذكر عشوائي
            dhikr = self.dhikr_service.get_random_dhikr()
            message = self.dhikr_service.format_dhikr_message(dhikr)
            keyboard = self._create_dhikr_keyboard()
            
            await update.message.reply_text(
                message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )
            
            logger.info(f"✅ تم إرسال ذكر عشوائي للمجموعة {update.effective_chat.id}")
            
        except Exception as e:
            logger.error(f"❌ خطأ في معالج أمر الذكر: {e}")
            await update.message.reply_text("❌ حدث خطأ في إرسال الذكر، حاول مرة أخرى")
    
    async def handle_morning_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """معالج أمر /morning لإرسال أذكار الصباح كصور"""
        try:
            chat_id = update.effective_chat.id
            await self.send_morning_dhikr_images(chat_id, context.bot)
            
        except Exception as e:
            logger.error(f"❌ خطأ في معالج أذكار الصباح: {e}")
            await update.message.reply_text("❌ حدث خطأ في إرسال أذكار الصباح")
    
    async def handle_evening_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """معالج أمر /evening لإرسال أذكار المساء كصور"""
        try:
            chat_id = update.effective_chat.id
            await self.send_evening_dhikr_images(chat_id, context.bot)
            
        except Exception as e:
            logger.error(f"❌ خطأ في معالج أذكار المساء: {e}")
            await update.message.reply_text("❌ حدث خطأ في إرسال أذكار المساء")
    
    async def send_morning_dhikr_images(self, chat_id: int, bot) -> bool:
        """إرسال صور أذكار الصباح"""
        try:
            # الحصول على صور أذكار الصباح
            image_paths = self.dhikr_service.get_morning_dhikr_images()
            
            if not image_paths:
                # إرسال رسالة نصية إذا لم توجد صور
                await bot.send_message(
                    chat_id=chat_id,
                    text="🌅 **أذكار الصباح** 🌅\n\n"
                         "⚠️ لم يتم العثور على صور أذكار الصباح\n"
                         "يرجى إضافة الصور في مجلد morning_dhikr_images\n\n"
                         "🤲 **اللهم بارك لنا في صباحنا**",
                    parse_mode=ParseMode.MARKDOWN
                )
                return False
            
            # إرسال رسالة ترحيبية
            await bot.send_message(
                chat_id=chat_id,
                text="🌅 **أذكار الصباح** 🌅\n\n"
                     "🤲 **اللهم بارك لنا في صباحنا وأعنا على ذكرك وشكرك وحسن عبادتك**",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # إرسال الصور واحدة تلو الأخرى
            for i, image_path in enumerate(image_paths):
                try:
                    with open(image_path, 'rb') as photo:
                        await bot.send_photo(
                            chat_id=chat_id,
                            photo=photo,
                            caption=f"🌅 أذكار الصباح ({i+1}/{len(image_paths)})" if len(image_paths) > 1 else "🌅 أذكار الصباح"
                        )
                    
                    # توقف قصير بين الصور لتجنب الحد الأقصى للرسائل
                    if i < len(image_paths) - 1:
                        await asyncio.sleep(1)
                
                except Exception as e:
                    logger.error(f"❌ خطأ في إرسال صورة أذكار الصباح {image_path}: {e}")
                    continue
            
            # إرسال رسالة ختامية
            await bot.send_message(
                chat_id=chat_id,
                text="✨ **تم إرسال أذكار الصباح** ✨\n\n"
                     "🤲 **اللهم اجعل صباحنا مباركاً وأعنا على ذكرك**",
                parse_mode=ParseMode.MARKDOWN
            )
            
            logger.info(f"✅ تم إرسال {len(image_paths)} صورة لأذكار الصباح للمجموعة {chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في إرسال صور أذكار الصباح: {e}")
            return False
    
    async def send_evening_dhikr_images(self, chat_id: int, bot) -> bool:
        """إرسال صور أذكار المساء"""
        try:
            # الحصول على صور أذكار المساء
            image_paths = self.dhikr_service.get_evening_dhikr_images()
            
            if not image_paths:
                # إرسال رسالة نصية إذا لم توجد صور
                await bot.send_message(
                    chat_id=chat_id,
                    text="🌆 **أذكار المساء** 🌆\n\n"
                         "⚠️ لم يتم العثور على صور أذكار المساء\n"
                         "يرجى إضافة الصور في مجلد evening_dhikr_images\n\n"
                         "🤲 **اللهم بارك لنا في مسائنا**",
                    parse_mode=ParseMode.MARKDOWN
                )
                return False
            
            # إرسال رسالة ترحيبية
            await bot.send_message(
                chat_id=chat_id,
                text="🌆 **أذكار المساء** 🌆\n\n"
                     "🤲 **اللهم بارك لنا في مسائنا وأعنا على ذكرك وشكرك وحسن عبادتك**",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # إرسال الصور واحدة تلو الأخرى
            for i, image_path in enumerate(image_paths):
                try:
                    with open(image_path, 'rb') as photo:
                        await bot.send_photo(
                            chat_id=chat_id,
                            photo=photo,
                            caption=f"🌆 أذكار المساء ({i+1}/{len(image_paths)})" if len(image_paths) > 1 else "🌆 أذكار المساء"
                        )
                    
                    # توقف قصير بين الصور لتجنب الحد الأقصى للرسائل
                    if i < len(image_paths) - 1:
                        await asyncio.sleep(1)
                
                except Exception as e:
                    logger.error(f"❌ خطأ في إرسال صورة أذكار المساء {image_path}: {e}")
                    continue
            
            # إرسال رسالة ختامية
            await bot.send_message(
                chat_id=chat_id,
                text="✨ **تم إرسال أذكار المساء** ✨\n\n"
                     "🤲 **اللهم اجعل مساءنا مباركاً وأعنا على ذكرك**",
                parse_mode=ParseMode.MARKDOWN
            )
            
            logger.info(f"✅ تم إرسال {len(image_paths)} صورة لأذكار المساء للمجموعة {chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في إرسال صور أذكار المساء: {e}")
            return False
    
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """معالج الاستعلامات المرتدة (الأزرار)"""
        try:
            query = update.callback_query
            await query.answer()
            
            if query.data == "quran_recitations":
                await query.message.reply_text(
                    "🎵 **تلاوات قرآنية مميزة** 🎵\n\n"
                    "انضم إلى قناة التلاوات للاستماع لأجمل التلاوات:\n"
                    "@Telawat_Quran_0",
                    parse_mode=ParseMode.MARKDOWN
                )
            
            elif query.data == "duas":
                # إرسال دعاء عشوائي
                duas = self.dhikr_service.get_dhikr_by_category("dua")
                if duas:
                    dhikr = random.choice(duas)
                else:
                    dhikr = self.dhikr_service.get_random_dhikr()
                
                message = self.dhikr_service.format_dhikr_message(dhikr)
                await query.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            
            elif query.data == "stats":
                stats = self.dhikr_service.get_stats()
                stats_message = f"""📊 **إحصائيات البوت** 📊

📿 **إجمالي الأذكار:** {stats['total_dhikr']}
🌅 **صور أذكار الصباح:** {stats['morning_images']}
🌆 **صور أذكار المساء:** {stats['evening_images']}

📚 **الفئات:**"""
                
                for category, count in stats['categories'].items():
                    category_name = {
                        'dhikr': 'أذكار',
                        'dua': 'أدعية', 
                        'quran': 'آيات قرآنية',
                        'hadith': 'أحاديث نبوية'
                    }.get(category, category)
                    stats_message += f"\n• {category_name}: {count}"
                
                await query.message.reply_text(stats_message, parse_mode=ParseMode.MARKDOWN)
        
        except Exception as e:
            logger.error(f"❌ خطأ في معالج الاستعلامات المرتدة: {e}")
    
    def _create_dhikr_keyboard(self) -> InlineKeyboardMarkup:
        """إنشاء لوحة مفاتيح الأذكار"""
        keyboard = [
            [
                InlineKeyboardButton("🎵 تلاوات قرآنية - أجر 🎵", url="https://t.me/Telawat_Quran_0")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)