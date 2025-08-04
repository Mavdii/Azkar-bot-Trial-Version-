#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🕌 البوت الإسلامي الشامل - Comprehensive Islamic Telegram Bot
=====================================================================
A complete Islamic bot with 200+ authentic dhikr, prayer reminders, 
morning/evening dhikr, and advanced group management features.

Features:
- 🕌 200+ Authentic Islamic Dhikr with sources
- 🕐 Prayer reminders for Cairo timezone
- 🌅 Morning dhikr at 5:30 AM
- 🌆 Evening dhikr at 7:30 PM
- 📱 Automatic group activation
- 💾 Supabase database integration
- 📊 Usage statistics tracking

Author: Islamic Bot Developer Team
Version: 3.0.0 - Complete Implementation
License: MIT
"""

import asyncio
import logging
import random
import time
from datetime import datetime, timedelta
import pytz
from typing import Dict, Any, List, Optional, Union, Tuple
import threading
import json
import os
import re
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import traceback
from functools import wraps
from concurrent.futures import ThreadPoolExecutor
import schedule
from collections import defaultdict
import aiocron  # Required for Quran scheduling

# Telegram Bot imports
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot,
    ChatMember, ChatMemberUpdated, Message, CallbackQuery,
    BotCommand, BotCommandScope, BotCommandScopeChat, User, Chat
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ContextTypes, ChatMemberHandler
)
from telegram.constants import ParseMode, ChatAction, ChatType, ChatMemberStatus
from telegram.error import TelegramError, BadRequest, Forbidden, NetworkError

# Supabase imports
try:
    from supabase.client import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("⚠️ Supabase not available, using local storage")

# Advanced logging configuration
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('islamic_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==================== CONFIGURATION & CONSTANTS ====================

# Import configuration from config.py
from .config import (
    config, BOT_TOKEN, DEVELOPER_ID, DEVELOPER_USERNAME, BOT_VERSION,
    SUPABASE_URL, SUPABASE_KEY, CAIRO_TZ, UTC_TZ,
    MORNING_DHIKR_TIME, EVENING_DHIKR_TIME, DHIKR_INTERVAL_MINUTES, POST_PRAYER_DELAY_MINUTES
)

# Print configuration summary on startup
if __name__ == "__main__":
    config.print_config_summary()

# --- Dynamic Cairo Prayer Times via Aladhan API ---
from .prayer_times_api import fetch_cairo_prayer_times
# Global cache for today's prayer times
DYNAMIC_PRAYER_TIMES = {}

# --- Quran Daily Pages Integration ---
from ..quran.quran_scheduler import QuranScheduler
from ..quran.quran_manager import QuranPageManager, PageTracker

# Dhikr Scheduling Configuration (loaded from config.py)
DHIKR_PER_PAGE = config.DHIKR_PER_PAGE

# Global Bot State Management
class BotState:
    """Centralized bot state management"""
    def __init__(self):
        self.active_dhikr_messages: Dict[int, int] = {}  # chat_id -> message_id
        self.active_groups: set = set()
        self.scheduled_jobs: list = []
        self.dhikr_stats: Dict[int, Dict] = {}
        self.user_preferences: Dict[int, Dict] = {}
        self.group_settings: Dict[int, Dict] = {}

        self.last_dhikr_time: Dict[int, datetime] = {}  # chat_id -> datetime
        self.prayer_reminder_messages: Dict[int, int] = {}  # chat_id -> message_id
        self.bot_username: str = ""
        self.send_as_image: bool = False  # Alternates between text and image
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.is_running = False
        self.app = None
        self.bot = None
        # Quran Daily Pages
        self.quran_scheduler: Optional[QuranScheduler] = None

# Initialize global state
bot_state = BotState()
supabase_client = None

def get_cairo_time() -> datetime:
    """Get current time in Cairo timezone"""
    return datetime.now(CAIRO_TZ)

def format_dhikr_message(dhikr: Dict[str, str]) -> str:
    """Format dhikr message - simple format with dhikr text only (no markdown)"""
    return dhikr['text']

def create_dhikr_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard with dhikr action buttons"""
    keyboard = [
        [
            InlineKeyboardButton(" تلاوات قرآنية - أجر ", url="https://t.me/Telawat_Quran_0")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_random_dhikr_image() -> Optional[str]:
    """Get a random dhikr image from random_images folder"""
    try:
        import glob
        image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.gif']
        image_files = []
        
        for extension in image_extensions:
            image_files.extend(glob.glob(f"random_images/{extension}"))
        
        # Filter out .keep file
        image_files = [f for f in image_files if not f.endswith('.keep')]
        
        if image_files:
            return random.choice(image_files)
        else:
            logger.warning("⚠️ No images found in random_images folder")
            return None
    except Exception as e:
        logger.error(f"❌ Error getting random dhikr image: {e}")
        return None

# ==================== DHIKR COLLECTIONS ====================

def load_azkar_from_file():
    """Load dhikr from Azkar.txt file - supports both old format (dhikr|source) and new format (--- separated)"""
    try:
        with open('Azkar.txt', 'r', encoding='utf-8') as file:
            content = file.read()
        
        azkar_list = []
        
        # Check if file uses new format (contains ---)
        if '---' in content:
            # New format: --- separated dhikr blocks
            dhikr_blocks = content.split('---')
            
            for i, block in enumerate(dhikr_blocks):
                block = block.strip()
                
                # Skip empty blocks
                if not block:
                    continue
                
                # Each block is a complete dhikr (can be multiple lines)
                dhikr_text = block.strip()
                
                if dhikr_text:
                    dhikr = {
                        'text': dhikr_text,
                        'source': ''  # No source in new format
                    }
                    azkar_list.append(dhikr)
            
            logger.info(f"✅ تم تحميل {len(azkar_list)} ذكر من ملف Azkar.txt (تنسيق جديد)")
            
        else:
            # Old format: dhikr_text|source (for backward compatibility)
            lines = content.split('\n')
            line_number = 0
            
            for line in lines:
                line_number += 1
                line = line.strip()
                
                # Skip empty lines
                if not line:
                    continue
                    
                # Check if line has proper format (dhikr_text|source)
                if '|' not in line:
                    logger.warning(f"⚠️ تخطي السطر {line_number}: تنسيق غير صحيح - {line[:50]}...")
                    continue
                    
                parts = line.split('|')
                if len(parts) != 2:
                    logger.warning(f"⚠️ تخطي السطر {line_number}: عدد الأجزاء غير صحيح - {line[:50]}...")
                    continue
                
                dhikr_text = parts[0].strip()
                source = parts[1].strip()
                
                # Validate that dhikr text is not empty
                if not dhikr_text:
                    logger.warning(f"⚠️ تخطي السطر {line_number}: نص الذكر فارغ")
                    continue
                
                dhikr = {
                    'text': dhikr_text,
                    'source': source
                }
                azkar_list.append(dhikr)
            
            logger.info(f"✅ تم تحميل {len(azkar_list)} ذكر من ملف Azkar.txt (تنسيق قديم)")
        
        return azkar_list
    
    except FileNotFoundError:
        logger.error("❌ ملف Azkar.txt غير موجود!")
        return []
    except UnicodeDecodeError as e:
        logger.error(f"❌ خطأ في ترميز الملف: {e}")
        return []
    except Exception as e:
        logger.error(f"❌ خطأ في تحميل ملف الأذكار: {e}")
        return []

# تحميل الأذكار من الملف
RANDOM_DHIKR = load_azkar_from_file()

# أذكار الصباح والمساء - يتم إرسالها كصور فقط من المجلدات المخصصة
# morning_dhikr_images/ و evening_dhikr_images/

# ==================== DHIKR COLLECTIONS END ====================

# ==================== COMMAND HANDLERS ====================

# مجلد صور أذكار ما بعد الصلاة
POST_PRAYER_IMAGES_DIR = "post_prayer_images"

# أذكار ما بعد الصلاة (للمرجع فقط - يتم إرسالها كصور)
POST_PRAYER_DHIKR_TEXT = [
    "**أَعُوذُ بِاللهِ مِنَ الشَّيْطَانِ الرَّجِيمِ**\n\n**اللّهُ لاَ إِلَـهَ إِلاَّ هُوَ الْحَيُّ الْقَيُّومُ لاَ تَأْخُذُهُ سِنَةٌ وَلاَ نَوْمٌ لَّهُ مَا فِي السَّمَاوَاتِ وَمَا فِي الأَرْضِ مَن ذَا الَّذِي يَشْفَعُ عِنْدَهُ إِلاَّ بِإِذْنِهِ يَعْلَمُ مَا بَيْنَ أَيْدِيهِمْ وَمَا خَلْفَهُمْ وَلاَ يُحِيطُونَ بِشَيْءٍ مِّنْ عِلْمِهِ إِلاَّ بِمَا شَاء وَسِعَ كُرْسِيُّهُ السَّمَاوَاتِ وَالأَرْضَ وَلاَ يَؤُودُهُ حِفْظُهُمَا وَهُوَ الْعَلِيُّ الْعَظِيمُ**\n\n*آية الكرسي*",
    "**بِسْمِ اللهِ الرَّحْمنِ الرَّحِيم**\n\n**قُلْ هُوَ اللَّهُ أَحَدٌ، اللَّهُ الصَّمَدُ، لَمْ يَلِدْ وَلَمْ يُولَدْ، وَلَمْ يَكُن لَّهُ كُفُواً أَحَدٌ**\n\n*سورة الإخلاص*",
    "**بِسْمِ اللهِ الرَّحْمنِ الرَّحِيم**\n\n**قُلْ أَعُوذُ بِرَبِّ الْفَلَقِ، مِن شَرِّ مَا خَلَقَ، وَمِن شَرِّ غَاسِقٍ إِذَا وَقَبَ، وَمِن شَرِّ النَّفَّاثَاتِ فِي الْعُقَدِ، وَمِن شَرِّ حَاسِدٍ إِذَا حَسَدَ**\n\n*سورة الفلق*",
    "**بِسْمِ اللهِ الرَّحْمنِ الرَّحِيم**\n\n**قُلْ أَعُوذُ بِرَبِّ النَّاسِ، مَلِكِ النَّاسِ، إِلَهِ النَّاسِ، مِن شَرِّ الْوَسْوَاسِ الْخَنَّاسِ، الَّذِي يُوَسْوِسُ فِي صُدُورِ النَّاسِ، مِنَ الْجِنَّةِ وَ النَّاسِ**\n\n*سورة الناس*"
]

# ==================== SUPABASE CLIENT INITIALIZATION ====================

def init_supabase():
    """Initialize Supabase client"""
    global supabase_client
    try:
        if SUPABASE_AVAILABLE and SUPABASE_URL:
            # Use service key for admin operations, fallback to anon key
            service_key = config.SUPABASE_SERVICE_KEY if hasattr(config, 'SUPABASE_SERVICE_KEY') else None
            key_to_use = service_key if service_key else SUPABASE_KEY
            
            if key_to_use:
                supabase_client = create_client(SUPABASE_URL, key_to_use)
                key_type = "service" if service_key else "anon"
                logger.info(f"✅ Supabase client initialized successfully with {key_type} key")
            else:
                logger.warning("⚠️ No Supabase key available")
                supabase_client = None
        else:
            logger.warning("⚠️ Supabase not available, using local storage")
            supabase_client = None
    except Exception as e:
        logger.error(f"❌ Failed to initialize Supabase: {e}")
        supabase_client = None
        
async def register_group(chat_id: int, chat_title: Optional[str] = None):
    """Register a new group in the database with proper error handling"""
    if not supabase_client:
        return True

    try:
        # Check if group already exists
        existing_group = supabase_client.table("groups").select("chat_id").eq("chat_id", chat_id).execute()
        
        if not existing_group.data:
            # Group doesn't exist, create it
            group_data = {
                "chat_id": chat_id,
                "group_name": chat_title or "Unknown Group",
                "is_active": True
            }
            supabase_client.table("groups").insert(group_data).execute()
            logger.info(f"✅ Created new group: {chat_id} - {chat_title}")
        else:
            logger.info(f"📝 Group already exists: {chat_id}")

        # Check if settings exist
        existing_settings = supabase_client.table("group_settings").select("chat_id").eq("chat_id", chat_id).execute()
        
        if not existing_settings.data:
            # Settings don't exist, create them
            settings_data = {
                "chat_id": chat_id,
                "dhikr_enabled": True,
                "prayer_reminders": True,
                "post_prayer_dhikr": True,
                "morning_evening_dhikr": True,
                "dhikr_interval_minutes": 5,
                "quran_daily_enabled": True,
                "quran_send_delay_minutes": 30
            }
            supabase_client.table("group_settings").insert(settings_data).execute()
            logger.info(f"✅ Created settings for group: {chat_id}")
            
            # Add group to Quran scheduler if enabled
            if bot_state.quran_scheduler:
                await bot_state.quran_scheduler.add_active_group(chat_id)
        else:
            logger.info(f"📝 Settings already exist for group: {chat_id}")

        return True

    except Exception as e:
        logger.error(f"❌ Error registering group {chat_id}: {e}")
        return False

def get_group_settings(chat_id: int) -> Dict[str, Any]:
    """Get group settings from database"""
    default_settings = {
        'dhikr_enabled': True,
        'prayer_reminders': True,
        'post_prayer_dhikr': True,
        'morning_evening_dhikr': True,
        'dhikr_interval_minutes': 5,
        'quran_daily_enabled': True,
        'quran_send_delay_minutes': 30
    }

    if not supabase_client:
        return default_settings

    try:
        # First ensure group exists
        group_check = supabase_client.table('groups').select('chat_id').eq('chat_id', chat_id).execute()
        if not group_check.data:
            # Register the group first
            supabase_client.table('groups').insert({
                'chat_id': chat_id,
                'group_name': 'Unknown Group',
                'is_active': True
            }).execute()

        # Get settings
        result = supabase_client.table('group_settings').select('*').eq('chat_id', chat_id).execute()
        if result.data:
            return {**default_settings, **result.data[0]}
        else:
            # Create default settings
            settings_data = {**default_settings, 'chat_id': chat_id}
            supabase_client.table('group_settings').insert(settings_data).execute()
            return default_settings

    except Exception as e:
        logger.error(f"❌ Error getting group settings: {e}")
        return default_settings

def update_group_settings(chat_id: int, settings: Dict[str, Any]) -> bool:
    """Update group settings in database"""
    if not supabase_client:
        return True

    try:
        # Ensure group exists first
        group_check = supabase_client.table('groups').select('chat_id').eq('chat_id', chat_id).execute()
        if not group_check.data:
            supabase_client.table('groups').insert({
                'chat_id': chat_id,
                'group_name': 'Unknown Group',
                'is_active': True
            }).execute()

        # Check if settings exist
        existing_settings = supabase_client.table('group_settings').select('id').eq('chat_id', chat_id).execute()
        
        if existing_settings.data:
            # Update existing settings
            supabase_client.table('group_settings').update(settings).eq('chat_id', chat_id).execute()
        else:
            # Insert new settings
            settings['chat_id'] = chat_id
            supabase_client.table('group_settings').insert(settings).execute()
        
        return True

    except Exception as e:
        logger.error(f"❌ Error updating group settings: {e}")
        return False

# ==================== MESSAGE FORMATTING ====================

def format_prayer_alert(prayer_name: str) -> str:
    """Format prayer alert message (5 minutes before prayer) - Egyptian dialect"""
    messages = {
        'الفجر': """🌅 **يا جماعة الخير** 🌅

⏰ **باقي 5 دقايق على صلاة الفجر** ⏰

�  _يلا بقى قوموا من النوم.. ده وقت الفجر جاي_
🌟 _الدنيا لسه بدري والملايكة بتدعيلكم_
💫 _اللي يصلي الفجر في وقته ربنا يحفظه طول اليوم_

🤲 **يا رب اصحينا على طاعتك واجعلنا من أهل الفجر**

⏰ **استعدوا.. الفجر على الأبواب** ⏰""",

        'الظهر': """☀️ **يا أهل الخير** ☀️

⏰ **باقي 5 دقايق على صلاة الظهر** ⏰

🏢 _سيبوا الشغل شوية وفكروا في ربنا_
🌟 _وسط زحمة اليوم ده وقت تاخدوا فيه نفس_
💫 _الصلاة دي هتريحكم من تعب النهار_

🤲 **يا رب اجعل صلاتنا راحة لقلوبنا**

⏰ **جهزوا نفسكم.. الظهر قرب** ⏰""",

        'العصر': """🌤️ **يا حبايب** 🌤️

⏰ **باقي 5 دقايق على صلاة العصر** ⏰

⚠️ _دي الصلاة اللي ربنا حذرنا منها.. ماتفوتوهاش_
🌟 _اللي يفوت العصر كإنه خسر كل حاجة_
💫 _النهار بيخلص والأعمال بتتحاسب_

🤲 **يا رب لا تجعلنا من الغافلين**

⏰ **بسرعة.. العصر مايستناش** ⏰""",

        'المغرب': """🌅 **يا أحباب الله** 🌅

⏰ **باقي 5 دقايق على صلاة المغرب** ⏰

🌇 _الشمس بتغرب والدعوة مستجابة_
🌟 _ده وقت الدعاء اللي ربنا بيسمعه_
💫 _اطلبوا من ربنا كل اللي في قلوبكم_

🤲 **يا رب استجب دعاءنا في الوقت ده**

⏰ **يلا بينا.. المغرب على الأبواب** ⏰""",

        'العشاء': """🌙 **يا أهلنا الغاليين** 🌙

⏰ **باقي 5 دقايق على صلاة العشاء** ⏰

🌃 _اليوم بيخلص وعايزين نختمه بالصلاة_
🌟 _دي آخر صلاة في اليوم.. خلوها حلوة_
💫 _اللي يصلي العشاء في جماعة كإنه قام نص الليل_

🤲 **يا رب اختم يومنا بالخير والطاعة**

⏰ **استعدوا.. العشاء جاي** ⏰"""
    }

    return messages.get(prayer_name, f"🕌 **باقي 5 دقايق على صلاة {prayer_name}** 🕌")

def format_prayer_reminder(prayer_name: str) -> str:
    """Format prayer reminder message (at prayer time)"""
    messages = {
        'الفجر': """🌅 **بسم الله الرحمن الرحيم** 🌅

✨ **حان الآن موعد صلاة الفجر** ✨

🕌 _استيقظوا يا أحباب الله، فقد أشرق نور الفجر_
🌟 _هذا وقت تتنزل فيه الرحمات والبركات_
💫 _من صلى الفجر في جماعة فكأنما قام الليل كله_

🤲 **اللهم بارك لنا في صلاتنا واجعلنا من المحافظين عليها**

⏰ **الآن وقت صلاة الفجر** ⏰""",

        'الظهر': """☀️ **بسم الله الرحمن الرحيم** ☀️

✨ **حان الآن موعد صلاة الظهر** ✨

🕌 _توقفوا عن أعمالكم وتوجهوا إلى الله_
🌟 _هذا وقت في وسط النهار للقاء مع الخالق_
💫 _الصلاة خير من العمل، والذكر خير من المال_

🤲 **اللهم اجعل صلاتنا نوراً وبرهاناً وشفاعة**

⏰ **الآن وقت صلاة الظهر** ⏰""",

        'العصر': """🌤️ **بسم الله الرحمن الرحيم** 🌤️

✨ **حان الآن موعد صلاة العصر** ✨

🕌 _هذا هو الوقت الأوسط، الصلاة الوسطى_
🌟 _من فاتته صلاة العصر فكأنما وتر أهله وماله_
💫 _بادروا إلى الصلاة قبل انشغال آخر النهار_

🤲 **اللهم أعنا على ذكرك وشكرك وحسن عبادتك**

⏰ **الآن وقت صلاة العصر** ⏰""",

        'المغرب': """🌅 **بسم الله الرحمن الرحيم** 🌅

✨ **حان الآن موعد صلاة المغرب** ✨

🕌 _مع غروب الشمس، يحين وقت لقاء مع الله_
🌟 _هذا وقت استجابة الدعاء، فأكثروا من الدعاء_
💫 _بين المغرب والعشاء ساعة مستجابة_

⏰ **الآن وقت صلاة المغرب** ⏰""",

        'العشاء': """🌙 **بسم الله الرحمن الرحيم** 🌙

✨ **حان الآن موعد صلاة العشاء** ✨

🕌 _مع دخول الليل، اختتموا يومكم بالصلاة_
🌟 _من صلى العشاء في جماعة فكأنما قام نصف الليل_
💫 _هذا وقت السكينة والطمأنينة مع الله_

🤲 **اللهم اجعل خير أعمالنا خواتيمها وخير أيامنا يوم نلقاك**

⏰ **الآن وقت صلاة العشاء** ⏰"""
    }

    return messages.get(prayer_name, f"🕌 **حان وقت صلاة {prayer_name}** 🕌")
def get_post_prayer_image_path() -> Optional[str]:
    """Get path to post-prayer dhikr image"""
    try:
        # Check if directory exists
        if not os.path.exists(POST_PRAYER_IMAGES_DIR):
            logger.warning(f"⚠️ Post-prayer images directory not found: {POST_PRAYER_IMAGES_DIR}")
            return None
        
        # Look for image files in the directory
        image_extensions = ['.jpg', '.jpeg', '.png', '.webp']
        for filename in os.listdir(POST_PRAYER_IMAGES_DIR):
            if any(filename.lower().endswith(ext) for ext in image_extensions):
                image_path = os.path.join(POST_PRAYER_IMAGES_DIR, filename)
                logger.info(f"✅ Found post-prayer dhikr image: {image_path}")
                return image_path
        
        logger.warning(f"⚠️ No image files found in {POST_PRAYER_IMAGES_DIR}")
        return None
        
    except Exception as e:
        logger.error(f"❌ Error getting post-prayer image path: {e}")
        return None

def format_post_prayer_caption() -> str:
    """Format caption for post-prayer dhikr image"""
    return "**لَا تَنْسَ قِرَاءَةَ أَذْكَارِ مَا بَعْدَ الصَّلَاةِ**"

def get_post_prayer_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for post-prayer dhikr with Quran recitations link"""
    keyboard = [
        [InlineKeyboardButton(" تلاوات قرآنية - أجر ", url="https://t.me/Telawat_Quran_0")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ==================== INLINE KEYBOARD HELPERS ====================

def get_main_keyboard() -> InlineKeyboardMarkup:
    """Get main inline keyboard with developer button (for start command only)"""
    keyboard = [
        [InlineKeyboardButton(" تلاوات قرآنية - أجر ", url="https://t.me/Telawat_Quran_0")],
        [InlineKeyboardButton("👨‍💻 مطور البوت", url="https://t.me/m4vdi")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_simple_keyboard() -> InlineKeyboardMarkup:
    """Get simple keyboard without developer button"""
    keyboard = [
        [InlineKeyboardButton("🎵 تلاوات قرآنية - أجر 🎵", url="https://t.me/Telawat_Quran_0")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_dhikr_navigation_keyboard(page: int, total_pages: int, dhikr_type: str) -> InlineKeyboardMarkup:
    """Get navigation keyboard for dhikr pagination"""
    keyboard = []

    # Navigation buttons
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ السابق", callback_data=f"{dhikr_type}_prev_{page}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("➡️ التالي", callback_data=f"{dhikr_type}_next_{page}"))

    if nav_buttons:
        keyboard.append(nav_buttons)

    # Page indicator
    keyboard.append([InlineKeyboardButton(f"📄 الصفحة {page + 1} من {total_pages}", callback_data="page_info")])

    # Main menu button
    keyboard.append([InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu")])

    return InlineKeyboardMarkup(keyboard)

# ==================== BOT HANDLERS ====================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command"""
    
    # Register group if in group chat
    if update.effective_chat.type in ['group', 'supergroup']:
        await register_group(update.effective_chat.id, update.effective_chat.title)
    
    welcome_message = f"""🕌 **أهلاً وسهلاً بكم في البوت الإسلامي الشامل** 🕌

🌟 **مرحباً بك في رحلة روحانية مباركة**

📿 **ما يقدمه لك هذا البوت:**
🔹 **أذكار متنوعة:** أكثر من 200 ذكر أصيل بالمصادر
🔹 **تذكير الصلوات:** في مواقيتها الشرعية (توقيت القاهرة)
🔹 **أذكار الصباح والمساء:** في أوقاتها المحددة
🔹 **الورد القرآني اليومي:** 3 صفحات بعد كل صلاة
🔹 **أذكار ما بعد الصلاة:** تذكير تلقائي بالأذكار المستحبة

⚡ **البوت يعمل تلقائياً في المجموعات!**

🤲 **بارك الله فيكم وجعل هذا البوت سبباً في تذكيركم بالله**

📚 **للمساعدة:** /help"""

    keyboard = get_main_keyboard()
    await update.message.reply_text(welcome_message, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command"""
    help_message = f"""📚 **دليل استخدام البوت الإسلامي الشامل** 📚

👤 **الأوامر المتاحة:**
• `/start` - رسالة الترحيب والتعريف بالبوت
• `/help` - عرض هذا الدليل
• `/dhikr` - الحصول على ذكر عشوائي فوري
• `/morning` - عرض أذكار الصباح
• `/evening` - عرض أذكار المساء
• `/quran_progress` - عرض تقدم قراءة القرآن
• `/quran_manual` - إرسال الورد القرآني يدوياً

⏰ **المواقيت (توقيت القاهرة):**
• الفجر: 4:23 ص
• الظهر: 1:01 م  
• العصر: 4:38 م
• المغرب: 7:57 م
• العشاء: 9:27 م

🕐 **أوقات الأذكار الخاصة:**
• أذكار الصباح: 5:30 ص
• أذكار المساء: 7:30 م
• الورد القرآني: بعد كل صلاة بـ 30 دقيقة (3 صفحات)

🤖 **ملاحظات مهمة:**
• البوت يعمل تلقائياً في المجموعات
• جميع الأذكار موثقة بالمصادر الشرعية

🤲 **جعلنا الله وإياكم من الذاكرين الله كثيراً والذاكرات**"""

    await update.message.reply_text(help_message, parse_mode=ParseMode.MARKDOWN)

async def dhikr_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /dhikr command"""
    if not RANDOM_DHIKR:
        await update.message.reply_text("❌ لا توجد أذكار متاحة حالياً")
        return
        
    dhikr = random.choice(RANDOM_DHIKR)
    message = format_dhikr_message(dhikr)
    keyboard = get_simple_keyboard()
    
    await update.message.reply_text(message, reply_markup=keyboard)

async def morning_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /morning command - send morning dhikr as image"""
    try:
        # البحث عن صورة أذكار الصباح
        morning_image_path = None
        if os.path.exists("morning_dhikr_images"):
            for filename in os.listdir("morning_dhikr_images"):
                if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    morning_image_path = os.path.join("morning_dhikr_images", filename)
                    break
        
        if morning_image_path and os.path.exists(morning_image_path):
            # إرسال الصورة مع تسمية توضيحية
            caption = "🌅 **أذكار الصباح** 🌅\n\n🤲 **اللهم بارك لنا في صباحنا واجعله خيراً وبركة**"
            keyboard = get_simple_keyboard()
            
            with open(morning_image_path, 'rb') as photo:
                await update.message.reply_photo(
                    photo=photo,
                    caption=caption,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=keyboard
                )
        else:
            await update.message.reply_text("❌ صورة أذكار الصباح غير متوفرة حالياً")
    
    except Exception as e:
        logger.error(f"Error in morning_command: {e}")
        await update.message.reply_text("❌ حدث خطأ في إرسال أذكار الصباح")

async def evening_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /evening command - send evening dhikr as image"""
    try:
        # البحث عن صورة أذكار المساء
        evening_image_path = None
        if os.path.exists("evening_dhikr_images"):
            for filename in os.listdir("evening_dhikr_images"):
                if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    evening_image_path = os.path.join("evening_dhikr_images", filename)
                    break
        
        if evening_image_path and os.path.exists(evening_image_path):
            # إرسال الصورة مع تسمية توضيحية
            caption = "🌆 **أذكار المساء** 🌆\n\n🤲 **اللهم بارك لنا في مسائنا واجعله خيراً وبركة**"
            keyboard = get_simple_keyboard()
            
            with open(evening_image_path, 'rb') as photo:
                await update.message.reply_photo(
                    photo=photo,
                    caption=caption,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=keyboard
                )
        else:
            await update.message.reply_text("❌ صورة أذكار المساء غير متوفرة حالياً")
    
    except Exception as e:
        logger.error(f"Error in evening_command: {e}")
        await update.message.reply_text("❌ حدث خطأ في إرسال أذكار المساء")

async def quran_progress_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /quran_progress command"""
    if update.effective_chat.type not in ['group', 'supergroup']:
        await update.message.reply_text("🚫 هذا الأمر متاح فقط في المجموعات")
        return

    chat_id = update.effective_chat.id
    
    try:
        # Initialize page tracker
        page_tracker = PageTracker(supabase_client)
        
        # Get progress stats
        stats = await page_tracker.get_progress_stats(chat_id)
        
        message = f"""📖 **تقدم قراءة القرآن الكريم** 📖

📊 **الإحصائيات:**
📄 الصفحة الحالية: {stats['current_page']}
📚 إجمالي الصفحات: {stats['total_pages']}
📈 نسبة التقدم: {stats['progress_percentage']}%
📖 الصفحات المتبقية: {stats['pages_remaining']}
🏆 عدد مرات الإكمال: {stats['completion_count']}

🤲 **"وَرَتِّلِ الْقُرْآنَ تَرْتِيلًا"**

💡 **يتم إرسال 3 صفحات بعد كل صلاة بـ 30 دقيقة**"""

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📖 إرسال الورد الآن", callback_data="send_quran_manual")]
        ])
        
        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
    
    except Exception as e:
        logger.error(f"Error in quran_progress_command: {e}")
        await update.message.reply_text("❌ حدث خطأ في جلب تقدم القراءة")

async def quran_manual_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /quran_manual command"""
    if update.effective_chat.type not in ['group', 'supergroup']:
        await update.message.reply_text("🚫 هذا الأمر متاح فقط في المجموعات")
        return

    chat_id = update.effective_chat.id
    
    try:
        if bot_state.quran_scheduler:
            success = await bot_state.quran_scheduler.send_manual_quran(chat_id)
            if not success:
                await update.message.reply_text("❌ حدث خطأ في إرسال الورد القرآني")
        else:
            await update.message.reply_text("❌ مجدول القرآن غير متاح حالياً")
    
    except Exception as e:
        logger.error(f"Error in quran_manual_command: {e}")
        await update.message.reply_text("❌ حدث خطأ في إرسال الورد القرآني")

# ==================== CALLBACK QUERY HANDLERS ====================

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all callback queries"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "main_menu":
        await query.edit_message_text(
            "🕌 **البوت الإسلامي الشامل** 🕌\n\n🤲 **اختر ما تريد:**",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_simple_keyboard()
        )
    
    elif data == "send_quran_manual":
        await send_manual_quran_callback(query)
    
    elif data == "stats":
        await query.answer("📊 الإحصائيات ستكون متاحة قريباً", show_alert=True)
    
    elif data == "page_info":
        await query.answer("ℹ️ معلومات الصفحة", show_alert=False)
    
    else:
        await query.answer("🔄 جاري التحديث...", show_alert=False)

async def send_manual_quran_callback(query) -> None:
    """Handle manual Quran sending callback"""
    if query.message.chat.type not in ['group', 'supergroup']:
        await query.answer("🚫 هذا متاح فقط في المجموعات", show_alert=True)
        return

    chat_id = query.message.chat.id
    
    try:
        if bot_state.quran_scheduler:
            success = await bot_state.quran_scheduler.send_manual_quran(chat_id)
            if success:
                await query.answer("تم إرسال الورد القرآني", show_alert=False)
            else:
                await query.answer("❌ حدث خطأ في الإرسال", show_alert=True)
        else:
            await query.answer("❌ مجدول القرآن غير متاح", show_alert=True)
    
    except Exception as e:
        logger.error(f"Error in send_manual_quran_callback: {e}")
        await query.answer("❌ حدث خطأ في الإرسال", show_alert=True)

# ==================== SCHEDULED FUNCTIONS ====================

async def send_random_dhikr():
    """Send random dhikr to all active groups"""
    logger.info("🚀 Starting send_random_dhikr function")
    try:
        # Check if dhikr list is available
        if not RANDOM_DHIKR:
            logger.warning("⚠️ No dhikr available in RANDOM_DHIKR list")
            return
        
        logger.info(f"📚 Found {len(RANDOM_DHIKR)} dhikr available")

        # Get active groups from database
        active_chats = []
        
        if supabase_client:
            try:
                result = supabase_client.table('group_settings').select('chat_id').eq('dhikr_enabled', True).execute()
                active_chats = result.data
                logger.info(f"📊 Found {len(active_chats)} groups with dhikr enabled")
                
                # Update active groups in memory
                bot_state.active_groups.clear()
                for chat_data in active_chats:
                    bot_state.active_groups.add(chat_data['chat_id'])
            except Exception as e:
                logger.error(f"❌ Error getting active groups from database: {e}")
                # Fallback to in-memory groups if available
                if bot_state.active_groups:
                    active_chats = [{'chat_id': chat_id} for chat_id in bot_state.active_groups]
        else:
            # Use in-memory active groups if no database
            if bot_state.active_groups:
                active_chats = [{'chat_id': chat_id} for chat_id in bot_state.active_groups]

        if not active_chats:
            logger.info("ℹ️ No active groups found for dhikr")
            return

        logger.info(f"🎯 Will send dhikr to {len(active_chats)} groups")

        # Check if bot is available
        if not bot_state.bot:
            logger.error("❌ Bot instance not available")
            return

        # Toggle between text and image
        bot_state.send_as_image = not bot_state.send_as_image
        send_mode = "صورة" if bot_state.send_as_image else "نص"
        logger.info(f"🔄 Sending mode: {send_mode}")

        # Select random dhikr
        dhikr = random.choice(RANDOM_DHIKR)
        logger.info(f"📝 Selected dhikr: {dhikr['text'][:50]}...")
        
        keyboard = create_dhikr_keyboard()
        logger.info("✅ Created keyboard")

        successful_sends = 0
        
        # Send to all active groups
        logger.info("🚀 Starting to send dhikr to groups...")
        for chat_data in active_chats:
            chat_id = chat_data['chat_id']
            logger.info(f"📤 Sending to group {chat_id} as {send_mode}")
            try:
                # Delete previous dhikr message if exists
                if chat_id in bot_state.active_dhikr_messages:
                    try:
                        await bot_state.bot.delete_message(chat_id, bot_state.active_dhikr_messages[chat_id])
                    except:
                        pass

                sent_message = None
                
                if bot_state.send_as_image:
                    # Send as image
                    image_path = get_random_dhikr_image()
                    if image_path and os.path.exists(image_path):
                        try:
                            logger.info(f"🖼️ Sending image: {image_path}")
                            with open(image_path, 'rb') as photo:
                                sent_message = await bot_state.bot.send_photo(
                                    chat_id=chat_id,
                                    photo=photo,
                                    reply_markup=keyboard
                                )
                        except Exception as img_error:
                            logger.warning(f"⚠️ Failed to send image, falling back to text: {img_error}")
                            # Fallback to text
                            sent_message = await bot_state.bot.send_message(
                                chat_id=chat_id,
                                text=format_dhikr_message(dhikr),
                                reply_markup=keyboard
                            )
                    else:
                        logger.warning("⚠️ No image available, sending as text")
                        # Fallback to text if no image
                        sent_message = await bot_state.bot.send_message(
                            chat_id=chat_id,
                            text=format_dhikr_message(dhikr),
                            reply_markup=keyboard
                        )
                else:
                    # Send as text
                    logger.info("📝 Sending as text")
                    sent_message = await bot_state.bot.send_message(
                        chat_id=chat_id,
                        text=format_dhikr_message(dhikr),
                        reply_markup=keyboard
                    )
                
                # Store message ID for future deletion
                if sent_message:
                    bot_state.active_dhikr_messages[chat_id] = sent_message.message_id
                    successful_sends += 1
                    logger.info(f"✅ Successfully sent to {chat_id}")
                
                await asyncio.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error sending dhikr to {chat_id}: {e}")
                # Remove from active groups if bot was blocked
                if "bot was blocked" in str(e).lower() or "chat not found" in str(e).lower():
                    bot_state.active_groups.discard(chat_id)
                continue

        if successful_sends > 0:
            logger.info(f"✅ Sent random dhikr as {send_mode} to {successful_sends} groups")
        else:
            logger.warning(f"⚠️ No dhikr sent - found {len(active_chats)} active groups")

        logger.info("✅ Random dhikr task completed")

    except Exception as e:
        logger.error(f"Error in send_random_dhikr: {e}")

async def send_prayer_alerts():
    """Send prayer alerts (5 minutes before prayer)"""
    try:
        if not supabase_client:
            return

        result = supabase_client.table('group_settings').select('chat_id').eq('prayer_reminders', True).execute()

        for group in result.data:
            chat_id = group['chat_id']
            
            # Get current prayer time
            current_time = get_cairo_time()
            prayer_name = get_current_prayer_name_for_alert(current_time)
            
            if prayer_name:
                message = format_prayer_alert(prayer_name)
                
                try:
                    await bot_state.bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        parse_mode=ParseMode.MARKDOWN
                    )
                    await asyncio.sleep(0.5)
                except Exception as e:
                    logger.error(f"Error sending prayer alert to {chat_id}: {e}")

    except Exception as e:
        logger.error(f"Error in send_prayer_alerts: {e}")

async def send_prayer_reminders():
    """Send prayer reminders based on current time"""
    try:
        if not supabase_client:
            return

        result = supabase_client.table('group_settings').select('chat_id').eq('prayer_reminders', True).execute()

        for group in result.data:
            chat_id = group['chat_id']
            
            # Get current prayer time
            current_time = get_cairo_time()
            prayer_name = get_current_prayer_name(current_time)
            
            if prayer_name:
                message = format_prayer_reminder(prayer_name)
                
                try:
                    await bot_state.bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        parse_mode=ParseMode.MARKDOWN
                    )
                    await asyncio.sleep(0.5)
                except Exception as e:
                    logger.error(f"Error sending prayer reminder to {chat_id}: {e}")

    except Exception as e:
        logger.error(f"Error in send_prayer_reminders: {e}")

def get_current_prayer_name_for_alert(current_time: datetime) -> Optional[str]:
    """Get current prayer name for alert (5 minutes before prayer)"""
    hour = current_time.hour
    minute = current_time.minute
    
    # Alert times (5 minutes before each prayer)
    if hour == 4 and minute == 18:  # 5 minutes before Fajr (4:23)
        return 'الفجر'
    elif hour == 12 and minute == 56:  # 5 minutes before Dhuhr (13:01)
        return 'الظهر'
    elif hour == 16 and minute == 33:  # 5 minutes before Asr (16:38)
        return 'العصر'
    elif hour == 19 and minute == 52:  # 5 minutes before Maghrib (19:57)
        return 'المغرب'
    elif hour == 21 and minute == 22:  # 5 minutes before Isha (21:27)
        return 'العشاء'
    
    return None

def get_current_prayer_name(current_time: datetime) -> Optional[str]:
    """Get current prayer name based on time"""
    hour = current_time.hour
    minute = current_time.minute
    
    # Simple time-based prayer detection
    if hour == 4 and minute == 23:
        return 'الفجر'
    elif hour == 13 and minute == 1:
        return 'الظهر'
    elif hour == 16 and minute == 38:
        return 'العصر'
    elif hour == 19 and minute == 57:
        return 'المغرب'
    elif hour == 21 and minute == 27:
        return 'العشاء'
    
    return Nonea
async def send_post_prayer_dhikr():
    """Send post-prayer dhikr reminders as image"""
    try:
        if not supabase_client:
            return

        result = supabase_client.table('group_settings').select('chat_id').eq('post_prayer_dhikr', True).execute()

        for group in result.data:
            chat_id = group['chat_id']
            
            # Get image path
            image_path = get_post_prayer_image_path()
            keyboard = get_post_prayer_keyboard()
            
            try:
                if image_path and os.path.exists(image_path):
                    # Send image with caption
                    with open(image_path, 'rb') as photo:
                        await bot_state.bot.send_photo(
                            chat_id=chat_id,
                            photo=photo,
                            caption=format_post_prayer_caption(),
                            parse_mode=ParseMode.MARKDOWN,
                            reply_markup=keyboard
                        )
                else:
                    # Fallback: send text message if no image found
                    fallback_message = """**لَا تَنْسَ قِرَاءَةَ أَذْكَارِ مَا بَعْدَ الصَّلَاةِ**

📷 _الصورة غير متوفرة حالياً_"""
                    
                    await bot_state.bot.send_message(
                        chat_id=chat_id,
                        text=fallback_message,
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=keyboard
                    )
                
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.error(f"Error sending post-prayer dhikr to {chat_id}: {e}")

    except Exception as e:
        logger.error(f"Error in send_post_prayer_dhikr: {e}")

async def send_morning_dhikr():
    """Send morning dhikr images to all active groups"""
    try:
        if not supabase_client:
            return
        result = supabase_client.table('group_settings').select('chat_id').eq('morning_evening_dhikr', True).execute()
        
        for group in result.data:
            chat_id = group['chat_id']
            
            try:
                # البحث عن صورة أذكار الصباح
                morning_image_path = None
                if os.path.exists("morning_dhikr_images"):
                    for filename in os.listdir("morning_dhikr_images"):
                        if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                            morning_image_path = os.path.join("morning_dhikr_images", filename)
                            break
                
                if morning_image_path and os.path.exists(morning_image_path):
                    # إرسال الصورة مع تسمية توضيحية
                    caption = "🌅 **أذكار الصباح** 🌅\n\n🤲 **اللهم بارك لنا في صباحنا واجعله خيراً وبركة**"
                    keyboard = get_simple_keyboard()
                    
                    with open(morning_image_path, 'rb') as photo:
                        await bot_state.bot.send_photo(
                            chat_id=chat_id,
                            photo=photo,
                            caption=caption,
                            parse_mode=ParseMode.MARKDOWN,
                            reply_markup=keyboard
                        )
                else:
                    # إرسال رسالة نصية في حالة عدم وجود صورة
                    fallback_message = "🌅 **أذكار الصباح** 🌅\n\n❌ صورة أذكار الصباح غير متوفرة حالياً\n\n🤲 **اللهم بارك لنا في صباحنا واجعله خيراً وبركة**"
                    await bot_state.bot.send_message(
                        chat_id=chat_id,
                        text=fallback_message,
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=get_simple_keyboard()
                    )
                
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.error(f"Error sending morning dhikr to {chat_id}: {e}")

    except Exception as e:
        logger.error(f"Error in send_morning_dhikr: {e}")

async def send_evening_dhikr():
    """Send evening dhikr images to all active groups"""
    try:
        if not supabase_client:
            return

        result = supabase_client.table('group_settings').select('chat_id').eq('morning_evening_dhikr', True).execute()

        for group in result.data:
            chat_id = group['chat_id']
            
            try:
                # البحث عن صورة أذكار المساء
                evening_image_path = None
                if os.path.exists("evening_dhikr_images"):
                    for filename in os.listdir("evening_dhikr_images"):
                        if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                            evening_image_path = os.path.join("evening_dhikr_images", filename)
                            break
                
                if evening_image_path and os.path.exists(evening_image_path):
                    # إرسال الصورة مع تسمية توضيحية
                    caption = "🌆 **أذكار المساء** 🌆\n\n🤲 **اللهم بارك لنا في مسائنا واجعله خيراً وبركة**"
                    keyboard = get_simple_keyboard()
                    
                    with open(evening_image_path, 'rb') as photo:
                        await bot_state.bot.send_photo(
                            chat_id=chat_id,
                            photo=photo,
                            caption=caption,
                            parse_mode=ParseMode.MARKDOWN,
                            reply_markup=keyboard
                        )
                else:
                    # إرسال رسالة نصية في حالة عدم وجود صورة
                    fallback_message = "🌆 **أذكار المساء** 🌆\n\n❌ صورة أذكار المساء غير متوفرة حالياً\n\n🤲 **اللهم بارك لنا في مسائنا واجعله خيراً وبركة**"
                    await bot_state.bot.send_message(
                        chat_id=chat_id,
                        text=fallback_message,
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=get_simple_keyboard()
                    )
                
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.error(f"Error sending evening dhikr to {chat_id}: {e}")

    except Exception as e:
        logger.error(f"Error in send_evening_dhikr: {e}")
        # ==================== SCHEDULER SETUP ====================

async def setup_scheduler_delayed():
    """Setup scheduler after a delay to ensure event loop is running"""
    await asyncio.sleep(3)  # Wait for the bot to fully start
    try:
        await setup_scheduler()
        logger.info("✅ Scheduler setup completed successfully")
    except Exception as e:
        logger.error(f"❌ Error setting up scheduler: {e}")
        # Continue without scheduler if it fails

async def simple_scheduler():
    """Simple asyncio-based scheduler to avoid event loop conflicts"""
    logger.info("⏰ Starting simple scheduler...")
    
    while bot_state.is_running:
        try:
            current_time = get_cairo_time()
            hour = current_time.hour
            minute = current_time.minute
            
            # Check for scheduled tasks every minute
            if minute % 1 == 0:  # Log every minute for debugging
                logger.info(f"⏰ Scheduler check: {hour:02d}:{minute:02d}")
            
            # Random dhikr every 5 minutes
            if minute % 5 == 0:
                logger.info(f"🕐 Time check: {hour:02d}:{minute:02d} - Sending random dhikr")
                try:
                    await send_random_dhikr()
                    logger.info("✅ Random dhikr task completed")
                except Exception as e:
                    logger.error(f"❌ Error in random dhikr task: {e}")
            
            # Morning dhikr at 5:30 AM
            if hour == 5 and minute == 30:
                asyncio.create_task(send_morning_dhikr())
                logger.info("🌅 Triggered morning dhikr")
            
            # Evening dhikr at 7:30 PM
            if hour == 19 and minute == 30:
                asyncio.create_task(send_evening_dhikr())
                logger.info("🌆 Triggered evening dhikr")
            
            # Prayer alerts (5 minutes before each prayer)
            if (hour == 4 and minute == 18) or \
               (hour == 12 and minute == 56) or \
               (hour == 16 and minute == 33) or \
               (hour == 19 and minute == 52) or \
               (hour == 21 and minute == 22):
                asyncio.create_task(send_prayer_alerts())
                logger.info("📢 Triggered prayer alert")
            
            # Prayer reminders (at prayer time)
            if (hour == 4 and minute == 23) or \
               (hour == 13 and minute == 1) or \
               (hour == 16 and minute == 38) or \
               (hour == 19 and minute == 57) or \
               (hour == 21 and minute == 27):
                asyncio.create_task(send_prayer_reminders())
                logger.info("🕌 Triggered prayer reminder")
            
            # Post-prayer dhikr (25 minutes after each prayer)
            if (hour == 4 and minute == 48) or \
               (hour == 13 and minute == 26) or \
               (hour == 17 and minute == 3) or \
               (hour == 20 and minute == 22) or \
               (hour == 21 and minute == 52):
                asyncio.create_task(send_post_prayer_dhikr())
                logger.info("📿 Triggered post-prayer dhikr")
            
            # Wait for 60 seconds before next check
            await asyncio.sleep(60)
            
        except Exception as e:
            logger.error(f"❌ Error in scheduler: {e}")
            await asyncio.sleep(60)  # Continue even if there's an error

async def auto_activate_bot():
    """Auto-activate the bot by sending dhikr to all registered groups"""
    try:
        if not supabase_client:
            logger.warning("⚠️ No database connection, skipping auto-activation")
            return
        
        # Get all registered groups
        result = supabase_client.table('groups').select('chat_id, group_name').eq('is_active', True).execute()
        groups = result.data
        
        if not groups:
            logger.info("ℹ️ No groups found for auto-activation")
            return
        
        logger.info(f"🚀 Auto-activating bot in {len(groups)} groups...")
        
        # Send welcome dhikr to all groups
        if RANDOM_DHIKR:
            welcome_dhikr = random.choice(RANDOM_DHIKR)
            welcome_message = f"""🕌 **البوت الإسلامي نشط الآن** 🕌

{format_dhikr_message(welcome_dhikr)}

⚡ **البوت سيرسل الأذكار تلقائياً كل 5 دقائق**
🌅 **أذكار الصباح: 5:30 ص**
🌆 **أذكار المساء: 7:30 م**

🤲 **بارك الله فيكم وجعل هذا في ميزان حسناتكم**"""
            
            keyboard = get_simple_keyboard()
            
            for group in groups:
                chat_id = group['chat_id']
                try:
                    # Add to active groups
                    bot_state.active_groups.add(chat_id)
                    
                    # Send activation message
                    sent_message = await bot_state.bot.send_message(
                        chat_id=chat_id,
                        text=welcome_message,
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=keyboard
                    )
                    
                    # Store message ID for future deletion
                    bot_state.active_dhikr_messages[chat_id] = sent_message.message_id
                    
                    logger.info(f"✅ Activated in group: {group.get('group_name', 'Unknown')} ({chat_id})")
                    await asyncio.sleep(1)  # Rate limiting
                    
                except Exception as e:
                    logger.error(f"❌ Failed to activate in group {chat_id}: {e}")
                    continue
            
            logger.info(f"🎉 Bot auto-activation completed! Active in {len(bot_state.active_groups)} groups")
        
    except Exception as e:
        logger.error(f"❌ Error in auto-activation: {e}")

async def setup_scheduler():
    """Setup the simple scheduler"""
    try:
        # Start the simple scheduler as a background task
        asyncio.create_task(simple_scheduler())
        logger.info("✅ Simple scheduler started successfully")
        
    except Exception as e:
        logger.error(f"❌ Error setting up scheduler: {e}")

# ==================== MAIN APPLICATION SETUP ====================

async def main():
    """Main function to run the bot"""
    try:
        # Initialize Supabase
        init_supabase()
        
        # Create application
        application = Application.builder().token(BOT_TOKEN).build()
        bot_state.app = application
        bot_state.bot = application.bot
        
        # Get bot info
        bot_info = await application.bot.get_me()
        bot_state.bot_username = bot_info.username
        logger.info(f"✅ Bot started: @{bot_state.bot_username}")
        
        # Initialize Quran scheduler
        try:
            # Create a simple prayer times manager
            class PrayerTimesManager:
                async def fetch_cairo_prayer_times(self):
                    return await fetch_cairo_prayer_times()
            
            prayer_manager = PrayerTimesManager()
            bot_state.quran_scheduler = QuranScheduler(application.bot, prayer_manager, supabase_client)
            await bot_state.quran_scheduler.initialize()
            logger.info("✅ Quran scheduler initialized")
        except Exception as e:
            logger.error(f"❌ Error initializing Quran scheduler: {e}")
        
        # Add handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("dhikr", dhikr_command))
        application.add_handler(CommandHandler("morning", morning_command))
        application.add_handler(CommandHandler("evening", evening_command))
        application.add_handler(CommandHandler("quran_progress", quran_progress_command))
        application.add_handler(CommandHandler("quran_manual", quran_manual_command))
        
        # Callback query handler
        application.add_handler(CallbackQueryHandler(handle_callback_query))
        
        # Error handler
        async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
            logger.error(f"Exception while handling an update: {context.error}")
        
        application.add_error_handler(error_handler)
        
        # Setup scheduler - we'll do this after the application starts
        logger.info("⏰ Setting up scheduler...")
        
        # Start the bot
        logger.info("🚀 Starting bot...")
        logger.info("=" * 50)
        logger.info("🕌 البوت الإسلامي الشامل - جاهز للعمل")
        logger.info(f"📱 Bot Username: @{bot_state.bot_username}")
        logger.info(f"📊 Loaded {len(RANDOM_DHIKR)} dhikr from file")
        logger.info("⚡ سيتم تفعيل البوت تلقائياً في جميع المجموعات")
        logger.info("=" * 50)
        bot_state.is_running = True

        # Setup scheduler and auto-activation
        async def setup_bot_services():
            await asyncio.sleep(3)  # Wait for bot to start
            await setup_scheduler()
            await auto_activate_bot()
        
        # Start bot services as background task
        asyncio.create_task(setup_bot_services())

        # Initialize and start the application manually to avoid event loop conflicts
        await application.initialize()
        await application.start()
        
        # Start the updater manually
        await application.updater.start_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
        
        # Keep the bot running
        logger.info("✅ Bot is now running and polling for updates...")
        logger.info("🔄 Press Ctrl+C to stop the bot")
        
        try:
            # Create a stop event and wait for it
            stop_event = asyncio.Event()
            
            # Set up signal handlers for graceful shutdown
            import signal
            def signal_handler():
                logger.info("🛑 Received stop signal")
                stop_event.set()
            
            # Register signal handlers
            if hasattr(signal, 'SIGINT'):
                signal.signal(signal.SIGINT, lambda s, f: signal_handler())
            if hasattr(signal, 'SIGTERM'):
                signal.signal(signal.SIGTERM, lambda s, f: signal_handler())
            
            # Wait for stop signal
            await stop_event.wait()
            
        except KeyboardInterrupt:
            logger.info("🛑 Bot stopped by user (KeyboardInterrupt)")
        except Exception as e:
            logger.error(f"❌ Error during bot operation: {e}")
        finally:
            logger.info("🛑 Stopping bot services...")
            try:
                # Stop the updater
                await application.updater.stop()
                logger.info("✅ Updater stopped")
            except Exception as e:
                logger.warning(f"⚠️ Error stopping updater: {e}")
            
            try:
                # Stop the application
                await application.stop()
                logger.info("✅ Application stopped")
            except Exception as e:
                logger.warning(f"⚠️ Error stopping application: {e}")
            
            try:
                # Shutdown the application
                await application.shutdown()
                logger.info("✅ Application shutdown completed")
            except Exception as e:
                logger.warning(f"⚠️ Error during shutdown: {e}")
        
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Critical error in main: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        logger.info("🧹 Cleaning up...")
        bot_state.is_running = False
        # Cleanup is handled in the main try block above

# ==================== COMMAND HANDLERS ====================



# Duplicate help_command removed

# Duplicate dhikr_command removed



async def quran_progress_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /quran_progress command"""
    try:
        chat_id = update.effective_chat.id
        
        if bot_state.quran_scheduler:
            stats = await bot_state.quran_scheduler.page_tracker.get_progress_stats(chat_id)
            
            message = f"""📖 **تقدمك في الورد القرآني** 📖

📄 **الصفحة الحالية:** {stats['current_page']} من {stats['total_pages']}
📊 **نسبة الإنجاز:** {stats['progress_percentage']}%
📋 **الصفحات المتبقية:** {stats['pages_remaining']}
🏆 **عدد مرات الإكمال:** {stats['completion_count']}

🤲 **بارك الله فيك وأعانك على إتمام المصحف الشريف**"""

            await update.message.reply_text(
                message,
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text("❌ خدمة الورد القرآني غير متاحة حالياً")
        
    except Exception as e:
        logger.error(f"❌ Error in quran_progress command: {e}")

async def quran_manual_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /quran_manual command"""
    try:
        chat_id = update.effective_chat.id
        
        if bot_state.quran_scheduler:
            success = await bot_state.quran_scheduler.send_manual_quran(chat_id)
            if success:
                await update.message.reply_text("✅ تم إرسال الورد القرآني بنجاح")
            else:
                await update.message.reply_text("❌ حدث خطأ في إرسال الورد القرآني")
        else:
            await update.message.reply_text("❌ خدمة الورد القرآني غير متاحة حالياً")
        
    except Exception as e:
        logger.error(f"❌ Error in quran_manual command: {e}")

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callback queries"""
    try:
        query = update.callback_query
        await query.answer()
        
        if query.data == "quran_recitations":
            await query.message.reply_text(
                "🎵 **تلاوات قرآنية مميزة** 🎵\n\n"
                "انضم إلى قناة التلاوات للاستماع لأجمل التلاوات:\n"
                "@Telawat_Quran_0"
            )
        elif query.data == "duas":
            dhikr = random.choice(RANDOM_DHIKR)
            message = format_dhikr_message(dhikr)
            await query.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
        elif query.data == "stats":
            await query.message.reply_text(
                "📊 **إحصائيات البوت** 📊\n\n"
                f"👥 المجموعات النشطة: {len(bot_state.active_groups)}\n"
                f"📿 الأذكار المرسلة: متاحة 24/7\n"
                f"📖 الورد القرآني: نشط\n"
                f"🕐 تذكير الصلاة: نشط"
            )
        
    except Exception as e:
        logger.error(f"❌ Error in callback query: {e}")

# ==================== SCHEDULER FUNCTIONS ====================



# send_random_dhikr function is already defined above

# Scheduler setup is handled by the setup_scheduler() function above

def run_bot():
    """Run the bot with proper event loop handling"""
    logger.info("🚀 Initializing bot...")
    
    # Try different methods to handle event loop issues
    methods = [
        ("asyncio.run", lambda: asyncio.run(main())),
        ("manual loop", run_with_manual_loop),
        ("nest_asyncio", run_with_nest_asyncio)
    ]
    
    for method_name, method_func in methods:
        try:
            logger.info(f"🔄 Trying {method_name}...")
            method_func()
            logger.info("✅ Bot started successfully!")
            break
        except RuntimeError as e:
            if "Cannot close a running event loop" in str(e) or "This event loop is already running" in str(e):
                logger.warning(f"⚠️ {method_name} failed due to event loop conflict, trying next method...")
                continue
            else:
                logger.error(f"❌ {method_name} failed with unexpected error: {e}")
                raise
        except KeyboardInterrupt:
            logger.info("🛑 Bot stopped by user")
            break
        except ImportError as e:
            if "nest_asyncio" in str(e):
                logger.warning("⚠️ nest_asyncio not available, skipping this method")
                continue
            else:
                raise
        except Exception as e:
            logger.error(f"❌ {method_name} failed: {e}")
            if method_name == methods[-1][0]:  # Last method
                logger.error("❌ All methods failed!")
                import traceback
                traceback.print_exc()
                raise
            else:
                logger.warning(f"⚠️ Trying next method...")
                continue

def run_with_manual_loop():
    """Run with manually created event loop"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    finally:
        try:
            # Cancel all running tasks
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            
            # Wait for tasks to complete cancellation
            if pending:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            
            # Close the loop
            loop.close()
        except Exception as e:
            logger.warning(f"⚠️ Error during loop cleanup: {e}")

def run_with_nest_asyncio():
    """Run with nest_asyncio for nested event loops"""
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(main())

if __name__ == "__main__":
    run_bot()