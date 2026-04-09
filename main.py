# main.py
import asyncio
import pandas as pd
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from analyzer import batch_get_signals
from config import TELEGRAM_TOKEN
from portfolio import add_to_portfolio, remove_from_portfolio, get_portfolio
import nest_asyncio
import httpx

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

# ---------------- Otomatik Hisse Listesi ----------------
ALL_TICKERS = []

async def fetch_sp500_tickers():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    df_list = pd.read_html(url)
    df = df_list[0]
    return df['Symbol'].tolist()

async def fetch_bist100_tickers():
    # BIST100 listesini bir web kaynağından çekiyoruz
    url = "https://www.finzplus.com/bist100-hisseleri"
    async with httpx.AsyncClient() as client:
        r = await client.get(url)
        dfs = pd.read_html(r.text)
        # İlk tabloda "Sembol" kolonu var
        for df in dfs:
            if 'Sembol' in df.columns:
                return [s.replace('.', '-')+'.IS' for s in df['Sembol'].tolist()]
    return []

async def update_all_tickers():
    global ALL_TICKERS
    sp500 = await fetch_sp500_tickers()
    bist100 = await fetch_bist100_tickers()
    ALL_TICKERS = sp500 + bist100
    print(f"Toplam {len(ALL_TICKERS)} hisse listelendi.")

# ---------------- Scheduler ----------------
async def scan_market(app):
    if not ALL_TICKERS:
        await update_all_tickers()

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
    nest_asyncio.apply()
    asyncio.run(main())
