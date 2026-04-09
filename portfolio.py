from typing import List, Tuple
from analyzer import get_signal

# Portföy listesi: (ticker, adet)
portfolio: List[Tuple[str, int]] = []

def add_stock(ticker: str, qty: int):
    for i, (t, q) in enumerate(portfolio):
        if t == ticker:
            portfolio[i] = (t, q + qty)
            return
    portfolio.append((ticker, qty))

def remove_stock(ticker: str, qty: int):
    for i, (t, q) in enumerate(portfolio):
        if t == ticker:
            if q <= qty:
                portfolio.pop(i)
            else:
                portfolio[i] = (t, q - qty)
            return

def get_portfolio_status():
    status = []
    for ticker, qty in portfolio:
        signal = get_signal(ticker)
        status.append(f"{ticker}: {signal} (adet: {qty})")
    return "\n".join(status) if status else "Portföy boş."
