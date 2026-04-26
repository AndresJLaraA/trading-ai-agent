# bridge/jsonl_bridge.py
"""
Fake JSONL Bridge — Trading AI Agent → Pixel Agents (VS Code)
Simula sesiones de Claude Code escribiendo JSONL en ~/.claude/projects/
Cada agente de trading aparece como un personaje animado en Pixel Agents.

Activar en core/config.py:
    "system": { "pixel_agents": True }

NO modificar agentes existentes. NO mezclar con bridge/writer.py.
"""
import os
import uuid
import orjson
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

# ── Path del proyecto codificado (Claude Code convention) ─────────────────────
_CWD = str(Path.cwd())
_ENCODED = _CWD.replace("/", "-")
_CLAUDE_DIR = Path.home() / ".claude" / "projects" / _ENCODED

# ── Mapeo agente → tool_use que activa cada animación en Pixel Agents ─────────
# Pixel Agents detecta: bash → corriendo, read → leyendo, write → escribiendo
AGENT_TOOL: dict[str, str] = {
    "data":        "bash",    # descarga datos → corre
    "indicator":   "read",    # procesa df    → lee
    "orb":         "write",   # señal ORB     → escribe
    "vwap":        "write",   # señal VWAP    → escribe
    "momentum":    "write",   # señal momentum→ escribe
    "smc":         "read",    # WATCH/idle    → lee
    "quality":     "bash",    # grade A/B/C   → corre
    "risk":        "write",   # SL/TP/RR      → escribe
    "aggregator":  "write",   # best signal   → escribe
}

# ── Descripción legible por agente (aparece en speech bubble) ─────────────────
AGENT_LABEL: dict[str, str] = {
    "data":       "Descargando datos de mercado…",
    "indicator":  "Calculando indicadores técnicos…",
    "orb":        "Evaluando Opening Range Breakout…",
    "vwap":       "Evaluando VWAP Reversion…",
    "momentum":   "Evaluando Momentum Scalping…",
    "smc":        "Observando estructura institucional…",
    "quality":    "Scoring calidad de señal…",
    "risk":       "Calculando SL / TP / R:R…",
    "aggregator": "Seleccionando mejor señal…",
}


