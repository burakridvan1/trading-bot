import os
import json
import threading
import schedule
import time
import yfinance as yf
import pandas as pd
import numpy as np
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Environment Variables
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = int(os.environ.get("CHAT_ID"))

PORTFOLIO_FILE = "portfolio.json"

# Portföy yükleme
try:
    with open(PORTFOLIO_FILE, "r") as f:
        portfolio = json.load(f)
except:
    portfolio = {}

def save_portfolio():
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(portfolio, f)

# ====== Telegram komutları ======
async def ekle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Lütfen bir hisse girin: /ekle TICKER")
        return
    ticker = context.args[0].upper()
    portfolio[ticker] = {}
    save_portfolio()
    await update.message.reply_text(f"{ticker} portföyüne eklendi ✅")

async def sil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Lütfen bir hisse girin: /sil TICKER")
        return
    ticker = context.args[0].upper()
    if ticker in portfolio:
        portfolio.pop(ticker)
        save_portfolio()
        await update.message.reply_text(f"{ticker} portföyünden silindi ✅")
    else:
        await update.message.reply_text(f"{ticker} portföyde yok ❌")

async def portfoy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not portfolio:
        await update.message.reply_text("Portföyünüz boş 📝")
        return
    text = "\n".join(portfolio.keys())
    await update.message.reply_text(f"Portföydeki hisseler:\n{text}")

# ====== AL/SAT analizi ======
def run_analysis():
    if not portfolio:
        return
    for ticker in portfolio.keys():
        try:
            data = yf.download(ticker, period="2mo", interval="1d")['Close']
            if data.empty:
                continue

            # RSI
            delta = data.diff()
            up = delta.clip(lower=0)
            down = -1*delta.clip(upper=0)
            roll_up = up.rolling(14).mean()
            roll_down = down.rolling(14).mean()
            RS = roll_up / roll_down
            RSI = 100.0 - (100.0 / (1.0 + RS))
            latest_rsi = RSI.iloc[-1]

            # Basit MACD
            ema12 = data.ewm(span=12, adjust=False).mean()
            ema26 = data.ewm(span=26, adjust=False).mean()
            MACD = ema12 - ema26
            signal = MACD.ewm(span=9, adjust=False).mean()
            latest_macd = MACD.iloc[-1]
            latest_signal = signal.iloc[-1]

            # Basit al/sat sinyali
            if latest_rsi < 30 and latest_macd > latest_signal:
                msg = f"{ticker} 📈 AL sinyali! RSI: {latest_rsi:.1f}, MACD: {latest_macd:.2f}"
                send_telegram(msg)
            elif latest_rsi > 70 and latest_macd < latest_signal:
                msg = f"{ticker} 📉 SAT sinyali! RSI: {latest_rsi:.1f}, MACD: {latest_macd:.2f}"
                send_telegram(msg)

        except Exception as e:
            print(f"Hata {ticker}: {e}")

# Telegram mesaj gönderme
def send_telegram(msg):
    import requests
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.get(url, params={"chat_id": CHAT_ID, "text": msg})

# ====== Bot Başlat ======
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("ekle", ekle))
    app.add_handler(CommandHandler("sil", sil))
    app.add_handler(CommandHandler("portfoy", portfoy))

    # Schedule analizi ayrı thread
    schedule.every(15).minutes.do(run_analysis)
    threading.Thread(target=lambda: schedule.run_pending_loop(), daemon=True).start()

    # Bot polling
    app.run_polling()

# ====== Schedule helper ======
def schedule_run_pending_loop():
    while True:
        schedule.run_pending()
        time.sleep(10)
