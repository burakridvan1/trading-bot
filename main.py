import os
import json
import threading
import time
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
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

# Örnek komut: /ekle
async def ekle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Lütfen bir hisse girin: /ekle TICKER")
        return
    ticker = context.args[0].upper()
    portfolio[ticker] = {}
    save_portfolio()
    await update.message.reply_text(f"{ticker} portföyüne eklendi ✅")
    if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("ekle", ekle))

    # Eğer schedule veya otomatik analiz ekleyeceksen thread ile
    def run_schedule():
        import schedule
        import time
        while True:
            schedule.run_pending()
            time.sleep(10)

    # schedule örnek
    import schedule
    schedule.every(15).minutes.do(lambda: print("Buraya analiz fonksiyonu"))

    threading.Thread(target=run_schedule, daemon=True).start()

    # Bot polling
    app.run_polling()
