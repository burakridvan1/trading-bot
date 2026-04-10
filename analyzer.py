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
# MARKET BENCHMARK
# =========================
def spy_benchmark():
    data = yf.download("SPY", period="1mo", interval="1d", progress=False)
    if data is None or data.empty:
        return 0
    return float(data["Close"].pct_change().mean())


# =========================
# CORE ANALYSIS ENGINE
# =========================
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
        df["ret"] = df["Close"].pct_change()

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
        # TREND STRUCTURE (HEAVY WEIGHT)
        # =========================
        if ma5 > ma21 > ma50:
            score += 35
            reasons.append("Strong bullish institutional trend (MA stack aligned)")
        elif ma5 > ma21:
            score += 20
            reasons.append("Short-term bullish structure")
        else:
            score -= 25
            reasons.append("Distribution / weak trend structure")

        # long term trend confirmation
        if price > ma200:
            score += 15
            reasons.append("Above 200 MA (macro uptrend)")
        else:
            score -= 10
            reasons.append("Below 200 MA (macro weakness)")

        # =========================
        # RSI ZONES
        # =========================
        if rsi_val < 30:
            score += 25
            reasons.append("Oversold institutional accumulation zone")
        elif rsi_val < 45:
            score += 10
            reasons.append("Accumulative zone")
        elif rsi_val > 70:
            score -= 25
            reasons.append("Overbought profit-taking risk")

        # =========================
        # MOMENTUM vs MARKET
        # =========================
        if momentum_30 > spy:
            score += 25
            reasons.append("Outperforming SPY (alpha generation)")
        else:
            score -= 10
            reasons.append("Underperforming market benchmark")

        # =========================
        # MOMENTUM ACCELERATION
        # =========================
        if momentum_10 > momentum_30:
            score += 10
            reasons.append("Momentum acceleration detected")

        # =========================
        # VOLATILITY RISK
        # =========================
        if volatility < 0.02:
            score += 10
            reasons.append("Low volatility institutional stability")
        elif volatility > 0.04:
            score -= 20
            reasons.append("High volatility risk regime")

        # =========================
        # PRICE ACTION QUALITY
        # =========================
        if price > ma50:
            score += 10
            reasons.append("Price above mid-term trend (MA50 support)")

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
        print("ERROR:", ticker, e)
        return None
