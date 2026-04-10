import pandas as pd
import numpy as np
import yfinance as yf


def rsi(series, period=14):
    delta = series.diff()

    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()

    rs = gain / loss
    return 100 - (100 / (1 + rs))


def analyze_stock(ticker, entry_price=None):
    try:
        df = yf.download(ticker, period="3mo", interval="1d", progress=False)

        if df is None or df.empty:
            return None

        df["ma5"] = df["Close"].rolling(5).mean()
        df["ma21"] = df["Close"].rolling(21).mean()

        df["rsi"] = rsi(df["Close"])

        last = df.iloc[-1]

        price = float(last["Close"])
        ma5 = float(last["ma5"])
        ma21 = float(last["ma21"])
        rsi_val = float(last["rsi"]) if not np.isnan(last["rsi"]) else 50

        score = 0

        # trend
        if ma5 > ma21:
            score += 30
        else:
            score -= 20

        # rsi
        if rsi_val < 30:
            score += 25
        elif rsi_val < 45:
            score += 10
        elif rsi_val > 70:
            score -= 25

        # momentum
        if price > ma5:
            score += 10

        confidence = max(0, min(100, score + 50))

        signal = None
        if confidence >= 75 and ma5 > ma21:
            signal = "BUY"
        elif confidence <= 35:
            signal = "SELL"

        return {
            "ticker": ticker,
            "price": price,
            "ma5": ma5,
            "ma21": ma21,
            "rsi": rsi_val,
            "confidence": confidence,
            "type": signal
        }

    except Exception as e:
        print("ERROR:", ticker, e)
        return None
