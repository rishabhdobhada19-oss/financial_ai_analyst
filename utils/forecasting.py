from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression


def add_technical_indicators(hist: pd.DataFrame) -> pd.DataFrame:
    if hist is None or hist.empty:
        return pd.DataFrame()
    df = hist.copy()
    close = df["Close"]
    df["SMA 20"] = close.rolling(20).mean()
    df["SMA 50"] = close.rolling(50).mean()
    df["SMA 200"] = close.rolling(200).mean()

    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    df["RSI"] = 100 - (100 / (1 + rs))

    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    df["MACD"] = ema12 - ema26
    df["MACD Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACD Histogram"] = df["MACD"] - df["MACD Signal"]
    df["Daily Return"] = close.pct_change()
    return df


def forecast_prices(hist: pd.DataFrame, days: int) -> pd.DataFrame:
    if hist is None or hist.empty or len(hist.dropna(subset=["Close"])) < 30:
        return pd.DataFrame()
    df = hist.dropna(subset=["Close"]).copy()
    x = np.arange(len(df)).reshape(-1, 1)
    y = df["Close"].to_numpy()
    model = LinearRegression()
    model.fit(x, y)
    future_x = np.arange(len(df), len(df) + days).reshape(-1, 1)
    predictions = model.predict(future_x)
    residual_std = float(np.std(y - model.predict(x)))
    future_index = pd.bdate_range(df.index[-1] + pd.Timedelta(days=1), periods=days)
    trend_width = residual_std * np.linspace(1.0, 1.8, days)
    return pd.DataFrame(
        {
            "Forecast": predictions,
            "Upper": predictions + trend_width,
            "Lower": predictions - trend_width,
        },
        index=future_index,
    )
