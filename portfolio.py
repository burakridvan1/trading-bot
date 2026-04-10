import json
import os

FILE = "portfolio.json"


def load_portfolio():
    if not os.path.exists(FILE):
        return {}

    with open(FILE, "r") as f:
        return json.load(f)


def save_portfolio(data):
    with open(FILE, "w") as f:
        json.dump(data, f)


def add_stock(ticker, price):
    data = load_portfolio()
    data[ticker] = price
    save_portfolio(data)
    return f"✅ {ticker} eklendi"


def remove_stock(ticker):
    data = load_portfolio()

    if ticker in data:
        del data[ticker]
        save_portfolio(data)
        return f"🗑 {ticker} silindi"

    return "❌ Bulunamadı"


def list_portfolio():
    data = load_portfolio()

    if not data:
        return "Boş portfolio"

    msg = "📊 PORTFOLIO\n\n"

    for k, v in data.items():
        msg += f"{k} → {v}\n"

    return msg
