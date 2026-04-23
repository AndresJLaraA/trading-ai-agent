def calculate_risk(df, signal: dict, risk_config: dict) -> dict | None:
    row    = df.iloc[-1]
    entry  = row["close"]
    atr    = row["atr"]
    volatility_pct = atr / entry

    atr_mult   = risk_config.get("atr_mult",   1.5)
    tp_min_pct = volatility_pct * risk_config.get("vol_factor", 1.2)
    min_rr     = risk_config.get("min_rr", 1.2)

    direction = signal.get("direction", "BUY")
    strategy  = signal.get("strategy", "")

    # Multiplicadores por estrategia
    if strategy == "vwap":
        sl_mult, tp_mult = 1.0, 1.5
    elif strategy == "momentum":
        sl_mult, tp_mult = 0.8, 1.2
    else:
        # orb, smc y default
        sl_mult, tp_mult = atr_mult, atr_mult * 2

    if direction == "BUY":
        stop = entry - atr * sl_mult
        tp   = entry + atr * tp_mult
    else:  # SELL
        stop = entry + atr * sl_mult
        tp   = entry - atr * tp_mult

    # Validar que el movimiento esperado supera el mínimo
    move_pct = abs(tp - entry) / entry
    rr = abs(tp - entry) / abs(entry - stop)

    # DEBUG (puedes quitar luego)
    print(f"DEBUG → move_pct: {move_pct:.4f}, rr: {rr:.2f}")

    if move_pct < tp_min_pct:
        return None
    if rr < min_rr:
        return None

    return {
        "entry":     round(entry, 2),
        "stop":      round(stop,  2),
        "tp":        round(tp,    2),
        "rr":        round(rr,    2),
        "direction": direction,
    }