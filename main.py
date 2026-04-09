# main.py
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
)
import yfinance as yf

TOKEN = "8789711602:AAEypX4ngAN0XZA2_B4cOB3HRTp5kT5JkVU"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

PORTFOLIO = ["AAPL", "TSLA", "GOOGL"]
MARKET = ["MSFT", "AMZN", "NVDA", "META", "NFLX"]

# Komutlar
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Merhaba! Portföy takip botuna hoş geldiniz.")

async def show_portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = {}
    for ticker in PORTFOLIO:
        stock = yf.Ticker(ticker)
        price = stock.history(period="1d")["Close"][-1]
        data[ticker] = price
    message = "💼 Portföy Fiyatları:\n" + "\n".join([f"{k}: {v:.2f}$" for k, v in data.items()])
    await update.message.reply_text(message)

# Portföy kontrolü
async def portfolio_check(context: ContextTypes.DEFAULT_TYPE):
    all_stocks = PORTFOLIO + MARKET
    message = "📊 Güncel Fiyatlar:\n"
    for ticker in all_stocks:
        try:
            price = yf.Ticker(ticker).history(period="1d")["Close"][-1]
            marker = "💼" if ticker in PORTFOLIO else ""
            message += f"{ticker}: {price:.2f}$ {marker}\n"
        except Exception as e:
            logging.warning(f"{ticker} alınamadı: {e}")

    chat_id = context.job.chat_id if hasattr(context.job, "chat_id") else None
    if chat_id:
        await context.bot.send_message(chat_id=chat_id, text=message)
    else:
        print(message)  # test için console yazdır

# Ana uygulama
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("portfolio", show_portfolio))

    # JobQueue ile periyodik kontrol
    app.job_queue.run_repeating(portfolio_check, interval=3600, first=10)

    # **Burada asyncio.run() kullanmayın**
    app.run_polling()  # Bu kendi event loop'unu yönetir

if __name__ == "__main__":
    main()
