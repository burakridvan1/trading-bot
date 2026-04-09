import asyncio
from telegram.ext import Application, CommandHandler
from telegram import Update
from telegram.ext import ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from analyzer import get_signal
from portfolio import add_stock, remove_stock, get_portfolio_status, portfolio

# ------------------- Ayarlar -------------------
TOKEN = "8789711602:AAEypX4ngAN0XZA2_B4cOB3HRTp5kT5JkVU"
CHAT_ID = 1328970821    # Opsiyonel, manuel mesaj göndermek için

# Örnek hisse listesi (BIST + NASDAQ)
tickers = ["AAPL", "TSLA", "GOOGL", "MSFT", "AMZN", "ASELS.IS", "KCHOL.IS"]

scheduler = AsyncIOScheduler()

# ------------------- Fonksiyonlar -------------------
async def scan_market(context: ContextTypes.DEFAULT_TYPE):
    message = "🚀 STRONG BUY Sinyalleri:\n"
    for ticker in tickers:
        signal = get_signal(ticker)
        if signal == "STRONG BUY":
            message += f"{ticker}: STRONG BUY\n"
    if message != "🚀 STRONG BUY Sinyalleri:\n":
        await context.bot.send_message(chat_id=CHAT_ID, text=message)

async def check_portfolio(context: ContextTypes.DEFAULT_TYPE):
    message = "📊 Portföy Durumu:\n" + get_portfolio_status()
    await context.bot.send_message(chat_id=CHAT_ID, text=message)

# ------------------- Telegram Komutları -------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Merhaba! Portföy botu aktif.")

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        ticker = context.args[0].upper()
        qty = int(context.args[1])
        add_stock(ticker, qty)
        await update.message.reply_text(f"{ticker} portföyüne {qty} adet eklendi.")
    except Exception as e:
        await update.message.reply_text(f"Hata: {e}\nKullanım: /add TICKER QTY")

async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        ticker = context.args[0].upper()
        qty = int(context.args[1])
        remove_stock(ticker, qty)
        await update.message.reply_text(f"{ticker} portföyünden {qty} adet çıkarıldı.")
    except Exception as e:
        await update.message.reply_text(f"Hata: {e}\nKullanım: /remove TICKER QTY")

async def portfolio_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_portfolio_status())

# ------------------- Main -------------------
async def main():
    app = Application.builder().token(TOKEN).build()
    
    # Telegram komutları
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("remove", remove))
    app.add_handler(CommandHandler("portfolio", portfolio_cmd))
    
    # Scheduler işleri
    scheduler.add_job(scan_market, "interval", minutes=60, kwargs={"context": app})
    scheduler.add_job(check_portfolio, "interval", minutes=30, kwargs={"context": app})
    scheduler.start()
    
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
