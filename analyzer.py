# analyzer.py
import yfinance as yf
from ta.momentum import RSIIndicator
from ta.trend import MACD, SMAIndicator
from ta.volatility import BollingerBands

def analyze_stock(ticker):
    try:
        data = yf.download(ticker, period="3mo", interval="1d", progress=False)

        if data is None or data.empty or len(data) < 50:
            return None

        close = data['Close']

        signals = []

        # RSI
        rsi = RSIIndicator(close).rsi().iloc[-1]
        if rsi < 30:
            signals.append("STRONG BUY")
        elif rsi > 70:
            signals.append("STRONG SELL")

        # MACD
        macd = MACD(close)
        if macd.macd_diff().iloc[-1] > 0:
            signals.append("BUY")
        else:
            signals.append("SELL")

        # Bollinger
        bb = BollingerBands(close)
        if close.iloc[-1] < bb.bollinger_lband().iloc[-1]:
            signals.append("STRONG BUY")
        elif close.iloc[-1] > bb.bollinger_hband().iloc[-1]:
            signals.append("STRONG SELL")

        # Trend
        sma20 = SMAIndicator(close, 20).sma_indicator().iloc[-1]
        sma50 = SMAIndicator(close, 50).sma_indicator().iloc[-1]

        if sma20 > sma50:
            signals.append("BUY")
        else:
            signals.append("SELL")

        strong = [s for s in signals if "STRONG" in s]

        if strong:
            return f"{ticker} → {', '.join(strong)}"

        return None

    except Exception as e:
        return None
