import asyncio
import nest_asyncio
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import config
from analyzer import analyze_stock
from portfolio_manager import load_portfolio

nest_asyncio.apply()

app = ApplicationBuilder().token(config.TELEGRAM_TOKEN).build()
sent_signals = set()


async def send(msg):
    await app.bot.send_message(chat_id=config.CHAT_ID, text=msg)


# KOMUTLAR (aynı kalıyor)
async def liste(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from portfolio_manager import list_portfolio
    await update.message.reply_text(list_portfolio())


# TICKER
def get_all_tickers():
    try:
        sp500 = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")[0]['Symbol'].tolist()
        return list(set(sp500))
    except:
        return []


# SCAN
async def scan_market():
    tickers = get_all_tickers()
    portfolio = load_portfolio()

    loop = asyncio.get_event_loop()

    with ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as executor:
        tasks = [
            loop.run_in_executor(executor, analyze_stock, t, None)
            for t in tickers
        ]

        # portföy ayrı
        for t, p in portfolio.items():
            tasks.append(loop.run_in_executor(executor, analyze_stock, t, p))

        results = await asyncio.gather(*tasks)

    top_candidates = []
    normal_signals = []

    for res in results:
        if not res:
            continue

        if isinstance(res, dict):

            # STOP / TP
            if res.get("type") in ["STOP", "TP"]:
                await send(res["msg"])

            # BUY adayları
            elif res.get("type") == "BUY":
                if res["confidence"] >= 70:
                    top_candidates.append(res)

            # SELL
            elif res.get("type") == "SELL":
                normal_signals.append(res["msg"])

    # TOP 5
    if top_candidates:
        top_candidates = sorted(top_candidates, key=lambda x: x["confidence"], reverse=True)[:5]

        msg = "🏆 TOP 5 FIRSAT:\n"
        for i, t in enumerate(top_candidates, 1):
            msg += f"{i}. {t['ticker']} → Score: {t['score']} | %{t['confidence']}\n"

        await send(msg)

    elif not normal_signals:
        await send("Sinyal yok.")


# LOOP
async def loop():
    while True:
        await scan_market()
        await asyncio.sleep(config.SCAN_INTERVAL_MINUTES * 60)


async def main():
    app.add_handler(CommandHandler("liste", liste))

    await app.initialize()
    await app.start()

    asyncio.create_task(loop())

    await app.updater.start_polling()


if __name__ == "__main__":
    asyncio.run(main())
