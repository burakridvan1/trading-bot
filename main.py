# main.py
import asyncio
import nest_asyncio
nest_asyncio.apply()

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import TELEGRAM_TOKEN
from analyzer import batch_get_signals
from portfolio import add_to_portfolio, remove_from_portfolio, get_portfolio

scheduler = AsyncIOScheduler()

# ---------------- Telegram Komutları ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Merhaba! Hisse botuna hoşgeldiniz.")

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Kullanım: /add TICKER")
        return
    ticker = context.args[0].upper()
    if add_to_portfolio(update.message.from_user.id, ticker):
        await update.message.reply_text(f"{ticker} portföyünüze eklendi.")
    else:
        await update.message.reply_text(f"{ticker} zaten portföyünüzde.")

async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Kullanım: /remove TICKER")
        return
    ticker = context.args[0].upper()
    if remove_from_portfolio(update.message.from_user.id, ticker):
        await update.message.reply_text(f"{ticker} portföyünüzden çıkarıldı.")
    else:
        await update.message.reply_text(f"{ticker} portföyünüzde yok.")

async def portfolio_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    portfolio = get_portfolio(update.message.from_user.id)
    if not portfolio:
        await update.message.reply_text("Portföyünüz boş.")
        return
    msg = "Portföyünüz:\n" + "\n".join(portfolio)
    await update.message.reply_text(msg)

# ---------------- Scheduler Fonksiyonları ----------------
async def scan_market(context):
    # ABD ve BIST tüm önemli hisseleri
    tickers = ["AAPL","TSLA","GOOGL","MSFT","AMZN","NFLX","META","ASELS.IS","THYAO.IS","GARAN.IS"]  # Daha fazla eklenebilir
    signals = batch_get_signals(tickers)
    for ticker, signal in signals.items():
        if signal == "STRONG BUY":
            for user_id in context.bot_data.get("users", []):
                await context.bot.send_message(chat_id=user_id, text=f"{ticker} için STRONG BUY sinyali!")

async def check_portfolio(context):
    for user_id, tickers in context.bot_data.get("users", {}).items():
        signals = batch_get_signals(tickers)
        for ticker, signal in signals.items():
            if signal == "SELL":
                await context.bot.send_message(chat_id=user_id, text=f"{ticker} için SELL sinyali!")

# ---------------- Main ----------------
async def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Komutlar
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
