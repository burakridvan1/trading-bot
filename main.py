import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import yfinance as yf
import pandas as pd
import numpy as np

# TELEGRAM TOKEN ve CHAT_ID environment variable olarak Railway'e ekle
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = int(os.environ.get("CHAT_ID"))

# Portföyünü buraya ekle (ör: ["AAPL","TSLA","THYAO.IS","ASELS.IS"])
portfolio = ["AAPL", "TSLA", "THYAO.IS", "ASELS.IS"]

# Basit analiz fonksiyonu: RSI, hareketli ortalama vs
def analyze_stock(ticker_symbol):
    try:
        data = yf.download(ticker_symbol, period="3mo", interval="1d")
        if data.empty:
            return f"{ticker_symbol} için veri yok."
        
        close = data["Close"]

        # RSI hesaplama
        delta = close.diff()
        up, down = delta.clip(lower=0), -1*delta.clip(upper=0)
        roll_up = up.rolling(14).mean()
        roll_down = down.rolling(14).mean()
        RS = roll_up / roll_down
        RSI = 100 - (100 / (1 + RS))

        # Basit al/sat sinyali
        signal = "⚪ Bekle"
        if RSI.iloc[-1] < 30:
            signal = "🟢 AL"
        elif RSI.iloc[-1] > 70:
            signal = "🔴 SAT"

        return f"{ticker_symbol} - Kapanış: {close.iloc[-1]:.2f} - RSI: {RSI.iloc[-1]:.2f} - Sinyal: {signal}"
    except Exception as e:
        return f"Hata: {ticker_symbol} - {str(e)}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="📈 Borsa botu çalışıyor!")

async def portfolio_check(context: ContextTypes.DEFAULT_TYPE):
    messages = []
    for stock in portfolio:
        msg = analyze_stock(stock)
        messages.append(msg)
    full_message = "\n".join(messages)
    await context.bot.send_message(chat_id=CHAT_ID, text=full_message)

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Komutlar
    app.add_handler(CommandHandler("start", start))

    # Portföy kontrolü her 1 saatte bir
    job_queue = app.job_queue
    job_queue.run_repeating(portfolio_check, interval=3600, first=10)

    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
