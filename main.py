import pandas as pd

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

import config
from analyzer import analyze_stock


app = ApplicationBuilder().token(config.TELEGRAM_TOKEN).build()


# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏦 KURUMSAL QUANT SİSTEM AKTİF\n\n"
        "/top5 → En güçlü yatırım fırsatları\n"
        "Sistem ABD hisselerini analiz eder ve kurumsal skor üretir"
    )


# =========================
# TICKERS
# =========================
def get_tickers():
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        df = pd.read_html(url)[0]
        return df["Symbol"].tolist()
    except:
        return []


# =========================
# TOP 5
# =========================
async def top5(update, context):
    await update.message.reply_text("📊 Piyasalar taranıyor... kurumsal analiz çalışıyor")

    tickers = get_tickers()
    results = []

    for t in tickers[:150]:
        r = analyze_stock(t)
        if r:
            results.append(r)

    results = sorted(results, key=lambda x: x["confidence"], reverse=True)

    top = results[:5]

    msg = "🏆 EN GÜÇLÜ 5 YATIRIM FIRSATI\n\n"

    for i, s in enumerate(top, 1):
        msg += f"{i}. {s['ticker']}\n"
        msg += f"💰 Fiyat: {s['price']:.2f}\n"
        msg += f"🧠 Güven Skoru: %{s['confidence']:.1f}\n"
        msg += "📌 Analiz:\n"

        for r in s["reasons"]:
            msg += f" - {r}\n"

        msg += "\n"

    await update.message.reply_text(msg)


# =========================
# MAIN
# =========================
def main():
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("top5", top5))

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
