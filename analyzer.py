# analyzer.py
import yfinance as yf
import pandas as pd
import numpy as np

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -1 * delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def compute_macd(series, fast=12, slow=26, signal=9):
    exp1 = series.ewm(span=fast, adjust=False).mean()
    exp2 = series.ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    return macd, signal_line

def get_stock_signal(ticker: str):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="6mo")
        if df.empty:
            return None
        
        # RSI
        df['RSI'] = compute_rsi(df['Close'])
        rsi_latest = df['RSI'].iloc[-1]
        
        # MACD
        macd, macd_signal = compute_macd(df['Close'])
        macd_latest = macd.iloc[-1]
        macd_signal_latest = macd_signal.iloc[-1]
        
        # Basit bilanço göstergeleri (PD/DD, fiyat/kazanç vb)
        info = stock.info
        pd_dd = info.get("priceToBook", None)
        pe_ratio = info.get("trailingPE", None)
        
        # STRONG BUY kriterleri
        if (rsi_latest < 30 and 
            macd_latest > macd_signal_latest and 
            pd_dd is not None and pd_dd < 1 and 
            pe_ratio is not None and pe_ratio < 15):
            return "STRONG BUY"
        
        # SELL kriterleri
        if (rsi_latest > 70 or macd_latest < macd_signal_latest):
            return "SELL"
        
        return "HOLD"
    
    except Exception as e:
        print(f"{ticker} alınamadı:", e)
        return None
