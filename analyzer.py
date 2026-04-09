# analyzer.py
import yfinance as yf
import pandas as pd

def get_all_tickers():
    """ABD ve BIST tüm hisselerini yfinance ile otomatik al"""
    try:
        us = yf.Tickers('AAPL MSFT TSLA GOOGL AMZN NFLX META NVDA JPM BAC XOM JNJ PG')
        # Örnek ABD, BIST ekleme:
        bist = yf.Tickers('ASELS.IS THYAO.IS GARAN.IS SISE.IS KRDMD.IS KOZAL.IS')
        tickers = list(us.tickers.keys()) + list(bist.tickers.keys())
        return tickers
    except Exception as e:
        print("Hisse listesi alınamadı:", e)
        return []

def get_stock_signal(ticker: str):
    """Tek hisseyi tarayıp STRONG BUY / SELL sinyali döndürür"""
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="6mo")
        if df.empty or len(df) < 2:
            return None

        # RSI Hesaplama
        delta = df["Close"].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(14).mean().iloc[-1]
        avg_loss = loss.rolling(14).mean().iloc[-1]
        rsi = 100 - (100 / (1 + avg_gain / (avg_loss + 1e-6)))

        # MACD Hesaplama
        ema12 = df["Close"].ewm(span=12, adjust=False).mean()
        ema26 = df["Close"].ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        signal_line = macd.ewm(span=9, adjust=False).mean()
        macd_signal = macd.iloc[-1] - signal_line.iloc[-1]

        # P/E ve P/B
        pe_ratio = stock.info.get("trailingPE", None)
        pb_ratio = stock.info.get("priceToBook", None)

        # STRONG BUY ve SELL koşulları
        strong_buy = rsi < 30 and macd_signal > 0
        sell = rsi > 70 and macd_signal < 0

        if pe_ratio and pb_ratio:
            if pe_ratio < 15 and pb_ratio < 3 and strong_buy:
                return "STRONG BUY"
            elif pe_ratio > 30 and pb_ratio > 5 and sell:
                return "SELL"

        if strong_buy:
            return "STRONG BUY"
        elif sell:
            return "SELL"
        else:
            return "HOLD"

    except Exception as e:
        print(f"{ticker} alınamadı:", e)
        return None

def batch_get_signals(tickers=None):
    """Tüm hisseleri tarayıp sinyalleri döndürür"""
    if tickers is None:
        tickers = get_all_tickers()
    results = {}
    for ticker in tickers:
        signal = get_stock_signal(ticker)
        if signal:
            results[ticker] = signal
    return results
