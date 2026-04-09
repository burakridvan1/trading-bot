import os
import json
import threading
import time
import schedule
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ====== Environment Variables ======
TOKEN = os.environ.get("8789711602:AAEypX4ngAN0XZA2_B4cOB3HRTp5kT5JkVU")
CHAT_ID = int(os.environ.get("1328970821"))

PORTFOLIO_FILE = "portfolio.json"

# ====== Portföy yönetimi ======
try:
    with open(PORTFOLIO_FILE, "r") as f:
        portfolio = json.load(f)
except:
    portfolio = {}

def save_portfolio():
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(portfolio, f)

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

# ====== Telegram mesaj gönder ======
def send_telegram(msg):
    requests.get(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                 params={"chat_id": CHAT_ID, "text": msg})

# ====== Teknik + Temel Analiz ======
def run_analysis():
    if not portfolio:
        return
    for ticker in portfolio.keys():
        try:
            # Tarihsel fiyat
            data = yf.download(ticker, period="2mo", interval="1d")['Close']
            if data.empty: 
                continue

            # ===== RSI =====
            delta = data.diff()
            up = delta.clip(lower=0)
            down = -1*delta.clip(upper=0)
            roll_up = up.rolling(14).mean()
            roll_down = down.rolling(14).mean()
            RS = roll_up / roll_down
            RSI = 100.0 - (100.0 / (1.0 + RS))
            latest_rsi = RSI.iloc[-1]

            # ===== MACD =====
            ema12 = data.ewm(span=12, adjust=False).mean()
            ema26 = data.ewm(span=26, adjust=False).mean()
            MACD = ema12 - ema26
            signal = MACD.ewm(span=9, adjust=False).mean()
            latest_macd = MACD.iloc[-1]
            latest_signal = signal.iloc[-1]

            # ===== Temel veriler =====
            info = yf.Ticker(ticker).info
            fk = info.get('forwardPE')
            pdd = info.get('priceToBook')
            volume = info.get('volume')

            # ===== Basit al/sat mantığı =====
            msg = f"{ticker} | RSI:{latest_rsi:.1f} MACD:{latest_macd:.2f} FK:{fk} PD/DD:{pdd} Hacim:{volume}"
            if latest_rsi < 30 and latest_macd > latest_signal:
                send_telegram("📈 AL sinyali! " + msg)
            elif latest_rsi > 70 and latest_macd < latest_signal:
                send_telegram("📉 SAT sinyali! " + msg)

        except Exception as e:
            print(f"Hata {ticker}: {e}")

# ====== Schedule Thread ======
def schedule_thread():
    while True:
        schedule.run_pending()
        time.sleep(10)

# ====== Bot Başlat ======
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("ekle", ekle))
    app.add_handler(CommandHandler("sil", sil))
    app.add_handler(CommandHandler("portfoy", portfoy))

    # Analiz için schedule
    schedule.every(15).minutes.do(run_analysis)
    threading.Thread(target=schedule_thread, daemon=True).start()

    # Telegram bot polling
    app.run_polling()
