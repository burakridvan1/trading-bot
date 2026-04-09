import yfinance as yf
import ta
import pandas as pd

def analyze(ticker):
    # Veri çek
    df = yf.download(ticker, period="3mo", interval="1d")
    if df.empty:
        return 0, 0, 0

    # Close sütunu kesin 1D Series
    close = df['Close']
    if isinstance(close, pd.DataFrame):
        close = close.squeeze()

    # RSI
    rsi_indicator = ta.momentum.RSIIndicator(close)
    df['rsi'] = rsi_indicator.rsi()

    # MACD
    macd_indicator = ta.trend.MACD(close)
    macd_series = macd_indicator.macd()
    macd_signal_series = macd_indicator.macd_signal()

    # Son değerleri float yap
    macd_value = float(macd_series.iloc[-1])
    macd_signal = float(macd_signal_series.iloc[-1])
    rsi_value = float(df['rsi'].iloc[-1])
    close_value = float(close.iloc[-1])

    # Skor hesapla
    score = 0
    if rsi_value < 30:
        score += 20
    if macd_value > macd_signal:
        score += 20

    return score, close_value, rsi_value
