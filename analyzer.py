import yfinance as yf
import ta

def analyze(ticker):
    # Veriyi çek
    df = yf.download(ticker, period="3mo", interval="1d")

    # Eğer veri boşsa hata vermesin
    if df.empty:
        return 0, 0, 0

    # Close sütunu Series olmalı
    close = df['Close'].squeeze()  # ndarray → Series yapar

    # RSI
    df['rsi'] = ta.momentum.RSIIndicator(close).rsi()

    # MACD
    macd = ta.trend.MACD(close)
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()

    last = df.iloc[-1]

    score = 0
    if last['rsi'] < 30:
        score += 20
    if last['macd'] > last['macd_signal']:
        score += 20

    return score, last['Close'], last['rsi']
