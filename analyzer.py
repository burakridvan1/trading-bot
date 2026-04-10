import yfinance as yf
import numpy as np
import pandas as pd


# =========================
# SAFE FLOAT (NO WARNING)
# =========================
def safe(series):
    try:
        if series is None:
            return None

        if isinstance(series, pd.Series):
            val = series.dropna()
            if len(val) == 0:
                return None
            return float(val.iloc[-1])

        return float(series)

    except:
        return None


# =========================
# RSI
# =========================
def compute_rsi(series, period=14):
    try:
        delta = series.diff()

        gain = delta.clip(lower=0).rolling(period).mean()
        loss = -delta.clip(upper=0).rolling(period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        val = rsi.dropna()

        if len(val) == 0:
            return 50

        return float(val.iloc[-1])

    except:
        return 50


# =========================
# MAIN ANALYZER
# =========================
def analyze_stock(ticker):

    try:
        df = yf.download(ticker, period="6mo", interval="1d", progress=False)

        if df is None or df.empty or len(df) < 60:
            return None

        close = df["Close"]
        volume = df["Volume"]

        # =========================
        # INDICATORS
        # =========================
        ma20 = close.rolling(20).mean()
        ma50 = close.rolling(50).mean()
        ma200 = close.rolling(200).mean()

        rsi = compute_rsi(close)

        price = safe(close)
        ma20 = safe(ma20)
        ma50 = safe(ma50)
        ma200 = safe(ma200)

        vol = safe(volume)
        vol_ma = safe(volume.rolling(20).mean())

        if None in [price, ma20, ma50, ma200]:
            return None

        # =========================
        # SCORE ENGINE
        # =========================
        score = 0
        reasons = []

        # TREND
        if price > ma20:
            score += 10
            reasons.append("MA20 üstü (kısa trend güçlü)")

        if ma20 > ma50:
            score += 15
            reasons.append("Orta trend yukarı")

        if ma50 > ma200:
            score += 20
            reasons.append("Uzun vadede güçlü trend")

        # RSI
        if rsi < 30:
            score += 15
            reasons.append("RSI aşırı satım (rebound)")
        elif rsi > 70:
            score -= 10
            reasons.append("RSI aşırı alım (risk)")

        # HACİM
        if vol and vol_ma and vol > vol_ma:
            score += 15
            reasons.append("Hacim artışı")

        # SIKIŞMA
        if abs(price - ma20) / price < 0.03:
            score += 10
            reasons.append("Sıkışma (breakout yakın)")

        # VOLATILITY (FIXED)
        returns = close.pct_change().dropna()

        if len(returns) > 0:
            volatility = np.std(returns.values) * 100  # ✅ FIX

            if volatility < 2:
                score += 10
                reasons.append("Düşük volatilite (akümülasyon)")

        score = max(0, min(100, score))

        return {
            "ticker": ticker,
            "price": price,
            "confidence": score,
            "rsi": rsi,
            "reasons": reasons
        }

    except Exception as e:
        print("ANALYZER ERROR:", ticker, e)
        return None
