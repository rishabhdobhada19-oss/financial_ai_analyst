from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config import CHART_TEMPLATE
from utils.financial_ratios import calculate_ratios
from utils.helpers import format_currency, format_percent, format_ratio, safe_float, show_data_warning
from utils.valuation import dcf_valuation


def _latest(ratios: pd.DataFrame, column: str) -> float | None:
    if ratios.empty or column not in ratios:
        return None
    values = ratios[column].dropna()
    return safe_float(values.iloc[-1]) if not values.empty else None


def _score_item(value: float | None, good: float, weak: float, higher_is_better: bool = True) -> int:
    if value is None:
        return 0
    if higher_is_better:
        return 1 if value >= good else -1 if value <= weak else 0
    return 1 if value <= good else -1 if value >= weak else 0


def _condition(score: int) -> str:
    if score >= 3:
        return "Strong"
    if score >= 1:
        return "Stable"
    if score <= -3:
        return "Weak"
    if score <= -1:
        return "Watchlist"
    return "Mixed"


def _rating(score: int) -> str:
    return "Buy" if score >= 3 else "Sell" if score <= -3 else "Hold"


def _status(value: float | None, good: float, weak: float, higher_is_better: bool = True) -> str:
    score = _score_item(value, good, weak, higher_is_better)
    if score > 0:
        return "Healthy"
    if score < 0:
        return "Risk"
    return "Neutral"


def _metric_card(label: str, value: str, note: str, tone: str = "neutral") -> str:
    return (
        f'<div class="bi-card bi-{tone}">'
        f'<div class="bi-label">{label}</div>'
        f'<div class="bi-value">{value}</div>'
        f'<div class="bi-note">{note}</div>'
        "</div>"
    )


def _health_gauge(score_percent: int, condition: str) -> go.Figure:
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score_percent,
            number={"suffix": "%", "font": {"size": 34}},
            title={"text": f"Financial Health: {condition}", "font": {"size": 15}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 0},
                "bar": {"color": "#38bdf8"},
                "bgcolor": "rgba(15, 23, 42, 0.72)",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 35], "color": "rgba(239, 68, 68, 0.25)"},
                    {"range": [35, 65], "color": "rgba(245, 158, 11, 0.25)"},
                    {"range": [65, 100], "color": "rgba(34, 197, 94, 0.25)"},
                ],
            },
        )
    )
    fig.update_layout(template=CHART_TEMPLATE, height=285, margin=dict(l=20, r=20, t=46, b=18))
    return fig


def _valuation_bar(current_price: float, fair_value: float) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Bar(x=["Current Price"], y=[current_price], marker_color="#94a3b8", name="Current Price"))
    fig.add_trace(go.Bar(x=["DCF Fair Value"], y=[fair_value], marker_color="#22c55e", name="DCF Fair Value"))
    fig.update_layout(
        template=CHART_TEMPLATE,
        title="Market Price vs Estimated Fair Value",
        height=285,
        margin=dict(l=20, r=20, t=50, b=24),
        showlegend=False,
    )
    fig.update_yaxes(title="Price")
    return fig


def _driver_chart(rows: list[dict]) -> go.Figure:
    chart_df = pd.DataFrame(rows)
    colors = {"Healthy": "#22c55e", "Neutral": "#f59e0b", "Risk": "#ef4444"}
    fig = go.Figure(
        go.Bar(
            x=chart_df["Score"],
            y=chart_df["Area"],
            orientation="h",
            marker_color=[colors.get(status, "#94a3b8") for status in chart_df["Status"]],
            text=chart_df["Status"],
            textposition="inside",
            hovertemplate="%{y}<br>Score: %{x}<br>Status: %{text}<extra></extra>",
        )
    )
    fig.update_layout(
        template=CHART_TEMPLATE,
        title="Investor Driver Scorecard",
        height=360,
        margin=dict(l=20, r=20, t=50, b=24),
        xaxis=dict(range=[-1.15, 1.15], tickvals=[-1, 0, 1], ticktext=["Risk", "Neutral", "Healthy"]),
    )
    return fig


def _mix_chart(rows: list[dict]) -> go.Figure:
    counts = pd.Series([row["Status"] for row in rows]).value_counts()
    fig = go.Figure(
        go.Pie(
            labels=counts.index,
            values=counts.values,
            hole=0.58,
            marker=dict(colors=["#22c55e" if label == "Healthy" else "#f59e0b" if label == "Neutral" else "#ef4444" for label in counts.index]),
            textinfo="label+value",
        )
    )
    fig.update_layout(template=CHART_TEMPLATE, title="Risk / Health Mix", height=360, margin=dict(l=20, r=20, t=50, b=24))
    return fig


def _takeaway(rating: str, condition: str, rows: list[dict]) -> str:
    healthy = [row["Area"] for row in rows if row["Status"] == "Healthy"]
    risks = [row["Area"] for row in rows if row["Status"] == "Risk"]
    positives = ", ".join(healthy[:3]) if healthy else "limited confirmed strengths"
    concerns = ", ".join(risks[:3]) if risks else "no major red flags from available data"
    return (
        f"The dashboard classifies the company as {condition} with a {rating} investor view. "
        f"Main positives: {positives}. Main concerns: {concerns}. "
        "Use this as a boardroom-style snapshot before reviewing detailed statements and peer comparisons."
    )


