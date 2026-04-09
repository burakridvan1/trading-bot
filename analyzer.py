import yfinance as yf
import ta
import pandas as pd

def analyze(ticker):
    # Veri çek
    df = yf.download(ticker, period="3mo", interval="1d")
    if df.empty:
        return 0, 0, 0

    # Close sütununu 1D Series yap
    close = df['Close'].copy()
    if isinstance(close, pd.DataFrame):
        close = close.squeeze()  # shape=(n,1) → shape=(n,)

    # RSI
    df['rsi'] = ta.momentum.RSIIndicator(close).rsi()

    # MACD
    macd_indicator = ta.trend.MACD(close)
    df['macd'] = macd_indicator.macd()
    df['macd_signal'] = macd_indicator.macd_signal()

    last = df.iloc[-1]

    # MACD ve MACD signal tek değer
    macd_value = last['macd']
    macd_signal = last['macd_signal']

    # Eğer hala Series ise tek eleman al
    if isinstance(macd_value, pd.Series):
        macd_value = macd_value.iloc[-1]
    if isinstance(macd_signal, pd.Series):
        macd_signal = macd_signal.iloc[-1]

    score = 0
    if last['rsi'] < 30:
        score += 20
    if macd_value > macd_signal:
        score += 20

    return score, last['Close'], last['rsi']
