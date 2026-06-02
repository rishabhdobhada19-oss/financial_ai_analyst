from __future__ import annotations

import os
from pathlib import Path

_MPLCONFIGDIR = Path(__file__).resolve().parent / "data" / ".matplotlib"
_MPLCONFIGDIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(_MPLCONFIGDIR))

import streamlit as st

from config import APP_TITLE, DEFAULT_PERIOD, DEFAULT_SEARCH_QUERY, PRICE_PERIODS
from pages import (
    company_overview,
    financial_statements,
    forecasting_dashboard,
    investor_insights,
    investment_summary,
    investor_dashboard,
    ratio_analysis,
    valuation_dashboard,
)
from utils.charts import macd_chart, price_volume_chart
from utils.fetch_data import get_financial_statements, get_price_history, get_ticker_info, search_companies
from utils.forecasting import add_technical_indicators
from utils.helpers import clean_ticker, inject_css, show_data_warning


def _company_option_label(company: dict) -> str:
    details = " / ".join(part for part in [company.get("exchange"), company.get("quote_type")] if part)
    return f"{company['symbol']} - {company['name']}" + (f" ({details})" if details else "")


def _manual_ticker_option(query: str) -> dict | None:
    ticker = clean_ticker(query)
    if not ticker or " " in ticker:
        return None
    return {"symbol": ticker, "name": "Use this ticker directly", "exchange": "", "quote_type": "Manual"}


def render_stock_performance(hist) -> None:
    st.subheader("Stock Performance Dashboard")
    if hist is None or hist.empty:
        show_data_warning("Price history is unavailable for this ticker.")
        return
    enriched = add_technical_indicators(hist)
    st.plotly_chart(price_volume_chart(enriched), width="stretch")
    cols = st.columns(2)
    with cols[0]:
        st.plotly_chart(macd_chart(enriched), width="stretch")
    with cols[1]:
        st.markdown("#### Returns and RSI")
        st.line_chart(enriched[["Daily Return", "RSI"]].dropna(), width="stretch")


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon="FA", layout="wide")
    inject_css()

    st.title(APP_TITLE)
    st.caption("Equity research, valuation, forecasting, and financial statement analysis from public market data.")

    with st.sidebar:
        st.header("Analysis Controls")
        query = st.text_input(
            "Search Company or Ticker",
            DEFAULT_SEARCH_QUERY,
            placeholder="Tesla, Microsoft, RELIANCE.NS, TCS.NS",
        )
        search_results = search_companies(query) if len(query.strip()) >= 2 else []
        manual_option = _manual_ticker_option(query)
        options = search_results.copy()
        if manual_option and all(item["symbol"] != manual_option["symbol"] for item in options):
            options.append(manual_option)

        selected_company = None
        if options:
            selected_company = st.selectbox(
                "Select Company",
                options,
                format_func=_company_option_label,
                index=0,
            )
            ticker = selected_company["symbol"]
            st.caption(f"Analyzing: {ticker}")
        else:
            ticker = ""
            if query.strip():
                st.info("No company match found. Try the exact Yahoo Finance ticker, such as `MSFT` or `RELIANCE.NS`.")

        period = st.selectbox("Price History", PRICE_PERIODS, index=PRICE_PERIODS.index(DEFAULT_PERIOD))
        statement_view = st.radio("Financial Statements", ["Annual", "Quarterly"], horizontal=True)
        page = st.radio(
            "Dashboard",
            [
                "Company Overview",
                "Financial Statements",
                "Ratio Analysis",
                "Stock Performance",
                "Forecasting",
                "DCF Valuation",
                "Investment Summary",
                "Investor Insights",
                "Investor Dashboard",
            ],
        )

    if not ticker:
        st.info("Search for a public company or enter a Yahoo Finance ticker to begin.")
        return

    with st.spinner(f"Loading {ticker} market and financial data..."):
        info = get_ticker_info(ticker)
        statements = get_financial_statements(ticker, quarterly=statement_view == "Quarterly")
        hist = get_price_history(ticker, period=period)

    if page == "Company Overview":
        company_overview.render(ticker, info)
    elif page == "Financial Statements":
        financial_statements.render(statements)
    elif page == "Ratio Analysis":
        ratio_analysis.render(statements, info)
    elif page == "Stock Performance":
        render_stock_performance(hist)
    elif page == "Forecasting":
        forecasting_dashboard.render(add_technical_indicators(hist))
    elif page == "DCF Valuation":
        valuation_dashboard.render(statements, info)
    elif page == "Investment Summary":
        investment_summary.render(statements, info)
    elif page == "Investor Insights":
        investor_insights.render(ticker, statements, info)
    elif page == "Investor Dashboard":
        investor_dashboard.render(ticker, statements, info)


if __name__ == "__main__":
    main()
