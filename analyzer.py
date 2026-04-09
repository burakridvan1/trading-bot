import yfinance as yf
from ta.momentum import RSIIndicator
from ta.trend import MACD, SMAIndicator, EMAIndicator
from ta.volatility import BollingerBands

def get_signals(ticker):
    """
    Tek bir hisse için tüm indikatörleri kontrol eder
    ve 'STRONG BUY', 'STRONG SELL' veya 'HOLD' döndürür.
    """
    try:
        df = yf.download(ticker, period="6mo", interval="1d", progress=False)
        if df.empty or len(df) < 20:
            return None

        # RSI
        rsi = RSIIndicator(df['Close'], window=14).rsi()
        rsi_signal = 'BUY' if rsi.iloc[-1] < 30 else 'SELL' if rsi.iloc[-1] > 70 else 'HOLD'

        # MACD
        macd = MACD(df['Close'])
        macd_signal = 'BUY' if macd.macd_diff().iloc[-1] > 0 else 'SELL' if macd.macd_diff().iloc[-1] < 0 else 'HOLD'

        # SMA trend
        sma_short = SMAIndicator(df['Close'], window=20).sma_indicator()
        sma_long = SMAIndicator(df['Close'], window=50).sma_indicator()
        sma_signal = 'BUY' if sma_short.iloc[-1] > sma_long.iloc[-1] else 'SELL' if sma_short.iloc[-1] < sma_long.iloc[-1] else 'HOLD'

        # EMA trend
        ema_short = EMAIndicator(df['Close'], window=20).ema_indicator()
        ema_long = EMAIndicator(df['Close'], window=50).ema_indicator()
        ema_signal = 'BUY' if ema_short.iloc[-1] > ema_long.iloc[-1] else 'SELL' if ema_short.iloc[-1] < ema_long.iloc[-1] else 'HOLD'

        # Bollinger Bands
        bb = BollingerBands(df['Close'], window=20, window_dev=2)
        bb_signal = 'BUY' if df['Close'].iloc[-1] < bb.bollinger_lband().iloc[-1] else 'SELL' if df['Close'].iloc[-1] > bb.bollinger_hband().iloc[-1] else 'HOLD'

        signals = [rsi_signal, macd_signal, sma_signal, ema_signal, bb_signal]

        # STRONG BUY / STRONG SELL
        if signals.count('BUY') >= 4:
            return 'STRONG BUY'
        elif signals.count('SELL') >= 4:
            return 'STRONG SELL'
        else:
            return 'HOLD'

    except Exception as e:
        print(f"Error for {ticker}: {e}")
        return None


def batch_get_signals(tickers):
    """
    Liste halinde hisse tarar ve sinyal olanları döndürür.
    """
    results = {}
    for ticker in tickers:
        signal = get_signals(ticker)
        if signal in ['STRONG BUY', 'STRONG SELL']:
            results[ticker] = signal
    return results