def render(ticker: str, statements: dict, info: dict) -> None:
    st.subheader("Investor Dashboard")
    if info.get("_error"):
        st.error(info["_error"])
        return

    ratios = calculate_ratios(statements, info)
    if ratios.empty:
        show_data_warning("Investor dashboard could not be generated because financial statements are missing.")
        return

    valuation = dcf_valuation(statements, info, 0.06, 0.10, 0.025, 5)
    company_name = info.get("longName") or info.get("shortName") or ticker

    revenue_growth = _latest(ratios, "Revenue Growth")
    net_margin = _latest(ratios, "Net Margin")
    roe = _latest(ratios, "ROE")
    current_ratio = _latest(ratios, "Current Ratio")
    debt_to_equity = _latest(ratios, "Debt to Equity")
    pe_ratio = safe_float(info.get("trailingPE"))
    upside = valuation["upside"]
    current_price = safe_float(valuation["current_price"], 0.0) or 0.0
    fair_value = safe_float(valuation["intrinsic_value"], 0.0) or 0.0

    drivers = [
        {
            "Area": "Growth",
            "Metric": "Revenue Growth",
            "Reading": format_percent(revenue_growth),
            "Status": _status(revenue_growth, 0.05, 0.0),
            "Score": _score_item(revenue_growth, 0.05, 0.0),
            "Investor Meaning": "Demand and scale are improving when revenue grows consistently.",
        },
        {
            "Area": "Profitability",
            "Metric": "Net Margin",
            "Reading": format_percent(net_margin),
            "Status": _status(net_margin, 0.12, 0.03),
            "Score": _score_item(net_margin, 0.12, 0.03),
            "Investor Meaning": "Higher margin means more revenue converts into profit.",
        },
        {
            "Area": "Capital Returns",
            "Metric": "ROE",
            "Reading": format_percent(roe),
            "Status": _status(roe, 0.15, 0.05),
            "Score": _score_item(roe, 0.15, 0.05),
            "Investor Meaning": "ROE shows efficiency in using shareholder capital.",
        },
        {
            "Area": "Liquidity",
            "Metric": "Current Ratio",
            "Reading": format_ratio(current_ratio),
            "Status": _status(current_ratio, 1.2, 0.8),
            "Score": _score_item(current_ratio, 1.2, 0.8),
            "Investor Meaning": "Liquidity measures near-term ability to pay obligations.",
        },
        {
            "Area": "Leverage",
            "Metric": "Debt / Equity",
            "Reading": format_ratio(debt_to_equity),
            "Status": _status(debt_to_equity, 1.0, 2.0, higher_is_better=False),
            "Score": _score_item(debt_to_equity, 1.0, 2.0, higher_is_better=False),
            "Investor Meaning": "Lower leverage usually means less balance-sheet risk.",
        },
        {
            "Area": "Valuation",
            "Metric": "DCF Upside",
            "Reading": format_percent(upside),
            "Status": _status(upside, 0.10, -0.10),
            "Score": _score_item(upside, 0.10, -0.10),
            "Investor Meaning": "Upside compares estimated fair value with market price.",
        },
    ]

    score = sum(row["Score"] for row in drivers)
    score_percent = max(0, min(100, int(((score + 6) / 12) * 100)))
    condition = _condition(score)
    rating = _rating(score)
    tone = "good" if rating == "Buy" else "bad" if rating == "Sell" else "neutral"

    st.markdown(f"### {company_name}")
    st.caption("Executive-style investor view of financial condition, valuation, strengths, and risks.")

    st.markdown(
        '<div class="bi-grid">'
        + _metric_card("Investor View", rating, "Overall recommendation from six drivers", tone)
        + _metric_card("Financial Condition", condition, f"Score {score} out of 6", tone)
        + _metric_card("Current Price", format_currency(current_price), "Latest market price", "neutral")
        + _metric_card("DCF Fair Value", format_currency(fair_value), f"Upside {format_percent(upside)}", tone)
        + _metric_card("Trailing P/E", format_ratio(pe_ratio), "Market valuation multiple", "neutral")
        + _metric_card("Debt / Equity", format_ratio(debt_to_equity), "Balance-sheet risk indicator", "neutral")
        + "</div>",
        unsafe_allow_html=True,
    )

    top_left, top_right = st.columns([0.9, 1.1])
    with top_left:
        st.plotly_chart(_health_gauge(score_percent, condition), width="stretch")
    with top_right:
        st.plotly_chart(_valuation_bar(current_price, fair_value), width="stretch")

    bottom_left, bottom_right = st.columns([1.25, 0.75])
    with bottom_left:
        st.plotly_chart(_driver_chart(drivers), width="stretch")
    with bottom_right:
        st.plotly_chart(_mix_chart(drivers), width="stretch")

    st.markdown("#### Investor Explanation")
    st.info(_takeaway(rating, condition, drivers))

    explanation = pd.DataFrame(drivers)[["Area", "Metric", "Reading", "Status", "Investor Meaning"]]
    st.dataframe(explanation, width="stretch", hide_index=True)
    st.caption("Educational dashboard only. Validate assumptions, industry context, and peer benchmarks before making investment decisions.")
