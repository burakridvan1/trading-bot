# analyzer.py
import yfinance as yf
import pandas as pd

def get_stock_signal(ticker: str):
    """
    Hisseyi alır ve basit bir STRONG BUY / SELL sinyali üretir
    """
    try:
        df = yf.Ticker(ticker).history(period="5d")
        if df.empty:
            return None
        # Basit strateji: son gün kapanış > önceki gün kapanış -> BUY
        if df["Close"][-1] > df["Close"][-2]:
            return "STRONG BUY"
        elif df["Close"][-1] < df["Close"][-2]:
            return "SELL"
        else:
            return "HOLD"
    except Exception as e:
        print(f"{ticker} alınamadı:", e)
        return None
