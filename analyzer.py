import yfinance as yf
import numpy as np


def safe(x):
    try:
        return float(x.iloc[-1])
    except:
        return None


def compute_rsi(series, period=14):
    try:
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return float(rsi.iloc[-1])
    except:
        return 50


def analyze_stock(ticker):

    try:
        df = yf.download(ticker, period="6mo", interval="1d", progress=False)

        if df is None or df.empty or len(df) < 60:
            return None

        close = df["Close"]
        volume = df["Volume"]

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

        score = 0
        reasons = []

        # TREND
        if price > ma20:
            score += 10
            reasons.append("Kısa vadede güçlü (MA20 üstü)")

        if ma20 > ma50:
            score += 15
            reasons.append("Orta vadede yükseliş trendi")

        if ma50 > ma200:
            score += 20
            reasons.append("Uzun vadede güçlü trend")

        # RSI
        if rsi < 30:
            score += 15
            reasons.append("Aşırı satım (alım fırsatı)")
        elif rsi > 70:
            score -= 10
            reasons.append("Aşırı alım (riskli)")

        # HACİM
        if vol and vol_ma and vol > vol_ma:
            score += 15
            reasons.append("Yüksek hacim (kurumsal giriş olabilir)")

        # SIKIŞMA
        if abs(price - ma20) / price < 0.03:
            score += 10
            reasons.append("Sıkışma (breakout potansiyeli)")

        # VOLATİLİTE
        volatility = np.std(close.pct_change().dropna()) * 100

        if volatility < 2:
            score += 10
            reasons.append("Düşük volatilite (stabil birikim)")

        score = max(0, min(100, score))

        return {
            "ticker": ticker,
            "price": price,
            "confidence": score,
            "rsi": rsi,
            "reasons": reasons
        }

    except:
        return None
