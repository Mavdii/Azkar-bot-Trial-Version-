#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🕌 Prayer Times Tests - اختبارات مواقيت الصلاة
===============================================
اختبارات شاملة لنظام مواقيت الصلاة المحسن

Author: Islamic Bot Developer Team
Version: 1.0.0
License: MIT
"""

import unittest
import asyncio
from datetime import datetime, timedelta
import pytz
from unittest.mock import Mock, AsyncMock, patch

# Import the modules to test
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prayer_times.cairo_manager import CairoPrayerTimes, CairoPrayerTimesManager
from prayer_times.enhanced_api_client import EnhancedPrayerAPIClient
from prayer_times.prayer_cache import PrayerTimesCache
from prayer_times.data_validator import PrayerTimesDataValidator, ValidationSeverity
from prayer_times.precise_quran_scheduler import PreciseQuranScheduler, QuranSchedule

# Cairo timezone
CAIRO_TZ = pytz.timezone('Africa/Cairo')

class TestCairoPrayerTimes(unittest.TestCase):
    """اختبارات كائن مواقيت الصلاة للقاهرة"""
    
    def setUp(self):
        """إعداد البيانات للاختبار"""
        self.today = datetime.now(CAIRO_TZ).replace(hour=0, minute=0, second=0, microsecond=0)
        self.sample_prayer_times = CairoPrayerTimes(
            date=self.today,
            fajr=self.today.replace(hour=4, minute=23),
            dhuhr=self.today.replace(hour=13, minute=1),
            asr=self.today.replace(hour=16, minute=38),
            maghrib=self.today.replace(hour=19, minute=57),
            isha=self.today.replace(hour=21, minute=27),
            source="test",
            cached_at=datetime.now(CAIRO_TZ)
        )
    
    def test_prayer_times_creation(self):
        """اختبار إنشاء كائن مواقيت الصلاة"""
        self.assertIsInstance(self.sample_prayer_times, CairoPrayerTimes)
        self.assertEqual(self.sample_prayer_times.source, "test")
        self.assertTrue(self.sample_prayer_times.is_valid())
    
    def test_get_next_prayer(self):
        """اختبار الحصول على الصلاة التالية"""
        # اختبار في وقت قبل الفجر
        before_fajr = self.today.replace(hour=3, minute=0)
        next_prayer = self.sample_prayer_times.get_next_prayer(before_fajr)
        self.assertIsNotNone(next_prayer)
        self.assertEqual(next_prayer[0], 'fajr')
        
        # اختبار في وقت بين الظهر والعصر
        between_dhuhr_asr = self.today.replace(hour=15, minute=0)
        next_prayer = self.sample_prayer_times.get_next_prayer(between_dhuhr_asr)
        self.assertIsNotNone(next_prayer)
        self.assertEqual(next_prayer[0], 'asr')
    
    def test_get_prayer_time(self):
        """اختبار الحصول على وقت صلاة محددة"""
        fajr_time = self.sample_prayer_times.get_prayer_time('fajr')
        self.assertEqual(fajr_time.hour, 4)
        self.assertEqual(fajr_time.minute, 23)
        
        # اختبار صلاة غير موجودة
        invalid_prayer = self.sample_prayer_times.get_prayer_time('invalid')
        self.assertIsNone(invalid_prayer)
    
    def test_prayer_times_validation(self):
        """اختبار التحقق من صحة المواقيت"""
        # مواقيت صحيحة
        self.assertTrue(self.sample_prayer_times.is_valid())
        
        # مواقيت خاطئة (ترتيب خاطئ)
        invalid_times = CairoPrayerTimes(
            date=self.today,
            fajr=self.today.replace(hour=15, minute=0),  # فجر في وقت خاطئ
            dhuhr=self.today.replace(hour=13, minute=1),
            asr=self.today.replace(hour=16, minute=38),
            maghrib=self.today.replace(hour=19, minute=57),
            isha=self.today.replace(hour=21, minute=27),
            source="test",
            cached_at=datetime.now(CAIRO_TZ)
        )
        self.assertFalse(invalid_times.is_valid())
    
    def test_to_dict_and_from_dict(self):
        """اختبار التحويل إلى قاموس والعكس"""
        # تحويل إلى قاموس
        prayer_dict = self.sample_prayer_times.to_dict()
        self.assertIsInstance(prayer_dict, dict)
        self.assertIn('fajr', prayer_dict)
        self.assertIn('source', prayer_dict)
        
        # تحويل من قاموس
        restored_times = CairoPrayerTimes.from_dict(prayer_dict)
        self.assertEqual(restored_times.source, self.sample_prayer_times.source)
        self.assertEqual(restored_times.fajr, self.sample_prayer_times.fajr)

class TestEnhancedPrayerAPIClient(unittest.TestCase):
    """اختبارات عميل API المحسن"""
    
    def setUp(self):
        """إعداد عميل API للاختبار"""
        self.api_client = EnhancedPrayerAPIClient()
    
    def test_api_client_initialization(self):
        """اختبار تهيئة عميل API"""
        self.assertIsInstance(self.api_client, EnhancedPrayerAPIClient)
        self.assertEqual(self.api_client.timeout, 30)
        self.assertEqual(self.api_client.max_retries, 3)
        self.assertIn('aladhan', self.api_client.apis)
    
    def test_api_configuration(self):
        """اختبار إعدادات API"""
        # تفعيل API
        self.assertTrue(self.api_client.enable_api('aladhan'))
        
        # تعطيل API
        self.assertTrue(self.api_client.disable_api('aladhan'))
        
        # تعيين أولوية
        self.assertTrue(self.api_client.set_api_priority('aladhan', 1))
        
        # API غير موجود
        self.assertFalse(self.api_client.enable_api('nonexistent'))
    
    @patch('aiohttp.ClientSession.get')
    async def test_fetch_cairo_prayer_times_success(self, mock_get):
        """اختبار جلب مواقيت القاهرة بنجاح"""
        # إعداد mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'code': 200,
            'status': 'OK',
            'data': {
                'timings': {
                    'Fajr': '04:23',
                    'Dhuhr': '13:01',
                    'Asr': '16:38',
                    'Maghrib': '19:57',
                    'Isha': '21:27'
                }
            }
        })
        mock_get.return_value.__aenter__.return_value = mock_response
        
        # تشغيل الاختبار
        result = await self.api_client.fetch_cairo_prayer_times()
        
        # التحقق من النتيجة
        self.assertIsNotNone(result)
        self.assertIn('fajr', result)
        self.assertEqual(result['fajr'], '04:23')

class TestPrayerTimesDataValidator(unittest.TestCase):
    """اختبارات نظام التحقق من البيانات"""
    
    def setUp(self):
        """إعداد نظام التحقق للاختبار"""
        self.validator = PrayerTimesDataValidator()
        self.valid_data = {
            'timings': {
                'fajr': '04:23',
                'dhuhr': '13:01',
                'asr': '16:38',
                'maghrib': '19:57',
                'isha': '21:27'
            },
            'source': 'test'
        }
    
    def test_valid_prayer_times(self):
        """اختبار بيانات صحيحة"""
        report = self.validator.validate_prayer_times(self.valid_data)
        self.assertTrue(report.is_valid)
        self.assertGreaterEqual(report.score, 70)
    
    def test_missing_prayers(self):
        """اختبار بيانات ناقصة"""
        invalid_data = {
            'timings': {
                'fajr': '04:23',
                'dhuhr': '13:01'
                # نقص العصر والمغرب والعشاء
            }
        }
        
        report = self.validator.validate_prayer_times(invalid_data)
        self.assertFalse(report.is_valid)
        self.assertTrue(report.has_critical_issues())
    
    def test_invalid_time_format(self):
        """اختبار صيغة وقت خاطئة"""
        invalid_data = {
            'timings': {
                'fajr': 'invalid_time',
                'dhuhr': '13:01',
                'asr': '16:38',
                'maghrib': '19:57',
                'isha': '21:27'
            }
        }
        
        report = self.validator.validate_prayer_times(invalid_data)
        self.assertFalse(report.is_valid)
        error_issues = report.get_issues_by_severity(ValidationSeverity.ERROR)
        self.assertGreater(len(error_issues), 0)
    
    def test_wrong_prayer_order(self):
        """اختبار ترتيب خاطئ للصلوات"""
        invalid_data = {
            'timings': {
                'fajr': '15:00',  # فجر في وقت خاطئ
                'dhuhr': '13:01',
                'asr': '16:38',
                'maghrib': '19:57',
                'isha': '21:27'
            }
        }
        
        report = self.validator.validate_prayer_times(invalid_data)
        self.assertFalse(report.is_valid)
        self.assertLess(report.score, 70)
    
    def test_30_minute_delay_calculation(self):
        """اختبار حساب تأخير الـ 30 دقيقة"""
        prayer_time = datetime.now(CAIRO_TZ).replace(hour=13, minute=1, second=0, microsecond=0)
        correct_send_time = prayer_time + timedelta(minutes=30)
        
        report = self.validator.validate_30_minute_delay_calculation(
            prayer_time, correct_send_time, 30
        )
        
        self.assertTrue(report.is_valid)
        self.assertEqual(report.score, 100.0)
        
        # اختبار تأخير خاطئ
        wrong_send_time = prayer_time + timedelta(minutes=45)
        report = self.validator.validate_30_minute_delay_calculation(
            prayer_time, wrong_send_time, 30
        )
        
        self.assertFalse(report.is_valid)
        self.assertLess(report.score, 90)

class TestQuranSchedule(unittest.TestCase):
    """اختبارات جدولة الورد القرآني"""
    
    def setUp(self):
        """إعداد جدولة الورد للاختبار"""
        self.prayer_time = datetime.now(CAIRO_TZ).replace(hour=13, minute=1, second=0, microsecond=0)
        self.schedule = QuranSchedule(
            prayer_name='dhuhr',
            prayer_time=self.prayer_time,
            send_time=self.prayer_time + timedelta(minutes=30)
        )
    
    def test_schedule_creation(self):
        """اختبار إنشاء جدولة"""
        self.assertEqual(self.schedule.prayer_name, 'dhuhr')
        self.assertEqual(self.schedule.prayer_time, self.prayer_time)
        self.assertFalse(self.schedule.scheduled)
        self.assertFalse(self.schedule.sent)
    
    def test_calculate_send_time(self):
        """اختبار حساب وقت الإرسال"""
        calculated_time = self.schedule.calculate_send_time(30)
        expected_time = self.prayer_time + timedelta(minutes=30)
        self.assertEqual(calculated_time, expected_time)
    
    def test_is_due(self):
        """اختبار التحقق من حان وقت الإرسال"""
        # قبل الوقت
        before_time = self.schedule.send_time - timedelta(minutes=5)
        self.assertFalse(self.schedule.is_due(before_time))
        
        # في الوقت المحدد
        self.assertTrue(self.schedule.is_due(self.schedule.send_time))
        
        # بعد الوقت
        after_time = self.schedule.send_time + timedelta(minutes=5)
        self.assertTrue(self.schedule.is_due(after_time))
    
    def test_is_overdue(self):
        """اختبار التحقق من تأخر الإرسال"""
        # في الوقت المحدد
        self.assertFalse(self.schedule.is_overdue(self.schedule.send_time))
        
        # متأخر قليلاً (أقل من ساعة)
        slightly_late = self.schedule.send_time + timedelta(minutes=30)
        self.assertFalse(self.schedule.is_overdue(slightly_late, grace_minutes=60))
        
        # متأخر كثيراً (أكثر من ساعة)
        very_late = self.schedule.send_time + timedelta(minutes=90)
        self.assertTrue(self.schedule.is_overdue(very_late, grace_minutes=60))
    
    def test_to_dict(self):
        """اختبار التحويل إلى قاموس"""
        schedule_dict = self.schedule.to_dict()
        self.assertIsInstance(schedule_dict, dict)
        self.assertEqual(schedule_dict['prayer_name'], 'dhuhr')
        self.assertIn('prayer_time', schedule_dict)
        self.assertIn('send_time', schedule_dict)

class AsyncTestCase(unittest.TestCase):
    """فئة أساسية للاختبارات غير المتزامنة"""
    
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
    
    def tearDown(self):
        self.loop.close()
    
    def run_async(self, coro):
        """تشغيل دالة غير متزامنة في الاختبار"""
        return self.loop.run_until_complete(coro)

class TestPrayerTimesCache(AsyncTestCase):
    """اختبارات نظام التخزين المؤقت"""
    
    def setUp(self):
        super().setUp()
        self.cache = PrayerTimesCache(
            cache_file="test_cache.json",
            supabase_client=None
        )
        
        # إنشاء مواقيت تجريبية
        today = datetime.now(CAIRO_TZ).replace(hour=0, minute=0, second=0, microsecond=0)
        self.test_prayer_times = CairoPrayerTimes(
            date=today,
            fajr=today.replace(hour=4, minute=23),
            dhuhr=today.replace(hour=13, minute=1),
            asr=today.replace(hour=16, minute=38),
            maghrib=today.replace(hour=19, minute=57),
            isha=today.replace(hour=21, minute=27),
            source="test",
            cached_at=datetime.now(CAIRO_TZ)
        )
    
    def test_cache_initialization(self):
        """اختبار تهيئة التخزين المؤقت"""
        result = self.run_async(self.cache.initialize())
        self.assertTrue(result)
    
    def test_cache_set_and_get(self):
        """اختبار حفظ واسترجاع البيانات"""
        # تهيئة التخزين المؤقت
        self.run_async(self.cache.initialize())
        
        # حفظ البيانات
        today_str = datetime.now(CAIRO_TZ).date().isoformat()
        result = self.run_async(self.cache.set_cached_times(today_str, self.test_prayer_times))
        self.assertTrue(result)
        
        # استرجاع البيانات
        cached_times = self.run_async(self.cache.get_cached_times(today_str))
        self.assertIsNotNone(cached_times)
        self.assertEqual(cached_times.source, "test")
    
    def test_cache_miss(self):
        """اختبار عدم وجود بيانات في التخزين المؤقت"""
        self.run_async(self.cache.initialize())
        
        # محاولة جلب بيانات غير موجودة
        cached_times = self.run_async(self.cache.get_cached_times("2025-01-01"))
        self.assertIsNone(cached_times)
    
    def tearDown(self):
        super().tearDown()
        # تنظيف ملف الاختبار
        import os
        if os.path.exists("test_cache.json"):
            os.remove("test_cache.json")

if __name__ == '__main__':
    # تشغيل جميع الاختبارات
    unittest.main(verbosity=2)