def momentum_signal(df, logic: dict = None) -> dict | None:
    if logic is None:
        logic = {}

    if len(df) < 2:
        return None

    last = df.iloc[-1]

    rvol  = last.get("rvol")
    close = last.get("close")
    ema20 = last.get("ema20")
    adx   = last.get("adx")

    if any(v is None for v in [rvol, close, ema20, adx]):
        return None

    rvol_min = logic.get("rvol_min", 1.5)
    adx_min  = logic.get("adx_min",  20)

    rvol_ok = rvol >= rvol_min
    adx_ok  = adx  >= adx_min

    if not rvol_ok or not adx_ok:
        return None

    if close > ema20:
        return {
            "strategy":  "momentum",
            "direction": "BUY",
            "signal":    "BUY",
            "score":     2,
            "rvol":      round(rvol, 2),
            "adx":       round(adx,  2),
        }

    if close < ema20:
        return {
            "strategy":  "momentum",
            "direction": "SELL",
            "signal":    "SELL",
            "score":     2,
            "rvol":      round(rvol, 2),
            "adx":       round(adx,  2),
        }

    return None