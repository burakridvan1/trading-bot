import numpy as np
import pandas as pd
import yfinance as yf


# =========================
# RSI
# =========================
def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


# =========================
# SMART MONEY PROXY (volume spike)
# =========================
def volume_score(df):
    try:
        if "Volume" not in df:
            return 0

        avg = df["Volume"].rolling(20).mean().iloc[-1]
        last = df["Volume"].iloc[-1]

        if last > avg * 1.5:
            return 2
        if last > avg:
            return 1
        return 0
    except:
        return 0


# =========================
# BLACKROCK ANALYZER v4
# =========================
def analyze_stock(ticker):
    try:
        df = yf.download(ticker, period="1y", interval="1d", progress=False)

        if df is None or df.empty or len(df) < 120:
            return None

        df["ma20"] = df["Close"].rolling(20).mean()
        df["ma50"] = df["Close"].rolling(50).mean()
        df["ma200"] = df["Close"].rolling(200).mean()
        df["rsi"] = rsi(df["Close"])

        last = df.iloc[-1]

        price = float(last["Close"])
        ma20 = float(last["ma20"])
        ma50 = float(last["ma50"])
        ma200 = float(last["ma200"])
        rsi_val = float(last["rsi"]) if not np.isnan(last["rsi"]) else 50

        returns = df["Close"].pct_change().dropna()
        momentum = float(np.mean(returns[-30:]))

        vol_score = volume_score(df)

        score = 50
        reasons = []

        # =========================
        # TREND STRUCTURE
        # =========================
        if ma20 > ma50 > ma200:
            score += 35
            reasons.append("BlackRock trend alignment (multi-timeframe)")
        else:
            score -= 15

        if price > ma200:
            score += 20
            reasons.append("Macro bull regime (MA200 üstü)")
        else:
            score -= 10

        # =========================
        # RSI
        # =========================
        if rsi_val < 30:
            score += 20
            reasons.append("Kurumsal birikim bölgesi (RSI düşük)")
        elif rsi_val > 70:
            score -= 20
            reasons.append("Aşırı alım riski")

        # =========================
        # MOMENTUM
        # =========================
        if momentum > 0:
            score += 15
            reasons.append("Pozitif momentum akışı")

        # =========================
        # SMART MONEY
        # =========================
        if vol_score == 2:
            score += 20
            reasons.append("Smart money giriş (volume spike)")
        elif vol_score == 1:
            score += 10

        # =========================
        # FINAL SCORE
        # =========================
        confidence = max(0, min(100, score))

        return {
            "ticker": ticker,
            "price": price,
            "confidence": confidence,
            "reasons": reasons
        }

    except:
        return None
