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

TOKEN = "8789711602:AAEypX4ngAN0XZA2_B4cOB3HRTp5kT5JkVU"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Kendi portföyünüzü buraya ekleyin
PORTFOLIO = ["AAPL", "TSLA", "GOOGL"]

# İzlemek istediğiniz genel piyasa hisseleri (örnek)
MARKET = ["MSFT", "AMZN", "NVDA", "META", "NFLX"]

# Komut: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Merhaba! Portföy takip botuna hoş geldiniz.")

# Portföy ve piyasa fiyatlarını kontrol eden görev
async def portfolio_check(context: ContextTypes.DEFAULT_TYPE):
    all_stocks = PORTFOLIO + MARKET
    data = {}
    
    for ticker in all_stocks:
        try:
            stock = yf.Ticker(ticker)
            price = stock.history(period="1d")["Close"][-1]
            data[ticker] = price
        except Exception as e:
            logging.warning(f"{ticker} alınamadı: {e}")

    message = "📊 Güncel Fiyatlar:\n"
    for k, v in data.items():
        marker = "💼" if k in PORTFOLIO else ""
        message += f"{k}: {v:.2f}$ {marker}\n"

    # İlk kullanıcıya gönderim (veya istediğiniz chat_id)
    chat_id = context.job.chat_id if hasattr(context.job, "chat_id") else None
    if chat_id:
        await context.bot.send_message(chat_id=chat_id, text=message)
    else:
        print(message)  # test için console yazdır

# Komut: /portfolio
async def show_portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = {}
    for ticker in PORTFOLIO:
        stock = yf.Ticker(ticker)
        price = stock.history(period="1d")["Close"][-1]
        data[ticker] = price
    message = "💼 Portföy Fiyatları:\n" + "\n".join([f"{k}: {v:.2f}$" for k, v in data.items()])
    await update.message.reply_text(message)

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Komutları ekle
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("portfolio", show_portfolio))

    # JobQueue
    if app.job_queue is None:
        raise RuntimeError("JobQueue yüklenemedi. requirements.txt'i kontrol et.")
    # Chat_id buraya manuel eklenebilir ya da start komutu ile kaydedilebilir
    # Örnek: job_queue.run_repeating(portfolio_check, interval=3600, first=10)
    app.job_queue.run_repeating(portfolio_check, interval=3600, first=10)

    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.get_event_loop().run_until_complete(main())
