"""Step 2 - Forecast next week's patient arrivals for every day and hour.

Method: seasonal average (mean of the same day+hour over recent weeks) with a trend
adjustment. It is compared against a naive "same as last week" forecast on a
hold-out week so we can show the forecast is actually better.
"""
import numpy as np
import pandas as pd


def seasonal_forecast(history, lookback=8):
    recent = history[history.week > history.week.max() - lookback]
    base = recent.groupby(["day", "hour"]).arrivals.mean()
    # simple trend: ratio of last 4 weeks to the 4 weeks before
    w = history.groupby("week").arrivals.sum()
    trend = (w.iloc[-4:].mean() / w.iloc[-8:-4].mean()) ** (1 / 4) if len(w) >= 8 else 1.0
    steps_ahead = (lookback + 1) / 2  # mid-point of lookback window to next week
    return (base * trend ** steps_ahead).rename("forecast").reset_index()


def naive_forecast(history):
    last = history[history.week == history.week.max()]
    return last[["day", "hour", "arrivals"]].rename(columns={"arrivals": "forecast"})


def mae(actual, pred):
    return float(np.mean(np.abs(actual - pred)))


def backtest(history):
    """Hold out the last week, forecast it with both methods, return the errors."""
    train = history[history.week < history.week.max()]
    test = history[history.week == history.week.max()]
    out = {}
    for name, fn in [("Seasonal average + trend", seasonal_forecast), ("Naive (last week)", naive_forecast)]:
        f = fn(train).merge(test, on=["day", "hour"])
        out[name] = mae(f.arrivals, f.forecast)
    return out


if __name__ == "__main__":
    from data import make_history
    h = make_history()
    print(backtest(h))
    print(seasonal_forecast(h).head())
