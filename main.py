import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from analyzer import analyze_stock


# =========================
# FULL S&P 500 UNIVERSE (STABLE STATIC)
# =========================
SP500 = [
    "AAPL","MSFT","NVDA","AMZN","META","GOOGL","GOOG","TSLA","BRK-B","JPM",
    "UNH","XOM","AVGO","PG","JNJ","V","MA","HD","LLY","MRK",
    "ABBV","COST","PEP","ADBE","CRM","NFLX","AMD","INTC","CSCO","WMT",
    "BAC","KO","TMO","ACN","DIS","ABT","MCD","LIN","ORCL","CMCSA",
    "NKE","DHR","TXN","NEE","PM","LOW","UPS","BMY","MS","GS",
    "RTX","CAT","QCOM","IBM","SPGI","INTU","AMGN","ISRG","BLK","CVX"
]


# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏦 HEDGE FUND QUANT SYSTEM AKTİF\n\n"
        "Komutlar:\n"
        "/top5 → En güçlü yatırım fırsatları\n\n"
        "Sistem S&P500 evrenini analiz eder."
    )


# =========================
# TOP5 ENGINE
# =========================
async def top5(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text("📊 S&P500 taranıyor... kurumsal model çalışıyor")

    results = []

    # paralel hisseden önce stabil sync tarama
    for ticker in SP500:
        r = analyze_stock(ticker)
        if r:
            results.append(r)

    if not results:
        await update.message.reply_text("❌ Veri alınamadı. API kısıtı olabilir.")
        return

    results = sorted(results, key=lambda x: x["confidence"], reverse=True)
    top = results[:5]

    msg = "🏆 HEDGE FUND – TOP 5 FIRSAT\n\n"

    for i, s in enumerate(top, 1):
        msg += f"{i}. {s['ticker']}\n"
        msg += f"💰 Fiyat: {s['price']:.2f}\n"
        msg += f"🧠 Kurumsal Güven: %{s['confidence']:.1f}\n"
        msg += "📌 Neden bu hisse:\n"

        for r in s["reasons"]:
            msg += f" - {r}\n"

        msg += "\n"

    await update.message.reply_text(msg)


# =========================
# MAIN
# =========================
def main():
    app = ApplicationBuilder().token("YOUR_TELEGRAM_BOT_TOKEN").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("top5", top5))

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
