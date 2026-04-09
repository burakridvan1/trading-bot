# portfolio.py
from typing import Dict

PORTFOLIOS: Dict[int, list] = {}  # user_id -> list of tickers

def add_to_portfolio(user_id: int, ticker: str):
    if user_id not in PORTFOLIOS:
        PORTFOLIOS[user_id] = []
    if ticker not in PORTFOLIOS[user_id]:
        PORTFOLIOS[user_id].append(ticker)
        return True
    return False

def remove_from_portfolio(user_id: int, ticker: str):
    if user_id in PORTFOLIOS and ticker in PORTFOLIOS[user_id]:
        PORTFOLIOS[user_id].remove(ticker)
        return True
    return False

def get_portfolio(user_id: int):
    return PORTFOLIOS.get(user_id, [])
