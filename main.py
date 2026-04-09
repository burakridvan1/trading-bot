# main.py
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from analyzer import batch_get_signals
from config import TELEGRAM_TOKEN
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

# ---------------- Scheduler ----------------
ALL_TICKERS = []  # Burayı BIST + ABD listesi ile dolduracağız

async def scan_market(app):
    if not ALL_TICKERS:
        # S&P500 ve BIST100 hisselerini tek seferde çekmek için hazır liste
        # Burada örnek basit ticker listesi var, gerçek listeleri CSV veya API ile çekebilirsin
        sp500 = ["AAPL","TSLA","GOOGL","MSFT","AMZN","NFLX","META"]
        bist100 = ["ASELS.IS","THYAO.IS","GARAN.IS"]
        global ALL_TICKERS
        ALL_TICKERS = sp500 + bist100

    signals = batch_get_signals(ALL_TICKERS)
    if not signals:
        return

    for ticker, signal in signals.items():
        if signal == "STRONG BUY":
            for user_id in app.bot_data.get("users", []):
                await app.bot.send_message(chat_id=user_id, text=f"{ticker} için STRONG BUY sinyali!")

async def check_portfolio(app):
    for user_id, tickers in app.bot_data.get("users", {}).items():
        if not tickers:
            continue
        signals = batch_get_signals(tickers)
        for ticker, signal in signals.items():
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

    await app.initialize()
    await app.run_polling()

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(main())
