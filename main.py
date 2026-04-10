import asyncio
from concurrent.futures import ThreadPoolExecutor
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from analyzer import analyze_stock
from config import TELEGRAM_TOKEN, CHAT_ID

# =========================
# SECTORS (same)
# =========================
SECTORS = {
    "TEKNOLOJİ": ["AAPL","MSFT","NVDA","AVGO","ORCL","ADBE","CRM","AMD","CSCO",
        "ACN","TXN","QCOM","AMAT","INTU","IBM","MU","LRCX","NOW","ADI","KLAC","PANW","SNPS","CDNS","APH","SNDK"],

    "FİNANS": ["JPM","V","MA","BAC","MS","GS","WFC","AXP","BLK",
        "SPGI","C","PGR","CB","AON","MET","USB","PNC","COF","BK"],

    "SAĞLIK": ["LLY","UNH","JNJ","ABBV","MRK","TMO","ABT","DHR","PFE","AMGN",
        "ISRG","SYK","ELV","VRTX","CI","REGN","BSX","GILD","BMY","MDT"],

    "ENERJİ": ["XOM","CVX","COP","EOG","SLB","MPC","PSX","VLO"],

    "TÜKETİM": ["AMZN","TSLA","HD","MCD","NKE","LOW","SBUX","BKNG","TJX",
        "WMT","PG","COST","KO","PEP","PM","MO","MDLZ","TGT","CL"],

    "İLETİŞİM": ["GOOGL","GOOG","META","NFLX","DIS","TMUS","VZ","T","CMCSA",
        "GE","CAT","UNP","HON","UPS","LMT","RTX","DE","BA",
        "NEE","DUK","SO","LIN","APD","PLD","AMT","EQIX"]
}

# =========================
# THREAD POOL (CRITICAL FIX)
# =========================
executor = ThreadPoolExecutor(max_workers=10)

# =========================
# SAFE WRAPPER
# =========================
async def run_analysis(ticker):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, analyze_stock, ticker)

# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🧠 BLACKROCK V7 STABLE AKTİF")

# =========================
# ANALYZE
# =========================
async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:
        await update.message.reply_text("Kullanım: /analyze AAPL")
        return

    ticker = context.args[0].upper()

    r = await run_analysis(ticker)

    if not r:
        await update.message.reply_text("Veri yok")
        return

    msg = f"""
{ticker}
💰 {r['price']}
🎯 Score: %{r['confidence']}
📈 WR: %{r['win_rate']}
"""

    await update.message.reply_text(msg)

# =========================
# TOP5 (FAST PARALLEL)
# =========================
async def top5(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text("Analiz yapılıyor...")

    tasks = []
    for sector in SECTORS.values():
        for t in sector:
            tasks.append(run_analysis(t))

    results = await asyncio.gather(*tasks)

    results = [r for r in results if r]

    if not results:
        await update.message.reply_text("Veri yok")
        return

    top = sorted(results, key=lambda x: x["confidence"], reverse=True)[:5]

    msg = "🔥 BLACKROCK TOP 5\n\n"

    for r in top:
        msg += f"{r['ticker']} %{r['confidence']} WR:{r['win_rate']}\n"

    await update.message.reply_text(msg)

# =========================
# SECTOR TOP
# =========================
async def sector(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text("Sector analiz...")

    tasks = []
    meta = []

    for sector_name, tickers in SECTORS.items():
        for t in tickers:
            tasks.append(run_analysis(t))
            meta.append(sector_name)

    results = await asyncio.gather(*tasks)

    final = []

    for r, s in zip(results, meta):
        if r:
            r["sector"] = s
            final.append(r)

    if not final:
        await update.message.reply_text("Veri yok")
        return

    top = sorted(final, key=lambda x: x["confidence"], reverse=True)[:10]

    msg = "🏦 SECTOR TOP 10\n\n"

    for r in top:
        msg += f"{r['ticker']} ({r['sector']})\n"
        msg += f"%{r['confidence']} WR:{r['win_rate']}\n\n"

    await update.message.reply_text(msg)

# =========================
# RESTART COMMAND (NEW)
# =========================
async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text("♻️ Bot restart ediliyor...")

    # restart simulation (safe reset)
    python = sys.executable
    os.execl(python, python, *sys.argv)

# =========================
# AUTO ENGINE (SAFE)
# =========================
async def auto_engine(app):

    while True:
        try:
            tasks = []

            for sector in SECTORS.values():
                for t in sector:
                    tasks.append(run_analysis(t))

            results = await asyncio.gather(*tasks)

            results = [r for r in results if r]

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
    app.add_handler(CommandHandler("sector", sector))
    app.add_handler(CommandHandler("restart", restart))

    print("BOT ACTIVE")

    # background task
    asyncio.get_event_loop().create_task(auto_engine(app))

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
