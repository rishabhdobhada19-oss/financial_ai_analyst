from __future__ import annotations

import math
import os
from typing import Any

import pandas as pd
import streamlit as st

_MPLCONFIGDIR = os.path.join(os.getcwd(), "data", ".matplotlib")
os.makedirs(_MPLCONFIGDIR, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", _MPLCONFIGDIR)


def clean_ticker(ticker: str) -> str:
    return ticker.strip().upper()


def is_missing(value: Any) -> bool:
    if value is None:
        return True
    try:
        return bool(pd.isna(value))
    except TypeError:
        return False


def safe_float(value: Any, default: float | None = None) -> float | None:
    if is_missing(value):
        return default
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    if math.isnan(result) or math.isinf(result):
        return default
    return result


def format_number(value: Any) -> str:
    number = safe_float(value)
    if number is None:
        return "N/A"
    sign = "-" if number < 0 else ""
    number = abs(number)
    for suffix, threshold in (("T", 1e12), ("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if number >= threshold:
            return f"{sign}{number / threshold:,.2f}{suffix}"
    return f"{sign}{number:,.0f}"


def format_currency(value: Any) -> str:
    number = safe_float(value)
    if number is None:
        return "N/A"
    return f"${format_number(number)}"


def format_percent(value: Any, as_decimal: bool = True) -> str:
    number = safe_float(value)
    if number is None:
        return "N/A"
    if as_decimal:
        number *= 100
    return f"{number:,.2f}%"


def format_ratio(value: Any) -> str:
    number = safe_float(value)
    if number is None:
        return "N/A"
    return f"{number:,.2f}x"


def statement_to_table(df: pd.DataFrame, rows: list[str]) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    available = [row for row in rows if row in df.index]
    table = df.loc[available].copy() if available else df.head(12).copy()
    table.columns = [_format_statement_column(col) for col in table.columns]
    return table.map(lambda x: safe_float(x))


def _format_statement_column(column: Any) -> str:
    try:
        return pd.to_datetime(column).strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        return str(column)


def get_line_item(df: pd.DataFrame, names: list[str] | str, default: float | None = None) -> float | None:
    if isinstance(names, str):
        names = [names]
    if df is None or df.empty:
        return default
    for name in names:
        if name in df.index:
            series = df.loc[name].dropna()
            if not series.empty:
                return safe_float(series.iloc[0], default)
    return default


def inject_css() -> None:
    st.markdown(
        """
        <style>
        :root { color-scheme: dark; }
        .block-container { padding-top: 1.4rem; max-width: 1280px; }
        [data-testid="stSidebar"] { background: #111827; }
        h1, h2, h3 { letter-spacing: 0; }
        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 12px;
            margin: 14px 0 22px;
        }
        .kpi-card {
            border: 1px solid rgba(148, 163, 184, 0.24);
            border-radius: 8px;
            background: rgba(15, 23, 42, 0.72);
            padding: 14px 16px;
            min-height: 92px;
        }
        .kpi-label {
            color: #94a3b8;
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: .04em;
            margin-bottom: 8px;
        }
        .kpi-value {
            color: #f8fafc;
            font-size: 1.35rem;
            font-weight: 650;
            overflow-wrap: anywhere;
        }
        .subtle { color: #94a3b8; }
        .bi-grid {
            display: grid;
            grid-template-columns: repeat(6, minmax(130px, 1fr));
            gap: 10px;
            margin: 12px 0 14px;
        }
        .bi-card {
            border: 1px solid rgba(148, 163, 184, 0.24);
            border-left: 4px solid #38bdf8;
            border-radius: 6px;
            background: rgba(15, 23, 42, 0.82);
            padding: 12px;
            min-height: 104px;
        }
        .bi-good { border-left-color: #22c55e; }
        .bi-bad { border-left-color: #ef4444; }
        .bi-neutral { border-left-color: #38bdf8; }
        .bi-label {
            color: #94a3b8;
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: .04em;
            min-height: 28px;
        }
        .bi-value {
            color: #f8fafc;
            font-size: 1.45rem;
            font-weight: 700;
            line-height: 1.2;
            overflow-wrap: anywhere;
        }
        .bi-note {
            color: #cbd5e1;
            font-size: 0.78rem;
            margin-top: 8px;
            line-height: 1.25;
        }
        @media (max-width: 1100px) {
            .bi-grid { grid-template-columns: repeat(3, minmax(140px, 1fr)); }
        }
        @media (max-width: 720px) {
            .bi-grid { grid-template-columns: repeat(2, minmax(130px, 1fr)); }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def kpi_grid(items: list[tuple[str, str]]) -> None:
    html = ['<div class="kpi-grid">']
    for label, value in items:
        html.append(
            f'<div class="kpi-card"><div class="kpi-label">{label}</div>'
            f'<div class="kpi-value">{value}</div></div>'
        )
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def show_data_warning(message: str) -> None:
    st.warning(message)
