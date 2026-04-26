CONFIG = {

    # =========================
    # Universe
    # =========================
    "symbols": [
        "BTC-USD",
        "SPY",
        "NXAUUSD",
        # "TSLA",
    ],

    "intervals": [
        "5m",
        "15m",
        "4h",
    ],


    # =========================
    # Strategy Modules
    # =========================
    "strategies": {

        "orb": {
            "enabled": True,
            "orb_minutes": 30,
        },

        "vwap": {
            "enabled": True,
        },

        "momentum": {
            "enabled": True,
        },

        "smc": {
            "enabled": True,
        },
    },


    # =========================
    # Signal Logic Filters
    # =========================
    "logic": {

        # Trend filters
        "adx_min": 20,

        # Momentum filters
        "rsi_low": 42,
        "rsi_high": 68,

        # Relative volume filter
        "rvol_min": 1.5,

        # VWAP dynamic deviation band
        # 0.50 = muy selectivo
        # 0.30 = balanceado (actual)
        # 0.20 = más sensible
        "vwap_band_mult": 0.20,

        # Quality Agent threshold
        # 0.50 más permisivo
        # 0.60 balanceado (actual)
        # 0.70 más exigente
        "entry_score_threshold": 0.50,
    },


    # =========================
    # Quality Agent
    # =========================
    "quality": {

        "enabled": True,

        "weights": {
            "vwap": 0.40,
            "momentum": 0.30,
            "structure": 0.30,
        },

        # score buckets
        "grade_a": 0.80,
        "grade_b": 0.60,

        # optional volatility regime
        "high_vol_atr_pct": 0.02,
    },


    # =========================
    # Risk Engine
    # =========================
    "risk": {

        "atr_mult": 1.5,

        "min_rr": 1.2,

        "vol_factor": 1.2,

        # Guía calibración tp_min_pct:
        # 0.0015 = 0.15% más permisivo
        # 0.0025 = 0.25% balanceado (actual)
        # 0.0050 = 0.50% más selectivo
        # mínimo movimiento esperado (0.25%) para validar reward potencial
        # evita trades con TP insignificante ("noise trades")
        # futura mejora: hacerlo dinámico según ATR/regime
        "tp_min_pct": 0.0025,
    },

    # =========================
    # System / Runtime
    # =========================
    "system": {

        # Development diagnostics
        "debug": False,
        # Audit
        "audit_quality": False,
        "audit_vwap": False,
        "audit_risk": False,
        "audit_orchestrator": False,
        # future:
        "paper_trading": True,
        "save_trade_journal": False,
        "pixel_agents": True,
    },
}
