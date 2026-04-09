import asyncio
import nest_asyncio
import yfinance as yf
from analyzer import batch_get_signals
from telegram import Bot

nest_asyncio.apply()

TOKEN = "8789711602:AAEypX4ngAN0XZA2_B4cOB3HRTp5kT5JkVU"
CHAT_ID = "1328970821"

bot = Bot(token=TOKEN)

# 🔥 SABİT VE SORUNSUZ TICKER KAYNAĞI
def get_us_tickers():
    """
    ABD hisseleri (yüksek hacimli + popüler)
    """
    return [
        "AAPL","MSFT","NVDA","AMZN","META","GOOGL","TSLA",
        "BRK-B","UNH","JNJ","XOM","V","PG","JPM","HD",
        "MA","AVGO","PFE","KO","PEP","ABBV","COST",
        "MRK","TMO","BAC","WMT","DIS","MCD","CSCO",
        "INTC","AMD","NFLX","ADBE","CRM","PYPL","QCOM",
        "NKE","TXN","LIN","UPS","LOW","ORCL","SPGI"
    ]

def get_bist_tickers():
    """
    BIST büyük hisseler
    """
    return [
        "THYAO.IS","GARAN.IS","AKBNK.IS","ASELS.IS",
        "BIMAS.IS","KCHOL.IS","EREGL.IS","TUPRS.IS",
        "SISE.IS","YKBNK.IS","SAHOL.IS","PETKM.IS"
    ]

async def send_message(text):
    try:
        await bot.send_message(chat_id=CHAT_ID, text=text)
    except Exception as e:
        print("Telegram hata:", e)


async def scan():
    tickers = get_us_tickers() + get_bist_tickers()

    print(f"{len(tickers)} hisse taranıyor...")

    signals = await batch_get_signals(tickers)

    if not signals:
        print("Sinyal yok")
        return

    for t, s in signals.items():
        msg = f"{t} → {s}"
        print(msg)
        await send_message(msg)


async def loop_scan():
    while True:
        await scan()
        await asyncio.sleep(600)  # 10 dakika


async def main():
    await loop_scan()


if __name__ == "__main__":
    asyncio.run(main())
