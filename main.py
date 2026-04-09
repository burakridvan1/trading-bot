# main.py
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
)

import yfinance as yf
import pandas as pd

TOKEN = "BOT_TOKENINIZI_BURAYA"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# PORTFÖYÜNÜZ
PORTFOLIO = ["AAPL", "TSLA", "GOOGL"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Merhaba! Portföy takip botuna hoş geldiniz.")

async def portfolio_check(context: ContextTypes.DEFAULT_TYPE):
    data = {}
    for ticker in PORTFOLIO:
        stock = yf.Ticker(ticker)
        price = stock.history(period="1d")["Close"][-1]
        data[ticker] = price
    message = "\n".join([f"{k}: {v:.2f}$" for k, v in data.items()])
    # Telegram mesajı göndermek için chat_id gerekli
    # Burada ilk kullanıcıya örnek: context.bot.send_message(chat_id, message)
    print("Portföy Güncellendi:\n", message)

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Komut ekleme
    app.add_handler(CommandHandler("start", start))

    # JobQueue kullanımı
    if app.job_queue is None:
        raise RuntimeError("JobQueue yüklenemedi. requirements.txt'i kontrol et.")
    app.job_queue.run_repeating(portfolio_check, interval=3600, first=10)

    # Botu çalıştır
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.get_event_loop().run_until_complete(main())
