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
# NEWS SENTIMENT (proxy - stable)
# =========================
def news_sentiment(ticker):
    try:
        news = yf.Ticker(ticker).news
        if not news:
            return 0

        score = 0
        for n in news[:5]:
            title = n.get("title", "").lower()

            if any(w in title for w in ["surge", "beat", "upgrade", "profit", "record"]):
                score += 1
            if any(w in title for w in ["fall", "miss", "downgrade", "loss"]):
                score -= 1

        return score
    except:
        return 0


# =========================
# ANALYSIS ENGINE v3
# =========================
def analyze_stock(ticker):
    try:
        df = yf.download(ticker, period="1y", interval="1d", progress=False)

        if df is None or df.empty or len(df) < 100:
            return None

        df["ma5"] = df["Close"].rolling(5).mean()
        df["ma21"] = df["Close"].rolling(21).mean()
        df["ma50"] = df["Close"].rolling(50).mean()
        df["ma200"] = df["Close"].rolling(200).mean()

        df["rsi"] = rsi(df["Close"])

        last = df.iloc[-1]

        price = float(last["Close"])
        ma5 = float(last["ma5"])
        ma21 = float(last["ma21"])
        ma50 = float(last["ma50"])
        ma200 = float(last["ma200"])
        rsi_val = float(last["rsi"]) if not np.isnan(last["rsi"]) else 50

        returns = df["Close"].pct_change().dropna()

        momentum_20 = float(np.mean(returns[-20:]))
        momentum_60 = float(np.mean(returns[-60:]))

        volatility = float(np.std(returns))

        news = news_sentiment(ticker)

        score = 50
        reasons = []

        # =========================
        # TREND
        # =========================
        if ma5 > ma21 > ma50:
            score += 30
            reasons.append("Güçlü kurumsal trend akışı")
        else:
            score -= 15

        if price > ma200:
            score += 20
            reasons.append("Makro boğa rejimi")
        else:
            score -= 10

        # =========================
        # RSI
        # =========================
        if rsi_val < 30:
            score += 20
            reasons.append("Aşırı satım (birikim)")
        elif rsi_val > 70:
            score -= 20
            reasons.append("Aşırı alım riski")

        # =========================
        # MOMENTUM
        # =========================
        if momentum_60 > 0:
            score += 15
        else:
            score -= 10

        # =========================
        # NEWS FLOW
        # =========================
        if news > 0:
            score += 20
            reasons.append("Pozitif haber akışı")
        elif news < 0:
            score -= 20
            reasons.append("Negatif haber akışı")

        # =========================
        # VOLATILITY
        # =========================
        if volatility < 0.02:
            score += 10
            reasons.append("Düşük risk rejimi")
        elif volatility > 0.04:
            score -= 15
            reasons.append("Yüksek risk")

        confidence = max(0, min(100, score))

        return {
            "ticker": ticker,
            "price": price,
            "confidence": confidence,
            "reasons": reasons
        }

    except:
        return None
