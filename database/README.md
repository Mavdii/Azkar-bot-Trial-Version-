# 🕌 Database Migrations - ترحيلات قاعدة البيانات

هذا المجلد يحتوي على ترحيلات قاعدة البيانات للنظام المحسن لمواقيت الصلاة.

## 📋 الترحيلات المتاحة

### 001_prayer_times_cache.sql
- **الهدف:** إنشاء جدول التخزين المؤقت لمواقيت الصلاة
- **المحتوى:**
  - جدول `prayer_times_cache` لحفظ المواقيت
  - فهارس للأداء الأمثل
  - دالة تنظيف البيانات المنتهية الصلاحية
  - مهمة تنظيف تلقائية

### 002_enhanced_group_settings.sql
- **الهدف:** تحسين جدول إعدادات المجموعات
- **المحتوى:**
  - إضافة أعمدة جديدة للإعدادات المتقدمة
  - قيود للتحقق من صحة البيانات
  - فهارس للاستعلامات السريعة
  - trigger لتحديث وقت التعديل تلقائياً

### 003_monitoring_tables.sql
- **الهدف:** إنشاء جداول المراقبة والإحصائيات
- **المحتوى:**
  - جدول `error_logs` لسجل الأخطاء
  - جدول `performance_metrics` لمقاييس الأداء
  - جدول `health_checks` لفحوصات الصحة
  - جدول `alerts` للتنبيهات
  - جدول `system_statistics` للإحصائيات العامة
  - دوال مساعدة للتنظيف والتحليل

## 🚀 تشغيل الترحيلات

### الطريقة الأولى: استخدام المنفذ الآلي
```bash
python database/run_migrations.py
```

### الطريقة الثانية: تشغيل يدوي
```bash
# تشغيل كل ترحيل على حدة
psql -h your_host -d your_database -f database/migrations/001_prayer_times_cache.sql
psql -h your_host -d your_database -f database/migrations/002_enhanced_group_settings.sql
psql -h your_host -d your_database -f database/migrations/003_monitoring_tables.sql
```

### الطريقة الثالثة: Supabase Dashboard
1. افتح Supabase Dashboard
2. اذهب إلى SQL Editor
3. انسخ والصق محتوى كل ملف ترحيل
4. شغل الاستعلامات بالترتيب

## ⚙️ متطلبات التشغيل

### متغيرات البيئة المطلوبة
```bash
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
# أو
SUPABASE_SERVICE_KEY=your_supabase_service_key  # للعمليات الإدارية
```

### المكتبات المطلوبة
```bash
pip install supabase
pip install psycopg2-binary  # للاتصال المباشر بـ PostgreSQL
```

## 📊 هيكل قاعدة البيانات بعد الترحيل

### الجداول الجديدة
- `prayer_times_cache` - التخزين المؤقت للمواقيت
- `error_logs` - سجل الأخطاء
- `performance_metrics` - مقاييس الأداء
- `health_checks` - فحوصات الصحة
- `alerts` - التنبيهات
- `system_statistics` - الإحصائيات العامة
- `schema_migrations` - تتبع الترحيلات

### الجداول المحدثة
- `group_settings` - إعدادات محسنة للمجموعات

## 🔧 الدوال المساعدة

### دوال التنظيف
- `cleanup_expired_prayer_times()` - تنظيف المواقيت المنتهية الصلاحية
- `cleanup_monitoring_data()` - تنظيف بيانات المراقبة القديمة

### دوال التحليل
- `get_system_health_summary()` - ملخص صحة النظام

## 📈 الفهارس المضافة

### فهارس الأداء
- فهارس التاريخ والوقت للاستعلامات السريعة
- فهارس الحالة للفلترة الفعالة
- فهارس المكونات للتجميع

### فهارس التحسين
- فهارس للمجموعات النشطة
- فهارس للإعدادات المفعلة
- فهارس للبيانات الحديثة

## 🛡️ الأمان والصلاحيات

### صلاحيات مطلوبة
- `CREATE TABLE` - لإنشاء الجداول الجديدة
- `ALTER TABLE` - لتعديل الجداول الموجودة
- `CREATE INDEX` - لإنشاء الفهارس
- `CREATE FUNCTION` - لإنشاء الدوال المساعدة
- `CREATE TRIGGER` - لإنشاء المحفزات

### اعتبارات الأمان
- استخدم `SUPABASE_SERVICE_KEY` للعمليات الإدارية
- تأكد من صحة الاتصال قبل التشغيل
- احتفظ بنسخة احتياطية قبل التشغيل

## 🔄 التراجع عن الترحيلات

في حالة الحاجة للتراجع:

```sql
-- حذف الجداول الجديدة
DROP TABLE IF EXISTS prayer_times_cache CASCADE;
DROP TABLE IF EXISTS error_logs CASCADE;
DROP TABLE IF EXISTS performance_metrics CASCADE;
DROP TABLE IF EXISTS health_checks CASCADE;
DROP TABLE IF EXISTS alerts CASCADE;
DROP TABLE IF EXISTS system_statistics CASCADE;

-- إزالة الأعمدة المضافة لجدول group_settings
ALTER TABLE group_settings 
DROP COLUMN IF EXISTS quran_send_delay_minutes,
DROP COLUMN IF EXISTS prayer_timezone,
DROP COLUMN IF EXISTS prayer_alert_minutes,
DROP COLUMN IF EXISTS last_prayer_update,
DROP COLUMN IF EXISTS created_at,
DROP COLUMN IF EXISTS updated_at;
```

## 📞 الدعم والمساعدة

في حالة مواجهة مشاكل:

1. **تحقق من السجلات:** راجع سجلات التشغيل للأخطاء
2. **تحقق من الصلاحيات:** تأكد من وجود الصلاحيات المطلوبة
3. **تحقق من الاتصال:** تأكد من صحة اتصال قاعدة البيانات
4. **النسخ الاحتياطية:** تأكد من وجود نسخة احتياطية قبل التشغيل

## 📝 ملاحظات مهمة

- **الترتيب مهم:** يجب تشغيل الترحيلات بالترتيب المحدد
- **النسخ الاحتياطية:** احتفظ بنسخة احتياطية قبل التشغيل
- **البيئة:** اختبر في بيئة التطوير أولاً
- **المراقبة:** راقب الأداء بعد التشغيل

## 🎯 الخطوات التالية

بعد تشغيل الترحيلات:

1. **اختبار النظام:** تأكد من عمل جميع الوظائف
2. **مراقبة الأداء:** راقب أداء قاعدة البيانات
3. **تحديث التطبيق:** حدث كود التطبيق لاستخدام الجداول الجديدة
4. **التوثيق:** حدث التوثيق ليعكس التغييرات