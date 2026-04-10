import asyncio
import threading
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from analyzer import analyze_stock
from config import TELEGRAM_TOKEN, CHAT_ID


SECTORS = {
    "TEKNOLOJİ": [
        "ACN", "ADBE", "AMD", "AKAM", "ALTR", "APH", "ADI", "AAPL", "AMAT", "ADSK", 
        "ADP", "CSCO", "CTXS", "CTSH", "CSC", "GLW", "EMC", "FFIV", "FIS", "FISV", 
        "FLIR", "GOOG", "HPQ", "INTC", "IBM", "INTU", "JBL", "JDSU", "JNPR", "KLAC", 
        "LRCX", "LXK", "LLTC", "LSI", "MCHP", "MU", "MSFT", "MOLX", "MSI", "NVDA", 
        "ORCL", "PAYX", "QCOM", "RHT", "SNDK", "STX", "SYMC", "TEL", "TER", "TXN", 
        "VRSN", "WU", "XLNX", "XRX"
    ],
    "FİNANS": [
        "AFL", "ALL", "AXP", "AIG", "AMP", "AON", "AIZ", "BAC", "BK", "BBT", 
        "BRK.B", "BLK", "SCHW", "CB", "CINF", "C", "CMA", "DFS", "ETFC", "EFX", 
        "FII", "FITB", "FHN", "BEN", "GS", "HIG", "HCP", "HCN", "HCBK", "HBAN", 
        "ICE", "IVZ", "JPM", "KEY", "LM", "LNC", "L", "MTB", "MMC", "MA", "MCO", 
        "MS", "NDAQ", "NTRS", "NYX", "PBCT", "PNC", "PFG", "PGR", "PRU", "RF", 
        "STT", "STI", "TROW", "TMK", "TRV", "USB", "UNM", "V", "WFC", "ZION"
    ],
    "SAĞLIK": [
        "ABT", "AET", "A", "ALXN", "AGN", "AMGN", "ABC", "BAX", "BCR", "BDX", 
        "BIIB", "BSX", "BMY", "CAH", "CELG", "CI", "CVH", "COV", "CVS", "DHR", 
        "DVA", "XRAY", "EW", "ESRX", "FRX", "GILD", "HSP", "HUM", "ISRG", "JNJ", 
        "LH", "LIFE", "LLY", "MCK", "MJN", "MDT", "MRK", "MYL", "PDCO", "PKI", 
        "PRGO", "PFE", "STJ", "SYK", "THC", "TMO", "VAR", "WPI", "WLP", "ZMH"
    ],
    "ENERJİ": [
        "GAS", "APD", "APC", "APA", "BHI", "COG", "CAM", "CHK", "CVX", "COP", 
        "CNX", "DNR", "DVN", "DO", "EOG", "EQT", "XOM", "FTI", "FCX", "HAL", 
        "HES", "KMI", "MRO", "MPC", "MUR", "NBR", "NOV", "NFX", "NBL", "OXY", 
        "OKE", "BTU", "PSX", "PXD", "QEP", "RRC", "RDC", "SLB", "SWN", "SUN", 
        "TSO", "VLO", "WMB", "WPX"
    ],
    "TÜKETİM": [
        "ANF", "MO", "AMZN", "AZO", "AVP", "BLL", "BEAM", "BBBY", "BMS", "BBY", 
        "BIG", "BWA", "BF.B", "CPB", "KMX", "CCL", "CBS", "CMG", "CLX", "COH", 
        "KO", "CCE", "CL", "CMCSA", "CAG", "STZ", "COST", "DRI", "DF", "DTV", 
        "DISCA", "DLTR", "RRD", "DPS", "EBAY", "EL", "EXPE", "FDO", "FDX", "F", 
        "FOSL", "GME", "GCI", "GPS", "GIS", "GPC", "GT", "HOG", "HAR", "HAS", 
        "HNZ", "HD", "HRL", "HST", "K", "KMB", "KSS", "KFT", "KR", "LEG", "LEN", 
        "LTD", "LO", "LOW", "M", "MAR", "MAS", "MAT", "MKC", "MCD", "MHP", "MWV", 
        "TAP", "MON", "MNST", "NFLX", "NWL", "NWSA", "NKE", "JWN", "ORLY", "OMC", 
        "JCP", "PEP", "PM", "RL", "PCLN", "PG", "ROST", "RAI", "R", "SWY", "SNI", 
        "SEE", "SHLD", "SJM", "LUV", "SBUX", "HOT", "SYY", "TGT", "HSY", "TIF", 
        "TWX", "TWC", "TJX", "TSS", "TRIP", "TSN", "URBN", "VFC", "VIAB", "WMT", 
        "WAG", "DIS", "WPO", "WHR", "WFM", "WYN", "WYNN", "YUM"
    ],
    "ENDÜSTRİYEL_VE_DİĞER": [
        "MMM", "ACE", "AES", "AEE", "AEP", "ARG", "AA", "ATI", "ANR", "AMT", 
        "AVB", "AVY", "BXP", "CHRW", "CA", "CVC", "CAT", "CBG", "CNP", "CTL", 
        "CERN", "CF", "CINF", "CTAS", "CMS", "CMA", "ED", "CBE", "CCI", "CSX", 
        "CMI", "DHI", "DE", "DELL", "DV", "D", "DOV", "DOW", "DTE", "DD", "DUK", 
        "DNB", "EMN", "ETN", "ECL", "EIX", "EMR", "ESV", "ETR", "EFX", "EQR", 
        "EXC", "EXPD", "FAST", "FE", "FLS", "FLR", "FMC", "FTR", "GD", "GE", 
        "GNW", "GWW", "HRS", "HON", "IR", "TEG", "IP", "IPG", "IRM", "JEC", 
        "JCI", "JOY", "KIM", "LLL", "LUK", "LMT", "MTB", "NEE", "NI", "NE", 
        "NSC", "NOC", "NU", "NRG", "NUE", "OI", "PCAR", "PLL", "PH", "POM", 
        "PCG", "PNW", "PBI", "PCL", "PPG", "PPL", "PX", "PCP", "PLD", "PEG", 
        "PSA", "PHM", "PWR", "DGX", "RTN", "RF", "RSG", "RHI", "ROK", "COL", 
        "ROP", "SAI", "SCG", "SRE", "SHW", "SIAL", "SPG", "SLM", "SNA", "SO", 
        "SE", "S", "SWK", "SPLS", "SRCL", "STI", "T", "TEL", "TE", "TDC", "TXT", 
        "TIE", "TYC", "UNP", "UPS", "X", "UTX", "VTR", "VNO", "VMC", "WM", "WAT", 
        "WY", "WIN", "WEC", "XEL", "XL", "XYL", "YHOO"
    ]
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
