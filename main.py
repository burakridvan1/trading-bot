import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from analyzer import analyze_stock
from config import TELEGRAM_TOKEN, CHAT_ID


SECTORS = {
    "TEKNOLOJİ": [
        "AAPL", "MSFT", "NVDA", "AVGO", "ORCL", "ADBE", "CRM", "AMD", "CSCO", 
        "ACN", "TXN", "QCOM", "AMAT", "INTU", "IBM", "MU", "LRCX", "NOW", 
        "ADI", "KLAC", "PANW", "SNPS", "CDNS", "APH"
    ],
    "FİNANS": [
        "BRK.B", "JPM", "V", "MA", "BAC", "MS", "GS", "WFC", "AXP", "BLK", 
        "SPGI", "C", "PGR", "MMC", "CB", "AON", "MET", "USB", "PNC", "COF", "BK"
    ],
    "SAĞLIK": [
        "LLY", "UNH", "JNJ", "ABBV", "MRK", "TMO", "ABT", "DHR", "PFE", "AMGN", 
        "ISRG", "SYK", "ELV", "VRTX", "CI", "REGN", "BSX", "GILD", "BMY", "MDT"
    ],
    "ENERJİ": [
        "XOM", "CVX", "COP", "EOG", "SLB", "MPC", "PSX", "VLO"
    ],
    "TÜKETİM": [
        "AMZN", "TSLA", "HD", "MCD", "NKE", "LOW", "SBUX", "BKNG", "TJX", 
        "WMT", "PG", "COST", "KO", "PEP", "PM", "MO", "MDLZ", "TGT", "CL"
    ],
    "İLETİŞİM_VE_DİĞER": [
        "GOOGL", "GOOG", "META", "NFLX", "DIS", "TMUS", "VZ", "T", "CMCSA",
        "GE", "CAT", "UNP", "HON", "UPS", "LMT", "RTX", "DE", "BA",
        "NEE", "DUK", "SO", "LIN", "APD", "PLD", "AMT", "EQIX"
    ]
}


# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🧠 BLACKROCK V7 AKTİF")


# =========================
# ANALYZE SINGLE
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

    msg = f"""
{ticker}
💰 {r['price']}
🎯 Score: %{r['confidence']}
📈 Win Rate: %{r['win_rate']}
"""

    await update.message.reply_text(msg)


# =========================
# SECTOR TOP
# =========================
async def sector(update: Update, context: ContextTypes.DEFAULT_TYPE):

    results = []

    for sector_name, tickers in SECTORS.items():

        for t in tickers:
            r = analyze_stock(t)
            if r:
                r["sector"] = sector_name
                results.append(r)

    if not results:
        await update.message.reply_text("Veri yok")
        return

    results = sorted(results, key=lambda x: x["confidence"], reverse=True)[:10]

    msg = "🏦 BLACKROCK SECTOR TOP 10\n\n"

    for r in results:
        msg += f"{r['ticker']} ({r['sector']})\n"
        msg += f"Score: %{r['confidence']} | WR %{r['win_rate']}\n\n"

    await update.message.reply_text(msg)


# =========================
# TOP5 GLOBAL
# =========================
async def top5(update: Update, context: ContextTypes.DEFAULT_TYPE):

    results = []

    for sector, tickers in SECTORS.items():
        for t in tickers:
            r = analyze_stock(t)
            if r:
                results.append(r)

    if not results:
        await update.message.reply_text("Veri yok")
        return

    top = sorted(results, key=lambda x: x["confidence"], reverse=True)[:5]

    msg = "🔥 BLACKROCK TOP 5\n\n"

    for r in top:
        msg += f"{r['ticker']} %{r['confidence']} WR:{r['win_rate']}\n"

    await update.message.reply_text(msg)


# =========================
# AUTO ENGINE
# =========================
async def auto_engine(app):

    while True:
        try:
            results = []

            for sector, tickers in SECTORS.items():
                for t in tickers:
                    r = analyze_stock(t)
                    if r:
                        results.append(r)

            if results:
                top = sorted(results, key=lambda x: x["confidence"], reverse=True)[:3]

                msg = "🚨 BLACKROCK SIGNAL\n\n"

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
    app.add_handler(CommandHandler("sector", sector))

    print("BOT ACTIVE")

    app.run_polling()


if __name__ == "__main__":
    main()
