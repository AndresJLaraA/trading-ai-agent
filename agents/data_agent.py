import yfinance as yf
import pandas as pd

PERIOD_MAP = {
    "5m":  "1d",
    "15m": "5d",
    "4h":  "60d",
}

def get_data(symbol, interval):
    try:
        actual_interval = "1h" if interval == "4h" else interval
        period = PERIOD_MAP.get(interval, "1d")

        df = yf.download(symbol, period=period, interval=actual_interval, progress=False)
        if df is None or df.empty:
            return None

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0].lower() for col in df.columns]
        else:
            df.columns = [c.lower() for c in df.columns]

        if interval == "4h":
            df = df.resample("4h").agg({
                "open":   "first",
                "high":   "max",
                "low":    "min",
                "close":  "last",
                "volume": "sum",
            }).dropna()

        return df

    except Exception as e:
        print(f"Error data {symbol} {interval}: {e}")
        return None