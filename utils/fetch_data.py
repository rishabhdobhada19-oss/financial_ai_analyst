from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st
import yfinance as yf


_YFINANCE_CACHE_DIR = Path(__file__).resolve().parents[1] / "data" / ".yfinance"
_YFINANCE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
try:
    yf.cache.set_cache_location(str(_YFINANCE_CACHE_DIR))
except Exception:
    pass


YAHOO_INFO_FIELDS = [
    "longName",
    "shortName",
    "longBusinessSummary",
    "sector",
    "industry",
    "country",
    "currency",
    "financialCurrency",
    "exchange",
    "currentPrice",
    "regularMarketPrice",
    "previousClose",
    "open",
    "dayHigh",
    "dayLow",
    "fiftyTwoWeekHigh",
    "fiftyTwoWeekLow",
    "marketCap",
    "enterpriseValue",
    "sharesOutstanding",
    "trailingPE",
    "forwardPE",
    "pegRatio",
    "priceToBook",
    "beta",
    "dividendYield",
    "targetMeanPrice",
    "enterpriseToEbitda",
    "totalCash",
    "totalDebt",
    "totalRevenue",
    "grossProfits",
    "freeCashflow",
    "operatingCashflow",
]

INDIA_SYMBOL_ALIASES = {
    "TATAMOTORS": "TMPV.NS",
    "TATAMOTORS.NS": "TMPV.NS",
    "TATAMOTORS:BSE": "TMPV.BO",
    "TATAMOTORS.BO": "TMPV.BO",
    "TMPV": "TMPV.NS",
    "RELIANCE": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "INFY": "INFY.NS",
    "HDFCBANK": "HDFCBANK.NS",
    "ICICIBANK": "ICICIBANK.NS",
    "SBIN": "SBIN.NS",
}


def normalize_yahoo_symbol(ticker: str) -> str:
    symbol = ticker.strip().upper()
    if symbol in INDIA_SYMBOL_ALIASES:
        return INDIA_SYMBOL_ALIASES[symbol]
    if ":" in symbol:
        base, exchange = symbol.split(":", 1)
        if exchange in {"NSE", "NSI"}:
            return f"{base}.NS"
        if exchange in {"BSE", "BOM"}:
            return f"{base}.BO"
    return symbol


def _ticker(ticker: str) -> yf.Ticker:
    return yf.Ticker(normalize_yahoo_symbol(ticker))


def _statement_frame(statement: pd.DataFrame) -> pd.DataFrame:
    if statement is None or statement.empty:
        return pd.DataFrame()
    frame = statement.copy()
    frame.columns = pd.to_datetime(frame.columns, errors="coerce")
    frame = frame.loc[:, frame.columns.notna()]
    return frame.apply(pd.to_numeric, errors="coerce")


def _manual_option(query: str) -> dict:
    symbol = normalize_yahoo_symbol(query)
    return {"symbol": symbol, "name": "Use this Yahoo Finance ticker directly", "exchange": "", "quote_type": "Manual"}


@st.cache_data(ttl=1800, show_spinner=False)
def search_companies(query: str, max_results: int = 8) -> list[dict]:
    query = query.strip()
    if len(query) < 2:
        return []

    results: list[dict] = []
    seen: set[str] = set()
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
        for quote in getattr(search, "quotes", []) or []:
            symbol = str(quote.get("symbol") or "").upper().strip()
            if not symbol or symbol in seen:
                continue
            seen.add(symbol)
            results.append(
                {
                    "symbol": normalize_yahoo_symbol(symbol),
                    "name": quote.get("longname") or quote.get("shortname") or symbol,
                    "exchange": quote.get("exchange") or quote.get("exchDisp") or "",
                    "quote_type": quote.get("quoteType") or quote.get("typeDisp") or "Security",
                }
            )
    except Exception:
        results = []

    manual = _manual_option(query)
    if manual["symbol"] and manual["symbol"] not in seen:
        results.append(manual)
    return results[:max_results]


@st.cache_data(ttl=1800, show_spinner=False)
def get_ticker_info(ticker: str) -> dict:
    symbol = normalize_yahoo_symbol(ticker)
    try:
        raw_info = _ticker(symbol).get_info()
    except Exception as exc:
        return {"_error": str(exc)}
    if not raw_info:
        return {"_error": f"No company profile found for {symbol}. Check the Yahoo Finance ticker."}

    info = {field: raw_info.get(field) for field in YAHOO_INFO_FIELDS}
    info["symbol"] = raw_info.get("symbol") or symbol
    info["longName"] = info.get("longName") or info.get("shortName") or symbol
    info["shortName"] = info.get("shortName") or info.get("longName") or symbol
    info["financialCurrency"] = info.get("financialCurrency") or info.get("currency")
    info["_data_source"] = "Yahoo Finance"
    return info


@st.cache_data(ttl=1800, show_spinner=False)
def get_price_history(ticker: str, period: str = "2y") -> pd.DataFrame:
    try:
        hist = _ticker(ticker).history(period=period, auto_adjust=False)
    except Exception:
        return pd.DataFrame()
    if hist is None or hist.empty:
        return pd.DataFrame()
    if isinstance(hist.columns, pd.MultiIndex):
        hist.columns = hist.columns.get_level_values(0)
    hist.index = pd.to_datetime(hist.index).tz_localize(None)
    return hist.dropna(subset=["Close"]).sort_index()


@st.cache_data(ttl=1800, show_spinner=False)
def get_financial_statements(ticker: str, quarterly: bool = False) -> dict[str, pd.DataFrame]:
    try:
        stock = _ticker(ticker)
        if quarterly:
            income = stock.quarterly_financials
            balance = stock.quarterly_balance_sheet
            cashflow = stock.quarterly_cashflow
        else:
            income = stock.financials
            balance = stock.balance_sheet
            cashflow = stock.cashflow
    except Exception:
        return {"income": pd.DataFrame(), "balance": pd.DataFrame(), "cashflow": pd.DataFrame()}

    return {
        "income": _statement_frame(income),
        "balance": _statement_frame(balance),
        "cashflow": _statement_frame(cashflow),
    }