def _ts() -> str:
    """Timestamp ISO 8601 UTC — formato exacto de Claude Code."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _line(obj: dict) -> bytes:
    """Serializa una línea JSONL."""
    return orjson.dumps(obj) + b"\n"


def _tool_use_record(tool_name: str, label: str, session_id: str) -> bytes:
    """
    Línea assistant con tool_use — activa la animación del personaje.
    Formato real de Claude Code confirmado en transcripts.
    """
    tool_id = f"toolu_{uuid.uuid4().hex[:24]}"
    return _line({
        "type": "assistant",
        "sessionId": session_id,
        "message": {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id":   tool_id,
                    "name": tool_name,
                    "input": {"command": label},
                }
            ],
        },
        "timestamp": _ts(),
    })


def _tool_result_record(tool_name: str, output: str, session_id: str) -> bytes:
    """
    Línea user con tool_result — completa el ciclo tool_use → result.
    Sin esto Pixel Agents queda en animación activa indefinidamente.
    """
    tool_id = f"toolu_{uuid.uuid4().hex[:24]}"
    return _line({
        "type": "user",
        "sessionId": session_id,
        "message": {
            "role": "user",
            "content": [
                {
                    "type":        "tool_result",
                    "tool_use_id": tool_id,
                    "content":     output,
                }
            ],
        },
        "timestamp": _ts(),
    })


def _turn_duration_record(session_id: str) -> bytes:
    """
    Señal de idle — Pixel Agents vuelve al personaje en reposo.
    subtype: turn_duration es la señal más confiable (~98% según CLAUDE.md).
    """
    return _line({
        "type":      "system",
        "subtype":   "turn_duration",
        "sessionId": session_id,
        "durationMs": 1000,
        "timestamp": _ts(),
    })


class JsonlBridge:
    """
    Escribe JSONL falsos en ~/.claude/projects/{encoded-path}/
    Un archivo por agente — Pixel Agents spawna un personaje por archivo.

    Uso:
        bridge = JsonlBridge()
        bridge.write_cycle(strategy_results, aggregated, risk, quality, symbol, interval)
    """

    def __init__(self) -> None:
        _CLAUDE_DIR.mkdir(parents=True, exist_ok=True)
        # UUID fijo por agente — mismo personaje entre ciclos
        self._session_ids: dict[str, str] = {
            name: str(uuid.uuid5(uuid.NAMESPACE_DNS, f"trading-{name}"))
            for name in AGENT_TOOL
        }
        self._jsonl_files: dict[str, Path] = {
            name: _CLAUDE_DIR / f"{sid}.jsonl"
            for name, sid in self._session_ids.items()
        }
        self._ensure_files()

    def _ensure_files(self) -> None:
        """Crea los JSONL con mensaje inicial si no existen."""
        for name, path in self._jsonl_files.items():
            if not path.exists():
                sid = self._session_ids[name]
                init = _line({
                    "type": "user",
                    "sessionId": sid,
                    "message": {
                        "role":    "user",
                        "content": f"[Trading AI Agent] {name.upper()} iniciado",
                    },
                    "timestamp": _ts(),
                })
                path.write_bytes(init)

    def _write_agent(
        self,
        name:   str,
        active: bool,
        output: str,
    ) -> None:
        """
        Escribe 3 líneas por agente:
        1. tool_use  → activa animación
        2. tool_result → completa el ciclo
        3. turn_duration → vuelve a idle (solo si no activo)
        """
        sid = self._session_ids[name]
        tool = AGENT_TOOL.get(name, "bash")
        path = self._jsonl_files[name]

        with path.open("ab") as f:
            f.write(_tool_use_record(tool, output, sid))
            f.write(_tool_result_record(tool, output, sid))
            if not active:
                f.write(_turn_duration_record(sid))

    def write_cycle(
        self,
        strategy_results: dict[str, dict | None],
        aggregated:       dict | None,
        risk_output:      dict | None,
        quality_output:   dict | None,
        symbol:           str,
        interval:         str,
    ) -> None:
        """
        Punto único de escritura — llamado desde orchestrator.py.
        Refleja el estado real de cada agente en el ciclo actual.
        """
        # ── Data Agent — siempre activo ───────────────────────────────────────
        self._write_agent(
            "data",
            active=True,
            output=f"OHLCV {symbol} {interval} descargado",
        )

        # ── Indicator Agent — siempre activo ─────────────────────────────────
        self._write_agent(
            "indicator",
            active=True,
            output=f"EMA/RSI/ATR/ADX/RVOL/VWAP calculados · {symbol} {interval}",
        )

        # ── Strategy Agents ───────────────────────────────────────────────────
        for name in ("orb", "vwap", "momentum", "smc"):
            result = strategy_results.get(name)
            if result:
                sig = result.get("signal", "—")
                scr = result.get("score", 0)
                out = f"{sig} score:{scr} · {symbol} {interval}"
                active = sig not in (None, "WATCH")
            else:
                out = f"Sin señal · {symbol} {interval}"
                active = False
            self._write_agent(name, active=active, output=out)

        # ── Quality Agent ─────────────────────────────────────────────────────
        if quality_output:
            grade = quality_output.get("quality_grade", "—")
            score = quality_output.get("score", 0)
            out = f"Grade:{grade} score:{score:.2f} · {symbol} {interval}"
            self._write_agent("quality", active=True, output=out)
        else:
            self._write_agent("quality", active=False,
                              output=f"Sin quality · {symbol} {interval}")

        # ── Risk Agent ────────────────────────────────────────────────────────
        if risk_output:
            sl = risk_output.get("stop",  "—")
            tp = risk_output.get("tp",    "—")
            rr = risk_output.get("rr",    "—")
            out = f"SL:{sl} TP:{tp} R:R:{rr} · {symbol} {interval}"
            self._write_agent("risk", active=True, output=out)
        else:
            self._write_agent("risk", active=False,
                              output=f"Señal descartada · {symbol} {interval}")

        # ── Signal Aggregator ─────────────────────────────────────────────────
        if aggregated:
            sig = aggregated.get("signal", "—")
            str = aggregated.get("strategy", "—")
            out = f"BEST:{sig} via {str} · {symbol} {interval}"
            self._write_agent("aggregator", active=True, output=out)
        else:
            self._write_agent("aggregator", active=False,
                              output=f"Sin consenso · {symbol} {interval}")
