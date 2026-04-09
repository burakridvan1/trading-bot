import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD
from ta.volatility import BollingerBands

async def analyze_ticker(ticker):
    """
    Bir hisse için tüm indikatörleri hesaplar ve STRONG BUY / STRONG SELL sonucu döner.
    """
    try:
        data = yf.download(ticker, period="6mo", interval="1d", progress=False)
        if data.empty:
            return None

        signals = []

        # RSI
        rsi = RSIIndicator(data['Close']).rsi()[-1]
        if rsi < 30:
            signals.append("BUY")
        elif rsi > 70:
            signals.append("SELL")

        # MACD
        macd = MACD(data['Close'])
        macd_hist = macd.macd_diff()[-1]
        if macd_hist > 0:
            signals.append("BUY")
        elif macd_hist < 0:
            signals.append("SELL")

        # Bollinger Bands
        bb = BollingerBands(data['Close'])
        last_close = data['Close'][-1]
        if last_close < bb.bollinger_lband()[-1]:
            signals.append("BUY")
        elif last_close > bb.bollinger_hband()[-1]:
            signals.append("SELL")

        # Strong sinyal
        if signals.count("BUY") >= 2:
            return "STRONG BUY"
        elif signals.count("SELL") >= 2:
            return "STRONG SELL"
        else:
            return None
    except Exception as e:
        print(f"Hata {ticker}: {e}")
        return None

async def batch_get_signals(tickers):
    """
    Bir liste ticker için analiz yapar ve sadece STRONG BUY/SELL olanları döner.
    """
    import asyncio
    tasks = [analyze_ticker(t) for t in tickers]
    results = await asyncio.gather(*tasks)
    return {t: r for t, r in zip(tickers, results) if r is not None}
