#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🕌 Quran Daily Pages Manager - مدير الورد اليومي من القرآن الكريم
=====================================================================
مدير شامل لإرسال صفحات القرآن الكريم كورد يومي للمستخدمين

Features:
- 📖 إرسال 3 صفحات من القرآن بعد كل صلاة بـ 30 دقيقة
- 📊 تتبع تقدم القراءة لكل مجموعة
- 🔄 إعادة البدء تلقائياً بعد إنهاء المصحف

- 💾 حفظ التقدم في قاعدة البيانات

Author: Islamic Bot Developer Team
Version: 1.0.0
License: MIT
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import asyncio
from pathlib import Path
import pytz

# Telegram imports
from telegram import Bot, InputMediaPhoto
from telegram.error import TelegramError

# Database imports
try:
    from supabase.client import Client as SupabaseClient
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    SupabaseClient = None

# Configure logging
logger = logging.getLogger(__name__)

# Constants
CAIRO_TZ = pytz.timezone('Africa/Cairo')
QURAN_PAGES_DIR = "quran_pages"
TOTAL_QURAN_PAGES = 604
PAGES_PER_SESSION = 3
POST_PRAYER_DELAY_MINUTES = 30

class QuranPageManager:
    """مدير صفحات القرآن الكريم"""
    
    def __init__(self):
        self.pages_directory = QURAN_PAGES_DIR
        self.total_pages = TOTAL_QURAN_PAGES
        self.pages_per_session = PAGES_PER_SESSION
        self._ensure_directory_exists()
    
    def _ensure_directory_exists(self) -> None:
        """التأكد من وجود مجلد الصور"""
        if not os.path.exists(self.pages_directory):
            os.makedirs(self.pages_directory)
            logger.info(f"✅ تم إنشاء مجلد الصور: {self.pages_directory}")
    
    async def get_next_pages(self, chat_id: int, current_page: int) -> List[str]:
        """الحصول على الصفحات التالية للإرسال"""
        pages = []
        for i in range(self.pages_per_session):
            page_num = current_page + i
            if page_num > self.total_pages:
                page_num = ((page_num - 1) % self.total_pages) + 1
            
            page_path = await self.get_page_image_path(page_num)
            if page_path and await self.validate_page_exists(page_num):
                pages.append(page_path)
            else:
                logger.warning(f"⚠️ الصفحة {page_num} غير موجودة، سيتم تخطيها")
        
        return pages
    
    async def get_page_image_path(self, page_number: int) -> str:
        """الحصول على مسار صورة الصفحة"""
        # Try different formats and naming conventions
        formats = ['jpg', 'jpeg', 'png', 'webp']
        naming_patterns = [
            f"{page_number:03d}",  # 001.jpg, 002.jpg, etc.
            f"page_{page_number:03d}",  # page_001.jpg
            f"{page_number}",  # 1.jpg, 2.jpg, etc.
            f"page_{page_number}"  # page_1.jpg
        ]
        
        for pattern in naming_patterns:
            for fmt in formats:
                filename = f"{pattern}.{fmt}"
                filepath = os.path.join(self.pages_directory, filename)
                if os.path.exists(filepath):
                    return filepath
        
        return ""
    
    async def validate_page_exists(self, page_number: int) -> bool:
        """التحقق من وجود صفحة معينة"""
        page_path = await self.get_page_image_path(page_number)
        return bool(page_path and os.path.exists(page_path))
    
    async def get_missing_pages(self) -> List[int]:
        """الحصول على قائمة الصفحات المفقودة"""
        missing_pages = []
        for page_num in range(1, self.total_pages + 1):
            if not await self.validate_page_exists(page_num):
                missing_pages.append(page_num)
        return missing_pages
    
    async def get_available_pages_count(self) -> int:
        """الحصول على عدد الصفحات المتوفرة"""
        count = 0
        for page_num in range(1, self.total_pages + 1):
            if await self.validate_page_exists(page_num):
                count += 1
        return count


