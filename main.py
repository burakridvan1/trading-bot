# main.py
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import TELEGRAM_TOKEN
from analyzer import get_stock_signal, get_all_us_tickers, get_all_bist_tickers
from portfolio import add_to_portfolio, remove_from_portfolio, get_portfolio, PORTFOLIOS

# ---------------- Scheduler ----------------
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

# ---------------- Piyasa Tarama ----------------
async def scan_market(app):
    us_tickers = get_all_us_tickers()
    bist_tickers = get_all_bist_tickers()
    tickers = us_tickers + bist_tickers

    for ticker in tickers:
        signal = get_stock_signal(ticker)
        if signal == "STRONG BUY":
            for user_id in PORTFOLIOS.keys():
                await app.bot.send_message(chat_id=user_id, text=f"{ticker} için STRONG BUY sinyali!")

# ---------------- Portföy Kontrol ----------------
async def check_portfolio(app):
    for user_id, tickers in PORTFOLIOS.items():
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
    scheduler.add_job(lambda: scan_market(app), "interval", minutes=60)
    scheduler.add_job(lambda: check_portfolio(app), "interval", minutes=30)
    scheduler.start()

    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
