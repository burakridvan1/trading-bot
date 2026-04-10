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
# 📩 KOMUTLAR
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Bot aktif!\n\n"
        "Komutlar:\n"
        "/ekle TSLA 250\n"
        "/sil TSLA\n"
        "/liste"
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
# 🔍 SCAN
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

    messages = []

    for res in results:
        if not res:
            continue

        if isinstance(res, dict):
            if res.get("type") in ["STOP", "TP"]:
                messages.append(res["msg"])
        else:
            if res not in sent_signals:
                messages.append(res)
                sent_signals.add(res)

    if messages:
        for m in messages[:20]:
            await app.bot.send_message(chat_id=config.CHAT_ID, text=m)
    else:
        await app.bot.send_message(chat_id=config.CHAT_ID, text="Sinyal yok.")


# =========================
# 🏆 TOP 5
# =========================

async def top5_loop():
    while True:
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

            msg = "🏆 TOP 5 FIRSAT:\n\n"
            for i, t in enumerate(top, 1):
                msg += f"{i}. {t['ticker']} → Score: {t['score']} | %{t['confidence']}\n"

            await app.bot.send_message(chat_id=config.CHAT_ID, text=msg)

        await asyncio.sleep(6 * 60 * 60)


# =========================
# 🔁 LOOP
# =========================

async def scan_loop():
    while True:
        await scan_market()
        await asyncio.sleep(config.SCAN_INTERVAL_MINUTES * 60)


# =========================
# 🚀 MAIN (EN KRİTİK KISIM)
# =========================

async def main():
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ekle", ekle))
    app.add_handler(CommandHandler("sil", sil))
    app.add_handler(CommandHandler("liste", liste))

    # 🔥 DOĞRU BAŞLATMA
    await app.initialize()
    await app.start()
    await app.bot.initialize()

    # looplar
    asyncio.create_task(scan_loop())
    asyncio.create_task(top5_loop())

    # ❗ KRİTİK SATIR
    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
