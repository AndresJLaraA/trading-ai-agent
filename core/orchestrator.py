from agents.data_agent import get_data
from agents.indicator_agent import compute_indicators
from agents.strategies.orb_agent import orb_signal
from agents.strategies.vwap_agent import vwap_signal
from agents.strategies.momentum_agent import momentum_signal
from agents.signal_aggregator import aggregate_signals
from agents.risk_agent import calculate_risk
from agents.alert_agent import send_alert
from agents.smc_agent import smc_signal
from core.config import CONFIG
from bridge.writer import BridgeWriter
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

# Inicialización única del bridge
bridge = BridgeWriter()


def run():
    for symbol in CONFIG["symbols"]:
        for interval in CONFIG["intervals"]:

            # === 1. DATA ===
            df = get_data(symbol, interval)
            if df is None or df.empty:
                bridge.write_empty_cycle(symbol, interval, reason="no_data")
                continue

            # === 2. INDICATORS ===
            df = compute_indicators(df, CONFIG["logic"])

            # === 3. STRATEGIES ===
            s1 = orb_signal(df)      if CONFIG["strategies"]["orb"]["enabled"]                    else None
            s2 = vwap_signal(df)     if CONFIG["strategies"]["vwap"]["enabled"]                   else None
            s3 = momentum_signal(df) if CONFIG["strategies"]["momentum"]["enabled"]               else None
            s4 = smc_signal(df, CONFIG["logic"]) if CONFIG["strategies"].get("smc", {}).get("enabled") else None

            strategy_results = {
                "orb":      s1,
                "vwap":     s2,
                "momentum": s3,
                "smc":      s4,
            }

            # === 4. MARKET SNAPSHOT (siempre disponible) ===
            last_price = float(df["close"].iloc[-1])
            timestamp  = datetime.now(timezone.utc).isoformat()

            # === 5. AGGREGATION ===
            signals = [s for s in strategy_results.values() if s]

            if not signals:
                # Bridge con todos idle — el dashboard muestra el estado real
                bridge.write(
                    strategy_results=strategy_results,
                    aggregated=None,
                    risk_output=None,
                    symbol=symbol,
                    interval=interval,
                    price=last_price,
                    timestamp=timestamp,
                )
                continue

            best = aggregate_signals(signals)
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
                continue

            # === 6. RISK ===
            risk = calculate_risk(df, best, CONFIG["risk"])

            # === 7. BRIDGE (SIEMPRE, con el estado real del ciclo) ===
            bridge.write(
                strategy_results=strategy_results,
                aggregated=best,
                risk_output=risk,        # puede ser None si no pasó validación
                symbol=symbol,
                interval=interval,
                price=last_price,
                timestamp=timestamp,
            )

            # === 8. ALERT (solo si riesgo válido) ===
            if not risk:
                logger.info("⚠️  %s %s — señal descartada por risk_agent", symbol, interval)
                continue

            send_alert(symbol, interval, best, risk)
            logger.info("📊 %s %s → %s | %s", symbol, interval, best["signal"], best["strategy"])