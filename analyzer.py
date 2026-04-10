import yfinance as yf
from ta.momentum import RSIIndicator
from ta.trend import MACD, SMAIndicator
from ta.volatility import BollingerBands


def analyze_stock(ticker, buy_price=None):
    try:
        data = yf.download(ticker, period="3mo", interval="1d", progress=False)

        if data is None or data.empty or len(data) < 50:
            return None

        close = data['Close']
        current_price = close.iloc[-1]

        signals = []

        # =====================
        # 📊 RSI
        # =====================
        rsi = RSIIndicator(close).rsi().iloc[-1]
        if rsi < 30:
            signals.append("STRONG BUY")
        elif rsi > 70:
            signals.append("STRONG SELL")

        # =====================
        # 📊 MACD
        # =====================
        macd = MACD(close)
        if macd.macd_diff().iloc[-1] > 0:
            signals.append("BUY")
        else:
            signals.append("SELL")

        # =====================
        # 📊 Bollinger Bands
        # =====================
        bb = BollingerBands(close)
        if current_price < bb.bollinger_lband().iloc[-1]:
            signals.append("STRONG BUY")
        elif current_price > bb.bollinger_hband().iloc[-1]:
            signals.append("STRONG SELL")

        # =====================
        # 📊 SMA TREND (20-50)
        # =====================
        sma20 = SMAIndicator(close, 20).sma_indicator().iloc[-1]
        sma50 = SMAIndicator(close, 50).sma_indicator().iloc[-1]

        if sma20 > sma50:
            signals.append("BUY")
        else:
            signals.append("SELL")

        # =====================
        # 🚀 YENİ: MA5 - MA21
        # =====================
        ma5 = SMAIndicator(close, 5).sma_indicator().iloc[-1]
        ma21 = SMAIndicator(close, 21).sma_indicator().iloc[-1]

        # Golden Cross (kısa vade güçlü yükseliş)
        if ma5 > ma21:
            signals.append("STRONG BUY")

        # Death Cross (kısa vade güçlü düşüş)
        elif ma5 < ma21:
            signals.append("STRONG SELL")

        # =====================
        # 🎯 STRONG FILTER
        # =====================
        strong = [s for s in signals if "STRONG" in s]

        # =====================
        # 📉 PORTFÖY SELL LOGIC
        # =====================
        if buy_price:
            change_pct = ((current_price - buy_price) / buy_price) * 100

            # STOP LOSS
            if change_pct <= -5:
                return f"🚨 {ticker} → STOP LOSS SELL (-{abs(round(change_pct,2))}%)"

            # TAKE PROFIT (trend dönüyorsa)
            if change_pct >= 10 and "SELL" in signals:
                return f"💰 {ticker} → TAKE PROFIT SELL (+{round(change_pct,2)}%)"

        # =====================
        # 📢 OUTPUT
        # =====================
        if strong:
            return f"🔥 {ticker} → {', '.join(set(strong))}"

        return None

    except Exception as e:
        return None
