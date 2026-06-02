# AI Financial Analyst Platform

A Streamlit application for public-company research, financial statement review, ratio analysis, technical stock performance, price forecasting, DCF valuation, and automated investment summaries.

## Features

- Company or ticker search with selectable Yahoo Finance matches
- Company overview with professional KPI cards
- Annual and quarterly financial statements from Yahoo Finance
- Profitability, liquidity, leverage, valuation, and growth ratio pie charts
- Investor explanation dashboard with plain-language financial condition interpretation
- Daily price, volume, SMA, RSI, and MACD analysis
- 30-day and 90-day linear-regression price forecasts
- Interactive DCF model with user-controlled valuation assumptions
- Automated Buy, Hold, or Sell summary with supporting explanation
- Invalid ticker, API failure, and missing-data handling

## Project Structure

```text
financial_ai_analyst/
|-- app.py
|-- config.py
|-- sitecustomize.py
|-- requirements.txt
|-- README.md
|-- assets/
|-- data/
|-- models/
|-- pages/
|   |-- __init__.py
|   |-- company_overview.py
|   |-- financial_statements.py
|   |-- forecasting_dashboard.py
|   |-- investment_summary.py
|   |-- ratio_analysis.py
|   `-- valuation_dashboard.py
`-- utils/
    |-- __init__.py
    |-- charts.py
    |-- fetch_data.py
    |-- financial_ratios.py
    |-- forecasting.py
    |-- helpers.py
    `-- valuation.py
```

## Installation

```bash
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

Use the sidebar search box to type a company name or Yahoo Finance ticker, select the matching company, and choose the dashboard you want to review. The app uses `yfinance`, so market and financial statement availability depends on Yahoo Finance responses for the selected company.
