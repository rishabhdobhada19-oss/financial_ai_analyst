from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.charts import pie_chart
from utils.financial_ratios import calculate_ratios
from utils.helpers import chart_template, format_percent, format_ratio, kpi_grid, safe_float, show_data_warning


PERCENT_RATIOS = {
    "Gross Margin",
    "EBITDA Margin",
    "Operating Margin",
    "Net Margin",
    "ROE",
    "ROA",
    "Debt Ratio",
    "Revenue Growth",
    "Earnings Growth",
}


def _format_ratio_table(ratios: pd.DataFrame) -> pd.DataFrame:
    output = ratios.copy()
    output.index = output.index.strftime("%Y-%m-%d")
    for column in output.columns:
        if column in PERCENT_RATIOS:
            output[column] = output[column].map(lambda value: format_percent(value))
        else:
            output[column] = output[column].map(format_ratio)
    return output


def _latest(ratios: pd.DataFrame, column: str) -> float | None:
    if ratios.empty or column not in ratios:
        return None
    values = ratios[column].dropna()
    return safe_float(values.iloc[-1]) if not values.empty else None


def _score(value: float | None, good: float, weak: float, higher_is_better: bool = True) -> int:
    if value is None:
        return 0
    if higher_is_better:
        return 1 if value >= good else -1 if value <= weak else 0
    return 1 if value <= good else -1 if value >= weak else 0


def _view(score: int) -> str:
    if score >= 2:
        return "Favorable"
    if score <= -2:
        return "Cautious"
    return "Neutral"


