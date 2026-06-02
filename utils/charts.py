from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from utils.helpers import chart_template


def line_chart(df: pd.DataFrame, title: str, y_title: str = "") -> go.Figure:
    fig = go.Figure()
    if df is not None and not df.empty:
        for column in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df[column], mode="lines+markers", name=str(column)))
    fig.update_layout(template=chart_template(), title=title, height=380, margin=dict(l=20, r=20, t=54, b=20))
    fig.update_yaxes(title=y_title)
    return fig


def pie_chart(values: pd.Series, title: str) -> go.Figure:
    fig = go.Figure()
    if values is not None and not values.empty:
        clean_values = pd.to_numeric(values, errors="coerce").dropna()
        clean_values = clean_values[clean_values > 0]
        if not clean_values.empty:
            fig.add_trace(
                go.Pie(
                    labels=clean_values.index,
                    values=clean_values.values,
                    hole=0.45,
                    textinfo="label+percent",
                    hovertemplate="%{label}<br>Value: %{value:.3f}<br>Share: %{percent}<extra></extra>",
                )
            )
    fig.update_layout(template=chart_template(), title=title, height=380, margin=dict(l=20, r=20, t=54, b=20))
    return fig


def price_volume_chart(hist: pd.DataFrame) -> go.Figure:
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.72, 0.28], vertical_spacing=0.04)
    if hist is not None and not hist.empty:
        fig.add_trace(go.Scatter(x=hist.index, y=hist["Close"], name="Close", line=dict(color="#38bdf8")), row=1, col=1)
        for ma, color in (("SMA 20", "#22c55e"), ("SMA 50", "#f59e0b"), ("SMA 200", "#ef4444")):
            if ma in hist:
                fig.add_trace(go.Scatter(x=hist.index, y=hist[ma], name=ma, line=dict(width=1.4, color=color)), row=1, col=1)
        fig.add_trace(go.Bar(x=hist.index, y=hist["Volume"], name="Volume", marker_color="#64748b"), row=2, col=1)
    fig.update_layout(template=chart_template(), height=560, title="Stock Price and Volume", margin=dict(l=20, r=20, t=54, b=20))
    fig.update_yaxes(title="Price (₹)", row=1, col=1)
    fig.update_yaxes(title="Volume", row=2, col=1)
    return fig


def macd_chart(hist: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if hist is not None and not hist.empty:
        fig.add_trace(go.Scatter(x=hist.index, y=hist["MACD"], name="MACD", line=dict(color="#38bdf8")))
        fig.add_trace(go.Scatter(x=hist.index, y=hist["MACD Signal"], name="Signal", line=dict(color="#f59e0b")))
        fig.add_trace(go.Bar(x=hist.index, y=hist["MACD Histogram"], name="Histogram", marker_color="#94a3b8"))
    fig.update_layout(template=chart_template(), height=340, title="MACD", margin=dict(l=20, r=20, t=54, b=20))
    return fig


def forecast_chart(hist: pd.DataFrame, forecast: pd.DataFrame, title: str) -> go.Figure:
    fig = go.Figure()
    if hist is not None and not hist.empty:
        fig.add_trace(go.Scatter(x=hist.index, y=hist["Close"], name="Historical Close", line=dict(color="#38bdf8")))
    if forecast is not None and not forecast.empty:
        fig.add_trace(go.Scatter(x=forecast.index, y=forecast["Forecast"], name="Forecast", line=dict(color="#22c55e", dash="dash")))
        fig.add_trace(
            go.Scatter(
                x=forecast.index,
                y=forecast["Upper"],
                name="Upper Trend",
                line=dict(width=0),
                showlegend=False,
            )
        )
        fig.add_trace(
            go.Scatter(
                x=forecast.index,
                y=forecast["Lower"],
                name="Confidence Trend",
                fill="tonexty",
                fillcolor="rgba(34,197,94,0.18)",
                line=dict(width=0),
            )
        )
    fig.update_layout(template=chart_template(), height=460, title=title, margin=dict(l=20, r=20, t=54, b=20))
    fig.update_yaxes(title="Price (₹)")
    return fig
