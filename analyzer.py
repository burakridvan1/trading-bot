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

        # RSI
        rsi = RSIIndicator(close).rsi().iloc[-1]
        if rsi < 30:
            score += 2
        elif rsi > 70:
            score -= 2

        # MACD
        macd = MACD(close)
        if macd.macd_diff().iloc[-1] > 0:
            score += 1
        else:
            score -= 1

        # Bollinger
        bb = BollingerBands(close)
        if current_price < bb.bollinger_lband().iloc[-1]:
            score += 2
        elif current_price > bb.bollinger_hband().iloc[-1]:
            score -= 2

        # Trend
        sma20 = SMAIndicator(close, 20).sma_indicator().iloc[-1]
        sma50 = SMAIndicator(close, 50).sma_indicator().iloc[-1]

        if sma20 > sma50:
            score += 1
        else:
            score -= 1

        # MA5 vs MA21
        ma5 = SMAIndicator(close, 5).sma_indicator().iloc[-1]
        ma21 = SMAIndicator(close, 21).sma_indicator().iloc[-1]

        if ma5 > ma21:
            score += 2
        else:
            score -= 2

        # Confidence
        confidence = round((abs(score) / max_score) * 100, 1)

        # PORTFÖY
        if buy_price:
            change_pct = ((current_price - buy_price) / buy_price) * 100

            if change_pct <= -5:
                return {"type": "STOP", "msg": f"🚨 {ticker} STOP LOSS (-{abs(round(change_pct,2))}%)"}

            if change_pct >= 10 and score < 0:
                return {"type": "TP", "msg": f"💰 {ticker} TAKE PROFIT (+{round(change_pct,2)}%)"}

        # TOP fırsatlar için veri döndür
        if score >= 4:
            return {
                "type": "BUY",
                "ticker": ticker,
                "score": score,
                "confidence": confidence
            }

        elif score <= -4:
            return {
                "type": "SELL",
                "msg": f"🚨 {ticker} STRONG SELL | Score: {score} | %{confidence}"
            }

        return None

    except:
        return None
