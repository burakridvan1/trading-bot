# main.py
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import yfinance as yf

from analyzer import get_stock_signal
from portfolio import add_to_portfolio, remove_from_portfolio, get_portfolio
from config import TELEGRAM_TOKEN

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

# ---------------- Piyasa Taraması ----------------
async def scan_market(app):
    # Tüm ABD ve BIST hisseleri otomatik çekiliyor
    tickers_us = yf.Tickers("AAPL MSFT GOOGL AMZN TSLA NFLX META").tickers
    tickers_bist = yf.Tickers("ASELS.IS THYAO.IS GARAN.IS").tickers  # Örnek BIST
    tickers = list(tickers_us.keys()) + list(tickers_bist.keys())

    for ticker in tickers:
        signal = get_stock_signal(ticker)
        if signal == "STRONG BUY":
            for user_id in app.bot_data.get("users", []):
                await app.bot.send_message(chat_id=user_id, text=f"{ticker} için STRONG BUY sinyali!")

# ---------------- Portföy Kontrol ----------------
async def check_portfolio(app):
    for user_id, tickers in app.bot_data.get("users", {}).items():
        for ticker in tickers:
            signal = get_stock_signal(ticker)
            if signal == "SELL":
                await app.bot.send_message(chat_id=user_id, text=f"{ticker} için SELL sinyali!")

# ---------------- Main ----------------
async def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Komutlar
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("remove", remove))
    app.add_handler(CommandHandler("portfolio", portfolio_cmd))

    # Scheduler işleri
    scheduler.add_job(scan_market, "interval", minutes=60, kwargs={"app": app})
    scheduler.add_job(check_portfolio, "interval", minutes=30, kwargs={"app": app})
    scheduler.start()
    
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
