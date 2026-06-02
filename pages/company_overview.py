from __future__ import annotations

import streamlit as st
import pandas as pd

from utils.helpers import format_currency, format_number, format_percent, kpi_grid


def render(ticker: str, info: dict) -> None:
    st.subheader("Company Overview")
    if info.get("_error"):
        st.error(info["_error"])
        return

    name = info.get("longName") or info.get("shortName") or ticker
    st.markdown(f"### {name}")
    st.caption(f"{info.get('sector', 'N/A')} / {info.get('industry', 'N/A')}")

    kpi_grid(
        [
            ("Current Price", format_currency(info.get("currentPrice") or info.get("regularMarketPrice"))),
            ("Market Cap", format_currency(info.get("marketCap"))),
            ("Enterprise Value", format_currency(info.get("enterpriseValue"))),
            ("Shares Outstanding", format_number(info.get("sharesOutstanding"))),
            ("Beta", f"{info.get('beta', 'N/A')}" if info.get("beta") else "N/A"),
            ("Dividend Yield", format_percent(info.get("dividendYield"))),
            ("52 Week High", format_currency(info.get("fiftyTwoWeekHigh"))),
            ("52 Week Low", format_currency(info.get("fiftyTwoWeekLow"))),
        ]
    )

    cols = st.columns([1.2, 0.8])
    with cols[0]:
        st.markdown("#### Business Summary")
        st.write(info.get("longBusinessSummary") or "No business summary available from Twelve Data.")
    with cols[1]:
        st.markdown("#### Trading Snapshot")
        rows = {
            "Exchange": info.get("exchange") or "N/A",
            "Display Currency": "₹",
            "Source Currency": info.get("_source_currency") or info.get("currency") or "N/A",
            "₹ Conversion Rate": format_currency(info.get("_inr_rate")),
            "Forward P/E": str(info.get("forwardPE") or "N/A"),
            "Trailing P/E": str(info.get("trailingPE") or "N/A"),
            "Price to Book": str(info.get("priceToBook") or "N/A"),
            "Analyst Target": format_currency(info.get("targetMeanPrice")),
        }
        st.dataframe(pd.DataFrame(rows.items(), columns=["Metric", "Value"]), width="stretch", hide_index=True)
