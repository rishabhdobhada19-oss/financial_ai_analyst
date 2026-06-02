from __future__ import annotations

import numpy as np
import pandas as pd


def _row(df: pd.DataFrame, names: list[str]) -> pd.Series:
    if df is None or df.empty:
        return pd.Series(dtype=float)
    for name in names:
        if name in df.index:
            return pd.to_numeric(df.loc[name], errors="coerce")
    return pd.Series(index=df.columns, dtype=float)


def _divide(a: pd.Series, b: pd.Series) -> pd.Series:
    result = a / b.replace(0, np.nan)
    return result.replace([np.inf, -np.inf], np.nan)


def calculate_ratios(statements: dict[str, pd.DataFrame], info: dict) -> pd.DataFrame:
    income = statements.get("income", pd.DataFrame())
    balance = statements.get("balance", pd.DataFrame())
    cashflow = statements.get("cashflow", pd.DataFrame())
    columns = income.columns if not income.empty else balance.columns if not balance.empty else cashflow.columns
    ratios = pd.DataFrame(index=columns)

    revenue = _row(income, ["Total Revenue"])
    gross_profit = _row(income, ["Gross Profit"])
    ebitda = _row(income, ["EBITDA", "Normalized EBITDA"])
    operating_income = _row(income, ["Operating Income"])
    net_income = _row(income, ["Net Income", "Net Income Common Stockholders"])
    assets = _row(balance, ["Total Assets"])
    liabilities = _row(balance, ["Total Liabilities Net Minority Interest", "Total Liab"])
    equity = _row(balance, ["Stockholders Equity", "Total Equity Gross Minority Interest"])
    current_assets = _row(balance, ["Current Assets", "Total Current Assets"])
    current_liabilities = _row(balance, ["Current Liabilities", "Total Current Liabilities"])
    cash = _row(balance, ["Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments"])
    receivables = _row(balance, ["Accounts Receivable", "Receivables"])
    inventory = _row(balance, ["Inventory"])
    debt = _row(balance, ["Total Debt", "Long Term Debt"])

    ratios["Gross Margin"] = _divide(gross_profit, revenue)
    ratios["EBITDA Margin"] = _divide(ebitda, revenue)
    ratios["Operating Margin"] = _divide(operating_income, revenue)
    ratios["Net Margin"] = _divide(net_income, revenue)
    ratios["ROE"] = _divide(net_income, equity)
    ratios["ROA"] = _divide(net_income, assets)
    ratios["Current Ratio"] = _divide(current_assets, current_liabilities)
    quick_assets = current_assets - inventory
    if quick_assets.dropna().empty:
        quick_assets = cash.add(receivables, fill_value=0)
    ratios["Quick Ratio"] = _divide(quick_assets, current_liabilities)
    ratios["Debt to Equity"] = _divide(debt, equity)
    ratios["Debt Ratio"] = _divide(liabilities, assets)
    ratios["Revenue Growth"] = revenue.pct_change(periods=-1)
    ratios["Earnings Growth"] = net_income.pct_change(periods=-1)

    ratios["PE Ratio"] = float(info.get("trailingPE") or np.nan)
    ratios["PB Ratio"] = float(info.get("priceToBook") or np.nan)
    ratios["EV/EBITDA"] = float(info.get("enterpriseToEbitda") or np.nan)
    ratios["PEG Ratio"] = float(info.get("pegRatio") or np.nan)

    ratios.index = pd.to_datetime(ratios.index)
    return ratios.sort_index()
