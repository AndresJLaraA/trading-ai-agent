from __future__ import annotations

"""
Quality Agent
-------------
Signal quality filter + scoring layer.

No genera señales.
Evalúa calidad antes de riesgo/ejecución.

Diseñado para:
- filtering
- confluence scoring
- backtesting features
- future feedback loops
"""

import logging
from core.config import CONFIG

logger = logging.getLogger(__name__)


def quality_filter(
    df,
    signal: dict,
    logic: dict
):
    """
    Returns
    -------
    tuple:
        (entry_ok, meta)
    """

    try:

        row = df.iloc[-1]

        direction = signal.get(
            "direction",
            signal.get(
                "signal",
                "BUY"
            )
        )

        score = 0.0
        details = {}

        # ==========================
        # 1 VWAP CONFIRM (40%)
        # ==========================
        vwap_ok = False

        if "vwap" in row:

            price = row["close"]
            vwap = row["vwap"]

            if direction == "BUY":
                vwap_ok = price > vwap
            else:
                vwap_ok = price < vwap

            if vwap_ok:
                score += 0.40

        details["vwap_confirm"] = vwap_ok

        # ==========================
        # 2 MOMENTUM CONFIRM (30%)
        # ==========================
        momentum_ok = False

        if "rsi" in row:

            rsi = row["rsi"]

            if direction == "BUY":
                momentum_ok = rsi > 52
            else:
                momentum_ok = rsi < 48

            if momentum_ok:
                score += 0.30

        details["momentum_confirm"] = momentum_ok

        # ==========================
        # 3 STRUCTURE CONFIRM (30%)
        # ==========================
        structure_ok = False

        if (
            "ema_fast" in row
            and "ema_slow" in row
        ):

            if direction == "BUY":
                structure_ok = (
                    row["ema_fast"]
                    >
                    row["ema_slow"]
                )

            else:
                structure_ok = (
                    row["ema_fast"]
                    <
                    row["ema_slow"]
                )

            if structure_ok:
                score += 0.30

        details["structure_confirm"] = structure_ok

        # ==========================
        # QUALITY GRADE
        # ==========================
        if score >= 0.80:
            quality_grade = "A"

        elif score >= 0.60:
            quality_grade = "B"

        else:
            quality_grade = "C"

        # ==========================
        # VOLATILITY REGIME TAG
        # ==========================
        volatility_bucket = "normal"

        if "atr" in row:
            if row["atr"] > row["close"] * 0.02:
                volatility_bucket = "high"

        # ==========================
        # FINAL DECISION
        # ==========================
        threshold = logic.get(
            "entry_score_threshold",
            0.60
        )

        quality_ok = (
            score >= threshold
        )

        meta = {

            "score": round(score, 2),
            "threshold": threshold,

            **details,

            "quality_grade": quality_grade,

            "volatility_bucket":
                volatility_bucket,

            "regime": (
                "trend"
                if structure_ok
                else "mixed"
            ),
        }

        # ==========================
        # DEBUG AUDIT (DEV ONLY)
        # ==========================
        if (
            CONFIG["system"]["debug"]
            and CONFIG["system"]["audit_quality"]
        ):
            logger.debug(
                "QUALITY score=%.2f threshold=%.2f pass=%s grade=%s",
                score,
                threshold,
                quality_ok,
                quality_grade
            )

        return quality_ok, meta

    except Exception as e:

        logger.exception(
            "quality_filter error"
        )

        return (
            False,
            {
                "score": 0.0,
                "threshold": 0.60,
                "quality_grade": "C",
                "error": str(e)
            }
        )
