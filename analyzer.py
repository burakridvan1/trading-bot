import yfinance as yf
import numpy as np
import pandas as pd


# =========================
# SAFE
# =========================
def safe(series):
    try:
        if isinstance(series, pd.Series):
            series = series.dropna()
            if len(series) == 0:
                return None
            return float(series.iloc[-1])
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

        rsi = rsi.dropna()
        if len(rsi) == 0:
            return 50

        return float(rsi.iloc[-1])
    except:
        return 50


# =========================
# WIN RATE (IMPROVED)
# =========================
def compute_win_rate(close):
    try:
        returns = close.pct_change().dropna()
        if len(returns) == 0:
            return 50

        return int((returns > 0).mean() * 100)
    except:
        return 50


# =========================
# BLACKROCK ANALYZER V7
# =========================
def analyze_stock(ticker, sector_weight=1.0):

    try:
        df = yf.download(
            ticker,
            period="6mo",
            interval="1d",
            progress=False,
            threads=False
        )

        if df is None or df.empty or len(df) < 50:
            return None

        close = df["Close"]
        volume = df["Volume"]

        price = safe(close)
        if price is None:
            return None

        ma20 = safe(close.rolling(20).mean())
        ma50 = safe(close.rolling(50).mean())
        ma200 = safe(close.rolling(200).mean())

        rsi = compute_rsi(close)

        vol = safe(volume)
        vol_ma = safe(volume.rolling(20).mean())

        win_rate = compute_win_rate(close)

        returns = close.pct_change().dropna()
        volatility = np.std(returns.values) * 100 if len(returns) > 0 else 0

        score = 50
        reasons = []

        # =========================
        # TREND (CORE WEIGHT)
        # =========================
        if ma20 and price > ma20:
            score += 10
            reasons.append("Trend +")

        if ma20 and ma50 and ma20 > ma50:
            score += 15
            reasons.append("Bull trend")

        if ma50 and ma200 and ma50 > ma200:
            score += 20
            reasons.append("Macro bull")

        # =========================
        # RSI
        # =========================
        if rsi < 30:
            score += 10
            reasons.append("Oversold")
        elif rsi > 70:
            score -= 10
            reasons.append("Overbought")

        # =========================
        # VOLUME
        # =========================
        if vol and vol_ma and vol > vol_ma:
            score += 10
            reasons.append("Smart money flow")

        # =========================
        # VOLATILITY FILTER
        # =========================
        if volatility < 2:
            score += 10
            reasons.append("Low risk zone")
        elif volatility > 6:
            score -= 10
            reasons.append("High risk")

        # =========================
        # WIN RATE BOOST
        # =========================
        score += (win_rate - 50) * 0.2

        # =========================
        # SECTOR MULTIPLIER
        # =========================
        score *= sector_weight

        score = max(0, min(100, score))

        if not reasons:
            reasons.append("Neutral")

        return {
            "ticker": ticker,
            "price": round(price, 2),
            "confidence": round(score, 2),
            "rsi": round(rsi, 2),
            "win_rate": win_rate,
            "volatility": round(volatility, 2),
            "reasons": reasons
        }

    except Exception as e:
        print("ERROR:", ticker, e)
        return None
