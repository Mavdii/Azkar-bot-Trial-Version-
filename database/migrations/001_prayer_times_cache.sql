-- 🕌 Prayer Times Cache Table Migration
-- ==========================================
-- إنشاء جدول التخزين المؤقت لمواقيت الصلاة

-- إنشاء جدول prayer_times_cache
CREATE TABLE IF NOT EXISTS prayer_times_cache (
    id SERIAL PRIMARY KEY,
    date DATE UNIQUE NOT NULL,
    prayer_times JSONB NOT NULL,
    source VARCHAR(50) NOT NULL DEFAULT 'aladhan',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- فهارس للأداء
    CONSTRAINT prayer_times_cache_date_unique UNIQUE (date),
    CONSTRAINT prayer_times_cache_expires_check CHECK (expires_at > created_at)
);

-- إنشاء فهرس للتاريخ
CREATE INDEX IF NOT EXISTS idx_prayer_times_cache_date ON prayer_times_cache (date);

-- إنشاء فهرس لوقت الانتهاء
CREATE INDEX IF NOT EXISTS idx_prayer_times_cache_expires ON prayer_times_cache (expires_at);

-- إنشاء فهرس للمصدر
CREATE INDEX IF NOT EXISTS idx_prayer_times_cache_source ON prayer_times_cache (source);

-- إضافة تعليق على الجدول
COMMENT ON TABLE prayer_times_cache IS 'جدول التخزين المؤقت لمواقيت الصلاة';
COMMENT ON COLUMN prayer_times_cache.date IS 'تاريخ المواقيت';
COMMENT ON COLUMN prayer_times_cache.prayer_times IS 'بيانات مواقيت الصلاة بصيغة JSON';
COMMENT ON COLUMN prayer_times_cache.source IS 'مصدر البيانات (aladhan, islamicfinder, etc.)';
COMMENT ON COLUMN prayer_times_cache.expires_at IS 'وقت انتهاء صلاحية البيانات';

-- دالة لتنظيف البيانات المنتهية الصلاحية
CREATE OR REPLACE FUNCTION cleanup_expired_prayer_times()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM prayer_times_cache 
    WHERE expires_at < NOW();
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- إنشاء مهمة تنظيف تلقائية (إذا كان pg_cron متاحاً)
-- SELECT cron.schedule('cleanup-prayer-cache', '0 2 * * *', 'SELECT cleanup_expired_prayer_times();');