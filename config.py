APP_TITLE = "AI Financial Analyst"
DEFAULT_TICKER = "AAPL"
DEFAULT_SEARCH_QUERY = ""
DEFAULT_PERIOD = "2y"
PRICE_PERIODS = ["6mo", "1y", "2y", "5y", "10y"]

CHART_TEMPLATE = "plotly_dark"

STATEMENT_LINE_ITEMS = {
    "income": [
        "Total Revenue",
        "Gross Profit",
        "EBITDA",
        "Normalized EBITDA",
        "Operating Income",
        "Operating Income Loss",
        "Net Income",
        "Net Income Common Stockholders",
    ],
    "balance": [
        "Total Assets",
        "Total Liabilities Net Minority Interest",
        "Total Liab",
        "Stockholders Equity",
        "Total Equity Gross Minority Interest",
        "Current Assets",
        "Total Current Assets",
        "Current Liabilities",
        "Total Current Liabilities",
        "Cash And Cash Equivalents",
        "Total Debt",
        "Long Term Debt",
    ],
    "cashflow": [
        "Operating Cash Flow",
        "Free Cash Flow",
        "Capital Expenditure",
    ],
}
