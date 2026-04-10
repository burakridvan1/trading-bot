import asyncio
import nest_asyncio
from concurrent.futures import ThreadPoolExecutor
import yfinance as yf
from telegram import Bot
import config
from analyzer import analyze_stock

nest_asyncio.apply()

bot = Bot(token=config.TELEGRAM_TOKEN)

# Aynı sinyali tekrar atmamak için cache
sent_signals = set()


async def send_telegram(message):
    try:
        await bot.send_message(chat_id=config.CHAT_ID, text=message)
    except Exception as e:
        print("Telegram hata:", e)


def get_all_tickers():
    try:
        # TÜM ABD hisseleri (yfinance internal)
        tickers = yf.Tickers(" ".join(yf.shared._EXCHANGE_TICKERS.get('NASDAQ', [])[:3000]))

        # fallback: S&P500 (garanti)
        import pandas as pd
        sp500 = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")[0]['Symbol'].tolist()

        return list(set(sp500))

    except:
        return []


async def scan_market():
    tickers = get_all_tickers()

    if not tickers:
        await send_telegram("Ticker listesi alınamadı ❌")
        return

    loop = asyncio.get_event_loop()
    results = []

    with ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as executor:
        tasks = [
            loop.run_in_executor(executor, analyze_stock, ticker)
            for ticker in tickers
        ]

        completed = await asyncio.gather(*tasks)

    for res in completed:
        if res and res not in sent_signals:
            results.append(res)
            sent_signals.add(res)

    if results:
        for r in results[:20]:  # spam önleme
            await send_telegram(r)
    else:
        await send_telegram("Sinyal yok.")


async def main():
    while True:
        await scan_market()
        await asyncio.sleep(config.SCAN_INTERVAL_MINUTES * 60)


if __name__ == "__main__":
    asyncio.run(main())
