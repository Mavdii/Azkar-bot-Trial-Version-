#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🕌 Prayer Times API - Enhanced Version
======================================
Enhanced prayer times API with integrated system support
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional
import pytz

# Import the new integrated system
from ..prayer_times.integrated_system import IntegratedPrayerTimesSystem

# Configure logging
logger = logging.getLogger(__name__)

# Cairo timezone
CAIRO_TZ = pytz.timezone('Africa/Cairo')

# Global integrated system instance
_integrated_system: Optional[IntegratedPrayerTimesSystem] = None

def initialize_integrated_system(bot, supabase_client=None, quran_page_manager=None, page_tracker=None):
    """Initialize the integrated prayer times system"""
    global _integrated_system
    _integrated_system = IntegratedPrayerTimesSystem(
        bot=bot,
        supabase_client=supabase_client,
        quran_page_manager=quran_page_manager,
        page_tracker=page_tracker
    )
    return _integrated_system

async def fetch_cairo_prayer_times():
    """
    Fetch today's Cairo prayer times using the enhanced integrated system.
    Returns dict with prayer names as keys and Cairo datetime objects as values.
    """
    try:
        if not _integrated_system or not _integrated_system.is_initialized:
            logger.warning("⚠️ Integrated system not initialized, falling back to basic API")
            return await _fallback_fetch_cairo_prayer_times()
        
        # Get prayer times from integrated system
        prayer_times = await _integrated_system.get_today_prayer_times()
        
        if prayer_times:
            # Convert to the expected format
            result = {
                'fajr': prayer_times.fajr,
                'dhuhr': prayer_times.dhuhr,
                'asr': prayer_times.asr,
                'maghrib': prayer_times.maghrib,
                'isha': prayer_times.isha
            }
            
            logger.info(f"✅ تم جلب مواقيت الصلاة من النظام المتكامل - المصدر: {prayer_times.source}")
            return result
        else:
            logger.warning("⚠️ فشل في جلب المواقيت من النظام المتكامل، استخدام fallback")
            return await _fallback_fetch_cairo_prayer_times()
            
    except Exception as e:
        logger.error(f"❌ خطأ في جلب مواقيت الصلاة: {e}")
        return await _fallback_fetch_cairo_prayer_times()

async def _fallback_fetch_cairo_prayer_times():
    """Fallback method using direct API call"""
    try:
        import aiohttp
        
        ALADHAN_API_URL = "https://api.aladhan.com/v1/timingsByCity?city=Cairo&country=Egypt&method=5"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(ALADHAN_API_URL) as resp:
                data = await resp.json()
                timings = data['data']['timings']
                today = datetime.now(CAIRO_TZ).date()
                result = {}
                for key in ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]:
                    time_str = timings[key]  # e.g. '04:23'
                    hour, minute = map(int, time_str.split(':'))
                    dt = CAIRO_TZ.localize(datetime(today.year, today.month, today.day, hour, minute))
                    result[key.lower()] = dt
                
                logger.info("✅ تم جلب مواقيت الصلاة من fallback API")
                return result
                
    except Exception as e:
        logger.error(f"❌ خطأ في fallback API: {e}")
        return None

def get_integrated_system() -> Optional[IntegratedPrayerTimesSystem]:
    """Get the integrated system instance"""
    return _integrated_system
