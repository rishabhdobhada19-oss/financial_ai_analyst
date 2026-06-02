from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.financial_ratios import calculate_ratios
from utils.helpers import format_percent, kpi_grid
from utils.valuation import dcf_valuation


def _latest(ratios: pd.DataFrame, column: str) -> float | None:
    if ratios.empty or column not in ratios:
        return None
    values = ratios[column].dropna()
    return float(values.iloc[-1]) if not values.empty else None


def render(statements: dict, info: dict) -> None:
    st.subheader("Investment Summary")
    ratios = calculate_ratios(statements, info)
    valuation = dcf_valuation(statements, info, 0.06, 0.10, 0.025, 5)

    score = 0
    insights = []

    revenue_growth = _latest(ratios, "Revenue Growth")
    net_margin = _latest(ratios, "Net Margin")
    debt_to_equity = _latest(ratios, "Debt to Equity")
    upside = valuation["upside"]

    if revenue_growth is not None and revenue_growth > 0.05:
        score += 1
        insights.append("Revenue is growing at a healthy pace.")
    elif revenue_growth is not None and revenue_growth < 0:
        score -= 1
        insights.append("Revenue has contracted in the latest comparable period.")

    if net_margin is not None and net_margin > 0.15:
        score += 1
        insights.append("Profit margins are strong versus broad-market expectations.")
    elif net_margin is not None and net_margin < 0.03:
        score -= 1
        insights.append("Profitability is thin or under pressure.")

    if debt_to_equity is not None and debt_to_equity < 1:
        score += 1
        insights.append("Leverage appears manageable based on debt to equity.")
    elif debt_to_equity is not None and debt_to_equity > 2:
        score -= 1
        insights.append("Leverage is elevated and deserves closer review.")

    if upside > 0.15:
        score += 1
        insights.append("DCF fair value suggests meaningful upside.")
    elif upside < -0.15:
        score -= 1
        insights.append("DCF fair value suggests potential overvaluation.")

    rating = "Buy" if score >= 2 else "Sell" if score <= -2 else "Hold"
    kpi_grid(
        [
            ("Automated Rating", rating),
            ("DCF Upside", format_percent(upside)),
            ("Revenue Growth", format_percent(revenue_growth)),
            ("Net Margin", format_percent(net_margin)),
        ]
    )

    st.markdown("#### Supporting Explanation")
    if insights:
        for insight in insights:
            st.write(f"- {insight}")
    else:
        st.write("- Available data is mixed or incomplete, supporting a neutral stance.")
    st.info("This summary is generated from public data and simple models. Use it as a research starting point, not as financial advice.")
