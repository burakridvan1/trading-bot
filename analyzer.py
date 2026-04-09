import yfinance as yf
import pandas as pd
import numpy as np

# ------------------- Tüm Hisseler -------------------
def get_all_us_tickers():
    try:
        table = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")[0]
        tickers = table['Symbol'].tolist()
        tickers = [t.replace('.', '-') for t in tickers]
        return tickers
    except:
        return []

def get_all_bist_tickers():
    try:
        table = pd.read_html("https://www.investing.com/indices/bist-100-components")[0]
        tickers = table['Symbol'].apply(lambda x: x.strip() + ".IS").tolist()
        return tickers
    except:
        return []

# ------------------- Teknik İndikatörler -------------------
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -1 * delta.clip(upper=0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(df):
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal

# ------------------- Hisse Analizi -------------------
def get_stock_signal(ticker):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="3mo")
        if df.empty:
            return None

        # RSI
        rsi = calculate_rsi(df['Close']).iloc[-1]

        # MACD
        macd, macd_signal = calculate_macd(df)
        macd_last = macd.iloc[-1]
        signal_last = macd_signal.iloc[-1]

        # PD/DD (Price / Book Value)
        info = stock.info
        price_to_book = info.get('priceToBook', None)
        current_price = info.get('currentPrice', None)
        previous_close = df['Close'].iloc[-2]

        # Basit temel kriterler
        strong_buy = False
        sell = False

        # RSI kriteri: <30 ise aşırı satım
        if rsi < 30:
            strong_buy = True

        # MACD kriteri: MACD > Signal line
        if macd_last > signal_last:
            strong_buy = strong_buy and True

        # PD/DD kriteri: <1.5 ise ucuz
        if price_to_book and price_to_book < 1.5:
            strong_buy = strong_buy and True

        # Fiyat düşerse SELL
        if current_price < previous_close:
            sell = True

        if strong_buy:
            return "STRONG BUY"
        elif sell:
            return "SELL"
        else:
            return "HOLD"

    except Exception as e:
        print(f"{ticker} analiz edilemedi:", e)
        return None
