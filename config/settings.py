import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
GOAPI_KEY = os.getenv("GOAPI_KEY")
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.goapi.io")

# Database Configuration
# Default to a local SQLite file if not specified
DB_PATH = os.getenv("DB_PATH", "market_data.db")
SQLITE_URL = f"sqlite:///{DB_PATH}"

# Validation
if not GOAPI_KEY:
    # Changed to warning instead of error to allow fallback mode
    print("WARNING: GOAPI_KEY is not set. Bot will run in Fallback Mode (YFinance Only).")

# AI Configuration
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Strategy Constants
RSI_OVERSOLD = 30
VOLUME_SPIKE_FACTOR = 1.2
EMA_LONG = 200
EMA_MEDIUM = 50
EMA_SHORT = 20

# Volatility Breakout Constants
VOL_BREAKOUT_FACTOR = 2.0 # 2x Average Volume
MIN_PRICE_CHANGE = 0.03   # 3% Price Increase

