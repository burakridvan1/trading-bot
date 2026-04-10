import asyncio
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import config
from analyzer import analyze_stock
from portfolio_manager import load_portfolio, add_stock, remove_stock, list_portfolio

app = ApplicationBuilder().token(config.TELEGRAM_TOKEN).build()
sent_signals = set()


# =====================
# 📩 COMMANDS
# =====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot aktif!")


async def ekle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        t = context.args[0]
        p = float(context.args[1])
        await update.message.reply_text(add_stock(t, p))
    except:
        await update.message.reply_text("Kullanım: /ekle TSLA 250")


async def sil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        t = context.args[0]
        await update.message.reply_text(remove_stock(t))
    except:
        await update.message.reply_text("Kullanım: /sil TSLA")


async def liste(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(list_portfolio())


# =====================
# 📊 TICKERS
# =====================

def get_all_tickers():
    try:
        return pd.read_html(
            "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        )[0]['Symbol'].tolist()
    except:
        return []


# =====================
# 🔍 SCAN
# =====================

async def scan_market():
    tickers = get_all_tickers()
    portfolio = load_portfolio()

    loop = asyncio.get_event_loop()

    with ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as ex:
        tasks = [
            loop.run_in_executor(ex, analyze_stock, t, None)
            for t in tickers
        ]

        for t, p in portfolio.items():
            tasks.append(loop.run_in_executor(ex, analyze_stock, t, p))

        results = await asyncio.gather(*tasks)

    msgs = []

    for r in results:
        if not r:
            continue

        if isinstance(r, dict):
            if r.get("type") in ["STOP", "TP"]:
                msgs.append(r["msg"])
        else:
            if r not in sent_signals:
                msgs.append(r)
                sent_signals.add(r)

    for m in msgs[:20]:
        await app.bot.send_message(chat_id=config.CHAT_ID, text=m)


# =====================
# 🏆 TOP 5
# =====================

async def send_top5():
    tickers = get_all_tickers()

    loop = asyncio.get_event_loop()

    with ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as ex:
        tasks = [
            loop.run_in_executor(ex, analyze_stock, t, None)
            for t in tickers
        ]

        results = await asyncio.gather(*tasks)

    candidates = [
        r for r in results
        if isinstance(r, dict)
        and r.get("type") == "BUY"
        and r.get("confidence", 0) >= 70
    ]

    if candidates:
        top = sorted(candidates, key=lambda x: x["confidence"], reverse=True)[:5]

        msg = "🏆 TOP 5 FIRSAT:\n\n"
        for i, t in enumerate(top, 1):
            msg += f"{i}. {t['ticker']} → %{t['confidence']}\n"

        await app.bot.send_message(chat_id=config.CHAT_ID, text=msg)


# =====================
# 🔁 BACKGROUND LOOP
# =====================

async def background_loop():
    while True:
        await scan_market()
        await asyncio.sleep(config.SCAN_INTERVAL_MINUTES * 60)


async def top5_loop():
    while True:
        await send_top5()
        await asyncio.sleep(6 * 60 * 60)


# =====================
# 🚀 MAIN
# =====================

async def main():
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ekle", ekle))
    app.add_handler(CommandHandler("sil", sil))
    app.add_handler(CommandHandler("liste", liste))

    await app.initialize()
    await app.start()

    asyncio.create_task(background_loop())
    asyncio.create_task(top5_loop())

    await app.updater.start_polling()


if __name__ == "__main__":
    asyncio.run(main())
