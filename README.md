# 🕌 البوت الإسلامي الشامل - Comprehensive Islamic Telegram Bot

<div align="center">

![Islamic Bot Logo](https://img.shields.io/badge/🕌-Islamic%20Bot-green?style=for-the-badge)
![Python Version](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python)
![Telegram Bot API](https://img.shields.io/badge/Telegram-Bot%20API-blue?style=for-the-badge&logo=telegram)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Version](https://img.shields.io/badge/Version-3.0.0-orange?style=for-the-badge)

**بوت تليجرام إسلامي شامل مع أكثر من 300 ذكر أصيل وميزات متقدمة**

[العربية](#العربية) | [English](#english) | [Features](#features) | [Installation](#installation) | [Documentation](#documentation)

</div>

---

## 📋 المحتويات

- [🌟 المميزات الرئيسية](#-المميزات-الرئيسية)
- [🚀 التثبيت السريع](#-التثبيت-السريع)
- [⚙️ الإعداد والتكوين](#️-الإعداد-والتكوين)
- [📱 الاستخدام](#-الاستخدام)
- [🗄️ قاعدة البيانات](#️-قاعدة-البيانات)
- [🔧 التطوير](#-التطوير)
- [📚 التوثيق](#-التوثيق)
- [🤝 المساهمة](#-المساهمة)
- [📄 الترخيص](#-الترخيص)

---

## 🌟 المميزات الرئيسية

### 📿 **الأذكار والتسبيح**
- **300+ ذكر أصيل** مع المصادر الشرعية
- **أذكار الصباح والمساء** في أوقاتها المحددة
- **أذكار ما بعد الصلاة** تلقائياً
- **أذكار عشوائية** على فترات منتظمة
- **تنسيق جميل** مع الفوائد والمصادر

### 🕐 **تذكير الصلوات**
- **مواقيت دقيقة** لمدينة القاهرة
- **تنبيهات مسبقة** قبل الصلاة بـ 5 دقائق
- **رسائل تذكير** بلهجة مصرية مؤثرة
- **تحديث تلقائي** للمواقيت يومياً

### 📖 **الورد القرآني اليومي**
- **3 صفحات** بعد كل صلاة
- **تتبع التقدم** في قراءة المصحف
- **إحصائيات مفصلة** للقراءة
- **إعادة تشغيل** عند إكمال المصحف

### 🎨 **واجهة احترافية**
- **تصميم عربي** متوافق مع RTL
- **أزرار تفاعلية** سهلة الاستخدام
- **رسائل منسقة** بشكل جميل
- **إيموجي مناسبة** للمحتوى الإسلامي

### 🗄️ **قاعدة بيانات متقدمة**
- **Supabase PostgreSQL** للموثوقية
- **إحصائيات شاملة** لكل مجموعة
- **نسخ احتياطي** تلقائي
- **أداء محسن** مع الفهارس

---

## 🚀 التثبيت السريع

### 📋 المتطلبات الأساسية

```bash
# Python 3.8 أو أحدث
python --version

# Git للتحكم في الإصدارات
git --version

# PostgreSQL (اختياري - يمكن استخدام Supabase)
psql --version
```

### 📥 تحميل المشروع

```bash
# استنساخ المستودع
git clone https://github.com/yourusername/islamic-telegram-bot.git
cd islamic-telegram-bot

# إنشاء بيئة افتراضية
python -m venv venv

# تفعيل البيئة الافتراضية
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# تثبيت المتطلبات
pip install -r requirements.txt
```

### 🔧 الإعداد الأولي

```bash
# نسخ ملف الإعدادات
cp .env.example .env

# تحرير الإعدادات
nano .env  # أو أي محرر نصوص
```

---

## ⚙️ الإعداد والتكوين

### 🤖 إنشاء بوت تليجرام

1. تحدث مع [@BotFather](https://t.me/BotFather) على تليجرام
2. أرسل `/newbot` واتبع التعليمات
3. احفظ الـ **Bot Token** الذي ستحصل عليه

### 🗄️ إعداد قاعدة البيانات

#### استخدام Supabase (مُوصى به)

1. اذهب إلى [Supabase](https://supabase.com)
2. أنشئ مشروع جديد
3. احصل على **URL** و **API Key**
4. شغل ملف `islamic_bot_database.sql` في SQL Editor

#### استخدام PostgreSQL محلي

```bash
# إنشاء قاعدة البيانات
createdb islamic_bot

# تشغيل ملف SQL
psql -d islamic_bot -f islamic_bot_database.sql
```

### 📝 تحرير ملف .env

```env
# معلومات البوت الأساسية
BOT_TOKEN=your_telegram_bot_token_here
DEVELOPER_ID=your_telegram_user_id
DEVELOPER_USERNAME=@yourusername

# إعدادات قاعدة البيانات
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key

# إعدادات الأوقات
MORNING_DHIKR_TIME=05:30
EVENING_DHIKR_TIME=19:30
DHIKR_INTERVAL_MINUTES=5
```

---

## 📱 الاستخدام

### 🚀 تشغيل البوت

```bash
# تشغيل البوت
python premium_Azkar.py

# تشغيل في الخلفية (Linux/Mac)
nohup python premium_Azkar.py &

# تشغيل مع إعادة التشغيل التلقائي
python -m supervisor premium_Azkar.py
```

### 📋 الأوامر المتاحة

| الأمر | الوصف |
|-------|--------|
| `/start` | بدء البوت وعرض الترحيب |
| `/help` | عرض دليل المساعدة |
| `/dhikr` | الحصول على ذكر عشوائي |
| `/morning` | عرض أذكار الصباح |
| `/evening` | عرض أذكار المساء |
| `/quran_progress` | عرض تقدم قراءة القرآن |
| `/quran_manual` | إرسال الورد القرآني يدوياً |

### 🕐 الجدولة التلقائية

البوت يعمل تلقائياً على الجدولة التالية:

- **أذكار الصباح**: 5:30 صباحاً
- **أذكار المساء**: 7:30 مساءً
- **تذكير الصلوات**: حسب المواقيت
- **الورد القرآني**: بعد كل صلاة بـ 30 دقيقة
- **أذكار عشوائية**: كل 5 دقائق

---

## 🗄️ قاعدة البيانات

### 📊 الجداول الرئيسية

```sql
-- المجموعات المسجلة
groups (id, chat_id, group_name, is_active, ...)

-- إعدادات كل مجموعة
group_settings (id, chat_id, dhikr_enabled, prayer_reminders, ...)

-- تقدم قراءة القرآن
quran_progress (id, chat_id, current_page, completion_count, ...)

-- إحصائيات الأذكار
dhikr_stats (id, chat_id, dhikr_type, sent_count, ...)

-- سجل الأنشطة
activity_log (id, chat_id, activity_type, success, ...)
```

### 🔧 الدوال المساعدة

```sql
-- حساب نسبة تقدم القرآن
calculate_quran_progress_percentage(current_page)

-- الحصول على رقم الجزء من الصفحة
get_juz_from_page(page_number)

-- تحديث الإحصائيات اليومية
update_bot_daily_stats()
```

---

## 🔧 التطوير

### 🏗️ هيكل المشروع

```
islamic-telegram-bot/
├── 📄 premium_Azkar.py          # الملف الرئيسي للبوت
├── ⚙️ config.py                # إدارة الإعدادات
├── 🗄️ islamic_bot_database.sql # ملف قاعدة البيانات
├── 📋 requirements.txt         # متطلبات Python
├── 🔒 .env.example             # مثال على ملف الإعدادات
├── 📝 .gitignore              # ملفات Git المتجاهلة
├── 📚 README.md               # هذا الملف
├── 📁 post_prayer_images/     # صور أذكار ما بعد الصلاة
├── 🔧 prayer_times_api.py     # API مواقيت الصلاة
├── 📖 quran_manager.py        # إدارة الورد القرآني
└── ⏰ quran_scheduler.py      # جدولة القرآن
```

### 🧪 اختبار البوت

```bash
# تشغيل الاختبارات
python -m pytest tests/

# اختبار التغطية
python -m pytest --cov=. tests/

# اختبار الأداء
python -m pytest --benchmark-only tests/
```

### 🔍 تصحيح الأخطاء

```bash
# تشغيل مع مستوى تسجيل مفصل
LOG_LEVEL=DEBUG python premium_Azkar.py

# مراقبة ملف السجل
tail -f islamic_bot.log

# فحص قاعدة البيانات
python -c "from config import config; config.print_config_summary()"
```

---

## 📚 التوثيق

### 📖 الوثائق المتاحة

- [📋 دليل التثبيت المفصل](docs/installation.md)
- [⚙️ دليل الإعدادات](docs/configuration.md)
- [🗄️ وثائق قاعدة البيانات](docs/database.md)
- [🔧 دليل المطورين](docs/development.md)
- [❓ الأسئلة الشائعة](docs/faq.md)

### 🎯 أمثلة الاستخدام

```python
# إضافة ذكر جديد
قم بإضافة أذكار جديدة حيثما تشاء فى ملف Azkar.txt لكن مع الحفاظ على نفس الترتيب كي لا تواجه اي اخطاء 

# تخصيص أوقات الأذكار
config.MORNING_DHIKR_TIME = "06:00"
config.EVENING_DHIKR_TIME = "18:00"

# إضافة مجموعة جديدة
await register_group(chat_id=-1001234567890, chat_title="مجموعة الأذكار")
```

---

## 🤝 المساهمة

نرحب بمساهماتكم في تطوير البوت! 

### 🔄 خطوات المساهمة

1. **Fork** المستودع
2. أنشئ **branch** جديد للميزة
3. اكتب **اختبارات** للكود الجديد
4. تأكد من **جودة الكود**
5. أرسل **Pull Request**

### 📋 إرشادات المساهمة

```bash
# استنساخ مستودعك
git clone https://github.com/Mavdii/Azkar-bot-Trial-Version.git

# إنشاء branch جديد
git checkout -b feature/new-feature

# إضافة التغييرات
git add .
git commit -m "إضافة ميزة جديدة"

# رفع التغييرات
git push origin feature/new-feature
```

### 🎯 مجالات المساهمة

- 📿 **إضافة أذكار جديدة** مع المصادر
- 🌍 **ترجمة البوت** للغات أخرى
- 🎨 **تحسين الواجهة** والتصميم
- 🔧 **إصلاح الأخطاء** والمشاكل
- 📚 **تحسين التوثيق**
- 🧪 **كتابة اختبارات** جديدة

---

## 🏆 المساهمون
Dev : Omar mahdy 

<div align="center">

</div>

---

---

## 🔗 روابط مفيدة

- [📱 Telegram Bot API](https://core.telegram.org/bots/api)
- [🗄️ Supabase Documentation](https://supabase.com/docs)
- [🐍 Python Telegram Bot](https://python-telegram-bot.readthedocs.io/)
- [🕐 Prayer Times API](https://aladhan.com/prayer-times-api)
- [📖 Quran API](https://alquran.cloud/api)

---

## 📞 الدعم والتواصل

### 💬 طرق التواصل

- **Telegram**: t.me/Mavdiii
- **Email**: omarelmhdi@gmail.com
- **GitHub Issues**: [إبلاغ عن مشكلة](https://github.com/Mavdii/Azkar-bot-Trial-Version/issues)


### ❓ الحصول على المساعدة

1. **اقرأ التوثيق** أولاً
2. **ابحث في Issues** الموجودة
3. **أنشئ Issue جديد** مع التفاصيل
4. **انتظر الرد** من الفريق

---

## 📄 الترخيص

هذا المشروع مرخص تحت رخصة **MIT License** - انظر ملف [LICENSE](LICENSE) للتفاصيل.

```
MIT License

Copyright (c) 2024 Islamic Bot Developer Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 🙏 شكر وتقدير

### 📚 المصادر الشرعية

- **القرآن الكريم** - المصدر الأول للآيات
- **صحيح البخاري** - للأحاديث النبوية
- **صحيح مسلم** - للأحاديث النبوية
- **سنن أبي داود** - للأحاديث والأدعية
- **سنن الترمذي** - للأحاديث والأذكار

### 🛠️ الأدوات والمكتبات

- **Python Telegram Bot** - إطار عمل البوت
- **Supabase** - قاعدة البيانات
- **Aladhan API** - مواقيت الصلاة
- **PyTZ** - التوقيتات الزمنية
- **AsyncIO** - البرمجة غير المتزامنة

---

<div align="center">

## 🕌 بارك الله فيكم وجزاكم الله خيراً

**"وَمَن يَعْمَلْ مِثْقَالَ ذَرَّةٍ خَيْراً يَرَهُ"**

---

Made with ❤️ by omar mahdy for the Muslim Ummah

![Islamic Bot](https://img.shields.io/badge/🕌-Made%20with%20Love%20for%20Islam-green?style=for-the-badge)

</div>
