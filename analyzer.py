# analyzer.py
import yfinance as yf
import pandas as pd
import numpy as np

def calculate_rsi(series: pd.Series, period: int = 14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    return macd, signal_line

def get_fundamental_signal(ticker: str):
    """
    Basit fundamental kontrol: PD/DD < 1.5, F/K < 20 vs.
    """
    try:
        info = yf.Ticker(ticker).info
        pd_dd = info.get("priceToBook", 0)
        pe_ratio = info.get("trailingPE", 0)
        if pd_dd < 1.5 and pe_ratio < 20:
            return True
        return False
    except:
        return False

def get_stock_signal(ticker: str, df: pd.DataFrame = None):
    """
    Hisseyi analiz eder ve STRONG BUY / SELL / HOLD döndürür
    """
    try:
        if df is None:
            df = yf.Ticker(ticker).history(period="60d")
        if df.empty or len(df) < 30:
            return None

        # RSI
        rsi = calculate_rsi(df['Close'])
        last_rsi = rsi.iloc[-1]

        # MACD
        macd, signal_line = calculate_macd(df['Close'])
        last_macd = macd.iloc[-1]
        last_signal = signal_line.iloc[-1]

        # Fiyat hareketi
        price_today = df['Close'].iloc[-1]
        price_yesterday = df['Close'].iloc[-2]

        # Fundamental
        fundamental_ok = get_fundamental_signal(ticker)

        # STRONG BUY koşulları
        if last_rsi < 30 and last_macd > last_signal and price_today > price_yesterday and fundamental_ok:
            return "STRONG BUY"
        # SELL koşulları
        elif last_rsi > 70 or last_macd < last_signal or price_today < price_yesterday:
            return "SELL"
        else:
            return "HOLD"
    except Exception as e:
        print(f"{ticker} analiz hatası:", e)
        return None

def batch_get_signals(tickers: list):
    """
    Tüm tickers için batch veri çekip sinyal üretir
    """
    signals = {}
    try:
        # Toplu veri çekme
        df_all = yf.download(tickers, period="60d", group_by='ticker', threads=True)
        for ticker in tickers:
            try:
                df = df_all[ticker].copy()
            except:
                df = None
            signal = get_stock_signal(ticker, df)
            if signal:
                signals[ticker] = signal
    except Exception as e:
        print("Batch veri çekme hatası:", e)
    return signals
