import pandas_ta as ta

def compute_indicators(df, logic=None):
    df["ema200"] = df["close"].ewm(span=200).mean()
    df["ema20"]  = df["close"].ewm(span=20).mean()

    df["rsi"] = ta.rsi(df["close"], length=14)

    df["atr"]     = ta.atr(df["high"], df["low"], df["close"], length=14)
    df["atr_pct"] = df["atr"] / df["close"]

    df["adx"] = ta.adx(df["high"], df["low"], df["close"])["ADX_14"]

    df["rvol"] = df["volume"] / df["volume"].rolling(20).mean()

    # VWAP reseteado por sesión — compatible con pandas 2.3.3 + Python 3.13
    df["_cv"] = df["close"] * df["volume"]
    df["vwap"] = (
        df.groupby(df.index.date)["_cv"].transform("cumsum") /
        df.groupby(df.index.date)["volume"].transform("cumsum")
    )
    df.drop(columns=["_cv"], inplace=True)

    df.dropna(subset=["rsi", "atr", "adx", "rvol"], inplace=True)
    return df