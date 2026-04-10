import asyncio
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from analyzer import analyze_stock


# =========================
# TOKEN SAFETY FIX (CRITICAL)
# =========================
TOKEN = os.getenv("8789711602:AAEypX4ngAN0XZA2_B4cOB3HRTp5kT5JkVU")

if not TOKEN:
    raise Exception("❌ TELEGRAM_TOKEN eksik (.env kullan)")


# =========================
# FULL S&P500 (STABLE)
# =========================
SP500 = [
    "AAPL","MSFT","NVDA","AMZN","META","GOOGL","GOOG","TSLA","BRK-B","JPM",
    "UNH","XOM","AVGO","PG","JNJ","V","MA","HD","LLY","MRK",
    "ABBV","COST","PEP","ADBE","CRM","NFLX","AMD","INTC","CSCO","WMT",
    "BAC","KO","TMO","ACN","DIS","ABT","MCD","LIN","ORCL","CMCSA",
    "NKE","DHR","TXN","NEE","PM","LOW","UPS","BMY","MS","GS"
]


# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏦 INSTITUTIONAL HEDGE FUND v3 AKTİF\n\n"
        "/top5 → Kurumsal fırsat taraması\n"
    )


# =========================
# TOP5 ENGINE v3
# =========================
async def top5(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text("📊 S&P500 + NEWS + MOMENTUM analiz ediliyor...")

    results = []

    for t in SP500:
        r = analyze_stock(t)
        if r:
            results.append(r)

    if not results:
        await update.message.reply_text("❌ Veri alınamadı")
        return

    results = sorted(results, key=lambda x: x["confidence"], reverse=True)[:5]

    msg = "🏆 INSTITUTIONAL TOP 5 (v3)\n\n"

    for i, s in enumerate(results, 1):
        msg += f"{i}. {s['ticker']}\n"
        msg += f"💰 {s['price']:.2f}\n"
        msg += f"🧠 Güven: %{s['confidence']:.1f}\n"
        msg += "📌 Gerekçe:\n"

        for r in s["reasons"]:
            msg += f"- {r}\n"

        msg += "\n"

    await update.message.reply_text(msg)


# =========================
# MAIN
# =========================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("top5", top5))

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
