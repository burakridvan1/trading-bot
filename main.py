import asyncio
import nest_asyncio
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import config
from analyzer import analyze_stock
from portfolio_manager import add_stock, remove_stock, list_portfolio, load_portfolio

nest_asyncio.apply()

sent_signals = set()

# TELEGRAM APP
app = ApplicationBuilder().token(config.TELEGRAM_TOKEN).build()


# 📩 KOMUTLAR
async def ekle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        ticker = context.args[0]
        price = float(context.args[1])
        msg = add_stock(ticker, price)
        await update.message.reply_text(msg)
    except:
        await update.message.reply_text("Kullanım: /ekle TSLA 250")


async def sil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        ticker = context.args[0]
        msg = remove_stock(ticker)
        await update.message.reply_text(msg)
    except:
        await update.message.reply_text("Kullanım: /sil TSLA")


async def liste(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = list_portfolio()
    await update.message.reply_text(msg)


# 📊 TICKER
def get_all_tickers():
    try:
        sp500 = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")[0]['Symbol'].tolist()
        return list(set(sp500))
    except:
        return []


# 🔍 MARKET SCAN
async def scan_market(bot: Bot):
    tickers = get_all_tickers()
    portfolio = load_portfolio()

    loop = asyncio.get_event_loop()
    results = []

    with ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as executor:
        tasks = []

        # Market
        for ticker in tickers:
            tasks.append(loop.run_in_executor(executor, analyze_stock, ticker, None))

        # Portfolio
        for ticker, price in portfolio.items():
            tasks.append(loop.run_in_executor(executor, analyze_stock, ticker, price))

        completed = await asyncio.gather(*tasks)

    for res in completed:
        if res and res not in sent_signals:
            results.append(res)
            sent_signals.add(res)

    if results:
        for r in results[:25]:
            await bot.send_message(chat_id=config.CHAT_ID, text=r)
    else:
        await bot.send_message(chat_id=config.CHAT_ID, text="Sinyal yok.")


# 🔁 LOOP
async def periodic_scan(app):
    while True:
        await scan_market(app.bot)
        await asyncio.sleep(config.SCAN_INTERVAL_MINUTES * 60)


# 🚀 MAIN
async def main():
    app.add_handler(CommandHandler("ekle", ekle))
    app.add_handler(CommandHandler("sil", sil))
    app.add_handler(CommandHandler("liste", liste))

    await app.initialize()
    await app.start()

    asyncio.create_task(periodic_scan(app))

    await app.updater.start_polling()


if __name__ == "__main__":
    asyncio.run(main())
