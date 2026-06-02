from __future__ import annotations

import streamlit as st

from config import STATEMENT_LINE_ITEMS
from utils.helpers import format_currency, show_data_warning, statement_to_table


def _show_statement(title: str, df, rows: list[str]) -> None:
    st.markdown(f"#### {title}")
    table = statement_to_table(df, rows)
    if table.empty:
        show_data_warning(f"{title} data is not available for this ticker.")
        return
    st.dataframe(table.map(format_currency), width="stretch")


def render(statements: dict) -> None:
    st.subheader("Financial Statements")
    tabs = st.tabs(["Income Statement", "Balance Sheet", "Cash Flow"])
    with tabs[0]:
        _show_statement("Income Statement", statements.get("income"), STATEMENT_LINE_ITEMS["income"])
    with tabs[1]:
        _show_statement("Balance Sheet", statements.get("balance"), STATEMENT_LINE_ITEMS["balance"])
    with tabs[2]:
        _show_statement("Cash Flow Statement", statements.get("cashflow"), STATEMENT_LINE_ITEMS["cashflow"])
