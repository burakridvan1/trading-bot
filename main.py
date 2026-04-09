import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import yfinance as yf
import pandas as pd

# ENV variables
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = int(os.environ.get("CHAT_ID"))

# Portföy: kendi hisselerini buraya ekle
portfolio = ["AAPL", "TSLA", "THYAO.IS", "ASELS.IS"]

# Basit RSI analiz fonksiyonu
def analyze_stock(ticker_symbol):
    try:
        data = yf.download(ticker_symbol, period="3mo", interval="1d")
        if data.empty:
            return f"{ticker_symbol} için veri yok."
        close = data["Close"]
        delta = close.diff()
        up, down = delta.clip(lower=0), -1*delta.clip(upper=0)
        roll_up = up.rolling(14).mean()
        roll_down = down.rolling(14).mean()
        RS = roll_up / roll_down
        RSI = 100 - (100 / (1 + RS))
        signal = "⚪ Bekle"
        if RSI.iloc[-1] < 30:
            signal = "🟢 AL"
        elif RSI.iloc[-1] > 70:
            signal = "🔴 SAT"
        return f"{ticker_symbol} - Kapanış: {close.iloc[-1]:.2f} - RSI: {RSI.iloc[-1]:.2f} - Sinyal: {signal}"
    except Exception as e:
        return f"Hata: {ticker_symbol} - {str(e)}"

# /start komutu
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="📈 Borsa botu çalışıyor!")

# Portföyü kontrol et ve mesaj gönder
async def portfolio_check(context: ContextTypes.DEFAULT_TYPE):
    messages = [analyze_stock(stock) for stock in portfolio]
    await context.bot.send_message(chat_id=CHAT_ID, text="\n".join(messages))

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Komut ekle
    app.add_handler(CommandHandler("start", start))

    # JobQueue kullanımı (sorunsuz)
    if app.job_queue:
        app.job_queue.run_repeating(portfolio_check, interval=3600, first=10)
    else:
        print("JobQueue mevcut değil, [job-queue] ile kurulum yapın!")

    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
