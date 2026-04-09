# async def main() ve asyncio.run() artık kullanılmıyor
if __name__ == "__main__":
    # Bot uygulaması
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("ekle", ekle))
    app.add_handler(CommandHandler("sil", sil))
    app.add_handler(CommandHandler("portfoy", portfoy))
    app.add_handler(CommandHandler("analiz", analiz))

    # Otomatik analiz schedule için ayrı thread
    import threading
    import schedule
    import time

    def run_schedule():
        while True:
            schedule.run_pending()
            time.sleep(10)

    schedule.every(15).minutes.do(run_analysis)
    threading.Thread(target=run_schedule, daemon=True).start()

    # Botu başlat
    app.run_polling()
