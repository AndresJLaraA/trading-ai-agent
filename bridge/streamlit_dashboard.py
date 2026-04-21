# bridge/streamlit_dashboard.py
"""
Dashboard Streamlit — Trading AI Agents
Lee agents_state.json generado por BridgeWriter.

Correr: streamlit run bridge/streamlit_dashboard.py
"""
import time
import orjson
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

# ── Config ────────────────────────────────────────────────────────────────────

STATE_FILE = Path(__file__).parent.parent / ".vscode" / \
    "pixel-agents" / "agents_state.json"
REFRESH_SEC = 5

st.set_page_config(
    page_title="Trading AI Agents",
    page_icon="📈",
    layout="wide",
)

# ── Constantes ────────────────────────────────────────────────────────────────

DIRECTION_EMOJI: dict[str | None, str] = {
    "BUY":  "🟢",
    "SELL": "🔴",
    None:   "⚪",
}

SCORE_COLOR: dict[int, str] = {
    4: "#2ecc71",
    3: "#27ae60",
    2: "#f39c12",
    1: "#e67e22",
    0: "#95a5a6",
}

# ── Helpers ───────────────────────────────────────────────────────────────────


def load_state() -> dict | None:
    """
    Lee y parsea agents_state.json.
    cache_data con ttl evita releer el archivo en cada rerun
    si el contenido no cambió.
    """
    if not STATE_FILE.exists():
        return None
    try:
        return orjson.loads(STATE_FILE.read_bytes())
    except (orjson.JSONDecodeError, OSError):
        return None


def fmt_price(v: float | None) -> str:
    return f"${v:,.2f}" if v is not None else "—"


def fmt_rr(v: float | None) -> str:
    return f"{v:.1f}:1" if v is not None else "—"


def age_str(ts: str) -> str:
    try:
        dt = datetime.fromisoformat(ts)
        s = int((datetime.now(timezone.utc) - dt).total_seconds())
        return f"{s}s ago" if s < 60 else f"{s // 60}m ago"
    except Exception:
        return ts


def _card_bg(active: bool) -> str:
    return "#0d1f12" if active else "#0d1117"


def render_agent_card(col, name: str, ch: dict) -> None:
    """Renderiza la card de un agente en la columna dada."""
    m = ch.get("metrics", {})
    direction = m.get("direction")
    # string real: "BUY"/"SELL"/"WATCH"/None
    signal = m.get("signal")
    score = int(m.get("score", 0))
    active = m.get("active", False)

    # Campos reales del risk_agent: stop / tp / rr  (no stop_loss / take_profit / rr_ratio)
    entry = m.get("entry")
    stop = m.get("stop")
    tp = m.get("tp")
    rr = m.get("rr")

    emoji = DIRECTION_EMOJI.get(direction, "⚪")
    s_color = SCORE_COLOR.get(score, "#95a5a6")

    with col:
        st.markdown(
            f"""<div style='
                border: 1.5px solid {s_color};
                border-radius: 10px;
                padding: 12px 16px;
                margin-bottom: 12px;
                background: {_card_bg(active)};
            '>
            <b style='font-size:16px'>{emoji} {ch.get("name", name)}</b>
            <span style='
                float: right;
                background: {s_color};
                color: #000;
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 12px;
                font-weight: 700;
            '>score {score}</span>
            <br/>
            <small style='color:#888'>
                {ch.get("label", "—")} · {ch.get("state", "idle")}
            </small>
            </div>""",
            unsafe_allow_html=True,
        )

        # Métricas de riesgo — solo si el risk_agent procesó esta señal
        if entry is not None:
            r1, r2, r3 = st.columns(3)
            r1.metric("Entry", fmt_price(entry))
            r2.metric("SL",    fmt_price(stop))   # campo real: stop
            r3.metric("TP",    fmt_price(tp))      # campo real: tp
            st.caption(f"R:R {fmt_rr(rr)}")        # campo real: rr


# ── Layout principal ──────────────────────────────────────────────────────────

st.title("📊 Trading AI Agents — Live Dashboard")

placeholder = st.empty()
status_bar = st.empty()

# Loop de refresco — st.rerun() recarga el script completo,
# placeholder.container() evita acumulación de elementos en pantalla.
state = load_state()

with placeholder.container():
    if state is None:
        st.warning(f"Esperando `{STATE_FILE}` — corre el orquestador primero.")
    elif state.get("empty_reason"):
        st.info(
            f"⏳ Ciclo vacío — `{state['empty_reason']}` · {state.get('symbol', '')} {state.get('interval', '')}")
    else:
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Símbolo",      state.get("symbol",   "—"))
        c2.metric("Intervalo",    state.get("interval", "—"))
        c3.metric("Precio",       fmt_price(state.get("price")))
        c4.metric("Mejor señal",  state.get("best_signal", "—") or "—")
        c5.metric("Ciclo",        age_str(state.get("cycle_ts", "")))

        risk_ok = state.get("risk_valid", False)
        st.caption(
            f"{'✅' if risk_ok else '⚠️'} Risk agent: "
            f"{'válido' if risk_ok else 'descartado'} · "
            f"Estrategia ganadora: **{state.get('best_strategy', '—') or '—'}**"
        )
        st.divider()

        chars = state.get("characters", {})
        if not chars:
            st.info("Sin agentes activos en este ciclo.")
        else:
            cols = st.columns(3)
            for i, (name, ch) in enumerate(chars.items()):
                render_agent_card(cols[i % 3], name, ch)

        st.divider()
        with st.expander("JSON completo del ciclo"):
            st.json(state)

status_bar.caption(
    f"⟳ Auto-refresh cada {REFRESH_SEC}s · "
    f"{datetime.now().strftime('%H:%M:%S')}"
)

# Rerun controlado — fuera del while, una sola vez
time.sleep(REFRESH_SEC)
st.rerun()
