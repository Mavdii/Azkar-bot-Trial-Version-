-- 🕌 Enhanced Group Settings Migration
-- =====================================
-- تحسين جدول إعدادات المجموعات

-- إضافة أعمدة جديدة لجدول group_settings
ALTER TABLE group_settings 
ADD COLUMN IF NOT EXISTS quran_send_delay_minutes INTEGER DEFAULT 30,
ADD COLUMN IF NOT EXISTS prayer_timezone VARCHAR(50) DEFAULT 'Africa/Cairo',
ADD COLUMN IF NOT EXISTS prayer_alert_minutes INTEGER DEFAULT 5,
ADD COLUMN IF NOT EXISTS last_prayer_update TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- إضافة قيود للتحقق من صحة البيانات
ALTER TABLE group_settings 
ADD CONSTRAINT IF NOT EXISTS check_quran_delay_valid 
    CHECK (quran_send_delay_minutes >= 1 AND quran_send_delay_minutes <= 120);

ALTER TABLE group_settings 
ADD CONSTRAINT IF NOT EXISTS check_prayer_alert_valid 
    CHECK (prayer_alert_minutes >= 1 AND prayer_alert_minutes <= 30);

-- إنشاء فهرس للمنطقة الزمنية
CREATE INDEX IF NOT EXISTS idx_group_settings_timezone ON group_settings (prayer_timezone);

-- إنشاء فهرس للمجموعات المفعلة للورد القرآني
CREATE INDEX IF NOT EXISTS idx_group_settings_quran_enabled ON group_settings (quran_daily_enabled) WHERE quran_daily_enabled = true;

-- إنشاء فهرس للمجموعات المفعلة لتذكيرات الصلاة
CREATE INDEX IF NOT EXISTS idx_group_settings_prayer_reminders ON group_settings (prayer_reminders_enabled) WHERE prayer_reminders_enabled = true;

-- دالة لتحديث updated_at تلقائياً
CREATE OR REPLACE FUNCTION update_group_settings_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- إنشاء trigger لتحديث updated_at
DROP TRIGGER IF EXISTS trigger_update_group_settings_updated_at ON group_settings;
CREATE TRIGGER trigger_update_group_settings_updated_at
    BEFORE UPDATE ON group_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_group_settings_updated_at();

-- تحديث البيانات الموجودة بالقيم الافتراضية
UPDATE group_settings 
SET 
    quran_send_delay_minutes = COALESCE(quran_send_delay_minutes, 30),
    prayer_timezone = COALESCE(prayer_timezone, 'Africa/Cairo'),
    prayer_alert_minutes = COALESCE(prayer_alert_minutes, 5),
    created_at = COALESCE(created_at, NOW()),
    updated_at = COALESCE(updated_at, NOW())
WHERE quran_send_delay_minutes IS NULL 
   OR prayer_timezone IS NULL 
   OR prayer_alert_minutes IS NULL
   OR created_at IS NULL
   OR updated_at IS NULL;

-- إضافة تعليقات على الأعمدة الجديدة
COMMENT ON COLUMN group_settings.quran_send_delay_minutes IS 'تأخير إرسال الورد القرآني بالدقائق بعد الصلاة';
COMMENT ON COLUMN group_settings.prayer_timezone IS 'المنطقة الزمنية للمجموعة';
COMMENT ON COLUMN group_settings.prayer_alert_minutes IS 'عدد الدقائق قبل الصلاة لإرسال التنبيه';
COMMENT ON COLUMN group_settings.last_prayer_update IS 'آخر تحديث لمواقيت الصلاة';
COMMENT ON COLUMN group_settings.created_at IS 'وقت إنشاء الإعدادات';
COMMENT ON COLUMN group_settings.updated_at IS 'وقت آخر تحديث للإعدادات';