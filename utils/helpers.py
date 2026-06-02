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
    return f"₹{format_number(number)}"


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


def chart_template() -> str:
    return "plotly_white" if st.session_state.get("theme_mode") == "Light" else "plotly_dark"


def inject_css(theme_mode: str = "Dark") -> None:
    is_light = theme_mode == "Light"
    color_scheme = "light" if is_light else "dark"
    page_bg = "#f8fafc" if is_light else "#0f172a"
    sidebar_bg = "#ffffff" if is_light else "#111827"
    text = "#0f172a" if is_light else "#e5e7eb"
    muted = "#64748b" if is_light else "#94a3b8"
    panel = "rgba(255, 255, 255, 0.94)" if is_light else "rgba(15, 23, 42, 0.72)"
    panel_strong = "rgba(255, 255, 255, 0.98)" if is_light else "rgba(15, 23, 42, 0.82)"
    border = "rgba(15, 23, 42, 0.14)" if is_light else "rgba(148, 163, 184, 0.24)"
    note = "#475569" if is_light else "#cbd5e1"
    input_bg = "#ffffff" if is_light else "#111827"
    input_hover = "#f1f5f9" if is_light else "#172033"
    alert_bg = "#dbeafe" if is_light else "rgba(30, 64, 175, 0.22)"
    alert_text = "#0f172a" if is_light else "#dbeafe"
    table_header = "#e2e8f0" if is_light else "#111827"
    st.markdown(
        f"""
        <style>
        :root {{ color-scheme: {color_scheme}; }}
        .stApp {{
            background: {page_bg};
            color: {text};
        }}
        [data-testid="stHeader"] {{
            background: {page_bg};
            border-bottom: 1px solid {border};
        }}
        [data-testid="stToolbar"], [data-testid="stDecoration"] {{
            background: transparent;
        }}
        .block-container {{ padding-top: 1.4rem; max-width: 1280px; }}
        [data-testid="stSidebar"] {{
            background: {sidebar_bg};
            border-right: 1px solid {border};
        }}
        [data-testid="stSidebar"], [data-testid="stSidebar"] * {{
            color: {text};
        }}
        .stMarkdown, .stCaption, p, label, h1, h2, h3, h4 {{
            color: {text};
        }}
        [data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] * {{
            color: {text};
        }}
        input, textarea, select {{
            background: {input_bg} !important;
            color: {text} !important;
            border-color: {border} !important;
            caret-color: #38bdf8 !important;
        }}
        input::placeholder, textarea::placeholder {{
            color: {muted} !important;
            opacity: 1 !important;
        }}
        [data-baseweb="input"],
        [data-baseweb="select"] > div,
        [data-baseweb="textarea"] {{
            background: {input_bg} !important;
            border-color: {border} !important;
            box-shadow: none !important;
        }}
        [data-baseweb="input"]:focus-within,
        [data-baseweb="select"] > div:focus-within,
        [data-baseweb="textarea"]:focus-within {{
            border-color: #38bdf8 !important;
            box-shadow: 0 0 0 1px #38bdf8 !important;
        }}
        [data-baseweb="input"]:hover,
        [data-baseweb="select"] > div:hover,
        [data-baseweb="textarea"]:hover {{
            background: {input_hover} !important;
        }}
        [data-baseweb="select"] span,
        [data-baseweb="popover"] *,
        [role="listbox"] *,
        [role="option"] {{
            color: {text} !important;
        }}
        [data-baseweb="popover"] > div,
        [role="listbox"] {{
            background: {input_bg} !important;
            border: 1px solid {border} !important;
        }}
        [role="option"]:hover {{
            background: {input_hover} !important;
        }}
        [data-testid="stRadio"] label span {{
            color: {text} !important;
        }}
        [data-testid="stAlert"] {{
            background: {alert_bg};
            color: {alert_text};
            border: 1px solid {border};
            border-radius: 8px;
        }}
        [data-testid="stAlert"] * {{
            color: {alert_text};
        }}
        [data-testid="stDataFrame"] {{
            border: 1px solid {border};
            border-radius: 8px;
            overflow: hidden;
        }}
        [data-testid="stDataFrame"] [role="columnheader"] {{
            background: {table_header};
            color: {text};
        }}
        h1, h2, h3 {{ letter-spacing: 0; }}
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 12px;
            margin: 14px 0 22px;
        }}
        .kpi-card {{
            border: 1px solid {border};
            border-radius: 8px;
            background: {panel};
            padding: 14px 16px;
            min-height: 92px;
        }}
        .kpi-label {{
            color: {muted};
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: .04em;
            margin-bottom: 8px;
        }}
        .kpi-value {{
            color: {text};
            font-size: 1.35rem;
            font-weight: 650;
            overflow-wrap: anywhere;
        }}
        .subtle {{ color: {muted}; }}
        .bi-grid {{
            display: grid;
            grid-template-columns: repeat(6, minmax(130px, 1fr));
            gap: 10px;
            margin: 12px 0 14px;
        }}
        .bi-card {{
            border: 1px solid {border};
            border-left: 4px solid #38bdf8;
            border-radius: 6px;
            background: {panel_strong};
            padding: 12px;
            min-height: 104px;
        }}
        .bi-good {{ border-left-color: #22c55e; }}
        .bi-bad {{ border-left-color: #ef4444; }}
        .bi-neutral {{ border-left-color: #38bdf8; }}
        .bi-label {{
            color: {muted};
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: .04em;
            min-height: 28px;
        }}
        .bi-value {{
            color: {text};
            font-size: 1.45rem;
            font-weight: 700;
            line-height: 1.2;
            overflow-wrap: anywhere;
        }}
        .bi-note {{
            color: {note};
            font-size: 0.78rem;
            margin-top: 8px;
            line-height: 1.25;
        }}
        @media (max-width: 1100px) {{
            .bi-grid {{ grid-template-columns: repeat(3, minmax(140px, 1fr)); }}
        }}
        @media (max-width: 720px) {{
            .bi-grid {{ grid-template-columns: repeat(2, minmax(130px, 1fr)); }}
        }}
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
