import json
import schedule
import time
from telegram import Bot
from analyzer import analyze

import os

TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

bot = Bot(TOKEN)

PORTFOLIO_FILE = "portfolio.json"

# Portföy yükle
try:
    with open(PORTFOLIO_FILE, "r") as f:
        portfolio = json.load(f)
except:
    portfolio = {}

# Kullanıcı komutları (manual, burada örnek)
def add_stock(ticker):
    ticker = ticker.upper()
    if ticker not in portfolio:
        portfolio[ticker] = {}
    save_portfolio()
    bot.send_message(chat_id=CHAT_ID, text=f"{ticker} portföyüne eklendi ✅")

def remove_stock(ticker):
    ticker = ticker.upper()
    if ticker in portfolio:
        portfolio.pop(ticker)
        save_portfolio()
        bot.send_message(chat_id=CHAT_ID, text=f"{ticker} portföyünden çıkarıldı ❌")

def save_portfolio():
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(portfolio, f)

# Otomatik analiz
def run_analysis():
    if not portfolio:
        bot.send_message(chat_id=CHAT_ID, text="Portföy boş 😅")
        return

    for ticker in portfolio.keys():
        score, close, rsi = analyze(ticker)
        msg = f"{ticker}\nFiyat: {close}\nRSI: {rsi}\nSkor: {score}\n"
        if score >= 40:
            msg += "🚀 STRONG BUY"
        elif score >= 20:
            msg += "⚡ BUY"
        else:
            msg += "⏸️ Hold"
        bot.send_message(chat_id=CHAT_ID, text=msg)

# Cron benzeri planlama (15 dk)
schedule.every(15).minutes.do(run_analysis)

# Sürekli döngü
while True:
    schedule.run_pending()
    time.sleep(10)