class PageTracker:
    """متتبع تقدم قراءة القرآن"""
    
    def __init__(self, supabase_client: Optional[SupabaseClient] = None):
        self.db = supabase_client
        self._local_cache: Dict[int, Dict[str, Any]] = {}
    
    async def get_current_page(self, chat_id: int) -> int:
        """الحصول على الصفحة الحالية للمجموعة"""
        if self.db:
            try:
                result = self.db.table('quran_progress').select('current_page').eq('chat_id', chat_id).execute()
                if result.data:
                    return result.data[0]['current_page']
            except Exception as e:
                logger.error(f"❌ خطأ في جلب الصفحة الحالية: {e}")
        
        # Fallback to local cache
        return self._local_cache.get(chat_id, {}).get('current_page', 1)
    
    async def update_current_page(self, chat_id: int, page_number: int) -> None:
        """تحديث الصفحة الحالية"""
        if self.db:
            try:
                # Check if record exists
                existing = self.db.table('quran_progress').select('id').eq('chat_id', chat_id).execute()
                
                if existing.data:
                    # Update existing record
                    self.db.table('quran_progress').update({
                        'current_page': page_number,
                        'updated_at': datetime.now().isoformat()
                    }).eq('chat_id', chat_id).execute()
                else:
                    # Insert new record
                    self.db.table('quran_progress').insert({
                        'chat_id': chat_id,
                        'current_page': page_number,
                        'total_pages_read': 0,
                        'completion_count': 0
                    }).execute()
                
                logger.info(f"✅ تم تحديث الصفحة الحالية للمجموعة {chat_id}: {page_number}")
                
            except Exception as e:
                logger.error(f"❌ خطأ في تحديث الصفحة الحالية: {e}")
        
        # Update local cache
        if chat_id not in self._local_cache:
            self._local_cache[chat_id] = {}
        self._local_cache[chat_id]['current_page'] = page_number
    
    async def get_progress_stats(self, chat_id: int) -> Dict[str, Any]:
        """الحصول على إحصائيات التقدم"""
        current_page = await self.get_current_page(chat_id)
        progress_percentage = round((current_page / TOTAL_QURAN_PAGES) * 100, 1)
        
        stats = {
            'current_page': current_page,
            'total_pages': TOTAL_QURAN_PAGES,
            'progress_percentage': progress_percentage,
            'pages_remaining': TOTAL_QURAN_PAGES - current_page + 1,
            'completion_count': 0
        }
        
        if self.db:
            try:
                result = self.db.table('quran_progress').select('*').eq('chat_id', chat_id).execute()
                if result.data:
                    data = result.data[0]
                    stats.update({
                        'total_pages_read': data.get('total_pages_read', 0),
                        'completion_count': data.get('completion_count', 0),
                        'last_sent_at': data.get('last_sent_at')
                    })
            except Exception as e:
                logger.error(f"❌ خطأ في جلب إحصائيات التقدم: {e}")
        
        return stats
    
    async def mark_completion(self, chat_id: int) -> None:
        """تسجيل إكمال قراءة المصحف"""
        if self.db:
            try:
                # Get current completion count
                result = self.db.table('quran_progress').select('completion_count').eq('chat_id', chat_id).execute()
                completion_count = 1
                if result.data:
                    completion_count = result.data[0].get('completion_count', 0) + 1
                
                # Update with new completion
                self.db.table('quran_progress').update({
                    'current_page': 1,  # Reset to first page
                    'completion_count': completion_count,
                    'total_pages_read': completion_count * TOTAL_QURAN_PAGES,
                    'updated_at': datetime.now().isoformat()
                }).eq('chat_id', chat_id).execute()
                
                logger.info(f"🎉 تم تسجيل إكمال المصحف للمجموعة {chat_id} - المرة رقم {completion_count}")
                
            except Exception as e:
                logger.error(f"❌ خطأ في تسجيل الإكمال: {e}")
        
        # Update local cache
        if chat_id not in self._local_cache:
            self._local_cache[chat_id] = {}
        self._local_cache[chat_id]['current_page'] = 1


# Export classes for use in main bot
__all__ = ['QuranPageManager', 'PageTracker']