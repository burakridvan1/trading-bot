import yfinance as yf
from ta.momentum import RSIIndicator
from ta.trend import MACD
from ta.volatility import BollingerBands

async def analyze_ticker(ticker):
    try:
        df = yf.download(ticker, period="6mo", interval="1d", progress=False)

        if df.empty or len(df) < 50:
            return None

        signals = []

        # RSI
        rsi = RSIIndicator(df['Close']).rsi().iloc[-1]
        if rsi < 30:
            signals.append("BUY")
        elif rsi > 70:
            signals.append("SELL")

        # MACD
        macd = MACD(df['Close'])
        if macd.macd_diff().iloc[-1] > 0:
            signals.append("BUY")
        else:
            signals.append("SELL")

        # Bollinger
        bb = BollingerBands(df['Close'])
        price = df['Close'].iloc[-1]

        if price < bb.bollinger_lband().iloc[-1]:
            signals.append("BUY")
        elif price > bb.bollinger_hband().iloc[-1]:
            signals.append("SELL")

        # Güçlü sinyal
        if signals.count("BUY") >= 2:
            return "STRONG BUY"
        elif signals.count("SELL") >= 2:
            return "STRONG SELL"

        return None

    except Exception as e:
        print(f"Hata ({ticker}): {e}")
        return None


async def batch_get_signals(tickers):
    import asyncio

    tasks = [analyze_ticker(t) for t in tickers]
    results = await asyncio.gather(*tasks)

    return {
        ticker: signal
        for ticker, signal in zip(tickers, results)
        if signal is not None
    }
