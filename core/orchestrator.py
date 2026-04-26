from agents.data_agent import get_data
from agents.indicator_agent import compute_indicators

from agents.strategies.orb_agent import orb_signal
from agents.strategies.vwap_agent import vwap_signal
from agents.strategies.momentum_agent import momentum_signal

from agents.signal_aggregator import aggregate_signals
from agents.quality_agent import quality_filter
from agents.risk_agent import calculate_risk
from agents.alert_agent import send_alert
from agents.smc_agent import smc_signal

from core.config import CONFIG
from bridge.writer import BridgeWriter
from bridge.jsonl_bridge import JsonlBridge

from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

bridge = BridgeWriter()
jsonl_bridge = JsonlBridge() if CONFIG["system"].get("pixel_agents") else None


def run():

    for symbol in CONFIG["symbols"]:

        # ==================================
        # MTF BUFFER por símbolo
        # ==================================
        mtf_buffer = {}

        for interval in CONFIG["intervals"]:

            # ==================================
            # 1. DATA
            # ==================================
            df = get_data(symbol, interval)

            if df is None or df.empty:
                bridge.write_empty_cycle(
                    symbol,
                    interval,
                    reason="no_data"
                )
                continue

            # ==================================
            # 2. INDICATORS
            # ==================================
            df = compute_indicators(
                df,
                CONFIG["logic"]
            )

            # ==================================
            # 3. STRATEGIES
            # ==================================
            s1 = (
                orb_signal(df)
                if CONFIG["strategies"]["orb"]["enabled"]
                else None
            )

            s2 = (
                vwap_signal(
                    df,
                    CONFIG["logic"]
                )
                if CONFIG["strategies"]["vwap"]["enabled"]
                else None
            )

            s3 = (
                momentum_signal(df)
                if CONFIG["strategies"]["momentum"]["enabled"]
                else None
            )

            s4 = (
                smc_signal(df, CONFIG["logic"])
                if CONFIG["strategies"].get("smc", {}).get("enabled")
                else None
            )

            strategy_results = {
                "orb": s1,
                "vwap": s2,
                "momentum": s3,
                "smc": s4,
            }

            # ==================================
            # 4. MARKET SNAPSHOT
            # ==================================
            last_price = float(df["close"].iloc[-1])

            timestamp = datetime.now(
                timezone.utc
            ).isoformat()

            # ==================================
            # 5. AGGREGATION
            # ==================================

            signals = [
                s for s in strategy_results.values()
                if s
            ]

            # DEBUG auditoría señales
            if (
                CONFIG["system"]["debug"]
                and CONFIG["system"]["audit_orchestrator"]
            ):
                logger.debug(
                    "%s %s signals=%s",
                    symbol,
                    interval,
                    len(signals)
                )

            if not signals:

                bridge.write(
                    strategy_results=strategy_results,
                    aggregated=None,
                    risk_output=None,
                    symbol=symbol,
                    interval=interval,
                    price=last_price,
                    timestamp=timestamp,
                )

                logger.info(
                    "⚪ %s %s — sin señales activas",
                    symbol,
                    interval
                )

                continue

            best = aggregate_signals(signals)

            # DEBUG agregador
            if (
                CONFIG["system"]["debug"]
                and CONFIG["system"]["audit_orchestrator"]
            ):
                logger.debug(
                    "Best signal: %s",
                    best
                )

            if not best:

                bridge.write(
                    strategy_results=strategy_results,
                    aggregated=None,
                    risk_output=None,
                    symbol=symbol,
                    interval=interval,
                    price=last_price,
                    timestamp=timestamp,
                )

                logger.info(
                    "⚠️ %s %s — sin consenso aggregator",
                    symbol,
                    interval
                )

                continue

            # ==================================
            # 5.1 QUALITY FILTER (Penalty Mode)
            # ==================================

            entry_ok, entry_meta = quality_filter(
                df=df,
                signal=best,
                logic=CONFIG["logic"]
            )

            # Antes: hard reject
            # Ahora: penalizar convicción, no matar señal

            if not entry_ok:

                penalty = entry_meta.get(
                    "score",
                    0.50
                )

                # piso mínimo para no destruir señal
                adjusted_score = best["score"] * max(
                    0.65,
                    penalty
                )

                best["score"] = round(
                    adjusted_score,
                    2
                )

                if (
                    CONFIG["system"]["debug"]
                    and CONFIG["system"]["audit_quality"]
                ):
                    logger.info(
                        "⚠️ %s %s — quality penalty aplicada | new score=%.2f",
                        symbol,
                        interval,
                        best["score"]
                    )

            # Guardar metadata para MTF y feedback futuro
            best["quality_meta"] = entry_meta

            # ==================================
            # 6. RISK
            # ==================================
            risk = calculate_risk(
                df,
                best,
                CONFIG["risk"]
            )

            if not risk:
                logger.info(
                    "⚠️ %s %s — descartado por risk_agent",
                    symbol,
                    interval
                )
                continue

            # ==================================
            # 7. ATOMIC WRITE TO MTF BUFFER
            # (solo sobreviven señales completas)
            # ==================================
            mtf_buffer[interval] = {
                "best": best,
                "df": df,
                "strategy_results": strategy_results,
                "price": last_price,
                "timestamp": timestamp,

                # nuevo diagnóstico híbrido
                "entry_meta": entry_meta,

                # señal validada por riesgo
                "risk": risk,
            }

            # ==================================
            # 8. BRIDGE (NO TOCAR)
            # ==================================
            bridge.write(
                strategy_results=strategy_results,
                aggregated=best,
                risk_output=risk,
                symbol=symbol,
                interval=interval,
                price=last_price,
                timestamp=timestamp,
            )

        # ==================================
        # 9. MULTI-TIMEFRAME HIERARCHY
        # ==================================

        TIMEFRAME_PRIORITY = {
            "1m": 1,
            "5m": 2,
            "15m": 3,
            "1h": 4,
            "4h": 5,
            "1d": 6,
        }

        valid_signals = [
            (interval, data)
            for interval, data in mtf_buffer.items()
            if data.get("risk") and data.get("best")
        ]

        if not valid_signals:
            continue

        # Higher Timeframe first
        valid_signals.sort(
            key=lambda x:
                TIMEFRAME_PRIORITY.get(
                    x[0],
                    0
                ),
            reverse=True
        )

        # HTF Dominante
        chosen_interval, chosen_data = valid_signals[0]

        chosen_direction = chosen_data["best"]["signal"]

        # conflictos con LTF
        conflicts = [
            (interval, data)
            for interval, data in valid_signals[1:]
            if data["best"]["signal"] != chosen_direction
        ]

        if conflicts:
            logger.info(
                "⚠️ %s — conflicto MTF, usando HTF (%s)",
                symbol,
                chosen_interval
            )

        # ==================================
        # 10. FINAL EXECUTION
        # ==================================

        send_alert(
            symbol,
            chosen_interval,
            chosen_data["best"],
            chosen_data["risk"]
        )

        logger.info(
            "📊 %s %s → %s | %s | entry_score %.2f (HTF DOMINANTE)",
            symbol,
            chosen_interval,
            chosen_data["best"]["signal"],
            chosen_data["best"]["strategy"],
            chosen_data["entry_meta"]["score"],
        )
