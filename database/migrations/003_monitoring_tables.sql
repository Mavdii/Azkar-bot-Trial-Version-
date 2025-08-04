-- 🕌 Monitoring Tables Migration
-- ===============================
-- إنشاء جداول المراقبة والإحصائيات

-- جدول سجلات الأخطاء
CREATE TABLE IF NOT EXISTS error_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    category VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    details JSONB,
    traceback_info TEXT,
    context JSONB,
    resolved BOOLEAN DEFAULT FALSE,
    resolution_time TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- فهارس لجدول الأخطاء
CREATE INDEX IF NOT EXISTS idx_error_logs_timestamp ON error_logs (timestamp);
CREATE INDEX IF NOT EXISTS idx_error_logs_category ON error_logs (category);
CREATE INDEX IF NOT EXISTS idx_error_logs_severity ON error_logs (severity);
CREATE INDEX IF NOT EXISTS idx_error_logs_resolved ON error_logs (resolved);

-- جدول مقاييس الأداء
CREATE TABLE IF NOT EXISTS performance_metrics (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metric_name VARCHAR(100) NOT NULL,
    metric_type VARCHAR(20) NOT NULL,
    value DECIMAL(15,4) NOT NULL,
    labels JSONB,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- فهارس لجدول المقاييس
CREATE INDEX IF NOT EXISTS idx_performance_metrics_timestamp ON performance_metrics (timestamp);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_name ON performance_metrics (metric_name);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_type ON performance_metrics (metric_type);

-- جدول فحوصات الصحة
CREATE TABLE IF NOT EXISTS health_checks (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    component VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    details JSONB,
    response_time_ms DECIMAL(10,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- فهارس لجدول فحوصات الصحة
CREATE INDEX IF NOT EXISTS idx_health_checks_timestamp ON health_checks (timestamp);
CREATE INDEX IF NOT EXISTS idx_health_checks_component ON health_checks (component);
CREATE INDEX IF NOT EXISTS idx_health_checks_status ON health_checks (status);

-- جدول التنبيهات
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    alert_id VARCHAR(100) UNIQUE NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    severity VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    component VARCHAR(100) NOT NULL,
    resolved BOOLEAN DEFAULT FALSE,
    resolution_time TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- فهارس لجدول التنبيهات
CREATE INDEX IF NOT EXISTS idx_alerts_alert_id ON alerts (alert_id);
CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts (timestamp);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts (severity);
CREATE INDEX IF NOT EXISTS idx_alerts_resolved ON alerts (resolved);
CREATE INDEX IF NOT EXISTS idx_alerts_component ON alerts (component);

-- جدول إحصائيات النظام
CREATE TABLE IF NOT EXISTS system_statistics (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    component VARCHAR(100) NOT NULL,
    statistics JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- فهرس لجدول الإحصائيات
CREATE INDEX IF NOT EXISTS idx_system_statistics_timestamp ON system_statistics (timestamp);
CREATE INDEX IF NOT EXISTS idx_system_statistics_component ON system_statistics (component);

-- دالة لتنظيف البيانات القديمة
CREATE OR REPLACE FUNCTION cleanup_monitoring_data()
RETURNS TABLE(
    error_logs_deleted INTEGER,
    metrics_deleted INTEGER,
    health_checks_deleted INTEGER,
    alerts_deleted INTEGER,
    statistics_deleted INTEGER
) AS $$
DECLARE
    error_count INTEGER;
    metrics_count INTEGER;
    health_count INTEGER;
    alerts_count INTEGER;
    stats_count INTEGER;
BEGIN
    -- تنظيف سجلات الأخطاء أكثر من 30 يوم
    DELETE FROM error_logs WHERE created_at < NOW() - INTERVAL '30 days';
    GET DIAGNOSTICS error_count = ROW_COUNT;
    
    -- تنظيف المقاييس أكثر من 7 أيام
    DELETE FROM performance_metrics WHERE created_at < NOW() - INTERVAL '7 days';
    GET DIAGNOSTICS metrics_count = ROW_COUNT;
    
    -- تنظيف فحوصات الصحة أكثر من 3 أيام
    DELETE FROM health_checks WHERE created_at < NOW() - INTERVAL '3 days';
    GET DIAGNOSTICS health_count = ROW_COUNT;
    
    -- تنظيف التنبيهات المحلولة أكثر من 7 أيام
    DELETE FROM alerts WHERE resolved = true AND resolution_time < NOW() - INTERVAL '7 days';
    GET DIAGNOSTICS alerts_count = ROW_COUNT;
    
    -- تنظيف الإحصائيات أكثر من 30 يوم
    DELETE FROM system_statistics WHERE created_at < NOW() - INTERVAL '30 days';
    GET DIAGNOSTICS stats_count = ROW_COUNT;
    
    RETURN QUERY SELECT error_count, metrics_count, health_count, alerts_count, stats_count;
END;
$$ LANGUAGE plpgsql;

-- دالة للحصول على ملخص الصحة
CREATE OR REPLACE FUNCTION get_system_health_summary()
RETURNS TABLE(
    component VARCHAR(100),
    latest_status VARCHAR(20),
    latest_message TEXT,
    last_check TIMESTAMP WITH TIME ZONE,
    avg_response_time_ms DECIMAL(10,2)
) AS $$
BEGIN
    RETURN QUERY
    WITH latest_checks AS (
        SELECT DISTINCT ON (hc.component) 
            hc.component,
            hc.status,
            hc.message,
            hc.timestamp,
            hc.response_time_ms
        FROM health_checks hc
        ORDER BY hc.component, hc.timestamp DESC
    )
    SELECT 
        lc.component,
        lc.status,
        lc.message,
        lc.timestamp,
        COALESCE(
            (SELECT AVG(response_time_ms) 
             FROM health_checks 
             WHERE component = lc.component 
               AND timestamp > NOW() - INTERVAL '1 hour'),
            lc.response_time_ms
        ) as avg_response_time_ms
    FROM latest_checks lc
    ORDER BY lc.component;
END;
$$ LANGUAGE plpgsql;

-- إضافة تعليقات على الجداول
COMMENT ON TABLE error_logs IS 'سجل الأخطاء والمشاكل في النظام';
COMMENT ON TABLE performance_metrics IS 'مقاييس الأداء والإحصائيات';
COMMENT ON TABLE health_checks IS 'فحوصات صحة المكونات';
COMMENT ON TABLE alerts IS 'التنبيهات والإشعارات';
COMMENT ON TABLE system_statistics IS 'إحصائيات النظام العامة';

-- إنشاء مهمة تنظيف تلقائية (إذا كان pg_cron متاحاً)
-- SELECT cron.schedule('cleanup-monitoring', '0 3 * * *', 'SELECT cleanup_monitoring_data();');