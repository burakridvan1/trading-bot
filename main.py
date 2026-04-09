import asyncio
import pandas as pd
import yfinance as yf
import nest_asyncio
from analyzer import batch_get_signals
from telegram import Bot

nest_asyncio.apply()

TOKEN = "TELEGRAM_BOT_TOKEN"  # buraya kendi bot tokenini koy
CHAT_ID = "TELEGRAM_CHAT_ID"   # buraya kendi chat id

bot = Bot(TOKEN)

async def get_all_tickers():
    """
    ABD (NASDAQ + NYSE + S&P500) + BIST tickers listesini getirir.
    """
    # ABD S&P500
    sp500 = pd.read_html(
        "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
        flavor='lxml'
    )[0]['Symbol'].tolist()

    # ABD NASDAQ ve NYSE (yfinance tickers) - yfinance.download ile tüm hisseleri çekmek için kullanılabilir
    # yfinance'in tüm tickers listesi için basit bir JSON endpoint kullanılabilir:
    nasdaq = pd.read_html("https://www.nasdaq.com/market-activity/stocks/screener")[0]['Symbol'].tolist()
    nyse = pd.read_html("https://www.nyse.com/listings_directory/stock")[0]['Symbol'].tolist()

    # BIST
    bist = pd.read_html("https://tr.investing.com/indices/borsa-istanbul-100-components")[0]['Symbol'].tolist()

    # Tümünü birleştir
    tickers = list(set(sp500 + nasdaq + nyse + bist))
    return tickers

async def scan_and_notify():
    tickers = await get_all_tickers()
    print(f"{len(tickers)} adet hisse taranıyor...")

    signals = await batch_get_signals(tickers)
    if not signals:
        print("STRONG sinyal yok.")
        return

    for ticker, signal in signals.items():
        message = f"{ticker}: {signal}"
        await bot.send_message(chat_id=CHAT_ID, text=message)
        print(message)

async def periodic_scan(interval_minutes=30):
    """
    Her interval_minutes dakikada bir tarama yapar.
    """
    while True:
        await scan_and_notify()
        await asyncio.sleep(interval_minutes * 60)

async def main():
    await periodic_scan(interval_minutes=10)  # her 10 dakikada bir tarar

if __name__ == "__main__":
    asyncio.run(main())
