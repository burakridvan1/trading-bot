import os
from dotenv import load_dotenv
from telegram import Bot
from analyzer import analyze

load_dotenv()

bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
CHAT_ID = os.getenv("CHAT_ID")

stocks = ["AAPL", "TSLA", "THYAO.IS", "ASELS.IS"]

def run():
    for s in stocks:
        try:
            score, price, rsi = analyze(s)

            if score >= 50:
                signal = "🚀 STRONG BUY"
            elif score >= 30:
                signal = "📈 BUY"
            else:
                continue

            msg = f"{s}\nFiyat: {price:.2f}\nRSI: {rsi:.2f}\nSkor: {score}\n{signal}"

            bot.send_message(chat_id=CHAT_ID, text=msg)

        except Exception as e:
            print(f"Hata: {s} - {e}")

if __name__ == "__main__":
    run()
