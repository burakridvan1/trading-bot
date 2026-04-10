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


def analyze_stock(ticker):

    try:
        df = yf.download(
            ticker,
            period="6mo",      # 🔥 MA200 için gerekli
            interval="1d",
            progress=False,
            threads=False
        )

        if df is None or df.empty:
            return None

        close = df["Close"]
        volume = df["Volume"]

        price = safe(close)
        if price is None:
            return None

        # =========================
        # INDICATORS
        # =========================
        ma20 = safe(close.rolling(20).mean())
        ma50 = safe(close.rolling(50).mean())
        ma200 = safe(close.rolling(200).mean())

        rsi = compute_rsi(close)

        vol = safe(volume)
        vol_ma = safe(volume.rolling(20).mean())

        # =========================
        # SCORE SYSTEM
        # =========================
        score = 0
        reasons = []

        # ✅ MA20 varsa kullan
        if ma20 is not None:
            if price > ma20:
                score += 10
                reasons.append("MA20 üstü (kısa trend)")

        # ✅ MA50 varsa kullan
        if ma20 is not None and ma50 is not None:
            if ma20 > ma50:
                score += 15
                reasons.append("MA20 > MA50 (trend güçlü)")

        # ✅ MA200 varsa kullan
        if ma50 is not None and ma200 is not None:
            if ma50 > ma200:
                score += 20
                reasons.append("MA50 > MA200 (uzun trend güçlü)")

        # RSI HER ZAMAN VAR
        if rsi < 30:
            score += 15
            reasons.append("RSI düşük (alım fırsatı)")
        elif rsi > 70:
            score -= 10
            reasons.append("RSI yüksek (risk)")

        # HACİM
        if vol and vol_ma:
            if vol > vol_ma:
                score += 10
                reasons.append("Hacim artışı")

        # VOLATILITY
        returns = close.pct_change().dropna()
        if len(returns) > 10:
            volatility = np.std(returns.values) * 100

            if volatility < 2:
                score += 10
                reasons.append("Düşük volatilite")

        # SIKIŞMA
        if ma20 is not None:
            if abs(price - ma20) / price < 0.03:
                score += 10
                reasons.append("Sıkışma (breakout yakın)")

        # 🔥 KRİTİK: minimum skor
        score = max(5, min(100, score))

        # 🔥 KRİTİK: reason boş kalmasın
        if not reasons:
            reasons.append("Temel teknik yapı nötr")

        return {
            "ticker": ticker,
            "price": price,
            "confidence": score,
            "rsi": rsi,
            "reasons": reasons
        }

    except Exception as e:
        print("ERROR:", ticker, e)
        return None
