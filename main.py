import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from analyzer import analyze_stock
from config import TELEGRAM_TOKEN, CHAT_ID


SECTORS = {
    "TEKNOLOJİ": ["AAPL","MSFT","NVDA","ADBE"],
    "FİNANS": ["JPM","BAC","GS"],
    "SAĞLIK": ["JNJ","PFE","MRK"],
    "ENERJİ": ["XOM","CVX"],
    "TÜKETİM": ["AMZN","COST","WMT"]
}

UNIVERSE = [t for s in SECTORS.values() for t in s]


# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("START KOMUTU GELDİ")
    await update.message.reply_text("✅ Bot aktif!")


# =========================
# ANALYZE
# =========================
async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        await update.message.reply_text("Kullanım: /analyze TSLA")
        return

    ticker = context.args[0].upper()
    r = analyze_stock(ticker)

    if not r:
        await update.message.reply_text("Veri alınamadı")
        return

    msg = f"📊 {ticker}\n"
    msg += f"💰 {r['price']:.2f}\n"
    msg += f"🧠 %{r['confidence']} 🎯{r['win_rate']}%\n\n"

    for reason in r["reasons"]:
        msg += f"- {reason}\n"

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

    if len(results) == 0:
        await update.message.reply_text("⚠️ Veri yok (API problem olabilir)")
        return

    results = sorted(results, key=lambda x: x["confidence"], reverse=True)[:5]

    msg = "🏆 EN GÜÇLÜ 5 HİSSE\n\n"

    for r in results:
        msg += f"{r['ticker']} %{r['confidence']} 🎯{r['win_rate']}%\n"

    await update.message.reply_text(msg)


# =========================
# AUTO ENGINE (SAFE)
# =========================
async def auto_engine(application):
    while True:
        try:
            results = []

            for t in UNIVERSE:
                r = analyze_stock(t)
                if r:
                    results.append(r)

            if results:
                top = sorted(results, key=lambda x: x["confidence"], reverse=True)[:3]

                msg = "🚨 SİNYAL\n\n"
                for r in top:
                    msg += f"{r['ticker']} %{r['confidence']} 🎯{r['win_rate']}%\n"

                await application.bot.send_message(chat_id=CHAT_ID, text=msg)

        except Exception as e:
            print("AUTO ERROR:", e)

        await asyncio.sleep(21600)


# =========================
# MAIN (FINAL)
# =========================
def main():

    print("BOT BAŞLIYOR...")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("top5", top5))
    app.add_handler(CommandHandler("analyze", analyze))

    # 🔥 DOĞRU ENGINE BAŞLATMA
    async def post_init(application):
        print("AUTO ENGINE BAŞLATILDI")
        asyncio.create_task(auto_engine(application))

    app.post_init = post_init

    print("BOT HAZIR → polling başlıyor")

    app.run_polling()


if __name__ == "__main__":
    main()
