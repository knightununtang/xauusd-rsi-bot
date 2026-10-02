import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

# Monitoring Settings
SYMBOL = os.getenv("SYMBOL", "GC=F").strip()
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "300"))  # Default: 300 seconds (5 minutes)
RSI_PERIOD = int(os.getenv("RSI_PERIOD", "14"))
TIMEFRAME = os.getenv("TIMEFRAME", "5m").strip()

# RSI Threshold Settings
RSI_HIGH_75 = float(os.getenv("RSI_HIGH_75", "75.0"))
RSI_HIGH_65 = float(os.getenv("RSI_HIGH_65", "65.0"))
RSI_LOW_35 = float(os.getenv("RSI_LOW_35", "35.0"))
RSI_LOW_25 = float(os.getenv("RSI_LOW_25", "25.0"))


