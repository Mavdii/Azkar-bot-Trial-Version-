#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🕌 Enhanced Prayer API Client - عميل API محسن لمواقيت الصلاة
================================================================
عميل API قوي مع دعم عدة مصادر احتياطية لضمان الموثوقية

Features:
- 🔄 دعم عدة APIs مع نظام fallback ذكي
- 🕌 تخصص في مواقيت القاهرة
- 🛡️ معالجة شاملة للأخطاء مع إعادة المحاولة
- ⚡ تحقق من صحة البيانات قبل الإرجاع
- 📊 إحصائيات مفصلة للأداء

Author: Islamic Bot Developer Team
Version: 1.0.0
License: MIT
"""

import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import pytz
from dataclasses import dataclass
import json
import time

# Configure logging
logger = logging.getLogger(__name__)

# Cairo timezone
CAIRO_TZ = pytz.timezone('Africa/Cairo')

@dataclass
class APIResponse:
    """نموذج استجابة API"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    source: Optional[str] = None
    response_time: float = 0.0
    status_code: Optional[int] = None

class EnhancedPrayerAPIClient:
    """عميل API محسن لمواقيت الصلاة مع نظام fallback"""
    
    def __init__(self, timeout: int = 30, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries
        
        # إعدادات APIs
        self.apis = {
            'aladhan': {
                'url': 'https://api.aladhan.com/v1/timingsByCity',
                'params': {
                    'city': 'Cairo',
                    'country': 'Egypt',
                    'method': 5,  # Egyptian General Authority of Survey
                    'school': 0   # Shafi
                },
                'enabled': True,
                'priority': 1
            },
            'islamicfinder': {
                'url': 'https://www.islamicfinder.org/api/prayer_times',
                'params': {
                    'city': 'Cairo',
                    'country': 'Egypt',
                    'juristic': 0,  # Shafi
                    'method': 5
                },
                'enabled': True,
                'priority': 2
            },
            'prayertimes': {
                'url': 'https://api.pray.zone/v2/times/today.json',
                'params': {
                    'city': 'cairo'
                },
                'enabled': True,
                'priority': 3
            }
        }
        
        # إحصائيات
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'api_usage': {},
            'average_response_time': 0.0,
            'last_successful_api': None,
            'last_request_time': None
        }
        
        # تهيئة إحصائيات APIs
        for api_name in self.apis.keys():
            self.stats['api_usage'][api_name] = {
                'requests': 0,
                'successes': 0,
                'failures': 0,
                'average_response_time': 0.0,
                'last_success': None,
                'last_failure': None
            }
    
    async def fetch_cairo_prayer_times(self) -> Optional[Dict[str, Any]]:
        """جلب مواقيت الصلاة للقاهرة مع نظام fallback"""
        start_time = time.time()
        self.stats['total_requests'] += 1
        self.stats['last_request_time'] = datetime.now().isoformat()
        
        # ترتيب APIs حسب الأولوية
        sorted_apis = sorted(
            [(name, config) for name, config in self.apis.items() if config['enabled']],
            key=lambda x: x[1]['priority']
        )
        
        last_error = None
        
        for api_name, api_config in sorted_apis:
            try:
                logger.info(f"🔄 محاولة جلب المواقيت من {api_name}")
                
                # محاولة جلب من API
                response = await self._fetch_from_api(api_name, api_config)
                
                if response.success and response.data:
                    # تحويل البيانات إلى تنسيق موحد
                    standardized_data = await self._standardize_response(response.data, api_name)
                    
                    if standardized_data and await self._validate_prayer_times(standardized_data):
                        # تحديث الإحصائيات
                        self.stats['successful_requests'] += 1
                        self.stats['last_successful_api'] = api_name
                        self._update_api_stats(api_name, True, response.response_time)
                        
                        # تحديث متوسط وقت الاستجابة العام
                        total_time = time.time() - start_time
                        self._update_average_response_time(total_time)
                        
                        logger.info(f"✅ تم جلب المواقيت بنجاح من {api_name}")
                        
                        # إضافة معلومات المصدر
                        standardized_data['source'] = api_name
                        standardized_data['response_time'] = response.response_time
                        
                        return standardized_data
                    else:
                        logger.warning(f"⚠️ بيانات غير صحيحة من {api_name}")
                        last_error = f"بيانات غير صحيحة من {api_name}"
                else:
                    logger.warning(f"⚠️ فشل في جلب البيانات من {api_name}: {response.error}")
                    last_error = response.error
                
                # تحديث إحصائيات الفشل
                self._update_api_stats(api_name, False, response.response_time)
                
            except Exception as e:
                logger.error(f"❌ خطأ في {api_name}: {e}")
                last_error = str(e)
                self._update_api_stats(api_name, False, 0)
                continue
        
        # فشل جميع APIs
        self.stats['failed_requests'] += 1
        logger.error(f"❌ فشل جميع APIs: {last_error}")
        
        return None
    
    async def _fetch_from_api(self, api_name: str, api_config: Dict[str, Any]) -> APIResponse:
        """جلب البيانات من API محدد مع إعادة المحاولة"""
        url = api_config['url']
        params = api_config['params'].copy()
        
        for attempt in range(self.max_retries):
            start_time = time.time()
            
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                    async with session.get(url, params=params) as response:
                        response_time = time.time() - start_time
                        
                        if response.status == 200:
                            data = await response.json()
                            return APIResponse(
                                success=True,
                                data=data,
                                source=api_name,
                                response_time=response_time,
                                status_code=response.status
                            )
                        else:
                            error_msg = f"HTTP {response.status}"
                            if attempt < self.max_retries - 1:
                                logger.warning(f"⚠️ {api_name} attempt {attempt + 1} failed: {error_msg}, retrying...")
                                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                                continue
                            else:
                                return APIResponse(
                                    success=False,
                                    error=error_msg,
                                    source=api_name,
                                    response_time=response_time,
                                    status_code=response.status
                                )
            
            except asyncio.TimeoutError:
                error_msg = "Timeout"
                if attempt < self.max_retries - 1:
                    logger.warning(f"⚠️ {api_name} timeout attempt {attempt + 1}, retrying...")
                    await asyncio.sleep(2 ** attempt)
                    continue
                else:
                    return APIResponse(
                        success=False,
                        error=error_msg,
                        source=api_name,
                        response_time=time.time() - start_time
                    )
            
            except Exception as e:
                error_msg = str(e)
                if attempt < self.max_retries - 1:
                    logger.warning(f"⚠️ {api_name} error attempt {attempt + 1}: {error_msg}, retrying...")
                    await asyncio.sleep(2 ** attempt)
                    continue
                else:
                    return APIResponse(
                        success=False,
                        error=error_msg,
                        source=api_name,
                        response_time=time.time() - start_time
                    )
        
        return APIResponse(
            success=False,
            error="Max retries exceeded",
            source=api_name,
            response_time=0
        )
    
    async def _standardize_response(self, data: Dict[str, Any], api_name: str) -> Optional[Dict[str, str]]:
        """توحيد تنسيق الاستجابة من APIs مختلفة"""
        try:
            if api_name == 'aladhan':
                return await self._standardize_aladhan_response(data)
            elif api_name == 'islamicfinder':
                return await self._standardize_islamicfinder_response(data)
            elif api_name == 'prayertimes':
                return await self._standardize_prayertimes_response(data)
            else:
                logger.error(f"❌ API غير مدعوم: {api_name}")
                return None
                
        except Exception as e:
            logger.error(f"❌ خطأ في توحيد استجابة {api_name}: {e}")
            return None
    
    async def _standardize_aladhan_response(self, data: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """توحيد استجابة Aladhan API"""
        try:
            if data.get('code') != 200 or data.get('status') != 'OK':
                logger.error(f"❌ خطأ في استجابة Aladhan: {data.get('status', 'Unknown')}")
                return None
            
            timings = data['data']['timings']
            
            return {
                'fajr': timings['Fajr'].split(' ')[0],  # إزالة المنطقة الزمنية
                'dhuhr': timings['Dhuhr'].split(' ')[0],
                'asr': timings['Asr'].split(' ')[0],
                'maghrib': timings['Maghrib'].split(' ')[0],
                'isha': timings['Isha'].split(' ')[0]
            }
            
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة استجابة Aladhan: {e}")
            return None
    
    async def _standardize_islamicfinder_response(self, data: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """توحيد استجابة Islamic Finder API"""
        try:
            # تنسيق Islamic Finder قد يختلف، هذا مثال
            if 'results' not in data:
                return None
            
            results = data['results']
            
            return {
                'fajr': results.get('Fajr', ''),
                'dhuhr': results.get('Dhuhr', ''),
                'asr': results.get('Asr', ''),
                'maghrib': results.get('Maghrib', ''),
                'isha': results.get('Isha', '')
            }
            
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة استجابة Islamic Finder: {e}")
            return None
    
    async def _standardize_prayertimes_response(self, data: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """توحيد استجابة Prayer Times API"""
        try:
            # تنسيق Prayer Times قد يختلف، هذا مثال
            if 'results' not in data:
                return None
            
            results = data['results']
            datetime_obj = results.get('datetime', [{}])[0]
            times = datetime_obj.get('times', {})
            
            return {
                'fajr': times.get('Fajr', ''),
                'dhuhr': times.get('Dhuhr', ''),
                'asr': times.get('Asr', ''),
                'maghrib': times.get('Maghrib', ''),
                'isha': times.get('Isha', '')
            }
            
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة استجابة Prayer Times: {e}")
            return None
    
    async def _validate_prayer_times(self, times: Dict[str, str]) -> bool:
        """التحقق من صحة مواقيت الصلاة"""
        try:
            required_prayers = ['fajr', 'dhuhr', 'asr', 'maghrib', 'isha']
            
            # التحقق من وجود جميع الصلوات
            for prayer in required_prayers:
                if prayer not in times or not times[prayer]:
                    logger.error(f"❌ صلاة {prayer} مفقودة")
                    return False
            
            # التحقق من صيغة الوقت
            parsed_times = []
            for prayer in required_prayers:
                time_str = times[prayer]
                try:
                    # التحقق من صيغة HH:MM
                    if ':' not in time_str:
                        logger.error(f"❌ صيغة وقت غير صحيحة لـ {prayer}: {time_str}")
                        return False
                    
                    hour, minute = map(int, time_str.split(':'))
                    
                    # التحقق من صحة الساعة والدقيقة
                    if not (0 <= hour <= 23) or not (0 <= minute <= 59):
                        logger.error(f"❌ وقت غير صحيح لـ {prayer}: {time_str}")
                        return False
                    
                    # تحويل إلى datetime للمقارنة
                    today = datetime.now(CAIRO_TZ).date()
                    prayer_time = CAIRO_TZ.localize(
                        datetime(today.year, today.month, today.day, hour, minute)
                    )
                    parsed_times.append((prayer, prayer_time))
                    
                except ValueError as e:
                    logger.error(f"❌ خطأ في تحويل وقت {prayer}: {time_str} - {e}")
                    return False
            
            # التحقق من ترتيب الصلوات
            for i in range(len(parsed_times) - 1):
                current_prayer, current_time = parsed_times[i]
                next_prayer, next_time = parsed_times[i + 1]
                
                if current_time >= next_time:
                    logger.error(f"❌ ترتيب خاطئ: {current_prayer} ({current_time.strftime('%H:%M')}) >= {next_prayer} ({next_time.strftime('%H:%M')})")
                    return False
            
            # التحقق من أن الأوقات معقولة للقاهرة
            fajr_hour = parsed_times[0][1].hour
            dhuhr_hour = parsed_times[1][1].hour
            asr_hour = parsed_times[2][1].hour
            maghrib_hour = parsed_times[3][1].hour
            isha_hour = parsed_times[4][1].hour
            
            # فحص نطاقات معقولة للقاهرة
            if not (3 <= fajr_hour <= 6):
                logger.error(f"❌ وقت الفجر غير معقول للقاهرة: {fajr_hour}:xx")
                return False
            
            if not (11 <= dhuhr_hour <= 14):
                logger.error(f"❌ وقت الظهر غير معقول للقاهرة: {dhuhr_hour}:xx")
                return False
            
            if not (14 <= asr_hour <= 18):
                logger.error(f"❌ وقت العصر غير معقول للقاهرة: {asr_hour}:xx")
                return False
            
            if not (17 <= maghrib_hour <= 20):
                logger.error(f"❌ وقت المغرب غير معقول للقاهرة: {maghrib_hour}:xx")
                return False
            
            if not (19 <= isha_hour <= 23):
                logger.error(f"❌ وقت العشاء غير معقول للقاهرة: {isha_hour}:xx")
                return False
            
            logger.debug("✅ تم التحقق من صحة المواقيت بنجاح")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في التحقق من صحة المواقيت: {e}")
            return False
    
    def _update_api_stats(self, api_name: str, success: bool, response_time: float) -> None:
        """تحديث إحصائيات API"""
        try:
            api_stats = self.stats['api_usage'][api_name]
            api_stats['requests'] += 1
            
            if success:
                api_stats['successes'] += 1
                api_stats['last_success'] = datetime.now().isoformat()
            else:
                api_stats['failures'] += 1
                api_stats['last_failure'] = datetime.now().isoformat()
            
            # تحديث متوسط وقت الاستجابة للـ API
            if api_stats['requests'] == 1:
                api_stats['average_response_time'] = response_time
            else:
                current_avg = api_stats['average_response_time']
                requests = api_stats['requests']
                api_stats['average_response_time'] = (
                    (current_avg * (requests - 1) + response_time) / requests
                )
                
        except Exception as e:
            logger.error(f"❌ خطأ في تحديث إحصائيات {api_name}: {e}")
    
    def _update_average_response_time(self, response_time: float) -> None:
        """تحديث متوسط وقت الاستجابة العام"""
        try:
            current_avg = self.stats['average_response_time']
            total_requests = self.stats['total_requests']
            
            if total_requests == 1:
                self.stats['average_response_time'] = response_time
            else:
                self.stats['average_response_time'] = (
                    (current_avg * (total_requests - 1) + response_time) / total_requests
                )
                
        except Exception as e:
            logger.error(f"❌ خطأ في تحديث متوسط وقت الاستجابة: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """الحصول على إحصائيات مفصلة"""
        return {
            'general_stats': {
                'total_requests': self.stats['total_requests'],
                'successful_requests': self.stats['successful_requests'],
                'failed_requests': self.stats['failed_requests'],
                'success_rate': (
                    (self.stats['successful_requests'] / self.stats['total_requests'] * 100)
                    if self.stats['total_requests'] > 0 else 0
                ),
                'average_response_time': self.stats['average_response_time'],
                'last_successful_api': self.stats['last_successful_api'],
                'last_request_time': self.stats['last_request_time']
            },
            'api_stats': self.stats['api_usage'].copy()
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """الحصول على حالة صحة APIs"""
        try:
            healthy_apis = []
            unhealthy_apis = []
            
            for api_name, api_stats in self.stats['api_usage'].items():
                if api_stats['requests'] > 0:
                    success_rate = (api_stats['successes'] / api_stats['requests']) * 100
                    if success_rate >= 70:  # 70% success rate threshold
                        healthy_apis.append(api_name)
                    else:
                        unhealthy_apis.append(api_name)
                else:
                    # لم يتم اختبار API بعد
                    if self.apis[api_name]['enabled']:
                        healthy_apis.append(api_name)
            
            # تحديد الحالة العامة
            if len(healthy_apis) == 0:
                status = "critical"
                message = "لا توجد APIs صحية"
            elif len(unhealthy_apis) > 0:
                status = "warning"
                message = f"{len(healthy_apis)} APIs صحية، {len(unhealthy_apis)} غير صحية"
            else:
                status = "healthy"
                message = f"جميع {len(healthy_apis)} APIs تعمل بشكل طبيعي"
            
            return {
                'status': status,
                'message': message,
                'healthy_apis': healthy_apis,
                'unhealthy_apis': unhealthy_apis,
                'total_apis': len(self.apis),
                'enabled_apis': len([api for api in self.apis.values() if api['enabled']])
            }
            
        except Exception as e:
            logger.error(f"❌ خطأ في فحص حالة APIs: {e}")
            return {
                'status': 'error',
                'message': f'خطأ في فحص الحالة: {e}',
                'healthy_apis': [],
                'unhealthy_apis': [],
                'total_apis': 0,
                'enabled_apis': 0
            }
    
    def enable_api(self, api_name: str) -> bool:
        """تفعيل API"""
        if api_name in self.apis:
            self.apis[api_name]['enabled'] = True
            logger.info(f"✅ تم تفعيل {api_name}")
            return True
        else:
            logger.error(f"❌ API غير موجود: {api_name}")
            return False
    
    def disable_api(self, api_name: str) -> bool:
        """تعطيل API"""
        if api_name in self.apis:
            self.apis[api_name]['enabled'] = False
            logger.info(f"⚠️ تم تعطيل {api_name}")
            return True
        else:
            logger.error(f"❌ API غير موجود: {api_name}")
            return False
    
    def set_api_priority(self, api_name: str, priority: int) -> bool:
        """تعيين أولوية API"""
        if api_name in self.apis:
            self.apis[api_name]['priority'] = priority
            logger.info(f"✅ تم تعيين أولوية {api_name} إلى {priority}")
            return True
        else:
            logger.error(f"❌ API غير موجود: {api_name}")
            return False
    
    def __str__(self) -> str:
        enabled_count = len([api for api in self.apis.values() if api['enabled']])
        return f"EnhancedPrayerAPIClient(enabled_apis={enabled_count}/{len(self.apis)})"
    
    def __repr__(self) -> str:
        return f"EnhancedPrayerAPIClient(timeout={self.timeout}, max_retries={self.max_retries}, stats={self.stats['total_requests']} requests)"


# Export للاستخدام في الملفات الأخرى
__all__ = ['EnhancedPrayerAPIClient', 'APIResponse']