import asyncio
import os
import sys
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from analyzer import analyze_stock
from config import TELEGRAM_TOKEN, CHAT_ID


# =========================
# SECTORS
# =========================
SECTORS = {
    "TECH": ["AAPL","MSFT","NVDA","GOOGL","META","AMD","AVGO","ORCL","ADBE"],
    "FINANCE": ["JPM","BAC","GS","MS","V","MA"],
    "HEALTH": ["JNJ","PFE","MRK","LLY","UNH"],
    "ENERGY": ["XOM","CVX","COP"],
    "CONSUMER": ["AMZN","TSLA","MCD","COST","WMT","NKE"]
}

UNIVERSE = [t for s in SECTORS.values() for t in s]


# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🧠 V7 BOT ACTIVE")


# =========================
# ANALYZE
# =========================
async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        await update.message.reply_text("Kullanım: /analyze AAPL")
        return

    ticker = context.args[0].upper()
    r = analyze_stock(ticker)

    if not r:
        await update.message.reply_text("Veri yok")
        return

    await update.message.reply_text(
        f"{ticker}\n"
        f"💰 {r['price']}\n"
        f"🎯 %{r['confidence']}\n"
        f"📊 WR %{r['win_rate']}"
    )


# =========================
# TOP5
# =========================
async def top5(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text("Analiz ediliyor...")

    results = []

    for t in UNIVERSE:
        r = analyze_stock(t)
        if r:
            results.append(r)

    if not results:
        await update.message.reply_text("Veri yok")
        return

    top = sorted(results, key=lambda x: x["confidence"], reverse=True)[:5]

    msg = "🔥 TOP 5\n\n"

    for r in top:
        msg += f"{r['ticker']} %{r['confidence']} WR:{r['win_rate']}\n"

    await update.message.reply_text(msg)


# =========================
# RESTART
# =========================
async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("♻️ Restarting...")

    os.execl(sys.executable, sys.executable, *sys.argv)


# =========================
# AUTO ENGINE
# =========================
async def auto_engine(app):

    while True:
        try:
            results = []

            for t in UNIVERSE:
                r = analyze_stock(t)
                if r:
                    results.append(r)

            if results:
                top = sorted(results, key=lambda x: x["confidence"], reverse=True)[:3]

                msg = "🚨 SIGNAL\n\n"

                for r in top:
                    msg += f"{r['ticker']} %{r['confidence']} WR:{r['win_rate']}\n"

                await app.bot.send_message(chat_id=CHAT_ID, text=msg)

        except Exception as e:
            print("AUTO ERROR:", e)

        await asyncio.sleep(7200)


# =========================
# MAIN
# =========================
def main():

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("analyze", analyze))
    app.add_handler(CommandHandler("top5", top5))
    app.add_handler(CommandHandler("restart", restart))

    print("BOT ACTIVE")

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
