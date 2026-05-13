import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# API Keys
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")
TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY", "")
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "")
FRED_API_KEY = os.getenv("FRED_API_KEY", "")

# Bot settings
BOTS_DIR = Path(os.getenv("BOTS_DIR", "./bots"))
BOT_LOGS_DIR = Path(os.getenv("BOT_LOGS_DIR", "./logs/bots"))
BOT_CONFIGS_DIR = Path(os.getenv("BOT_CONFIGS_DIR", "./configs/bots"))

# Server
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# DB
DB_PATH = os.getenv("DB_PATH", "./data/terminal.db")
