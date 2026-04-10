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
# BENCHMARK (SPY)
# =========================
def benchmark():
    try:
        df = yf.download("SPY", period="1mo", interval="1d", progress=False)
        return float(df["Close"].pct_change().mean())
    except:
        return 0.001


# =========================
# MAIN ANALYSIS ENGINE
# =========================
def analyze_stock(ticker):
    try:
        df = yf.download(ticker, period="9mo", interval="1d", progress=False)

        if df is None or df.empty or len(df) < 80:
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

        volatility = float(np.std(returns))
        momentum_10 = float(np.mean(returns[-10:]))
        momentum_60 = float(np.mean(returns[-60:]))

        spy = benchmark()

        score = 55
        reasons = []

        # =========================
        # TREND STRUCTURE
        # =========================
        if ma5 > ma21 > ma50:
            score += 30
            reasons.append("Güçlü kurumsal yükseliş trendi (MA uyumu)")
        elif ma5 > ma21:
            score += 15
            reasons.append("Kısa vadeli yükseliş trendi")
        else:
            score -= 20
            reasons.append("Trend zayıf / dağıtım bölgesi")

        if price > ma200:
            score += 20
            reasons.append("Uzun vadeli boğa piyasası yapısı (MA200 üstü)")
        else:
            score -= 15
            reasons.append("Makro trend zayıf (MA200 altı)")

        # =========================
        # RSI LOGIC
        # =========================
        if rsi_val < 30:
            score += 25
            reasons.append("Aşırı satım – akümülasyon bölgesi")
        elif rsi_val < 45:
            score += 10
            reasons.append("Birikim bölgesi")
        elif rsi_val > 70:
            score -= 25
            reasons.append("Aşırı alım – düzeltme riski")

        # =========================
        # MOMENTUM
        # =========================
        if momentum_60 > spy:
            score += 25
            reasons.append("Endeks üstü performans (alfa üretimi)")
        else:
            score -= 10
            reasons.append("Endeks altı performans")

        if momentum_10 > momentum_60:
            score += 10
            reasons.append("Momentum hızlanması")

        # =========================
        # VOLATILITY RISK
        # =========================
        if volatility < 0.02:
            score += 10
            reasons.append("Düşük riskli volatilite rejimi")
        elif volatility > 0.04:
            score -= 20
            reasons.append("Yüksek volatilite – risk artışı")

        # =========================
        # FINAL SCORE
        # =========================
        confidence = max(0, min(100, score))

        return {
            "ticker": ticker,
            "price": price,
            "confidence": confidence,
            "rsi": rsi_val,
            "volatility": volatility,
            "momentum": momentum_60,
            "reasons": reasons
        }

    except:
        return None
