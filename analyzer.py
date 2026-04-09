import yfinance as yf
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_signal(ticker: str):
    """
    Hisseye göre STRONG BUY veya SELL sinyali üretir.
    Basit simülasyon: son kapanış ortalamadan yüksekse STRONG BUY,
    düşükse SELL, diğer durumlarda HOLD döner.
    """
    try:
        df = yf.Ticker(ticker).history(period="5d")
        if df.empty:
            return None
        close = df["Close"]
        if close.iloc[-1] > close.mean():
            return "STRONG BUY"
        elif close.iloc[-1] < close.mean():
            return "SELL"
        else:
            return "HOLD"
    except Exception as e:
        logger.warning(f"{ticker} alınamadı: {e}")
        return None
