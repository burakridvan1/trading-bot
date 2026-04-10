import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

SCAN_INTERVAL_MINUTES = 15
TOP_K = 5

if not TELEGRAM_TOKEN:
    raise Exception("❌ TELEGRAM_TOKEN eksik (.env dosyasına ekle)")

if not CHAT_ID:
    raise Exception("❌ CHAT_ID eksik (.env dosyasına ekle)")
