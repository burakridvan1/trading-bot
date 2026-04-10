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

        score = 0
        max_score = 8
        reasons = []

        # =====================
        # 📊 RSI
        # =====================
        rsi = RSIIndicator(close).rsi().iloc[-1]
        if rsi < 30:
            score += 2
            reasons.append("RSI Oversold")
        elif rsi > 70:
            score -= 2
            reasons.append("RSI Overbought")

        # =====================
        # 📊 MACD
        # =====================
        macd = MACD(close)
        if macd.macd_diff().iloc[-1] > 0:
            score += 1
            reasons.append("MACD Bullish")
        else:
            score -= 1
            reasons.append("MACD Bearish")

        # =====================
        # 📊 Bollinger
        # =====================
        bb = BollingerBands(close)
        if current_price < bb.bollinger_lband().iloc[-1]:
            score += 2
            reasons.append("BB Lower")
        elif current_price > bb.bollinger_hband().iloc[-1]:
            score -= 2
            reasons.append("BB Upper")

        # =====================
        # 📊 SMA TREND
        # =====================
        sma20 = SMAIndicator(close, 20).sma_indicator().iloc[-1]
        sma50 = SMAIndicator(close, 50).sma_indicator().iloc[-1]

        if sma20 > sma50:
            score += 1
            reasons.append("Trend Up")
        else:
            score -= 1
            reasons.append("Trend Down")

        # =====================
        # 🚀 MA5 - MA21
        # =====================
        ma5 = SMAIndicator(close, 5).sma_indicator().iloc[-1]
        ma21 = SMAIndicator(close, 21).sma_indicator().iloc[-1]

        if ma5 > ma21:
            score += 2
            reasons.append("Short Trend Up")
        else:
            score -= 2
            reasons.append("Short Trend Down")

        # =====================
        # 📉 PORTFÖY LOGIC
        # =====================
        if buy_price:
            change_pct = ((current_price - buy_price) / buy_price) * 100

            if change_pct <= -5:
                return f"🚨 {ticker} → STOP LOSS SELL (-{abs(round(change_pct,2))}%)"

            if change_pct >= 10 and score < 0:
                return f"💰 {ticker} → TAKE PROFIT SELL (+{round(change_pct,2)}%)"

        # =====================
        # 🎯 CONFIDENCE
        # =====================
        confidence = round((abs(score) / max_score) * 100, 1)

        # =====================
        # 📢 KARAR
        # =====================
        if score >= 4:
            return f"🔥 {ticker} → STRONG BUY | Score: {score} | Confidence: %{confidence}"

        elif score <= -4:
            return f"🚨 {ticker} → STRONG SELL | Score: {score} | Confidence: %{confidence}"

        return None

    except:
        return None
