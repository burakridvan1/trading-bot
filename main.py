from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "BURAYA_TOKEN"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("START KOMUTU GELDİ")
    await update.message.reply_text("Bot çalışıyor ✅")


def main():
    print("BOT BAŞLIYOR...")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    print("Polling başlatılıyor...")
    app.run_polling()


if __name__ == "__main__":
    main()
