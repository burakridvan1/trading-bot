import logging
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import yfinance as yf
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ----------------------------
# Ayarlar
# ----------------------------
TOKEN = "8789711602:AAEypX4ngAN0XZA2_B4cOB3HRTp5kT5JkVU"
PORTFOLIO = ["AAPL", "TSLA"]
MARKET = ["GOOGL", "MSFT", "AMZN"]

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

    # Eğer Telegram context mevcutsa, mesaj gönder
    if context and hasattr(context, "bot") and getattr(context, "job", None):
        await context.bot.send_message(chat_id=context.job.chat_id, text=message)
    else:
        print(message)

# ----------------------------
# Telegram komutları
# ----------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Merhaba! Portföy takibine hazır.")
    await portfolio_check(context)

# ----------------------------
# Main
# ----------------------------
async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Komut ekle
    app.add_handler(CommandHandler("start", start))
    
    # Scheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(portfolio_check, "interval", hours=1)
    scheduler.start()
    
    # Botu başlat
    await app.initialize()
    await app.start()
    try:
        await app.updater.start_polling()
    finally:
        await app.stop()
        await app.shutdown()

# ----------------------------
# Başlat
# ----------------------------
if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    loop.create_task(main())
    loop.run_forever()
