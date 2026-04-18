def vwap_signal(df, logic: dict = None) -> dict | None:
    if logic is None:
        logic = {}

    if len(df) < 2:
        return None

    last = df.iloc[-1]

    close = last.get("close")
    vwap  = last.get("vwap")
    atr   = last.get("atr")
    rsi   = last.get("rsi")

    if any(v is None for v in [close, vwap, atr, rsi]):
        return None

    rsi_low  = logic.get("rsi_low",  40)
    rsi_high = logic.get("rsi_high", 70)

    # Banda dinámica basada en ATR en lugar de porcentaje fijo
    band = atr * 0.5
    deviation = close - vwap

    # BUY: precio bajo VWAP + RSI en zona de sobreventa
    if deviation < -band and rsi < rsi_low:
        return {
            "strategy":  "vwap",
            "direction": "BUY",
            "signal":    "BUY",
            "score":     2,
            "deviation": round(deviation, 4),
            "vwap_pos":  "lower",
        }

    # SELL: precio sobre VWAP + RSI en zona de sobrecompra
    if deviation > band and rsi > rsi_high:
        return {
            "strategy":  "vwap",
            "direction": "SELL",
            "signal":    "SELL",
            "score":     2,
            "deviation": round(deviation, 4),
            "vwap_pos":  "upper",
        }

    return None