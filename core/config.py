CONFIG = {
    "symbols": ["SPY", "NVDA", "TSLA"],
    "intervals": ["5m", "15m", "4h"],

    "strategies": {
        "orb":      {"enabled": True, "orb_minutes": 30},
        "vwap":     {"enabled": True},
        "momentum": {"enabled": True},
        "smc":      {"enabled": True},
    },

    "logic": {
        "adx_min":  20,
        "rsi_low":  40,
        "rsi_high": 70,
        "rvol_min": 1.5,
    },

    "risk": {
        "atr_mult": 1.5,
        "min_rr": 1.2,
        "vol_factor": 1.2,
    }
}