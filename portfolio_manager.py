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
        json.dump(data, f, indent=4)


def add_stock(ticker, price):
    data = load_portfolio()
    data[ticker.upper()] = float(price)
    save_portfolio(data)
    return f"{ticker} eklendi @ {price}"


def remove_stock(ticker):
    data = load_portfolio()
    ticker = ticker.upper()
    if ticker in data:
        del data[ticker]
        save_portfolio(data)
        return f"{ticker} silindi"
    return f"{ticker} bulunamadı"


def list_portfolio():
    data = load_portfolio()
    if not data:
        return "Portföy boş"

    msg = "📊 Portföy:\n"
    for t, p in data.items():
        msg += f"{t} → {p}\n"
    return msg
