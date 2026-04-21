# bridge/writer.py
"""
Bridge entre Trading AI Agent (GitHub Actions) y Pixel Agents (VS Code).
Ajustado al formato real de salida de cada agente (v1.0).

Formatos reales confirmados:
  strategy_agent → {"strategy", "direction", "signal", "score", ...extras}
  risk_agent     → {"entry", "stop", "tp", "rr", "direction"}
  aggregator     → retorna el dict del agente ganador tal cual (mismo formato)
"""
import os
import orjson
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ── Constantes de mapeo ───────────────────────────────────────────────────────

STRATEGY_SPRITES: dict[str, str] = {
    "orb":        "warrior",   # Opening Range Breakout → rompe barreras
    "vwap":       "mage",      # VWAP Reversion → equilibrio/precio justo
    "momentum":   "rogue",     # Momentum Scalping → rápido, oportunista
    "smc":        "paladin",   # Smart Money Concepts → institucional
    "aggregator": "oracle",    # Signal Aggregator → decide la señal final
    "risk":       "monk",      # Risk Agent → disciplina SL/TP
}

# signal string real → estado del personaje
SIGNAL_TO_STATE: dict[str | None, str] = {
    "BUY":   "running",
    "SELL":  "dancing",
    "WATCH": "idle",
    None:    "idle",
}

# score → escala visual del personaje
SCORE_TO_SCALE: dict[int, float] = {
    4: 1.00,   # SMC NY Open
    3: 0.85,   # SMC London Expansion
    2: 0.65,   # ORB / VWAP / Momentum base
    1: 0.45,
    0: 0.30,
}

_EMPTY_RISK: dict[str, Any] = {
    "entry": None, "stop": None, "tp": None, "rr": None,
}


# ── Builder ───────────────────────────────────────────────────────────────────

