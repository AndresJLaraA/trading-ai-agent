import logging
from core.config import CONFIG

logger = logging.getLogger(__name__)


def vwap_signal(
    df,
    logic: dict = None
) -> dict | None:

    if logic is None:
        logic = {}

    if len(df) < 2:
        return None

    last = df.iloc[-1]

    close = last.get("close")
    vwap = last.get("vwap")
    atr = last.get("atr")
    rsi = last.get("rsi")

    if any(v is None for v in [close, vwap, atr, rsi]):
        return None

    # =========================
    # Dynamic signal thresholds
    # =========================

    rsi_low = logic.get("rsi_low", 42)
    rsi_high = logic.get("rsi_high", 68)

    band = atr * logic.get(
        "vwap_band_mult",
        0.20
    )

    deviation = close - vwap

    # =========================
    # DEBUG AUDIT (solo si activado)
    # =========================
    if (
        CONFIG["system"]["debug"]
        and CONFIG["system"]["audit_vwap"]
    ):
        logger.debug(
            "VWAP close=%.2f vwap=%.2f dev=%.2f band=%.2f rsi=%.2f",
            close,
            vwap,
            deviation,
            band,
            rsi
        )

    # =========================
    # BUY setup
    # =========================
    if deviation < -band and rsi < rsi_low:
        return {
            "strategy": "vwap",
            "direction": "BUY",
            "signal": "BUY",
            "score": 2,
            "deviation": round(deviation, 4),
            "vwap_pos": "lower"
        }

    # =========================
    # SELL setup
    # =========================
    if deviation > band and rsi > rsi_high:
        return {
            "strategy": "vwap",
            "direction": "SELL",
            "signal": "SELL",
            "score": 2,
            "deviation": round(deviation, 4),
            "vwap_pos": "upper"
        }

    return None
