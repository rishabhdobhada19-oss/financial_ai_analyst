from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st
import yfinance as yf

from utils.helpers import safe_float


INR_CURRENCY = "INR"

FALLBACK_INR_RATES = {
    "USD": 83.50,
    "EUR": 90.00,
    "GBP": 105.00,
    "GBp": 1.05,
    "JPY": 0.55,
    "CAD": 61.00,
    "AUD": 55.00,
    "CHF": 92.00,
    "CNY": 11.50,
    "HKD": 10.70,
    "SGD": 62.00,
}

PRICE_COLUMNS = ["Open", "High", "Low", "Close", "Adj Close"]

INFO_MONEY_FIELDS = [
    "currentPrice",
    "regularMarketPrice",
    "previousClose",
    "open",
    "dayLow",
    "dayHigh",
    "fiftyTwoWeekLow",
    "fiftyTwoWeekHigh",
    "targetMeanPrice",
    "marketCap",
    "enterpriseValue",
    "totalCash",
    "totalDebt",
    "totalRevenue",
    "grossProfits",
    "freeCashflow",
    "operatingCashflow",
]


def _source_currency(info: dict[str, Any]) -> str:
    return str(info.get("financialCurrency") or info.get("currency") or INR_CURRENCY)


def _api_key() -> str:
    return ""


@st.cache_data(ttl=6 * 60 * 60, show_spinner=False)
def get_inr_rate(currency: str) -> float:
    currency = (currency or INR_CURRENCY).strip()
    if currency.upper() == INR_CURRENCY:
        return 1.0

    try:
        yahoo_currency = "GBP" if currency == "GBp" else currency.upper()
        fx = yf.Ticker(f"{yahoo_currency}INR=X").history(period="5d")
        rate = safe_float(fx["Close"].dropna().iloc[-1]) if fx is not None and not fx.empty else None
        if rate:
            return rate / 100 if currency == "GBp" else rate
    except Exception:
        pass
    return FALLBACK_INR_RATES.get(currency, FALLBACK_INR_RATES.get(currency.upper(), 1.0))


def convert_value_to_inr(value: Any, rate: float) -> float | None:
    number = safe_float(value)
    return number * rate if number is not None else None


def convert_info_to_inr(info: dict[str, Any]) -> dict[str, Any]:
    if not info or info.get("_error"):
        return info

    source_currency = _source_currency(info)
    rate = get_inr_rate(source_currency)
    converted = info.copy()
    converted["_source_currency"] = source_currency
    converted["_inr_rate"] = rate
    converted["currency"] = INR_CURRENCY
    converted["financialCurrency"] = INR_CURRENCY

    for field in INFO_MONEY_FIELDS:
        if field in converted:
            converted[field] = convert_value_to_inr(converted[field], rate)
    return converted


def convert_statements_to_inr(statements: dict[str, pd.DataFrame], info: dict[str, Any]) -> dict[str, pd.DataFrame]:
    rate = safe_float(info.get("_inr_rate"), 1.0) or 1.0
    converted: dict[str, pd.DataFrame] = {}
    for name, statement in statements.items():
        if statement is None or statement.empty:
            converted[name] = pd.DataFrame()
            continue
        converted[name] = statement.apply(pd.to_numeric, errors="coerce") * rate
    return converted


def convert_price_history_to_inr(hist: pd.DataFrame, info: dict[str, Any]) -> pd.DataFrame:
    if hist is None or hist.empty:
        return pd.DataFrame()

    rate = safe_float(info.get("_inr_rate"), 1.0) or 1.0
    converted = hist.copy()
    for column in PRICE_COLUMNS:
        if column in converted:
            converted[column] = pd.to_numeric(converted[column], errors="coerce") * rate
    return converted
