import pandas as pd
import numpy as np
import yfinance as yf


def rsi(series, period=14):
    delta = series.diff()

    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()

    rs = gain / loss
    return 100 - (100 / (1 + rs))


def analyze_stock(ticker):
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

        score = 50  # base score

        reasons = []

        # TREND
        if ma5 > ma21:
            score += 25
            reasons.append("📈 MA5 > MA21 (bullish trend)")
        else:
            score -= 15
            reasons.append("📉 MA5 < MA21 (weak trend)")

        # RSI
        if rsi_val < 30:
            score += 25
            reasons.append("🔥 RSI oversold rebound potential")
        elif rsi_val < 45:
            score += 10
            reasons.append("📊 RSI low zone (accumulation)")
        elif rsi_val > 70:
            score -= 20
            reasons.append("⚠ RSI overbought risk")

        # PRICE MOMENTUM
        if price > ma5:
            score += 10
            reasons.append("🚀 Price above MA5 momentum")

        # VOLATILITY SAFETY FILTER
        volatility = np.std(df["Close"].pct_change().dropna())
        if volatility < 0.02:
            score += 5
            reasons.append("🧊 Low volatility stable structure")

        confidence = max(0, min(100, score))

        return {
            "ticker": ticker,
            "price": price,
            "ma5": ma5,
            "ma21": ma21,
            "rsi": rsi_val,
            "confidence": confidence,
            "reasons": reasons
        }

    except Exception as e:
        print("ERROR:", ticker, e)
        return None
