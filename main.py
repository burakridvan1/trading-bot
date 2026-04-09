import logging
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import yfinance as yf
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ----------------------------
# Ayarlar
# ----------------------------
TOKEN = "BOT_TOKENINIZI_BURAYA_YAZIN"
PORTFOLIO = ["AAPL", "TSLA"]       # Kendi portföyün
MARKET = ["GOOGL", "MSFT", "AMZN"] # Takip etmek istediğin piyasa hisseleri

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ----------------------------
# Portföy kontrol fonksiyonu
# ----------------------------
async def portfolio_check(context: ContextTypes.DEFAULT_TYPE = None):
    all_stocks = PORTFOLIO + MARKET
    message = "📊 Güncel Fiyatlar:\n"
    
    for ticker in all_stocks:
        try:
            df = yf.Ticker(ticker).history(period="1d")
            if df.empty:
                raise ValueError("No price data found")
            price = df["Close"].iloc[-1]
            marker = "💼" if ticker in PORTFOLIO else ""
            message += f"{ticker}: {price:.2f}$ {marker}\n"
        except Exception as e:
            logging.warning(f"{ticker} alınamadı: {e}")

    if context and hasattr(context, "bot") and context.job:
        await context.bot.send_message(chat_id=context.job.chat_id, text=message)
    else:
        print(message)

# ----------------------------
# Telegram komutları
# ----------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Merhaba! Portföy takibine hazır.")
    # Hemen bir portföy kontrolü yap
    await portfolio_check(context)

# ----------------------------
# Main
# ----------------------------
async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Komutları ekle
    app.add_handler(CommandHandler("start", start))
    
    # Scheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(portfolio_check, "interval", hours=1)  # Her 1 saatte bir çalışacak
    scheduler.start()
    
    # Botu başlat
    await app.run_polling()

# ----------------------------
# Başlat
# ----------------------------
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError:
        # Jupyter/Docker vs async loop zaten çalışıyorsa:
        loop = asyncio.get_event_loop()
        loop.create_task(main())
        loop.run_forever()
