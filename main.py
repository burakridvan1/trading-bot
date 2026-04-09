import json
import os
import schedule
import time
from telegram import Bot, Update
from telegram.ext import CommandHandler, ApplicationBuilder, ContextTypes
from analyzer import analyze

TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
PORTFOLIO_FILE = "portfolio.json"

# Portföy yükle
try:
    with open(PORTFOLIO_FILE, "r") as f:
        portfolio = json.load(f)
except:
    portfolio = {}

def save_portfolio():
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(portfolio, f)

# Komutlar
async def ekle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Lütfen bir hisse girin: /ekle TICKER")
        return
    ticker = context.args[0].upper()
    portfolio[ticker] = {}
    save_portfolio()
    await update.message.reply_text(f"{ticker} portföyüne eklendi ✅")

async def sil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Lütfen bir hisse girin: /sil TICKER")
        return
    ticker = context.args[0].upper()
    if ticker in portfolio:
        portfolio.pop(ticker)
        save_portfolio()
        await update.message.reply_text(f"{ticker} portföyünden çıkarıldı ❌")
    else:
        await update.message.reply_text(f"{ticker} portföyde yok ❌")

async def portfoy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not portfolio:
        await update.message.reply_text("Portföyünüz boş 😅")
        return
    msg = "📈 Portföyünüz:\n" + "\n".join(portfolio.keys())
    await update.message.reply_text(msg)

async def analiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not portfolio:
        await update.message.reply_text("Portföyünüz boş 😅")
        return
    for ticker in portfolio.keys():
        score, close, rsi = analyze(ticker)
        msg = f"{ticker}\nFiyat: {close}\nRSI: {rsi}\nSkor: {score}\n"
        if score >= 40:
            msg += "🚀 STRONG BUY"
        elif score >= 20:
            msg += "⚡ BUY"
        else:
            msg += "⏸️ Hold"
        await update.message.reply_text(msg)

# Otomatik analiz (cron gibi)
def run_analysis():
    if not portfolio:
        bot.send_message(chat_id=CHAT_ID, text="Portföy boş 😅")
        return
    for ticker in portfolio.keys():
        score, close, rsi = analyze(ticker)
        msg = f"{ticker}\nFiyat: {close}\nRSI: {rsi}\nSkor: {score}\n"
        if score >= 40:
            msg += "🚀 STRONG BUY"
        elif score >= 20:
            msg += "⚡ BUY"
        else:
            msg += "⏸️ Hold"
        bot.send_message(chat_id=CHAT_ID, text=msg)

# Bot uygulaması
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("ekle", ekle))
app.add_handler(CommandHandler("sil", sil))
app.add_handler(CommandHandler("portfoy", portfoy))
app.add_handler(CommandHandler("analiz", analiz))

# Bot ve cron
bot = Bot(TOKEN)
schedule.every(15).minutes.do(run_analysis)

async def run_schedule():
    while True:
        schedule.run_pending()
        await asyncio.sleep(10)

import asyncio
async def main():
    asyncio.create_task(run_schedule())
    await app.run_polling()

asyncio.run(main())
