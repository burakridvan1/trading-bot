import yfinance as yf
import numpy as np
import pandas as pd


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


def compute_win_rate(close):
    try:
        future_returns = close.pct_change().shift(-5)
        signals = close.pct_change()

        wins = ((signals > 0) & (future_returns > 0)).sum()
        total = len(close)

        if total == 0:
            return 50

        return int((wins / total) * 100)
    except:
        return 50


def analyze_stock(ticker):
    try:
        df = yf.download(
            ticker,
            period="6mo",
            interval="1d",
            progress=False,
            threads=False
        )

        if df is None or df.empty:
            return None

        close = df["Close"]
        volume = df["Volume"]

        price = safe(close)
        ma20 = safe(close.rolling(20).mean())
        ma50 = safe(close.rolling(50).mean())
        ma200 = safe(close.rolling(200).mean())

        rsi = compute_rsi(close)
        vol = safe(volume)
        vol_ma = safe(volume.rolling(20).mean())

        win_rate = compute_win_rate(close)

        score = 0
        reasons = []

        if price and ma20 and price > ma20:
            score += 10
            reasons.append("MA20 üstü")

        if ma20 and ma50 and ma20 > ma50:
            score += 15
            reasons.append("Trend güçlü")

        if ma50 and ma200 and ma50 > ma200:
            score += 20
            reasons.append("Uzun trend güçlü")

        if rsi < 30:
            score += 15
            reasons.append("RSI düşük")
        elif rsi > 70:
            score -= 10
            reasons.append("RSI yüksek")

        if vol and vol_ma and vol > vol_ma:
            score += 10
            reasons.append("Hacim artışı")

        returns = close.pct_change().dropna()
        if len(returns) > 10:
            volatility = np.std(returns.values) * 100
            if volatility < 2:
                score += 10
                reasons.append("Düşük volatilite")

        if ma20 and abs(price - ma20) / price < 0.03:
            score += 10
            reasons.append("Sıkışma")

        score = max(5, min(100, score))

        if not reasons:
            reasons.append("Nötr")

        return {
            "ticker": ticker,
            "price": price,
            "confidence": score,
            "rsi": rsi,
            "win_rate": win_rate,
            "reasons": reasons
        }

    except Exception as e:
        print("ERROR:", ticker, e)
        return None
