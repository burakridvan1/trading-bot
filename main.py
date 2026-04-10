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
# TELEGRAM COMMANDS
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot aktif! Tarama başladı.")


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
# ALL US STOCKS (S&P500)
# =========================

def get_all_tickers():
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        df = pd.read_html(url)[0]
        return df["Symbol"].tolist()
    except:
        return []


# =========================
# MARKET SCANNER LOOP
# =========================

def scan_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    sent_signals = set()

    while True:
        try:
            tickers = get_all_tickers()
            portfolio = load_portfolio()

            messages = []

            # ALL MARKET SCAN
            for t in tickers:
                result = analyze_stock(t, None)

                if isinstance(result, dict):
                    if result.get("type") in ["BUY", "SELL", "STOP", "TP"]:
                        messages.append(result["msg"])
                elif result:
                    if result not in sent_signals:
                        messages.append(result)
                        sent_signals.add(result)

            # PORTFOLIO SCAN
            for t, price in portfolio.items():
                result = analyze_stock(t, price)

                if isinstance(result, dict):
                    messages.append(result["msg"])

            # SEND TELEGRAM (limit 20 msg per cycle)
            for msg in messages[:20]:
                loop.run_until_complete(
                    app.bot.send_message(
                        chat_id=config.CHAT_ID,
                        text=msg
                    )
                )

            time.sleep(config.SCAN_INTERVAL_MINUTES * 60)

        except Exception as e:
            print("SCAN ERROR:", e)
            time.sleep(10)


# =========================
# TOP 5 LOOP (EVERY 6 HOURS)
# =========================

def top5_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    while True:
        try:
            tickers = get_all_tickers()
            results = []

            for t in tickers:
                r = analyze_stock(t, None)

                if isinstance(r, dict):
                    if r.get("type") == "BUY" and r.get("confidence", 0) >= 70:
                        results.append(r)

            top5 = sorted(
                results,
                key=lambda x: x["confidence"],
                reverse=True
            )[:5]

            if top5:
                msg = "🏆 TOP 5 FIRSAT\n\n"

                for i, t in enumerate(top5, 1):
                    msg += f"{i}. {t['ticker']} → %{t['confidence']}\n"

                loop.run_until_complete(
                    app.bot.send_message(
                        chat_id=config.CHAT_ID,
                        text=msg
                    )
                )

            time.sleep(6 * 60 * 60)

        except Exception as e:
            print("TOP5 ERROR:", e)
            time.sleep(10)


# =========================
# START THREADS
# =========================

def start_background_tasks():
    threading.Thread(target=scan_loop, daemon=True).start()
    threading.Thread(target=top5_loop, daemon=True).start()


# =========================
# MAIN
# =========================

def main():
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ekle", ekle))
    app.add_handler(CommandHandler("sil", sil))
    app.add_handler(CommandHandler("liste", liste))

    start_background_tasks()

    # STABLE START (IMPORTANT)
    app.run_polling()


if __name__ == "__main__":
    main()
