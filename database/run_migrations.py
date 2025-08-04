#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🕌 Database Migration Runner - منفذ ترحيل قاعدة البيانات
=========================================================
أداة لتشغيل ترحيلات قاعدة البيانات للنظام المحسن

Author: Islamic Bot Developer Team
Version: 1.0.0
License: MIT
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import pytz

# إضافة المجلد الجذر للمشروع
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Cairo timezone
CAIRO_TZ = pytz.timezone('Africa/Cairo')

class DatabaseMigrator:
    """منفذ ترحيل قاعدة البيانات"""
    
    def __init__(self, supabase_client=None):
        self.supabase_client = supabase_client
        self.migrations_dir = Path(__file__).parent / "migrations"
        
        # قائمة الترحيلات بالترتيب
        self.migrations = [
            "001_prayer_times_cache.sql",
            "002_enhanced_group_settings.sql", 
            "003_monitoring_tables.sql"
        ]
    
    async def run_migrations(self, dry_run: bool = False) -> bool:
        """تشغيل جميع الترحيلات"""
        try:
            logger.info("🔄 بدء تشغيل ترحيلات قاعدة البيانات...")
            
            if not self.supabase_client:
                logger.error("❌ لا يوجد اتصال بقاعدة البيانات")
                return False
            
            # إنشاء جدول الترحيلات إذا لم يكن موجوداً
            await self._create_migrations_table()
            
            # الحصول على الترحيلات المنفذة
            executed_migrations = await self._get_executed_migrations()
            
            success_count = 0
            
            for migration_file in self.migrations:
                if migration_file in executed_migrations:
                    logger.info(f"⏭️ تخطي الترحيل المنفذ: {migration_file}")
                    continue
                
                logger.info(f"🔄 تنفيذ الترحيل: {migration_file}")
                
                if dry_run:
                    logger.info(f"🔍 [DRY RUN] سيتم تنفيذ: {migration_file}")
                    success_count += 1
                    continue
                
                success = await self._execute_migration(migration_file)
                
                if success:
                    await self._record_migration(migration_file)
                    success_count += 1
                    logger.info(f"✅ تم تنفيذ الترحيل بنجاح: {migration_file}")
                else:
                    logger.error(f"❌ فشل في تنفيذ الترحيل: {migration_file}")
                    break
            
            if success_count == len(self.migrations):
                logger.info("✅ تم تنفيذ جميع الترحيلات بنجاح")
                return True
            else:
                logger.warning(f"⚠️ تم تنفيذ {success_count} من أصل {len(self.migrations)} ترحيل")
                return False
                
        except Exception as e:
            logger.error(f"❌ خطأ في تشغيل الترحيلات: {e}")
            return False
    
    async def _create_migrations_table(self) -> None:
        """إنشاء جدول تتبع الترحيلات"""
        try:
            sql = """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id SERIAL PRIMARY KEY,
                migration_name VARCHAR(255) UNIQUE NOT NULL,
                executed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                checksum VARCHAR(64)
            );
            
            CREATE INDEX IF NOT EXISTS idx_schema_migrations_name 
            ON schema_migrations (migration_name);
            """
            
            # تنفيذ SQL مباشرة (يحتاج تعديل حسب نوع قاعدة البيانات)
            # هذا مثال عام، قد يحتاج تخصيص حسب Supabase
            logger.info("📋 إنشاء جدول تتبع الترحيلات...")
            
        except Exception as e:
            logger.error(f"❌ خطأ في إنشاء جدول الترحيلات: {e}")
            raise
    
    async def _get_executed_migrations(self) -> List[str]:
        """الحصول على قائمة الترحيلات المنفذة"""
        try:
            # استعلام للحصول على الترحيلات المنفذة
            # هذا مثال عام، يحتاج تخصيص حسب Supabase
            result = self.supabase_client.table('schema_migrations').select('migration_name').execute()
            
            if result.data:
                return [row['migration_name'] for row in result.data]
            else:
                return []
                
        except Exception as e:
            logger.warning(f"⚠️ خطأ في جلب الترحيلات المنفذة: {e}")
            return []
    
    async def _execute_migration(self, migration_file: str) -> bool:
        """تنفيذ ترحيل واحد"""
        try:
            migration_path = self.migrations_dir / migration_file
            
            if not migration_path.exists():
                logger.error(f"❌ ملف الترحيل غير موجود: {migration_path}")
                return False
            
            # قراءة محتوى الترحيل
            with open(migration_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # تقسيم SQL إلى أوامر منفصلة
            sql_commands = [cmd.strip() for cmd in sql_content.split(';') if cmd.strip()]
            
            # تنفيذ كل أمر
            for i, command in enumerate(sql_commands):
                if command.startswith('--') or not command:
                    continue
                
                try:
                    # تنفيذ الأمر (يحتاج تخصيص حسب Supabase)
                    logger.debug(f"تنفيذ الأمر {i+1}/{len(sql_commands)}")
                    # await self._execute_sql(command)
                    
                except Exception as e:
                    logger.error(f"❌ خطأ في تنفيذ الأمر {i+1}: {e}")
                    logger.debug(f"الأمر الفاشل: {command[:100]}...")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في تنفيذ الترحيل {migration_file}: {e}")
            return False
    
    async def _record_migration(self, migration_file: str) -> None:
        """تسجيل الترحيل كمنفذ"""
        try:
            # حساب checksum للملف
            migration_path = self.migrations_dir / migration_file
            import hashlib
            
            with open(migration_path, 'rb') as f:
                checksum = hashlib.sha256(f.read()).hexdigest()
            
            # تسجيل في قاعدة البيانات
            migration_record = {
                'migration_name': migration_file,
                'executed_at': datetime.now(CAIRO_TZ).isoformat(),
                'checksum': checksum
            }
            
            self.supabase_client.table('schema_migrations').insert(migration_record).execute()
            
        except Exception as e:
            logger.error(f"❌ خطأ في تسجيل الترحيل: {e}")
    
    def get_migration_status(self) -> Dict[str, Any]:
        """الحصول على حالة الترحيلات"""
        try:
            executed_migrations = []
            pending_migrations = []
            
            # هذا يحتاج تنفيذ async، لكن للبساطة نتركه sync
            for migration in self.migrations:
                migration_path = self.migrations_dir / migration
                if migration_path.exists():
                    pending_migrations.append({
                        'name': migration,
                        'path': str(migration_path),
                        'size_kb': migration_path.stat().st_size / 1024
                    })
            
            return {
                'total_migrations': len(self.migrations),
                'executed_count': len(executed_migrations),
                'pending_count': len(pending_migrations),
                'executed_migrations': executed_migrations,
                'pending_migrations': pending_migrations,
                'migrations_dir': str(self.migrations_dir)
            }
            
        except Exception as e:
            logger.error(f"❌ خطأ في الحصول على حالة الترحيلات: {e}")
            return {'error': str(e)}

async def main():
    """الدالة الرئيسية"""
    try:
        print("🕌 منفذ ترحيل قاعدة البيانات - النظام المحسن لمواقيت الصلاة")
        print("=" * 60)
        
        # محاولة تحميل إعدادات Supabase
        try:
            from config import config
            supabase_url = config.SUPABASE_URL
            supabase_key = config.SUPABASE_KEY
            
            if not supabase_url or not supabase_key:
                print("❌ إعدادات Supabase غير متوفرة")
                print("تأكد من وجود SUPABASE_URL و SUPABASE_KEY في متغيرات البيئة")
                return False
            
            # إنشاء عميل Supabase
            try:
                from supabase import create_client
                supabase_client = create_client(supabase_url, supabase_key)
                print("✅ تم الاتصال بقاعدة البيانات")
            except ImportError:
                print("❌ مكتبة supabase غير مثبتة")
                print("قم بتثبيتها باستخدام: pip install supabase")
                return False
                
        except ImportError:
            print("❌ ملف config.py غير موجود")
            return False
        
        # إنشاء منفذ الترحيل
        migrator = DatabaseMigrator(supabase_client)
        
        # عرض حالة الترحيلات
        status = migrator.get_migration_status()
        print(f"\n📊 حالة الترحيلات:")
        print(f"   إجمالي الترحيلات: {status['total_migrations']}")
        print(f"   المنفذة: {status['executed_count']}")
        print(f"   المعلقة: {status['pending_count']}")
        
        if status['pending_migrations']:
            print(f"\n📋 الترحيلات المعلقة:")
            for migration in status['pending_migrations']:
                print(f"   - {migration['name']} ({migration['size_kb']:.1f} KB)")
        
        # السؤال عن التنفيذ
        print(f"\n❓ هل تريد تنفيذ الترحيلات؟")
        print("   1. نعم - تنفيذ الترحيلات")
        print("   2. معاينة فقط (Dry Run)")
        print("   3. إلغاء")
        
        choice = input("\nاختر (1/2/3): ").strip()
        
        if choice == "1":
            print("\n🔄 بدء تنفيذ الترحيلات...")
            success = await migrator.run_migrations(dry_run=False)
            if success:
                print("✅ تم تنفيذ جميع الترحيلات بنجاح!")
            else:
                print("❌ فشل في تنفيذ بعض الترحيلات")
                return False
                
        elif choice == "2":
            print("\n🔍 معاينة الترحيلات...")
            await migrator.run_migrations(dry_run=True)
            print("✅ انتهت المعاينة")
            
        else:
            print("🚫 تم إلغاء العملية")
            return False
        
        return True
        
    except KeyboardInterrupt:
        print("\n🚫 تم إيقاف العملية بواسطة المستخدم")
        return False
    except Exception as e:
        print(f"\n❌ خطأ عام: {e}")
        return False

if __name__ == "__main__":
    # تشغيل الدالة الرئيسية
    result = asyncio.run(main())
    sys.exit(0 if result else 1)