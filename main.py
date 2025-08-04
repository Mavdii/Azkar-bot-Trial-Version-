#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🕌 Islamic Bot - Main Entry Point
=================================
Main entry point for the Islamic Telegram Bot

Author: Islamic Bot Developer Team
Version: 3.0.0
License: MIT
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import and run the bot
from core.start_bot import main

if __name__ == "__main__":
    main()