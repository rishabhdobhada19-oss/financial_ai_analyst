from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.financial_ratios import calculate_ratios
from utils.helpers import format_percent, format_ratio, kpi_grid, safe_float, show_data_warning
from utils.valuation import dcf_valuation


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


def _overall_view(score: int) -> str:
    if score >= 5:
        return "Good for Investment"
    if score <= -4:
        return "Not Attractive Now"
    return "Watchlist / Selective"


def _rating(score: int) -> str:
    if score >= 5:
        return "Buy"
    if score <= -4:
        return "Avoid"
    return "Hold"


def render(ticker: str, statements: dict, info: dict) -> None:
    st.subheader("Investor Insights, Suggestions and Conclusion")

    ratios = calculate_ratios(statements, info)
    if ratios.empty:
        show_data_warning("Investor insights could not be generated because financial statements are missing.")
        return

    valuation = dcf_valuation(statements, info, 0.06, 0.10, 0.025, 5)
    company_name = info.get("longName") or info.get("shortName") or ticker

    revenue_growth = _latest(ratios, "Revenue Growth")
    earnings_growth = _latest(ratios, "Earnings Growth")
    net_margin = _latest(ratios, "Net Margin")
    roe = _latest(ratios, "ROE")
    current_ratio = _latest(ratios, "Current Ratio")
    debt_to_equity = _latest(ratios, "Debt to Equity")
    pe_ratio = safe_float(info.get("trailingPE"))
    peg_ratio = safe_float(info.get("pegRatio"))
    dcf_upside = safe_float(valuation.get("upside"), 0.0)

    short_score = sum(
        [
            _score(revenue_growth, 0.03, 0.0),
            _score(net_margin, 0.08, 0.02),
            _score(current_ratio, 1.2, 0.8),
            _score(dcf_upside, 0.05, -0.10),
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
            _score(dcf_upside, 0.15, -0.15),
        ]
    )
    total_score = short_score + long_score

    overall_view = _overall_view(total_score)
    rating = _rating(total_score)
    short_view = _view(short_score)
    long_view = _view(long_score)

    st.markdown(f"### {company_name}")
    st.caption("Financial analyst style conclusion based on public financial ratios and a simple DCF estimate.")
    kpi_grid(
        [
            ("Final Rating", rating),
            ("Overall Conclusion", overall_view),
            ("Short-Term View", short_view),
            ("Long-Term View", long_view),
            ("DCF Upside", format_percent(dcf_upside)),
            ("Debt / Equity", format_ratio(debt_to_equity)),
        ]
    )

    positives: list[str] = []
    risks: list[str] = []

    if revenue_growth is not None:
        if revenue_growth > 0.05:
            positives.append("Revenue growth is healthy, which supports demand momentum.")
        elif revenue_growth < 0:
            risks.append("Revenue has declined, which weakens growth visibility.")
    if earnings_growth is not None:
        if earnings_growth > 0.05:
            positives.append("Earnings growth is positive, supporting long-term compounding.")
        elif earnings_growth < 0:
            risks.append("Earnings growth is negative, so profitability momentum needs review.")
    if net_margin is not None:
        if net_margin > 0.12:
            positives.append("Net margin is strong, showing good profit conversion.")
        elif net_margin < 0.03:
            risks.append("Net margin is thin, leaving less cushion in weak markets.")
    if roe is not None:
        if roe > 0.15:
            positives.append("ROE is strong, indicating efficient use of shareholder capital.")
        elif roe < 0.05:
            risks.append("ROE is weak, suggesting limited return generation.")
    if current_ratio is not None:
        if current_ratio >= 1.2:
            positives.append("Liquidity appears comfortable for short-term obligations.")
        elif current_ratio < 0.8:
            risks.append("Liquidity looks tight for near-term obligations.")
    if debt_to_equity is not None:
        if debt_to_equity <= 1:
            positives.append("Debt to equity is manageable.")
        elif debt_to_equity >= 2:
            risks.append("Debt to equity is elevated and increases financial risk.")
    if pe_ratio is not None and pe_ratio > 35:
        risks.append("P/E valuation is high, so the stock may be sensitive to growth disappointment.")
    if dcf_upside is not None:
        if dcf_upside > 0.15:
            positives.append("DCF estimate suggests meaningful upside from the current price.")
        elif dcf_upside < -0.15:
            risks.append("DCF estimate suggests the stock may be overvalued.")

    left, right = st.columns(2)
    with left:
        st.markdown("#### Key Positive Signals")
        if positives:
            for item in positives[:5]:
                st.success(item)
        else:
            st.info("No strong positive signal is confirmed from the available data.")
    with right:
        st.markdown("#### Key Risk Signals")
        if risks:
            for item in risks[:5]:
                st.warning(item)
        else:
            st.success("No major risk signal is confirmed from the available data.")

    st.markdown("#### Suggestions for Investors")
    if short_view == "Favorable":
        st.write("- For short-term investment, the company looks suitable if price trend, market sentiment, and volume also support entry.")
    elif short_view == "Cautious":
        st.write("- For short-term investment, avoid aggressive entry until liquidity, margins, or valuation improve.")
    else:
        st.write("- For short-term investment, wait for a better entry price or stronger quarterly confirmation.")

    if long_view == "Favorable":
        st.write("- For long-term investment, the company can be considered for accumulation after peer comparison and business-quality review.")
    elif long_view == "Cautious":
        st.write("- For long-term investment, wait for clearer growth, stronger returns, or lower leverage before committing capital.")
    else:
        st.write("- For long-term investment, keep the stock on a watchlist and invest selectively rather than all at once.")

    st.markdown("#### Final Financial Analyst Conclusion")
    if rating == "Buy":
        st.success(
            f"{company_name} appears good for investment based on the available financial ratios, especially for long-term investors if valuation remains reasonable."
        )
    elif rating == "Avoid":
        st.error(
            f"{company_name} does not look attractive for investment right now. Investors should wait for better fundamentals or a better valuation."
        )
    else:
        st.info(
            f"{company_name} is a hold/watchlist candidate. Investors should be selective and confirm the view with industry comparison, news, and price action."
        )

    st.caption("Educational analysis only. This is not personalized financial advice or a guarantee of future returns.")
