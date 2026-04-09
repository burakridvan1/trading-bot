# analyzer.py
import yfinance as yf
import pandas as pd

def get_stock_signal(ticker: str):
    """
    Hisseyi alır ve temel göstergeleri kontrol edip STRONG BUY / SELL üretir
    Göstergeler: RSI, MACD, PD/DD, Basit Bilanço kontrolü
    """
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="6mo")  # 6 aylık fiyat verisi
        if df.empty or len(df) < 2:
            return None

        # ----- RSI Hesaplama -----
        delta = df["Close"].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(14).mean().iloc[-1]
        avg_loss = loss.rolling(14).mean().iloc[-1]
        rsi = 100 - (100 / (1 + avg_gain / (avg_loss + 1e-6)))

        # ----- MACD Hesaplama -----
        ema12 = df["Close"].ewm(span=12, adjust=False).mean()
        ema26 = df["Close"].ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        signal_line = macd.ewm(span=9, adjust=False).mean()
        macd_signal = macd.iloc[-1] - signal_line.iloc[-1]

        # ----- Basit Fiyat/Kazanç ve Bilanço -----
        pe_ratio = stock.info.get("trailingPE", None)
        pb_ratio = stock.info.get("priceToBook", None)

        # ----- STRONG BUY / SELL Kararı -----
        strong_buy = rsi < 30 and macd_signal > 0
        sell = rsi > 70 and macd_signal < 0

        # Ek koşullar: PE ve PB makul ise buy, aşırı yüksekse sell
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
