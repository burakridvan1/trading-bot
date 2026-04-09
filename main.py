import asyncio
import nest_asyncio
nest_asyncio.apply()

from analyzer import batch_get_signals
import yfinance as yf
from telegram import Bot
import pandas as pd

TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"

bot = Bot(token=TELEGRAM_TOKEN)

async def send_telegram_message(message):
    try:
        await bot.send_message(chat_id=CHAT_ID, text=message)
    except Exception as e:
        print(f"Telegram Error: {e}")


async def get_all_tickers():
    """
    Tüm ABD ve BIST hisselerini toplar.
    """
    # NASDAQ + NYSE + SP500
    sp500 = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")[0]['Symbol'].tolist()
    nasdaq = pd.read_html("https://en.wikipedia.org/wiki/NASDAQ-100")[0]['Ticker'].tolist()
    nyse = pd.read_html("https://en.wikipedia.org/wiki/List_of_largest_companies_on_the_New_York_Stock_Exchange")[0]['Symbol'].tolist()

    # BIST
    bist = pd.read_html("https://tr.wikipedia.org/wiki/Borsa_Istanbul")[0]
    bist_tickers = bist[bist.columns[0]].astype(str).tolist()
    bist_tickers = [t.replace('.','-') + ".IS" for t in bist_tickers]

    tickers = list(set(sp500 + nasdaq + nyse + bist_tickers))
    return tickers


async def scan_and_notify():
    tickers = await get_all_tickers()
    print(f"Toplam {len(tickers)} hisse taranıyor...")
    signals = batch_get_signals(tickers)
    if signals:
        for ticker, signal in signals.items():
            await send_telegram_message(f"{ticker}: {signal}")
    else:
        print("Hiç STRONG sinyal bulunamadı.")


async def periodic_scan(interval_minutes=10):
    while True:
        await scan_and_notify()
        await asyncio.sleep(interval_minutes * 60)


async def main():
    await periodic_scan(interval_minutes=10)


if __name__ == "__main__":
    asyncio.run(main())
