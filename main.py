import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from analyzer import analyze_stock
from config import TELEGRAM_TOKEN, CHAT_ID


# =========================
# SECTORS
# =========================
SECTORS = {
    "TEKNOLOJİ": ["AAPL", "MSFT", "NVDA", "ADBE"],
    "FİNANS": ["JPM", "BAC", "GS"],
    "SAĞLIK": ["JNJ", "PFE", "MRK"],
    "ENERJİ": ["XOM", "CVX"],
    "TÜKETİM": ["AMZN", "COST", "WMT"]
}

UNIVERSE = [
    t.upper().replace(".", "-")
    for s in SECTORS.values()
    for t in s
]


# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("START COMMAND RECEIVED")
    await update.message.reply_text(
        "✅ HEDGE FUND AI AKTİF\n\n"
        "/analyze TSLA\n"
        "/top5 → En güçlü hisseler"
    )


# =========================
# ANALYZE SINGLE STOCK
# =========================
async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        await update.message.reply_text("Kullanım: /analyze TSLA")
        return

    ticker = context.args[0].upper().replace(".", "-")

    r = analyze_stock(ticker)

    if not r:
        await update.message.reply_text("❌ Veri alınamadı (ticker hatalı veya API boş)")
        return

    msg = f"📊 {r['ticker']}\n"
    msg += f"💰 Price: {r['price']:.2f}\n"
    msg += f"🧠 Score: %{r['confidence']}\n"
    msg += f"🎯 Win Rate: %{r['win_rate']}\n\n"

    for reason in r["reasons"]:
        msg += f"• {reason}\n"

    await update.message.reply_text(msg)


# =========================
# TOP 5
# =========================
async def top5(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text("📊 Market scan başlatıldı...")

    results = []

    for t in UNIVERSE:
        try:
            r = analyze_stock(t)
            if r:
                results.append(r)
        except Exception as e:
            print("ERROR:", t, e)

    if len(results) == 0:
        await update.message.reply_text("❌ Veri alınamadı (yfinance / network sorunu)")
        return

    results = sorted(results, key=lambda x: x["confidence"], reverse=True)[:5]

    msg = "🏆 HEDGE FUND TOP 5\n\n"

    for r in results:
        msg += f"{r['ticker']}\n"
        msg += f"💰 {r['price']:.2f}\n"
        msg += f"🧠 %{r['confidence']} | 🎯 {r['win_rate']}%\n\n"

    await update.message.reply_text(msg)


# =========================
# AUTO SIGNAL ENGINE
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

                msg = "🚨 AUTO SIGNAL\n\n"

                for r in top:
                    msg += f"{r['ticker']} → %{r['confidence']} | 🎯 {r['win_rate']}%\n"

                await app.bot.send_message(
                    chat_id=CHAT_ID,
                    text=msg
                )

        except Exception as e:
            print("AUTO ENGINE ERROR:", e)

        await asyncio.sleep(21600)  # 6 saat


# =========================
# MAIN (STABLE VERSION)
# =========================
def main():

    print("BOT STARTING...")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("analyze", analyze))
    app.add_handler(CommandHandler("top5", top5))

    # background engine
    async def post_init(application):
        print("AUTO ENGINE STARTED")
        asyncio.create_task(auto_engine(application))

    app.post_init = post_init

    print("BOT READY - polling started")

    app.run_polling()


if __name__ == "__main__":
    main()
