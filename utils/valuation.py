from __future__ import annotations

import pandas as pd

from utils.helpers import get_line_item, safe_float


def dcf_valuation(
    statements: dict[str, pd.DataFrame],
    info: dict,
    revenue_growth: float,
    discount_rate: float,
    terminal_growth: float,
    forecast_period: int,
) -> dict:
    cashflow = statements.get("cashflow", pd.DataFrame())
    latest_fcf = get_line_item(cashflow, ["Free Cash Flow", "Operating Cash Flow"], 0.0) or 0.0
    current_price = safe_float(info.get("currentPrice") or info.get("regularMarketPrice"), 0.0) or 0.0
    shares = safe_float(info.get("sharesOutstanding"), 0.0) or 0.0
    total_debt = safe_float(info.get("totalDebt"), 0.0) or 0.0
    cash = safe_float(info.get("totalCash"), 0.0) or 0.0

    forecast_rows = []
    enterprise_value = 0.0
    fcf = latest_fcf
    for year in range(1, forecast_period + 1):
        fcf *= 1 + revenue_growth
        discounted = fcf / ((1 + discount_rate) ** year)
        enterprise_value += discounted
        forecast_rows.append({"Year": year, "Free Cash Flow": fcf, "Discounted FCF": discounted})

    if discount_rate <= terminal_growth:
        terminal_value = 0.0
        terminal_discounted = 0.0
    else:
        terminal_value = fcf * (1 + terminal_growth) / (discount_rate - terminal_growth)
        terminal_discounted = terminal_value / ((1 + discount_rate) ** forecast_period)
        enterprise_value += terminal_discounted

    equity_value = enterprise_value - total_debt + cash
    intrinsic_value = equity_value / shares if shares else 0.0
    upside = ((intrinsic_value - current_price) / current_price) if current_price else 0.0
    conclusion = "Buy" if upside > 0.15 else "Sell" if upside < -0.15 else "Hold"

    return {
        "latest_fcf": latest_fcf,
        "forecast": pd.DataFrame(forecast_rows),
        "terminal_value": terminal_value,
        "terminal_discounted": terminal_discounted,
        "enterprise_value": enterprise_value,
        "equity_value": equity_value,
        "intrinsic_value": intrinsic_value,
        "current_price": current_price,
        "upside": upside,
        "conclusion": conclusion,
    }
