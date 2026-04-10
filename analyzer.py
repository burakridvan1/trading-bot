import pandas as pd
import numpy as np
import yfinance as yf


# =========================
# INDICATORS
# =========================

def rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()

    rs = gain / loss
    return 100 - (100 / (1 + rs))


def moving_averages(df):
    df["ma5"] = df["Close"].rolling(5).mean()
    df["ma21"] = df["Close"].rolling(21).mean()
    return df


def volume_spike(df):
    df["vol_ma"] = df["Volume"].rolling(20).mean()
    df["vol_spike"] = df["Volume"] / df["vol_ma"]
    return df


# =========================
# HEDGE FUND SCORING ENGINE
# =========================

def analyze_stock(ticker, entry_price=None):
    try:
        df = yf.download(ticker, period="3mo", interval="1d", progress=False)

        if df.empty:
            return None

        df = moving_averages(df)
        df = volume_spike(df)
        df["rsi"] = rsi(df["Close"])

        last = df.iloc[-1]

        price = float(last["Close"])
        ma5 = float(last["ma5"])
        ma21 = float(last["ma21"])
        rsi_val = float(last["rsi"]) if not np.isnan(last["rsi"]) else 50
        vol_spike = float(last["vol_spike"]) if not np.isnan(last["vol_spike"]) else 1

        # =========================
        # SCORING SYSTEM (HEDGE FUND STYLE)
        # =========================

        score = 0

        # TREND
        if ma5 > ma21:
            score += 30
        else:
            score -= 20

        # RSI
        if rsi_val < 30:
            score += 25
        elif rsi_val < 45:
            score += 10
        elif rsi_val > 70:
            score -= 25

        # VOLUME
        if vol_spike > 1.5:
            score += 20
        elif vol_spike > 1.2:
            score += 10

        # PRICE MOMENTUM
        if price > ma5:
            score += 10

        # ENTRY PRICE (portfolio logic)
        if entry_price:
            if price < entry_price * 0.95:
                score -= 30  # stop loss pressure
            elif price > entry_price * 1.05:
                score += 20  # profit zone

        # =========================
        # CONFIDENCE NORMALIZATION
        # =========================

        confidence = max(0, min(100, score + 50))

        # =========================
        # SIGNAL TYPE
        # =========================

        signal_type = None

        if confidence >= 75 and ma5 > ma21:
            signal_type = "BUY"
        elif confidence <= 35:
            signal_type = "SELL"

        msg = f"""
📊 {ticker}
💰 Price: {price:.2f}
📈 MA5: {ma5:.2f} | MA21: {ma21:.2f}
📉 RSI: {rsi_val:.2f}
📦 Volume Spike: {vol_spike:.2f}
🧠 Confidence: %{confidence}
"""

        if signal_type:
            msg += f"\n🚨 SIGNAL: {signal_type}"

        return {
            "ticker": ticker,
            "price": price,
            "ma5": ma5,
            "ma21": ma21,
            "rsi": rsi_val,
            "volume_spike": vol_spike,
            "confidence": confidence,
            "type": signal_type,
            "msg": msg
        }

    except Exception as e:
        print(f"ERROR {ticker}:", e)
        return None
