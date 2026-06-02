from __future__ import annotations

import streamlit as st

from utils.charts import forecast_chart
from utils.forecasting import forecast_prices
from utils.helpers import format_currency, kpi_grid, show_data_warning


def render(hist) -> None:
    st.subheader("Forecasting Model")
    if hist is None or hist.empty:
        show_data_warning("Historical prices are not available for forecasting.")
        return

    cols = st.columns(2)
    forecast_30 = forecast_prices(hist, 30)
    forecast_90 = forecast_prices(hist, 90)
    latest = hist["Close"].dropna().iloc[-1]
    kpi_grid(
        [
            ("Latest Close", format_currency(latest)),
            ("30 Day Forecast", format_currency(forecast_30["Forecast"].iloc[-1] if not forecast_30.empty else None)),
            ("90 Day Forecast", format_currency(forecast_90["Forecast"].iloc[-1] if not forecast_90.empty else None)),
        ]
    )

    with cols[0]:
        st.plotly_chart(forecast_chart(hist.tail(252), forecast_30, "Next 30 Trading Days"), width="stretch")
    with cols[1]:
        st.plotly_chart(forecast_chart(hist.tail(252), forecast_90, "Next 90 Trading Days"), width="stretch")
    st.caption("Forecasts use linear regression on historical closing prices and are educational estimates, not investment advice.")
