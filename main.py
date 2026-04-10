import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from analyzer import analyze_stock
from config import TELEGRAM_TOKEN, CHAT_ID


UNIVERSE = [
    "AAPL","MSFT","NVDA","AMZN","META","GOOGL","TSLA",
    "JPM","UNH","XOM","AVGO","PG","JNJ","V","MA",
    "HD","LLY","MRK","ABBV","COST","PEP","ADBE"
]


# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏦 V7 HEDGE FUND AI AKTİF\n\n"
        "/top5 → en iyi fırsatlar\n"
        "/scan → tüm liste\n"
        "/analyze AAPL → tek hisse analiz\n"
    )


# =========================
# ANALYZE SINGLE
# =========================
async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if len(context.args) == 0:
        await update.message.reply_text("Kullanım: /analyze AAPL")
        return

    ticker = context.args[0].upper()

    result = analyze_stock(ticker)

    if not result:
        await update.message.reply_text("Veri alınamadı")
        return

    msg = f"📊 {ticker} ANALİZ\n\n"
    msg += f"💰 Fiyat: {result['price']:.2f}\n"
    msg += f"🧠 Skor: %{result['confidence']}\n"
    msg += f"📉 RSI: {result['rsi']:.1f}\n\n"

    for r in result["reasons"]:
        msg += f"- {r}\n"

    await update.message.reply_text(msg)


# =========================
# TOP5
# =========================
async def top5(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text("Analiz yapılıyor...")

    results = []

    for t in UNIVERSE:
        r = analyze_stock(t)
        if r:
            results.append(r)

    results = sorted(results, key=lambda x: x["confidence"], reverse=True)[:5]

    msg = "🏆 EN GÜÇLÜ 5 YATIRIM FIRSATI\n\n"

    for i, r in enumerate(results, 1):
        msg += f"{i}. {r['ticker']} (%{r['confidence']})\n"

    await update.message.reply_text(msg)


# =========================
# SCAN
# =========================
async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text("Tarama yapılıyor...")

    results = []

    for t in UNIVERSE:
        r = analyze_stock(t)
        if r:
            results.append(r)

    results = sorted(results, key=lambda x: x["confidence"], reverse=True)

    msg = "📊 TÜM PİYASA\n\n"

    for r in results[:10]:
        msg += f"{r['ticker']} → %{r['confidence']}\n"

    await update.message.reply_text(msg)


# =========================
# AUTO SIGNAL
# =========================
async def auto_engine(app):
    while True:
        try:
            results = []

            for t in UNIVERSE:
                r = analyze_stock(t)
                if r:
                    results.append(r)

            top = sorted(results, key=lambda x: x["confidence"], reverse=True)[:5]

            msg = "🚨 OTOMATİK SİNYAL\n\n"

            for r in top:
                msg += f"{r['ticker']} → %{r['confidence']}\n"

            await app.bot.send_message(chat_id=CHAT_ID, text=msg)

        except Exception as e:
            print(e)

        await asyncio.sleep(21600)


async def post_init(app):
    asyncio.create_task(auto_engine(app))


# =========================
# MAIN
# =========================
def main():

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("top5", top5))
    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(CommandHandler("analyze", analyze))

    app.run_polling()


if __name__ == "__main__":
    main()