def _bar_chart(ratios: pd.DataFrame, columns: list[str], title: str) -> go.Figure:
    chart_df = ratios[columns].copy()
    chart_df.index = chart_df.index.year.astype(str)

    fig = go.Figure()
    colors = ["#38bdf8", "#22c55e", "#f59e0b", "#ef4444", "#a78bfa", "#14b8a6"]
    for index, column in enumerate(columns):
        values = pd.to_numeric(chart_df[column], errors="coerce")
        label = column
        if column in PERCENT_RATIOS:
            values = values * 100
            label = f"{column} (%)"
        fig.add_trace(
            go.Bar(
                x=chart_df.index,
                y=values,
                name=label,
                marker_color=colors[index % len(colors)],
                hovertemplate="%{x}<br>%{fullData.name}: %{y:.2f}<extra></extra>",
            )
        )

    fig.update_layout(
        template=chart_template(),
        title=title,
        barmode="group",
        height=420,
        margin=dict(l=20, r=20, t=54, b=28),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.update_xaxes(title="Year")
    fig.update_yaxes(title="Value (% for margins/growth/debt ratio, x for multiples)")
    return fig


def _investment_insights(ratios: pd.DataFrame, info: dict) -> None:
    revenue_growth = _latest(ratios, "Revenue Growth")
    earnings_growth = _latest(ratios, "Earnings Growth")
    net_margin = _latest(ratios, "Net Margin")
    roe = _latest(ratios, "ROE")
    current_ratio = _latest(ratios, "Current Ratio")
    debt_to_equity = _latest(ratios, "Debt to Equity")
    pe_ratio = safe_float(info.get("trailingPE"))
    peg_ratio = safe_float(info.get("pegRatio"))

    short_score = sum(
        [
            _score(revenue_growth, 0.03, 0.0),
            _score(net_margin, 0.08, 0.02),
            _score(current_ratio, 1.2, 0.8),
            _score(debt_to_equity, 1.0, 2.0, higher_is_better=False),
        ]
    )
    long_score = sum(
        [
            _score(revenue_growth, 0.05, 0.0),
            _score(earnings_growth, 0.05, 0.0),
            _score(roe, 0.15, 0.05),
            _score(net_margin, 0.12, 0.03),
            _score(debt_to_equity, 1.0, 2.0, higher_is_better=False),
            _score(peg_ratio, 1.5, 2.5, higher_is_better=False),
        ]
    )

    short_view = _view(short_score)
    long_view = _view(long_score)
    overall_score = short_score + long_score
    overall_view = "Good for investment" if overall_score >= 4 else "Avoid / wait for better evidence" if overall_score <= -4 else "Watchlist / selective investment"

    positives: list[str] = []
    cautions: list[str] = []

    if revenue_growth is not None:
        if revenue_growth > 0.05:
            positives.append("Revenue growth supports demand momentum.")
        elif revenue_growth < 0:
            cautions.append("Revenue growth is weak or negative.")
    if net_margin is not None:
        if net_margin > 0.12:
            positives.append("Profit margins are healthy.")
        elif net_margin < 0.03:
            cautions.append("Profit margins need monitoring.")
    if roe is not None:
        if roe > 0.15:
            positives.append("ROE indicates efficient use of shareholder capital.")
        elif roe < 0.05:
            cautions.append("ROE is not yet strong.")
    if current_ratio is not None:
        if current_ratio >= 1.2:
            positives.append("Liquidity appears comfortable for near-term obligations.")
        elif current_ratio < 0.8:
            cautions.append("Liquidity is tight.")
    if debt_to_equity is not None:
        if debt_to_equity <= 1:
            positives.append("Leverage looks manageable.")
        elif debt_to_equity >= 2:
            cautions.append("Debt levels are elevated.")
    if pe_ratio is not None and pe_ratio > 0:
        if pe_ratio > 35:
            cautions.append("P/E is rich, so price risk may be higher if growth slows.")
        elif pe_ratio < 20:
            positives.append("P/E is not excessive versus broad-market growth stocks.")

    st.markdown("#### Analyst Insights and Investor Conclusion")
    kpi_grid(
        [
            ("Overall View", overall_view),
            ("Short-Term View", short_view),
            ("Long-Term View", long_view),
            ("Latest Revenue Growth", format_percent(revenue_growth)),
            ("Latest Net Margin", format_percent(net_margin)),
            ("Debt / Equity", format_ratio(debt_to_equity)),
        ]
    )

    st.markdown("**Suggestions for Investors**")
    if short_view == "Favorable":
        st.write("- Short-term investors can consider the company if price trend and market sentiment also confirm momentum.")
    elif short_view == "Cautious":
        st.write("- Short-term investors should be careful because the latest ratios do not show enough near-term strength.")
    else:
        st.write("- Short-term investors may wait for clearer quarterly improvement or a better entry price.")

    if long_view == "Favorable":
        st.write("- Long-term investors can consider accumulation after comparing the company with peers and industry growth.")
    elif long_view == "Cautious":
        st.write("- Long-term investors should wait for stronger growth, profitability, or balance-sheet improvement.")
    else:
        st.write("- Long-term investors can keep it on the watchlist and invest selectively after deeper valuation review.")

    if positives:
        st.success("Key positives: " + " ".join(positives[:4]))
    if cautions:
        st.warning("Key risks: " + " ".join(cautions[:4]))
    st.info("Conclusion is an educational financial-analysis view based on available public ratios. It is not personalized investment advice.")


def render(statements: dict, info: dict) -> None:
    st.subheader("Financial Ratio Analysis")
    ratios = calculate_ratios(statements, info)
    if ratios.empty:
        show_data_warning("Ratio analysis could not be generated because financial statements are missing.")
        return

    groups = {
        "Profitability": ["Gross Margin", "EBITDA Margin", "Operating Margin", "Net Margin", "ROE", "ROA"],
        "Liquidity": ["Current Ratio", "Quick Ratio"],
        "Leverage": ["Debt to Equity", "Debt Ratio"],
        "Valuation": ["PE Ratio", "PB Ratio", "EV/EBITDA", "PEG Ratio"],
        "Growth": ["Revenue Growth", "Earnings Growth"],
    }
    tabs = st.tabs(list(groups))
    for tab, (name, columns) in zip(tabs, groups.items()):
        with tab:
            selected = [col for col in columns if col in ratios.columns]
            latest = ratios[selected].dropna(how="all").tail(1)
            if latest.empty:
                show_data_warning(f"{name} ratios are not available for this ticker.")
            else:
                st.plotly_chart(pie_chart(latest.iloc[0], f"Latest {name} Ratio Mix"), width="stretch")
                st.plotly_chart(_bar_chart(ratios, selected, f"Yearly {name} Ratios"), width="stretch")
            st.dataframe(_format_ratio_table(ratios[selected]), width="stretch")

    _investment_insights(ratios, info)
