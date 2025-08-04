#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة الأذكار للبوت الإسلامي
تتعامل مع قراءة وإدارة الأذكار من الملفات
"""

import json
import random
import os
import logging
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class DhikrService:
    """خدمة إدارة الأذكار"""
    
    def __init__(self, content_file: str = "data/dhikr_content.txt"):
        self.content_file = content_file
        self.dhikr_list: List[Dict] = []
        self.morning_images_dir = "morning_dhikr_images"
        self.evening_images_dir = "evening_dhikr_images"
        self.load_dhikr_content()
        self._ensure_image_directories()
    
    def _ensure_image_directories(self):
        """التأكد من وجود مجلدات صور الأذكار"""
        os.makedirs(self.morning_images_dir, exist_ok=True)
        os.makedirs(self.evening_images_dir, exist_ok=True)
    
    def load_dhikr_content(self) -> bool:
        """تحميل محتوى الأذكار من الملف"""
        try:
            if os.path.exists(self.content_file):
                with open(self.content_file, 'r', encoding='utf-8') as f:
                    self.dhikr_list = json.load(f)
                logger.info(f"✅ تم تحميل {len(self.dhikr_list)} ذكر من الملف")
                return True
            else:
                logger.warning(f"⚠️ ملف الأذكار غير موجود: {self.content_file}")
                self._load_default_dhikr()
                return False
        except Exception as e:
            logger.error(f"❌ خطأ في تحميل الأذكار: {e}")
            self._load_default_dhikr()
            return False
    
    def _load_default_dhikr(self):
        """تحميل أذكار افتراضية في حالة فشل قراءة الملف"""
        self.dhikr_list = [
            {
                "text": "لَا إِلَٰهَ إِلَّا اللَّهُ وَحْدَهُ لَا شَرِيكَ لَهُ، لَهُ الْمُلْكُ وَلَهُ الْحَمْدُ وَهُوَ عَلَىٰ كُلِّ شَيْءٍ قَدِيرٌ",
                "benefit": "من قالها عشر مرات كان كمن أعتق أربعة أنفس من ولد إسماعيل",
                "source": "صحيح البخاري",
                "category": "dhikr"
            },
            {
                "text": "سُبْحَانَ اللَّهِ وَبِحَمْدِهِ، سُبْحَانَ اللَّهِ الْعَظِيمِ",
                "benefit": "كلمتان خفيفتان على اللسان، ثقيلتان في الميزان، حبيبتان إلى الرحمن",
                "source": "صحيح البخاري",
                "category": "dhikr"
            },
            {
                "text": "اللَّهُمَّ صَلِّ وَسَلِّمْ وَبَارِكْ عَلَى نَبِيِّنَا مُحَمَّدٍ",
                "benefit": "من صلى عليّ صلاة صلى الله عليه بها عشراً",
                "source": "صحيح مسلم",
                "category": "dhikr"
            }
        ]
        logger.info("✅ تم تحميل الأذكار الافتراضية")
    
    def get_random_dhikr(self) -> Dict:
        """الحصول على ذكر عشوائي"""
        if not self.dhikr_list:
            self._load_default_dhikr()
        
        return random.choice(self.dhikr_list)
    
    def get_morning_dhikr_images(self) -> List[str]:
        """الحصول على صور أذكار الصباح"""
        try:
            image_files = []
            if os.path.exists(self.morning_images_dir):
                # البحث عن الصور بترتيب الأرقام
                for i in range(1, 21):  # نفترض أن هناك حتى 20 صورة
                    for ext in ['jpg', 'jpeg', 'png', 'webp']:
                        filename = f"{i:02d}.{ext}"  # 01.jpg, 02.jpg, etc.
                        filepath = os.path.join(self.morning_images_dir, filename)
                        if os.path.exists(filepath):
                            image_files.append(filepath)
                            break
                
                # إذا لم نجد صور مرقمة، نبحث عن أي صور
                if not image_files:
                    for filename in os.listdir(self.morning_images_dir):
                        if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                            image_files.append(os.path.join(self.morning_images_dir, filename))
            
            if image_files:
                logger.info(f"✅ تم العثور على {len(image_files)} صورة لأذكار الصباح")
            else:
                logger.warning("⚠️ لم يتم العثور على صور أذكار الصباح")
            
            return sorted(image_files)
        
        except Exception as e:
            logger.error(f"❌ خطأ في الحصول على صور أذكار الصباح: {e}")
            return []
    
    def get_evening_dhikr_images(self) -> List[str]:
        """الحصول على صور أذكار المساء"""
        try:
            image_files = []
            if os.path.exists(self.evening_images_dir):
                # البحث عن الصور بترتيب الأرقام
                for i in range(1, 21):  # نفترض أن هناك حتى 20 صورة
                    for ext in ['jpg', 'jpeg', 'png', 'webp']:
                        filename = f"{i:02d}.{ext}"  # 01.jpg, 02.jpg, etc.
                        filepath = os.path.join(self.evening_images_dir, filename)
                        if os.path.exists(filepath):
                            image_files.append(filepath)
                            break
                
                # إذا لم نجد صور مرقمة، نبحث عن أي صور
                if not image_files:
                    for filename in os.listdir(self.evening_images_dir):
                        if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                            image_files.append(os.path.join(self.evening_images_dir, filename))
            
            if image_files:
                logger.info(f"✅ تم العثور على {len(image_files)} صورة لأذكار المساء")
            else:
                logger.warning("⚠️ لم يتم العثور على صور أذكار المساء")
            
            return sorted(image_files)
        
        except Exception as e:
            logger.error(f"❌ خطأ في الحصول على صور أذكار المساء: {e}")
            return []
    
    def format_dhikr_message(self, dhikr: Dict) -> str:
        """تنسيق رسالة الذكر"""
        try:
            message = "🌟 **ذِكْرُ اللهِ** 🌟\n\n"
            message += f"**{dhikr['text']}**\n\n"
            
            if dhikr.get('benefit'):
                if dhikr.get('category') == 'quran':
                    message += f"📖 **الفضل:** {dhikr['benefit']}\n"
                elif dhikr.get('category') == 'hadith':
                    message += f"🌟 **الحديث:** {dhikr['benefit']}\n"
                else:
                    message += f"✨ **الفضل:** {dhikr['benefit']}\n"
            
            if dhikr.get('source'):
                message += f"📚 **المصدر:** {dhikr['source']}\n\n"
            
            message += "🤲 **اللهم اجعلنا من الذاكرين الله كثيراً والذاكرات**"
            
            return message
        
        except Exception as e:
            logger.error(f"❌ خطأ في تنسيق رسالة الذكر: {e}")
            return "🌟 **ذِكْرُ اللهِ** 🌟\n\n**سُبْحَانَ اللَّهِ وَبِحَمْدِهِ**"
    
    def get_dhikr_by_category(self, category: str) -> List[Dict]:
        """الحصول على الأذكار حسب الفئة"""
        try:
            return [dhikr for dhikr in self.dhikr_list if dhikr.get('category') == category]
        except Exception as e:
            logger.error(f"❌ خطأ في الحصول على الأذكار حسب الفئة: {e}")
            return []
    
    def get_stats(self) -> Dict:
        """الحصول على إحصائيات الأذكار"""
        try:
            stats = {
                'total_dhikr': len(self.dhikr_list),
                'morning_images': len(self.get_morning_dhikr_images()),
                'evening_images': len(self.get_evening_dhikr_images()),
                'categories': {}
            }
            
            # إحصائيات الفئات
            for dhikr in self.dhikr_list:
                category = dhikr.get('category', 'other')
                stats['categories'][category] = stats['categories'].get(category, 0) + 1
            
            return stats
        
        except Exception as e:
            logger.error(f"❌ خطأ في الحصول على إحصائيات الأذكار: {e}")
            return {'total_dhikr': 0, 'morning_images': 0, 'evening_images': 0, 'categories': {}}