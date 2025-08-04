#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🕌 البوت الإسلامي الشامل - ملف التشغيل
=============================================
ملف مبسط لتشغيل البوت مع معالجة أفضل للأخطاء
"""

import sys
import logging
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

def check_requirements():
    """Check if all required files and dependencies exist"""
    logger.info("🔍 Checking requirements...")
    
    # Check required files
    required_files = ['Azkar.txt', 'config.py', '.env']
    missing_files = []
    
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        logger.error(f"❌ Missing required files: {missing_files}")
        return False
    
    # Check required directories
    required_dirs = ['morning_dhikr_images', 'evening_dhikr_images']
    missing_dirs = []
    
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            logger.warning(f"⚠️ Directory not found: {dir_name}")
            missing_dirs.append(dir_name)
    
    if missing_dirs:
        logger.warning(f"⚠️ Some image directories are missing: {missing_dirs}")
        logger.warning("⚠️ Morning/evening dhikr will show error messages instead of images")
    
    # Check Python packages
    try:
        import telegram
        import supabase
        import pytz
        logger.info("✅ All required packages are installed")
    except ImportError as e:
        logger.error(f"❌ Missing required package: {e}")
        logger.error("❌ Please install: pip install python-telegram-bot supabase pytz")
        return False
    
    logger.info("✅ All requirements check passed")
    return True

def main():
    """Main function to start the bot"""
    try:
        logger.info("🕌 البوت الإسلامي الشامل - بدء التشغيل")
        logger.info("=" * 50)
        
        # Check requirements
        if not check_requirements():
            logger.error("❌ Requirements check failed. Please fix the issues above.")
            sys.exit(1)
        
        # Import and run the bot
        logger.info("📦 Loading bot modules...")
        from bot import run_bot
        
        logger.info("🚀 Starting bot...")
        run_bot()
        
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Failed to start bot: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()