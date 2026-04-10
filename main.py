import yfinance as yf
import numpy as np
import pandas as pd


# =========================
# SAFE FLOAT
# =========================
def safe_last(series):
    try:
        if series is None:
            return None
        return float(series.iloc[-1])
    except:
        return None


# =========================
# MAIN ANALYZER
# =========================
def analyze_stock(ticker: str):

    try:
        df = yf.download(ticker, period="6mo", interval="1d", progress=False)

        if df is None or df.empty or len(df) < 50:
            return None

        df["ma5"] = df["Close"].rolling(5).mean()
        df["ma21"] = df["Close"].rolling(21).mean()
        df["ma50"] = df["Close"].rolling(50).mean()
        df["ma200"] = df["Close"].rolling(200).mean()

        df["vol_ma20"] = df["Volume"].rolling(20).mean()
        df["returns"] = df["Close"].pct_change()

        last = df.iloc[-1]

        price = safe_last(last["Close"])
        ma5 = safe_last(last["ma5"])
        ma21 = safe_last(last["ma21"])
        ma50 = safe_last(last["ma50"])
        ma200 = safe_last(last["ma200"])
        vol = safe_last(last["Volume"])
        vol_ma = safe_last(last["vol_ma20"])

        if None in [price, ma5, ma21, ma50, ma200]:
            return None

        # =========================
        # SCORING ENGINE (0-100)
        # =========================
        score = 0
        reasons = []

        # Trend
        if price > ma5:
            score += 10
            reasons.append("Fiyat MA5 üstünde (short momentum)")

        if ma5 > ma21:
            score += 15
            reasons.append("MA5 > MA21 (trend bullish)")

        if ma21 > ma50:
            score += 20
            reasons.append("MA21 > MA50 (orta vade yükseliş)")

        if price > ma200:
            score += 20
            reasons.append("Fiyat MA200 üstünde (bull market zone)")
        else:
            reasons.append("Fiyat MA200 altında (riskli bölge)")

        # Volume confirmation
        if vol and vol_ma and vol > vol_ma:
            score += 15
            reasons.append("Hacim artışı (kurumsal ilgi olabilir)")

        # Volatility check
        recent_return = df["returns"].iloc[-1]
        if recent_return and recent_return > 0:
            score += 10
            reasons.append("Pozitif momentum")

        # Stability bonus
        if ma21 and ma50 and abs(ma21 - ma50) / price < 0.05:
            score += 10
            reasons.append("Fiyat sıkışma bölgesi (breakout potansiyeli)")

        # clamp
        score = max(0, min(100, score))

        return {
            "ticker": ticker,
            "price": price,
            "confidence": score,
            "reasons": reasons
        }

    except:
        return None
