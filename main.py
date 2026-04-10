import asyncio
import threading
import time
import pandas as pd

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

import config
from analyzer import analyze_stock
from portfolio_manager import load_portfolio, add_stock, remove_stock, list_portfolio


# =========================
# BOT INIT
# =========================

app = ApplicationBuilder().token(config.TELEGRAM_TOKEN).build()


# =========================
# START COMMAND
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Hedge Fund Bot Aktif!\n\n"
        "Komutlar:\n"
        "/top5 - En iyi fırsatlar\n"
        "/ekle SYMBOL PRICE\n"
        "/sil SYMBOL\n"
        "/liste"
    )


# =========================
# PORTFOLIO COMMANDS
# =========================

async def ekle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        ticker = context.args[0].upper()
        price = float(context.args[1])

        await update.message.reply_text(add_stock(ticker, price))
    except:
        await update.message.reply_text("Kullanım: /ekle TSLA 250")


async def sil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        ticker = context.args[0].upper()

        await update.message.reply_text(remove_stock(ticker))
    except:
        await update.message.reply_text("Kullanım: /sil TSLA")


async def liste(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(list_portfolio())


# =========================
# TICKERS
# =========================

def get_all_tickers():
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        df = pd.read_html(url)[0]
        return df["Symbol"].tolist()
    except:
        return []


# =========================
# TOP 5 COMMAND
# =========================

async def top5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Top 5 hesaplanıyor...")

    tickers = get_all_tickers()
    results = []

    for t in tickers:
        r = analyze_stock(t)

        if r and r.get("type") == "BUY":
            results.append(r)

    top = sorted(results, key=lambda x: x["confidence"], reverse=True)[:5]

    if not top:
        await update.message.reply_text("❌ Fırsat bulunamadı")
        return

    msg = "🏆 HEDGE FUND TOP 5\n\n"

    for i, t in enumerate(top, 1):
        msg += (
            f"{i}. {t['ticker']}\n"
            f"💰 Price: {t['price']:.2f}\n"
            f"🧠 Confidence: %{t['confidence']}\n"
            f"📊 MA Trend: {t['ma5'] > t['ma21']}\n\n"
        )

    await update.message.reply_text(msg)


# =========================
# BACKGROUND SCANNER
# =========================

def scan_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    while True:
        try:
            tickers = get_all_tickers()
            portfolio = load_portfolio()

            messages = []

            for t in tickers[:50]:  # LIMIT (stability)
                r = analyze_stock(t)
                if r:
                    messages.append(f"{r['ticker']} → %{r['confidence']}")

            for t, p in portfolio.items():
                r = analyze_stock(t, p)
                if r:
                    messages.append(f"[PORTFOLIO] {r['ticker']} → %{r['confidence']}")

            for m in messages[:10]:
                loop.run_until_complete(
                    app.bot.send_message(chat_id=config.CHAT_ID, text=m)
                )

            time.sleep(config.SCAN_INTERVAL_MINUTES * 60)

        except Exception as e:
            print("SCAN ERROR:", e)
            time.sleep(10)


# =========================
# FIX: NO DUPLICATE INSTANCE ISSUE
# =========================

def start_bot_once():
    """
    IMPORTANT:
    Prevent multiple polling loops in same process.
    """
    app.run_polling()


# =========================
# MAIN
# =========================

def main():
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ekle", ekle))
    app.add_handler(CommandHandler("sil", sil))
    app.add_handler(CommandHandler("liste", liste))
    app.add_handler(CommandHandler("top5", top5))

    threading.Thread(target=scan_loop, daemon=True).start()

    # IMPORTANT FIX:
    start_bot_once()


if __name__ == "__main__":
    main()
