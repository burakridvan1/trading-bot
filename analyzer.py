import yfinance as yf
import numpy as np
import pandas as pd


# =========================
# SAFE VALUE
# =========================
def safe(series):
    try:
        if series is None:
            return None

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
# WIN RATE (SAFE)
# =========================
def compute_win_rate(close):
    try:
        if close is None or len(close) < 30:
            return 50

        future = close.shift(-5)
        returns = close.pct_change()

        valid = (returns > 0) & (future.pct_change() > 0)

        if len(valid) == 0:
            return 50

        return int((valid.sum() / len(close)) * 100)

    except:
        return 50


# =========================
# ANALYZE STOCK
# =========================
def analyze_stock(ticker):

    try:
        df = yf.download(
            ticker,
            period="1y",
            interval="1d",
            progress=False,
            threads=False,
            auto_adjust=False
        )

        # =========================
        # DATA CHECK
        # =========================
        if df is None or df.empty:
            return None

        if "Close" not in df:
            return None

        close = df["Close"]
        volume = df["Volume"]

        if len(close.dropna()) < 30:
            return None

        # =========================
        # VALUES
        # =========================
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

        # =========================
        # SCORE ENGINE
        # =========================
        score = 0
        reasons = []

        # Trend
        if ma20 and price > ma20:
            score += 10
            reasons.append("MA20 üstü")

        if ma20 and ma50 and ma20 > ma50:
            score += 15
            reasons.append("Trend güçlü")

        if ma50 and ma200 and ma50 > ma200:
            score += 20
            reasons.append("Uzun trend")

        # RSI
        if rsi < 30:
            score += 15
            reasons.append("RSI oversold")
        elif rsi > 70:
            score -= 10
            reasons.append("RSI overbought")

        # Volume
        if vol and vol_ma and vol > vol_ma:
            score += 10
            reasons.append("Hacim artışı")

        # Volatility
        try:
            returns = close.pct_change().dropna()
            if len(returns) > 10:
                volatility = np.std(returns) * 100
                if volatility < 2:
                    score += 10
                    reasons.append("Düşük volatilite")
        except:
            pass

        # Compression
        if ma20 and price:
            if abs(price - ma20) / price < 0.03:
                score += 10
                reasons.append("Sıkışma")

        score = max(5, min(100, score))

        if not reasons:
            reasons = ["Nötr"]

        return {
            "ticker": ticker,
            "price": round(price, 2),
            "confidence": score,
            "rsi": rsi,
            "win_rate": win_rate,
            "reasons": reasons
        }

    except:
        return None
