def orb_signal(df, logic: dict = None, orb_minutes: int = 30, interval_minutes: int = 5) -> dict | None:
    if logic is None:
        logic = {}

    orb_bars  = orb_minutes // interval_minutes
    rvol_min  = logic.get("rvol_min", 1.5)
    adx_min   = logic.get("adx_min",  20)

    if len(df) < orb_bars + 1:
        return None

    opening  = df.iloc[:orb_bars]
    orb_high = opening["high"].max()
    orb_low  = opening["low"].min()

    last = df.iloc[-1]

    # Filtros de calidad
    rvol_ok = last.get("rvol", 0) >= rvol_min
    adx_ok  = last.get("adx",  0) >= adx_min

    if not rvol_ok or not adx_ok:
        return None

    if last["close"] > orb_high:
        return {
            "strategy":  "orb",
            "direction": "BUY",
            "signal":    "BUY",
            "score":     2,
            "orb_high":  round(orb_high, 2),
            "orb_low":   round(orb_low,  2),
        }

    if last["close"] < orb_low:
        return {
            "strategy":  "orb",
            "direction": "SELL",
            "signal":    "SELL",
            "score":     2,
            "orb_high":  round(orb_high, 2),
            "orb_low":   round(orb_low,  2),
        }

    return None