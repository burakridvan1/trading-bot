import yfinance as yf
import ta

def analyze(ticker):
    df = yf.download(ticker, period="3mo", interval="1d")

    df['rsi'] = ta.momentum.RSIIndicator(df['Close']).rsi()
    macd = ta.trend.MACD(df['Close'])
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()

    last = df.iloc[-1]

    score = 0

    if last['rsi'] < 30:
        score += 20
    if last['macd'] > last['macd_signal']:
        score += 20

    return score, last['Close'], last['rsi']