def _build_character(
    agent_name: str,
    strategy_dict: dict[str, Any] | None,
    risk_dict: dict[str, Any] | None,
    symbol: str,
    interval: str,
) -> dict[str, Any]:
    """
    Construye el personaje Pixel Agents desde los dicts reales del sistema.

    strategy_dict: salida directa de orb_signal / vwap_signal / etc.
    risk_dict:     salida directa de calculate_risk() — campos: entry/stop/tp/rr
    """
    s = strategy_dict or {}
    r = risk_dict or _EMPTY_RISK

    # Campos del strategy dict (formato real confirmado)
    strategy = s.get("strategy",  agent_name)
    direction = s.get("direction")           # "BUY" | "SELL" | None
    signal = s.get("signal")              # "BUY" | "SELL" | "WATCH" | None
    score = int(s.get("score", 0))
    active = signal not in (None, "WATCH")

    # Campos del risk dict (nombres reales: stop, tp, rr — no stop_loss/take_profit/rr_ratio)
    entry = r.get("entry")
    stop = r.get("stop")
    tp = r.get("tp")
    rr = r.get("rr")

    # Estado y escala del personaje
    state = SIGNAL_TO_STATE.get(signal, "idle") if active else "idle"
    scale = SCORE_TO_SCALE.get(score, 0.30)

    # Label legible para Pixel Agents
    if active and direction:
        label = f"{direction} s{score}"
    elif signal == "WATCH":
        label = "WATCH"
    else:
        label = "—"

    # Tooltip con métricas operativas
    parts: list[str] = [f"{symbol} {interval}"]
    if entry is not None:
        parts.append(f"E:{entry:.2f}")
    if stop is not None:
        parts.append(f"SL:{stop:.2f}")
    if tp is not None:
        parts.append(f"TP:{tp:.2f}")
    if rr is not None:
        parts.append(f"R:R {rr:.1f}")

    return {
        "id":     agent_name,
        "name":   strategy,
        "sprite": STRATEGY_SPRITES.get(strategy, STRATEGY_SPRITES.get(agent_name, "warrior")),
        "state":  state,
        "scale":  scale,
        "label":  label,
        "tooltip": " | ".join(parts),
        "metrics": {
            # strategy layer
            "signal":    signal,
            "direction": direction,
            "score":     score,
            "active":    active,
            # risk layer (nombres reales del risk_agent)
            "entry": entry,
            "stop":  stop,
            "tp":    tp,
            "rr":    rr,
        },
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


# ── BridgeWriter ──────────────────────────────────────────────────────────────

class BridgeWriter:
    """
    Escribe agents_state.json en .vscode/pixel-agents/ al final de cada ciclo.
    Siempre ejecuta — refleja el estado real aunque no haya señal activa.
    """

    def __init__(self, output_dir: str = ".vscode/pixel-agents") -> None:
        self.out = Path(output_dir)
        self.state_file = self.out / "agents_state.json"
        self.out.mkdir(parents=True, exist_ok=True)
        self._write_config_once()

    # ── API pública ───────────────────────────────────────────────────────────

    def write(
        self,
        strategy_results: dict[str, dict | None],  # {"orb": dict|None, ...}
        aggregated:  dict | None,                  # señal ganadora del aggregator
        risk_output: dict | None,                  # salida de calculate_risk()
        symbol:   str = "",
        interval: str = "",
        price:    float | None = None,
        timestamp: str | None = None,
    ) -> None:
        """
        Punto único de escritura. Llamado desde orchestrator.py en cada ciclo,
        independientemente de si hay señal activa o no.
        """
        characters: dict[str, Any] = {}

        # Las 4 estrategias — risk solo aplica a la ganadora
        for name, result in strategy_results.items():
            is_winner = (
                aggregated is not None
                and result is not None
                and result.get("strategy") == aggregated.get("strategy")
            )
            characters[name] = _build_character(
                agent_name=name,
                strategy_dict=result,
                risk_dict=risk_output if is_winner else None,
                symbol=symbol,
                interval=interval,
            )

        # Agente aggregator — muestra la señal ganadora + riesgo
        characters["aggregator"] = _build_character(
            agent_name="aggregator",
            strategy_dict={**(aggregated or {}), "strategy": "aggregator"},
            risk_dict=risk_output,
            symbol=symbol,
            interval=interval,
        )

        state: dict[str, Any] = {
            "version":     "1.0",
            "run_id":      os.environ.get("GITHUB_RUN_ID", "local"),
            "symbol":      symbol,
            "interval":    interval,
            "price":       price,
            "cycle_ts":    timestamp or datetime.now(timezone.utc).isoformat(),
            "best_signal": aggregated.get("signal") if aggregated else None,
            "best_strategy": aggregated.get("strategy") if aggregated else None,
            "risk_valid":  risk_output is not None,
            "characters":  characters,
        }

        self.state_file.write_bytes(
            orjson.dumps(state, option=orjson.OPT_INDENT_2 |
                         orjson.OPT_SERIALIZE_NUMPY)
        )

    def write_empty_cycle(
        self,
        symbol: str,
        interval: str,
        reason: str = "no_data",
    ) -> None:
        """
        Escribe un estado vacío cuando el data agent no retorna datos.
        Permite que el dashboard distinga 'sin datos' de 'sin señal'.
        """
        state: dict[str, Any] = {
            "version":       "1.0",
            "run_id":        os.environ.get("GITHUB_RUN_ID", "local"),
            "symbol":        symbol,
            "interval":      interval,
            "price":         None,
            "cycle_ts":      datetime.now(timezone.utc).isoformat(),
            "best_signal":   None,
            "best_strategy": None,
            "risk_valid":    False,
            "empty_reason":  reason,
            "characters":    {},
        }
        self.state_file.write_bytes(
            orjson.dumps(state, option=orjson.OPT_INDENT_2)
        )

    # ── Config inicial ────────────────────────────────────────────────────────

    def _write_config_once(self) -> None:
        """Genera pixel_agents_config.json solo si no existe."""
        cfg = self.out / "pixel_agents_config.json"
        if cfg.exists():
            return
        config: dict[str, Any] = {
            "version":    "1.0",
            "state_file": "agents_state.json",
            "refresh_ms": 5000,
            "sprite_map": STRATEGY_SPRITES,
            "state_animations": {
                "idle":    "stand",
                "running": "run",
                "dancing": "dance",
            },
        }
        cfg.write_bytes(orjson.dumps(config, option=orjson.OPT_INDENT_2))
