import asyncio
import threading
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from analyzer import analyze_stock
from config import TELEGRAM_TOKEN, CHAT_ID


SECTORS = {
    "TEKNOLOJİ": ["AAPL", "MSFT", "NVDA", "ADBE"],
    "FİNANS": ["JPM", "BAC", "GS"],
    "SAĞLIK": ["JNJ", "PFE", "MRK"],
    "ENERJİ": ["XOM", "CVX"],
    "TÜKETİM": ["AMZN", "COST", "WMT"]
}

UNIVERSE = [t for s in SECTORS.values() for t in s]


# =========================
# BOT HANDLERS
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Hedge Fund Bot Aktif")


async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        await update.message.reply_text("Kullanım: /analyze TSLA")
        return

    ticker = context.args[0].upper()

    r = analyze_stock(ticker)

    if not r:
        await update.message.reply_text("❌ Veri alınamadı")
        return

    msg = f"{ticker}\n💰 {r['price']:.2f}\n🧠 %{r['confidence']}\n🎯 %{r['win_rate']}"
    await update.message.reply_text(msg)


async def top5(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text("📊 Tarama başladı...")

    results = []

    for t in UNIVERSE:
        r = analyze_stock(t)
        if r:
            results.append(r)

    if not results:
        await update.message.reply_text("❌ Veri yok")
        return

    top = sorted(results, key=lambda x: x["confidence"], reverse=True)[:5]

    msg = "🏆 TOP 5\n\n"

    for r in top:
        msg += f"{r['ticker']} %{r['confidence']} 🎯{r['win_rate']}\n"

    await update.message.reply_text(msg)


# =========================
# AUTO ENGINE (THREAD SAFE)
# =========================
def auto_engine(app):

    import time

    while True:
        try:
            results = []

            for t in UNIVERSE:
                r = analyze_stock(t)
                if r:
                    results.append(r)

            if results:
                top = sorted(results, key=lambda x: x["confidence"], reverse=True)[:3]

                msg = "🚨 AUTO SIGNAL\n\n"

                for r in top:
                    msg += f"{r['ticker']} %{r['confidence']}\n"

                asyncio.run(app.bot.send_message(chat_id=CHAT_ID, text=msg))

        except Exception as e:
            print("AUTO ERROR:", e)

        time.sleep(21600)


# =========================
# MAIN (SAFE)
# =========================
def main():

    print("BOT STARTING...")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("analyze", analyze))
    app.add_handler(CommandHandler("top5", top5))

    # 🔥 BOTU THREAD İLE ÇALIŞTIR
    threading.Thread(target=auto_engine, args=(app,), daemon=True).start()

    print("BOT RUNNING...")

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
