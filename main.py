import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from analyzer import analyze_stock
from config import TELEGRAM_TOKEN, CHAT_ID


# =========================
# S&P500 UNIVERSE
# =========================
SP500 = [
    "AAPL","MSFT","NVDA","AMZN","META","GOOGL","GOOG","TSLA","BRK-B","JPM",
    "UNH","XOM","AVGO","PG","JNJ","V","MA","HD","LLY","MRK",
    "ABBV","COST","PEP","ADBE","CRM","NFLX","AMD","INTC","CSCO","WMT",
    "BAC","KO","TMO","ACN","DIS","ABT","MCD","LIN","ORCL","CMCSA"
]


# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏦 BLACKROCK MODE v4 AKTİF\n\n"
        "/top5 → Kurumsal fırsatlar\n"
    )


# =========================
# TOP5 ENGINE
# =========================
async def top5(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text("📊 BlackRock AI tarıyor...")

    results = []

    for t in SP500:
        r = analyze_stock(t)
        if r:
            results.append(r)

    if not results:
        await update.message.reply_text("❌ Veri alınamadı")
        return

    results = sorted(results, key=lambda x: x["confidence"], reverse=True)[:5]

    msg = "🏦 BLACKROCK TOP 5 PICKS\n\n"

    for i, s in enumerate(results, 1):
        msg += f"{i}. {s['ticker']}\n"
        msg += f"💰 {s['price']:.2f}\n"
        msg += f"🧠 Güven: %{s['confidence']:.1f}\n"
        msg += "📌 Kurumsal gerekçe:\n"

        for r in s["reasons"]:
            msg += f"- {r}\n"

        msg += "\n"

    await update.message.reply_text(msg)


# =========================
# AUTO SIGNAL PUSH (BLACKROCK FEATURE)
# =========================
async def auto_signal(app):
    while True:
        try:
            results = []

            for t in SP500:
                r = analyze_stock(t)
                if r:
                    results.append(r)

            top = sorted(results, key=lambda x: x["confidence"], reverse=True)[:5]

            msg = "🚨 BLACKROCK AUTO SIGNAL\n\n"

            for s in top:
                msg += f"{s['ticker']} → %{s['confidence']:.1f}\n"

            await app.bot.send_message(chat_id=CHAT_ID, text=msg)

        except Exception as e:
            print("Auto signal error:", e)

        await asyncio.sleep(60 * 60)  # 1 saat


# =========================
# MAIN
# =========================
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("top5", top5))

    # background task
    app.job_queue.run_repeating(lambda ctx: asyncio.create_task(auto_signal(app)), interval=3600, first=10)

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
