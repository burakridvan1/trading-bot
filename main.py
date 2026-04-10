import asyncio
import nest_asyncio
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import config
from analyzer import analyze_stock
from portfolio_manager import (
    load_portfolio,
    add_stock,
    remove_stock,
    list_portfolio
)

nest_asyncio.apply()

app = ApplicationBuilder().token(config.TELEGRAM_TOKEN).build()
sent_signals = set()


# =========================
# 📩 TELEGRAM KOMUTLARI
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Bot aktif!\n\n"
        "Komutlar:\n"
        "/ekle TSLA 250\n"
        "/sil TSLA\n"
        "/liste\n"
    )


async def ekle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        ticker = context.args[0]
        price = float(context.args[1])
        msg = add_stock(ticker, price)
        await update.message.reply_text(f"✅ {msg}")
    except:
        await update.message.reply_text("Kullanım: /ekle TSLA 250")


async def sil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        ticker = context.args[0]
        msg = remove_stock(ticker)
        await update.message.reply_text(f"🗑️ {msg}")
    except:
        await update.message.reply_text("Kullanım: /sil TSLA")


async def liste(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(list_portfolio())


# =========================
# 📊 TICKER
# =========================

def get_all_tickers():
    try:
        sp500 = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")[0]['Symbol'].tolist()
        return list(set(sp500))
    except:
        return []


# =========================
# 🔍 MARKET SCAN
# =========================

async def scan_market():
    tickers = get_all_tickers()
    portfolio = load_portfolio()

    loop = asyncio.get_event_loop()

    with ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as executor:
        tasks = [
            loop.run_in_executor(executor, analyze_stock, t, None)
            for t in tickers
        ]

        for t, p in portfolio.items():
            tasks.append(loop.run_in_executor(executor, analyze_stock, t, p))

        results = await asyncio.gather(*tasks)

    normal_signals = []

    for res in results:
        if not res:
            continue

        if isinstance(res, dict):
            if res.get("type") in ["STOP", "TP"]:
                await send(res["msg"])
        else:
            if res not in sent_signals:
                normal_signals.append(res)
                sent_signals.add(res)

    for msg in normal_signals[:20]:
        await send(msg)

    if not normal_signals:
        await send("Sinyal yok.")


# =========================
# 🏆 TOP 5 FIRSATLAR
# =========================

async def send_top5():
    tickers = get_all_tickers()

    loop = asyncio.get_event_loop()

    with ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as executor:
        tasks = [
            loop.run_in_executor(executor, analyze_stock, t, None)
            for t in tickers
        ]

        results = await asyncio.gather(*tasks)

    candidates = []

    for res in results:
        if isinstance(res, dict) and res.get("type") == "BUY":
            if res["confidence"] >= 70:
                candidates.append(res)

    if candidates:
        top = sorted(candidates, key=lambda x: x["confidence"], reverse=True)[:5]

        msg = "🏆 TOP 5 FIRSAT (6 SAATLİK):\n\n"
        for i, t in enumerate(top, 1):
            msg += f"{i}. {t['ticker']} → Score: {t['score']} | %{t['confidence']}\n"

        await send(msg)


# =========================
# 📤 TELEGRAM GÖNDER
# =========================

async def send(msg):
    await app.bot.send_message(chat_id=config.CHAT_ID, text=msg)


# =========================
# 🔁 LOOPLAR
# =========================

async def scan_loop():
    while True:
        await scan_market()
        await asyncio.sleep(config.SCAN_INTERVAL_MINUTES * 60)


async def top5_loop():
    while True:
        await send_top5()
        await asyncio.sleep(6 * 60 * 60)  # 6 saat


# =========================
# 🚀 MAIN
# =========================

async def main():
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ekle", ekle))
    app.add_handler(CommandHandler("sil", sil))
    app.add_handler(CommandHandler("liste", liste))

    await app.initialize()
    await app.start()

    asyncio.create_task(scan_loop())
    asyncio.create_task(top5_loop())

    await app.updater.start_polling()


if __name__ == "__main__":
    asyncio.run(main())
