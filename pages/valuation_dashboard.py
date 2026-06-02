from __future__ import annotations

import streamlit as st

from utils.helpers import format_currency, format_percent, kpi_grid
from utils.valuation import dcf_valuation


def render(statements: dict, info: dict) -> None:
    st.subheader("DCF Valuation Model")
    cols = st.columns(4)
    with cols[0]:
        revenue_growth = st.slider("Revenue Growth", -0.10, 0.30, 0.06, 0.01)
    with cols[1]:
        discount_rate = st.slider("Discount Rate", 0.05, 0.20, 0.10, 0.01)
    with cols[2]:
        terminal_growth = st.slider("Terminal Growth", 0.00, 0.06, 0.025, 0.005)
    with cols[3]:
        forecast_period = st.number_input("Forecast Years", min_value=3, max_value=10, value=5, step=1)

    valuation = dcf_valuation(statements, info, revenue_growth, discount_rate, terminal_growth, int(forecast_period))
    kpi_grid(
        [
            ("Fair Value", format_currency(valuation["intrinsic_value"])),
            ("Current Price", format_currency(valuation["current_price"])),
            ("Upside / Downside", format_percent(valuation["upside"])),
            ("Conclusion", valuation["conclusion"]),
            ("Enterprise Value", format_currency(valuation["enterprise_value"])),
            ("Equity Value", format_currency(valuation["equity_value"])),
        ]
    )

    if valuation["latest_fcf"] == 0:
        st.warning("DCF inputs are limited because free cash flow data is unavailable. Try another ticker or reporting period.")
    forecast = valuation["forecast"].copy()
    for column in ["Free Cash Flow", "Discounted FCF"]:
        if column in forecast:
            forecast[column] = forecast[column].map(format_currency)
    st.dataframe(forecast, width="stretch", hide_index=True)
