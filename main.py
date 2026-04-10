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
# BOT APP
# =========================

app = ApplicationBuilder().token(config.TELEGRAM_TOKEN).build()


# =========================
# START MESSAGE
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Hedge Fund Bot Aktif\n\n"
        "/top5 - en iyi hisseler\n"
        "/ekle SYMBOL PRICE\n"
        "/sil SYMBOL\n"
        "/liste - portfolio"
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
# ALL SP500 TICKERS
# =========================

def get_tickers():
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        df = pd.read_html(url)[0]
        return df["Symbol"].tolist()
    except:
        return []


# =========================
# TOP5 HEDGE FUND SCORING
# =========================

async def top5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Analiz yapılıyor...")

    tickers = get_tickers()
    results = []

    for t in tickers[:80]:  # stability limit
        r = analyze_stock(t)

        if r and r["type"] == "BUY":
            results.append(r)

    top = sorted(results, key=lambda x: x["confidence"], reverse=True)[:5]

    if not top:
        await update.message.reply_text("❌ Sinyal yok")
        return

    msg = "🏆 TOP 5 HİSSE\n\n"

    for i, s in enumerate(top, 1):
        msg += (
            f"{i}. {s['ticker']}\n"
            f"💰 {s['price']:.2f}\n"
            f"🧠 %{s['confidence']}\n"
            f"📊 MA Trend: {s['ma5'] > s['ma21']}\n\n"
        )

    await update.message.reply_text(msg)


# =========================
# BACKGROUND SCANNER (SAFE)
# =========================

def scanner():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    while True:
        try:
            tickers = get_tickers()
            portfolio = load_portfolio()

            signals = []

            for t in tickers[:40]:
                r = analyze_stock(t)
                if r:
                    signals.append(f"{r['ticker']} %{r['confidence']}")

            for t, p in portfolio.items():
                r = analyze_stock(t, p)
                if r:
                    signals.append(f"[PORTFOLIO] {r['ticker']} %{r['confidence']}")

            for s in signals[:10]:
                loop.run_until_complete(
                    app.bot.send_message(chat_id=config.CHAT_ID, text=s)
                )

            time.sleep(config.SCAN_INTERVAL_MINUTES * 60)

        except Exception as e:
            print("SCANNER ERROR:", e)
            time.sleep(10)


# =========================
# SAFE START (CRITICAL FIX)
# =========================

def main():
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("top5", top5))
    app.add_handler(CommandHandler("ekle", ekle))
    app.add_handler(CommandHandler("sil", sil))
    app.add_handler(CommandHandler("liste", liste))

    # background thread
    threading.Thread(target=scanner, daemon=True).start()

    # IMPORTANT: ONLY ONE INSTANCE
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
