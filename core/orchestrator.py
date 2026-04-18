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

def _interval_to_minutes(interval: str) -> int:
    if interval.endswith("h"):
        return int(interval.replace("h", "")) * 60
    return int(interval.replace("m", ""))

def run():
    for symbol in CONFIG["symbols"]:
        for interval in CONFIG["intervals"]:
            df = get_data(symbol, interval)
            if df is None:
                continue

            df = compute_indicators(df, CONFIG["logic"])

            s1 = orb_signal(df)      if CONFIG["strategies"]["orb"]["enabled"]      else None
            s2 = vwap_signal(df)     if CONFIG["strategies"]["vwap"]["enabled"]      else None
            s3 = momentum_signal(df) if CONFIG["strategies"]["momentum"]["enabled"]  else None
            s4 = smc_signal(df, CONFIG["logic"]) if CONFIG["strategies"].get("smc", {}).get("enabled") else None

            signals = [s for s in [s1, s2, s3, s4] if s]

            best = aggregate_signals(signals)
            if not best:
                continue

            risk = calculate_risk(df, best, CONFIG["risk"])
            if not risk:
                continue

            send_alert(symbol, interval, best, risk)