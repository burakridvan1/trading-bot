# analyzer.py
import yfinance as yf
import pandas as pd
import numpy as np

def calculate_rsi(series, period=14):
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    avg_gain = up.rolling(period, min_periods=1).mean()
    avg_loss = down.rolling(period, min_periods=1).mean()
    rs = avg_gain / avg_loss.replace(0, 1)
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(series, fast=12, slow=26, signal=9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    macd_signal = macd.ewm(span=signal, adjust=False).mean()
    return macd, macd_signal

def get_stock_signal(ticker: str):
    """
    STRONG BUY / SELL sinyali üreten fonksiyon
    RSI < 30 -> oversold -> BUY
    MACD crossover -> BUY/SELL
    PD/DD < 1.5 -> değerli -> BUY
    Son bilanço olumlu -> BUY
    """
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="6mo")
        if df.empty or len(df) < 30:
            return None

        close = df["Close"]

        # ----- RSI -----
        rsi = calculate_rsi(close)
        latest_rsi = rsi.iloc[-1]

        # ----- MACD -----
        macd, macd_signal = calculate_macd(close)
        latest_macd = macd.iloc[-1]
        latest_signal = macd_signal.iloc[-1]

        # MACD crossover kontrolü
        macd_buy = latest_macd > latest_signal and macd.iloc[-2] <= macd_signal.iloc[-2]
        macd_sell = latest_macd < latest_signal and macd.iloc[-2] >= macd_signal.iloc[-2]

        # ----- Temel analiz -----
        info = stock.info
        pe_ratio = info.get("forwardPE", None) or info.get("trailingPE", None)
        pb_ratio = info.get("priceToBook", None)
        pd_ratio = info.get("debtToEquity", None)
        earnings = info.get("earningsQuarterlyGrowth", None)

        strong_buy_conditions = [
            latest_rsi < 30,
            macd_buy,
            pd_ratio is not None and pd_ratio < 1.5,
            earnings is not None and earnings > 0
        ]

        strong_sell_conditions = [
            latest_rsi > 70,
            macd_sell,
            pd_ratio is not None and pd_ratio > 2.5,
            earnings is not None and earnings < 0
        ]

        if all(strong_buy_conditions):
            return "STRONG BUY"
        elif all(strong_sell_conditions):
            return "SELL"
        else:
            return "HOLD"

    except Exception as e:
        print(f"{ticker} alınamadı:", e)
        return None
