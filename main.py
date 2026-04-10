async def top5(update, context):
    await update.message.reply_text("🔍 Tüm piyasalar taranıyor, hedge fund scoring çalışıyor...")

    tickers = get_tickers()

    results = []

    for t in tickers[:100]:  # güvenli limit
        r = analyze_stock(t)
        if r:
            results.append(r)

    top = sorted(results, key=lambda x: x["confidence"], reverse=True)[:5]

    if not top:
        await update.message.reply_text("❌ Analiz sonucu bulunamadı")
        return

    msg = "🏆 HEDGE FUND TOP 5 PICKS\n\n"

    for i, s in enumerate(top, 1):
        msg += f"{i}. {s['ticker']}\n"
        msg += f"💰 Price: {s['price']:.2f}\n"
        msg += f"🧠 Confidence: %{s['confidence']:.1f}\n"
        msg += "📌 Reasons:\n"

        for r in s["reasons"]:
            msg += f"   - {r}\n"

        msg += "\n"

    await update.message.reply_text(msg)
