from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st
import yfinance as yf

_YFINANCE_CACHE = Path.cwd() / "data" / ".yfinance"
_YFINANCE_CACHE.mkdir(parents=True, exist_ok=True)
yf.set_tz_cache_location(str(_YFINANCE_CACHE))


@st.cache_data(ttl=1800, show_spinner=False)
def search_companies(query: str, max_results: int = 8) -> list[dict]:
    query = query.strip()
    if len(query) < 2:
        return []
    try:
        search = yf.Search(
            query,
            max_results=max_results,
            news_count=0,
            lists_count=0,
            include_research=False,
            include_cultural_assets=False,
            enable_fuzzy_query=True,
            raise_errors=False,
        )
    except Exception:
        return []

    results = []
    seen = set()
    for quote in getattr(search, "quotes", []) or []:
        symbol = str(quote.get("symbol") or "").upper().strip()
        if not symbol or symbol in seen:
            continue
        seen.add(symbol)
        quote_type = quote.get("quoteType") or quote.get("typeDisp") or "Security"
        results.append(
            {
                "symbol": symbol,
                "name": quote.get("longname") or quote.get("shortname") or symbol,
                "exchange": quote.get("exchange") or quote.get("exchDisp") or "",
                "quote_type": quote_type,
            }
        )
    return results


@st.cache_data(ttl=1800, show_spinner=False)
def get_ticker_info(ticker: str) -> dict:
    try:
        info = yf.Ticker(ticker).info
    except Exception as exc:
        return {"_error": str(exc)}
    if not info or info.get("regularMarketPrice") is None and info.get("currentPrice") is None:
        return {"_error": "No company profile found. Check the ticker symbol."}
    return info


@st.cache_data(ttl=1800, show_spinner=False)
def get_price_history(ticker: str, period: str = "2y") -> pd.DataFrame:
    try:
        hist = yf.download(ticker, period=period, auto_adjust=True, progress=False, threads=False)
    except Exception:
        return pd.DataFrame()
    if hist is None or hist.empty:
        return pd.DataFrame()
    if isinstance(hist.columns, pd.MultiIndex):
        hist.columns = hist.columns.get_level_values(0)
    return hist.dropna(how="all")


@st.cache_data(ttl=1800, show_spinner=False)
def get_financial_statements(ticker: str, quarterly: bool = False) -> dict[str, pd.DataFrame]:
    stock = yf.Ticker(ticker)
    try:
        if quarterly:
            income = stock.quarterly_income_stmt
            balance = stock.quarterly_balance_sheet
            cashflow = stock.quarterly_cashflow
        else:
            income = stock.income_stmt
            balance = stock.balance_sheet
            cashflow = stock.cashflow
    except Exception:
        return {"income": pd.DataFrame(), "balance": pd.DataFrame(), "cashflow": pd.DataFrame()}
    return {
        "income": income if income is not None else pd.DataFrame(),
        "balance": balance if balance is not None else pd.DataFrame(),
        "cashflow": cashflow if cashflow is not None else pd.DataFrame(),
    }
