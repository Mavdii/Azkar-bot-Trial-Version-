# 🕌 Islamic Bot - Source Code Structure

## 📁 Project Structure

```
src/
├── 📁 core/                    # Core system components
│   ├── bot.py                  # Main bot implementation
│   ├── config.py               # Configuration management
│   ├── start_bot.py           # Bot startup script
│   └── prayer_times_api.py    # Prayer times API wrapper
│
├── 📁 prayer_times/           # Prayer times system
│   ├── cairo_manager.py       # Cairo-specific prayer times manager
│   ├── enhanced_api_client.py # Enhanced API client with fallback
│   ├── prayer_cache.py        # Caching system
│   ├── precise_quran_scheduler.py # Precise Quran scheduling
│   ├── active_groups_manager.py # Active groups management
│   ├── error_handler.py       # Error handling and logging
│   ├── prayer_reminders.py    # Prayer reminders system
│   ├── integrated_system.py   # Integrated prayer times system
│   ├── monitoring.py          # System monitoring
│   └── data_validator.py      # Data validation
│
├── 📁 quran/                  # Quran management
│   ├── quran_manager.py       # Quran page management
│   └── quran_scheduler.py     # Quran scheduling
│
├── 📁 handlers/               # Message handlers
├── 📁 services/               # Business logic services
└── 📁 utils/                  # Utility functions
```

## 🚀 How to Run

```bash
# From project root
python main.py
```

## 📋 Features

- ✅ **Prayer Times**: Accurate Cairo prayer times with multiple API fallback
- ✅ **Quran Scheduler**: Daily Quran portions after each prayer (30 minutes delay)
- ✅ **Prayer Reminders**: 5 minutes before each prayer
- ✅ **Dhikr System**: 200+ authentic dhikr with sources
- ✅ **Error Handling**: Comprehensive error handling and logging
- ✅ **Monitoring**: System health monitoring and statistics
- ✅ **Caching**: 24-hour intelligent caching system