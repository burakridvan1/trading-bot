import numpy as np
import pandas as pd
import yfinance as yf


def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def spy_benchmark():
    data = yf.download("SPY", period="1mo", interval="1d", progress=False)
    if data is None or data.empty:
        return 0
    return float(data["Close"].pct_change().mean())


def analyze_stock(ticker):
    try:
        df = yf.download(ticker, period="6mo", interval="1d", progress=False)

        if df is None or len(df) < 60:
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
        momentum_30 = float(np.mean(returns[-30:]))

        spy = spy_benchmark()

        score = 50
        reasons = []

        # =========================
        # TREND
        # =========================
        if ma5 > ma21 > ma50:
            score += 35
            reasons.append("Güçlü yükseliş trendi (kurumsal MA uyumu)")
        elif ma5 > ma21:
            score += 20
            reasons.append("Kısa vadeli yükseliş trendi")
        else:
            score -= 25
            reasons.append("Zayıf trend / dağıtım bölgesi")

        if price > ma200:
            score += 15
            reasons.append("Ana trend (MA200) üzerinde – boğa piyasası yapısı")
        else:
            score -= 10
            reasons.append("MA200 altında – makro zayıflık")

        # =========================
        # RSI
        # =========================
        if rsi_val < 30:
            score += 25
            reasons.append("Aşırı satım – kurumsal birikim bölgesi")
        elif rsi_val < 45:
            score += 10
            reasons.append("Birikim bölgesi")
        elif rsi_val > 70:
            score -= 25
            reasons.append("Aşırı alım – kâr realizasyonu riski")

        # =========================
        # MOMENTUM vs PİYASA
        # =========================
        if momentum_30 > spy:
            score += 25
            reasons.append("Piyasa üzerinde getiri (alfa üretiyor)")
        else:
            score -= 10
            reasons.append("Piyasa endeksinin altında performans")

        # =========================
        # MOMENTUM HIZLANMA
        # =========================
        if momentum_10 > momentum_30:
            score += 10
            reasons.append("Momentum hızlanması tespit edildi")

        # =========================
        # VOLATİLİTE
        # =========================
        if volatility < 0.02:
            score += 10
            reasons.append("Düşük volatilite – kurumsal stabil yapı")
        elif volatility > 0.04:
            score -= 20
            reasons.append("Yüksek riskli volatilite rejimi")

        # =========================
        # FİYAT KONUMU
        # =========================
        if price > ma50:
            score += 10
            reasons.append("Orta vadeli trend (MA50) üzerinde")

        confidence = max(0, min(100, score))

        return {
            "ticker": ticker,
            "price": price,
            "confidence": confidence,
            "rsi": rsi_val,
            "volatility": volatility,
            "momentum": momentum_30,
            "reasons": reasons
        }

    except Exception as e:
        print("HATA:", ticker, e)
        return None
