# analyzer.py
import yfinance as yf
import pandas as pd
import numpy as np

def get_all_tickers():
    """
    ABD + BIST tüm hisse sembollerini alır.
    ABD: NASDAQ + NYSE
    BIST: BIST100 sembolleri
    """
    # ABD hisseleri (yfinance Tickers sınıfını kullanıyoruz)
    try:
        nasdaq = pd.read_html("https://en.wikipedia.org/wiki/NASDAQ-100")[3]  # NASDAQ-100 tablosu
        nyse = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")[0]  # S&P500 tablosu
        tickers_us = nasdaq['Ticker'].tolist() + nyse['Symbol'].tolist()
        tickers_us = [t.replace('.', '-') for t in tickers_us]  # yfinance uyumu
    except Exception as e:
        print("ABD hisseleri alınamadı:", e)
        tickers_us = []

    # BIST100 sembolleri
    try:
        bist100 = pd.read_html("https://tr.wikipedia.org/wiki/Borsa_Istanbul_100")[0]
        tickers_bist = [str(t).replace('.', '-') + ".IS" for t in bist100['Sembol']]
    except Exception as e:
        print("BIST hisseleri alınamadı:", e)
        tickers_bist = []

    return tickers_us + tickers_bist


def get_stock_signal(ticker: str):
    """
    Hisse için STRONG BUY / SELL / HOLD sinyali üretir
    Teknik ve temel göstergeler kullanılır (RSI, MACD, PD/DD, bilanço)
    """
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="60d")
        if df.empty:
            return None

        # -------- RSI Hesaplama --------
        delta = df['Close'].diff()
        gain = delta.clip(lower=0)
        loss = -1 * delta.clip(upper=0)
        avg_gain = gain.rolling(14).mean().iloc[-1]
        avg_loss = loss.rolling(14).mean().iloc[-1]
        rsi = 100 - (100 / (1 + (avg_gain / (avg_loss + 0.0001))))

        # -------- MACD Hesaplama --------
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=9, adjust=False).mean()
        macd_signal = macd.iloc[-1] - signal_line.iloc[-1]

        # -------- Temel Göstergeler --------
        try:
            info = stock.info
            pd_ratio = info.get('priceToBook', None)
            debt_equity = info.get('debtToEquity', None)
        except:
            pd_ratio = None
            debt_equity = None

        # -------- STRONG BUY / SELL Kararı --------
        # Basit kriterler:
        # RSI < 30 ve MACD pozitif → STRONG BUY
        # RSI > 70 veya MACD negatif → SELL
        if rsi < 30 and macd_signal > 0:
            return "STRONG BUY"
        elif rsi > 70 or macd_signal < 0:
            return "SELL"
        else:
            return "HOLD"

    except Exception as e:
        print(f"{ticker} alınamadı:", e)
        return None


def batch_get_signals():
    """
    Tüm hisse senetlerini tarar ve STRONG BUY olanları döndürür
    """
    tickers = get_all_tickers()
    results = {}
    for ticker in tickers:
        signal = get_stock_signal(ticker)
        if signal in ["STRONG BUY", "SELL"]:
            results[ticker] = signal
    return results
