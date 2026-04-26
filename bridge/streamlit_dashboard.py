# bridge/streamlit_dashboard.py
"""
Trading AI Agents — Investment Floor Dashboard
Tema: piso de bolsa de inversión, estilo terminal financiero retro-futurista.
Correr: streamlit run bridge/streamlit_dashboard.py
"""
import time
import orjson
from datetime import datetime, timezone
from pathlib import Path
import streamlit as st

STATE_FILE = Path(__file__).parent.parent / ".vscode" / \
    "pixel-agents" / "agents_state.json"
REFRESH_SEC = 5

st.set_page_config(
    page_title="Trading Floor — AI Agents",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Orbitron:wght@400;700;900&family=DM+Mono:wght@300;400;500&display=swap');
:root {
    --bg:#040810;--panel:#080f1a;--border:#0d2137;
    --green:#00ff88;--red:#ff3060;--yellow:#ffd200;
    --blue:#00b4ff;--purple:#b06cff;--orange:#ff7d00;
    --dim:#1a3050;--text:#c8dff0;--subtext:#4a6880;
}
html,body,[data-testid="stAppViewContainer"]{
    background:var(--bg)!important;color:var(--text)!important;
    font-family:'DM Mono',monospace!important;
}
[data-testid="stAppViewContainer"]::before{
    content:'';position:fixed;inset:0;pointer-events:none;z-index:9999;
    background:repeating-linear-gradient(0deg,transparent,transparent 3px,
    rgba(0,180,255,.018) 3px,rgba(0,180,255,.018) 4px);
}
.floor-title{
    font-family:'Orbitron',monospace;font-size:22px;font-weight:900;
    color:var(--green);letter-spacing:4px;text-transform:uppercase;
    text-shadow:0 0 20px rgba(0,255,136,.5),0 0 40px rgba(0,255,136,.2);
}
.floor-sub{
    font-family:'Share Tech Mono',monospace;font-size:11px;
    color:var(--subtext);letter-spacing:3px;margin-top:2px;
}
.stat-box{
    background:var(--panel);border:1px solid var(--border);
    border-radius:2px;padding:12px 16px;position:relative;overflow:hidden;
    margin-bottom:0;
}
.stat-box::before{
    content:'';position:absolute;top:0;left:0;right:0;height:1px;
    background:var(--accent,var(--green));box-shadow:0 0 8px var(--accent,var(--green));
}
.stat-label{
    font-family:'Share Tech Mono',monospace;font-size:9px;
    color:var(--subtext);letter-spacing:2px;text-transform:uppercase;margin-bottom:4px;
}
.stat-value{
    font-family:'Orbitron',monospace;font-size:18px;font-weight:700;
    color:var(--accent,var(--green));
}
.stat-value.buy{color:var(--green);text-shadow:0 0 10px rgba(0,255,136,.4);}
.stat-value.sell{color:var(--red);text-shadow:0 0 10px rgba(255,48,96,.4);}
.section-hdr{
    font-family:'Orbitron',monospace;font-size:9px;font-weight:700;
    letter-spacing:3px;color:var(--subtext);text-transform:uppercase;
    border-bottom:1px solid var(--border);padding-bottom:6px;
    margin-bottom:12px;margin-top:20px;
}
.agent-card{
    background:var(--panel);border:1px solid var(--border);
    border-radius:2px;padding:14px;margin-bottom:10px;
    position:relative;overflow:hidden;
}
.agent-card.abuy{
    border-color:rgba(0,255,136,.35);
    background:linear-gradient(135deg,#080f1a 60%,rgba(0,255,136,.04));
}
.agent-card.asell{
    border-color:rgba(255,48,96,.35);
    background:linear-gradient(135deg,#080f1a 60%,rgba(255,48,96,.04));
}
.agent-card::before{
    content:'';position:absolute;top:0;left:0;width:3px;height:100%;
    background:var(--ac,var(--dim));box-shadow:0 0 8px var(--ac,transparent);
}
.agent-name{
    font-family:'Orbitron',monospace;font-size:10px;font-weight:700;
    letter-spacing:2px;color:var(--text);
}
.agent-role{font-family:'Share Tech Mono',monospace;font-size:9px;color:var(--subtext);}
.spill{
    display:inline-block;font-family:'Orbitron',monospace;font-size:9px;
    font-weight:700;padding:2px 8px;border-radius:1px;letter-spacing:1px;
}
.sb{background:rgba(0,255,136,.15);color:var(--green);border:1px solid rgba(0,255,136,.3);}
.ss{background:rgba(255,48,96,.15);color:var(--red);border:1px solid rgba(255,48,96,.3);}
.si{background:rgba(74,104,128,.15);color:var(--subtext);border:1px solid var(--border);}
.sw{background:rgba(255,210,0,.1);color:var(--yellow);border:1px solid rgba(255,210,0,.3);}
.bar-wrap{background:var(--dim);border-radius:1px;height:3px;margin-top:8px;overflow:hidden;}
.bar{height:100%;border-radius:1px;}
.risk-grid{
    display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:8px;
    margin-top:10px;padding-top:10px;border-top:1px solid var(--border);
}
.rl{font-family:'Share Tech Mono',monospace;font-size:8px;color:var(--subtext);
    letter-spacing:1px;text-transform:uppercase;}
.rv{font-family:'Orbitron',monospace;font-size:12px;font-weight:700;margin-top:2px;}
.alert-banner{
    background:linear-gradient(90deg,rgba(0,255,136,.08),transparent);
    border:1px solid rgba(0,255,136,.3);border-radius:2px;
    padding:12px 16px;margin-bottom:16px;
    font-family:'Share Tech Mono',monospace;font-size:11px;
    display:flex;align-items:center;gap:12px;flex-wrap:wrap;
}
.alert-banner.sell{
    background:linear-gradient(90deg,rgba(255,48,96,.08),transparent);
    border-color:rgba(255,48,96,.3);
}
.adot{width:8px;height:8px;border-radius:50%;background:var(--green);
      box-shadow:0 0 8px var(--green);animation:blink 1s ease-in-out infinite;flex-shrink:0;}
.adot.sell{background:var(--red);box-shadow:0 0 8px var(--red);}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.3}}
.log-row{
    font-family:'Share Tech Mono',monospace;font-size:10px;
    padding:7px 12px;border-bottom:1px solid var(--border);
    display:flex;gap:12px;align-items:center;
}
.log-row:last-child{border-bottom:none;}
.lts{color:var(--subtext);min-width:65px;}
.lsy{color:var(--blue);min-width:90px;font-weight:700;}
.lsg.buy{color:var(--green);}
.lsg.sell{color:var(--red);}
.ldt{color:var(--subtext);flex:1;}
#MainMenu,footer,header{visibility:hidden;}
[data-testid="stToolbar"]{display:none;}
.stDivider{border-color:var(--border)!important;}
</style>
""", unsafe_allow_html=True)

# ── Constantes ────────────────────────────────────────────────────────────────
AGENT_META = {
    "orb":        ("ORB",  "Opening Range Breakout", "#ffd200"),
    "vwap":       ("VWAP", "Mean Reversion Analyst", "#00b4ff"),
    "momentum":   ("MOM",  "Momentum Scalper",       "#ff7d00"),
    "smc":        ("SMC",  "Smart Money Concepts",   "#b06cff"),
    "aggregator": ("AGGR", "Signal Aggregator",      "#00ff88"),
}


# ── Helpers ───────────────────────────────────────────────────────────────────
def load_state() -> dict | None:
    if not STATE_FILE.exists():
        return None
    try:
        return orjson.loads(STATE_FILE.read_bytes())
    except (orjson.JSONDecodeError, OSError):
        return None


def fmt_price(v) -> str:
    return f"${v:,.2f}" if v is not None else "—"


def fmt_rr(v) -> str:
    return f"{v:.2f}" if v is not None else "—"


def age_str(ts: str) -> str:
    try:
        dt = datetime.fromisoformat(ts)
        s = int((datetime.now(timezone.utc) - dt).total_seconds())
        return f"{s}s" if s < 60 else f"{s//60}m {s % 60}s"
    except Exception:
        return "—"


def sig_class(sig) -> str:
    return "buy" if sig == "BUY" else "sell" if sig == "SELL" else "idle"


def pill_cls(sig) -> str:
    if sig == "BUY":
        return "sb"
    if sig == "SELL":
        return "ss"
    if sig == "WATCH":
        return "sw"
    return "si"


def bar_col(sig) -> str:
    return "#00ff88" if sig == "BUY" else "#ff3060" if sig == "SELL" else "#1a3050"


def card_cls(sig) -> str:
    return "agent-card abuy" if sig == "BUY" else "agent-card asell" if sig == "SELL" else "agent-card"


def ac_col(name: str, sig) -> str:
    if sig == "BUY":
        return "#00ff88"
    if sig == "SELL":
        return "#ff3060"
    return AGENT_META.get(name, ("", "", "#1a3050"))[2]


def render_card(ch: dict, name: str) -> None:
    m = ch.get("metrics", {})
    signal = m.get("signal")
    score = int(m.get("score", 0))
    entry = m.get("entry")
    stop = m.get("stop")
    tp = m.get("tp")
    rr = m.get("rr")

    short, role, _ = AGENT_META.get(name, (name.upper(), name, "#1a3050"))
    ac = ac_col(name, signal)
    pct = min(100, score * 25)

    risk_html = ""
    if entry is not None:
        risk_html = f"""
        <div class="risk-grid">
            <div><div class="rl">ENTRY</div>
                 <div class="rv" style="color:#c8dff0">{fmt_price(entry)}</div></div>
            <div><div class="rl">STOP</div>
                 <div class="rv" style="color:#ff3060">{fmt_price(stop)}</div></div>
            <div><div class="rl">TARGET</div>
                 <div class="rv" style="color:#00ff88">{fmt_price(tp)}</div></div>
            <div><div class="rl">R:R</div>
                 <div class="rv" style="color:#ffd200">{fmt_rr(rr)}</div></div>
        </div>"""

    st.markdown(f"""
    <div class="{card_cls(signal)}" style="--ac:{ac}">
        <div style="display:flex;justify-content:space-between;align-items:flex-start">
            <div>
                <div class="agent-name">{short}</div>
                <div class="agent-role">{role}</div>
            </div>
            <div style="text-align:right">
                <span class="spill {pill_cls(signal)}">{signal or "IDLE"}</span>
                <div style="font-family:'Share Tech Mono';font-size:9px;
                            color:var(--subtext);margin-top:4px">score {score}</div>
            </div>
        </div>
        <div class="bar-wrap">
            <div class="bar" style="width:{pct}%;background:{bar_col(signal)};
                 box-shadow:0 0 6px {bar_col(signal)}"></div>
        </div>
        {risk_html}
    </div>""", unsafe_allow_html=True)


# ── Session state ─────────────────────────────────────────────────────────────
if "signal_log" not in st.session_state:
    st.session_state.signal_log = []

# ── Cargar estado ─────────────────────────────────────────────────────────────
state = load_state()

# ── Header ────────────────────────────────────────────────────────────────────
hc1, hc2 = st.columns([3, 1])
with hc1:
    st.markdown('<div class="floor-title">⬡ TRADING FLOOR</div>',
                unsafe_allow_html=True)
    st.markdown('<div class="floor-sub">AI MULTI-AGENT SIGNAL INTELLIGENCE · PAPER TRADING MODE</div>',
                unsafe_allow_html=True)
with hc2:
    st.markdown(f"""
    <div style="text-align:right;font-family:'Share Tech Mono';font-size:10px;
                color:var(--subtext);padding-top:8px;letter-spacing:1px">
        {datetime.now().strftime('%Y-%m-%d')}<br>
        <span style="font-size:14px;color:var(--blue)">{datetime.now().strftime('%H:%M:%S')}</span><br>
        AUTO-REFRESH {REFRESH_SEC}s
    </div>""", unsafe_allow_html=True)

st.markdown("---")

# ── Sin datos ─────────────────────────────────────────────────────────────────
if state is None or state.get("empty_reason"):
    reason = state.get("empty_reason", "no_data") if state else "no_state"
    st.markdown(f"""
    <div style="text-align:center;padding:80px;font-family:'Share Tech Mono';
                font-size:12px;color:var(--subtext);letter-spacing:2px">
        ◌ AWAITING MARKET DATA · {reason.upper()}<br><br>
        <span style="font-size:10px">Corre python main.py para iniciar el pipeline</span>
    </div>""", unsafe_allow_html=True)

else:
    symbol = state.get("symbol", "—")
    interval = state.get("interval", "—")
    price = state.get("price")
    best_signal = state.get("best_signal")
    best_strat = state.get("best_strategy", "—") or "—"
    risk_valid = state.get("risk_valid", False)
    cycle_ts = state.get("cycle_ts", "")
    chars = state.get("characters", {})

    # ── Registrar señal válida en historial ───────────────────────────────────
    if best_signal and risk_valid:
        last = st.session_state.signal_log[-1] if st.session_state.signal_log else {}
        if last.get("ts") != cycle_ts:
            agg_m = chars.get("aggregator", {}).get("metrics", {})
            st.session_state.signal_log.append({
                "ts":       cycle_ts,
                "symbol":   symbol,
                "interval": interval,
                "signal":   best_signal,
                "strategy": best_strat,
                "entry":    agg_m.get("entry"),
                "stop":     agg_m.get("stop"),
                "tp":       agg_m.get("tp"),
                "rr":       agg_m.get("rr"),
            })
            st.session_state.signal_log = st.session_state.signal_log[-20:]

    # ── Alert banner ──────────────────────────────────────────────────────────
    if best_signal and risk_valid:
        is_sell = best_signal == "SELL"
        bc = "sell" if is_sell else ""
        sig_col = "#ff3060" if is_sell else "#00ff88"
        agg_m = chars.get("aggregator", {}).get("metrics", {})
        st.markdown(f"""
        <div class="alert-banner {bc}">
            <div class="adot {bc}"></div>
            <span style="color:{sig_col};font-family:'Orbitron';font-size:11px;
                         font-weight:700;letter-spacing:2px">{best_signal} SIGNAL ACTIVE</span>
            <span style="color:var(--subtext)">·</span>
            <span style="color:var(--text)">{symbol} [{interval}]</span>
            <span style="color:var(--subtext)">·</span>
            <span>via <span style="color:var(--blue)">{best_strat.upper()}</span></span>
            <span style="color:var(--subtext)">·</span>
            <span>
                E:{fmt_price(agg_m.get('entry'))} &nbsp;
                SL:{fmt_price(agg_m.get('stop'))} &nbsp;
                TP:{fmt_price(agg_m.get('tp'))} &nbsp;
                R:R <span style="color:var(--yellow)">{fmt_rr(agg_m.get('rr'))}</span>
            </span>
            <span style="margin-left:auto;color:var(--subtext)">{age_str(cycle_ts)} ago</span>
        </div>""", unsafe_allow_html=True)

    # ── Stats row ─────────────────────────────────────────────────────────────
    s1, s2, s3, s4, s5, s6 = st.columns(6)
    sig_col2 = "#00ff88" if best_signal == "BUY" else "#ff3060" if best_signal == "SELL" else "#4a6880"
    risk_col = "#00ff88" if risk_valid else "#ff3060"

    s1.markdown(
        f'<div class="stat-box" style="--accent:#00b4ff"><div class="stat-label">SYMBOL</div><div class="stat-value">{symbol}</div></div>', unsafe_allow_html=True)
    s2.markdown(
        f'<div class="stat-box" style="--accent:#4a6880"><div class="stat-label">TIMEFRAME</div><div class="stat-value" style="color:var(--text)">{interval}</div></div>', unsafe_allow_html=True)
    s3.markdown(
        f'<div class="stat-box" style="--accent:#ffd200"><div class="stat-label">PRICE</div><div class="stat-value" style="color:var(--yellow)">{fmt_price(price)}</div></div>', unsafe_allow_html=True)
    s4.markdown(
        f'<div class="stat-box" style="--accent:{sig_col2}"><div class="stat-label">BEST SIGNAL</div><div class="stat-value {sig_class(best_signal)}">{best_signal or "NONE"}</div></div>', unsafe_allow_html=True)
    s5.markdown(
        f'<div class="stat-box" style="--accent:{risk_col}"><div class="stat-label">RISK ENGINE</div><div class="stat-value" style="color:{risk_col}">{"VALID" if risk_valid else "REJECTED"}</div></div>', unsafe_allow_html=True)
    s6.markdown(
        f'<div class="stat-box" style="--accent:#4a6880"><div class="stat-label">LAST CYCLE</div><div class="stat-value" style="color:var(--subtext);font-size:14px">{age_str(cycle_ts)}</div></div>', unsafe_allow_html=True)

    # ── Strategy agents ───────────────────────────────────────────────────────
    st.markdown('<div class="section-hdr">◈ AGENT FLOOR — STRATEGY LAYER</div>',
                unsafe_allow_html=True)
    strategy_names = ["orb", "vwap", "momentum", "smc"]
    cols = st.columns(4)
    for i, name in enumerate(strategy_names):
        with cols[i]:
            render_card(chars.get(name, {}), name)

    # ── Aggregator + consensus ────────────────────────────────────────────────
    st.markdown('<div class="section-hdr">◈ SIGNAL AGGREGATOR · CONSENSUS</div>',
                unsafe_allow_html=True)
    ac1, ac2 = st.columns([2, 1])
    with ac1:
        render_card(chars.get("aggregator", {}), "aggregator")
    with ac2:
        active_n = sum(
            1 for n in strategy_names
            if chars.get(n, {}).get("metrics", {}).get("active", False)
        )
        buy_n = sum(1 for n in strategy_names if chars.get(
            n, {}).get("metrics", {}).get("signal") == "BUY")
        sell_n = sum(1 for n in strategy_names if chars.get(
            n, {}).get("metrics", {}).get("signal") == "SELL")
        st.markdown(f"""
        <div class="stat-box" style="--accent:#00b4ff;margin-bottom:8px">
            <div class="stat-label">ACTIVE STRATEGIES</div>
            <div class="stat-value" style="color:var(--blue)">{active_n} / 4</div>
        </div>
        <div class="stat-box" style="--accent:#00ff88;margin-bottom:8px">
            <div class="stat-label">BUY CONSENSUS</div>
            <div class="stat-value buy">{buy_n} / 4</div>
        </div>
        <div class="stat-box" style="--accent:#ff3060">
            <div class="stat-label">SELL CONSENSUS</div>
            <div class="stat-value sell">{sell_n} / 4</div>
        </div>""", unsafe_allow_html=True)

    # ── Signal log ────────────────────────────────────────────────────────────
    st.markdown('<div class="section-hdr">◈ SIGNAL LOG — SESSION HISTORY</div>',
                unsafe_allow_html=True)

    if st.session_state.signal_log:
        rows_html = ""
        for row in reversed(st.session_state.signal_log):
            try:
                ts_str = datetime.fromisoformat(row["ts"]).strftime("%H:%M:%S")
            except Exception:
                ts_str = "—"
            sc = sig_class(row["signal"])
            rows_html += f"""
            <div class="log-row">
                <span class="lts">{ts_str}</span>
                <span class="lsy">{row['symbol']} [{row['interval']}]</span>
                <span class="lsg {sc}">{row['signal']}</span>
                <span class="ldt">
                    via {row.get('strategy', '—').upper()} ·
                    E:{fmt_price(row.get('entry'))} ·
                    SL:{fmt_price(row.get('stop'))} ·
                    TP:{fmt_price(row.get('tp'))} ·
                    R:R {fmt_rr(row.get('rr'))}
                </span>
            </div>"""
        st.markdown(
            f'<div style="background:var(--panel);border:1px solid var(--border);border-radius:2px">'
            f'{rows_html}</div>',
            unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background:var(--panel);border:1px solid var(--border);border-radius:2px;
                    padding:20px;text-align:center;font-family:'Share Tech Mono';
                    font-size:10px;color:var(--subtext);letter-spacing:2px">
            ◌ NO SIGNALS RECORDED THIS SESSION
        </div>""", unsafe_allow_html=True)

    # ── JSON debug ────────────────────────────────────────────────────────────
    with st.expander("◈ RAW STATE — JSON"):
        st.json(state)

# ── Status bar ────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="position:fixed;bottom:0;left:0;right:0;background:var(--panel);
            border-top:1px solid var(--border);padding:4px 16px;
            font-family:'Share Tech Mono';font-size:9px;color:var(--subtext);
            letter-spacing:1px;display:flex;justify-content:space-between;z-index:1000">
    <span>TRADING AI AGENT · v0.8.0-beta · PAPER TRADING MODE</span>
    <span>AUTO-REFRESH {REFRESH_SEC}s · {datetime.now().strftime('%H:%M:%S')} UTC</span>
</div>""", unsafe_allow_html=True)

time.sleep(REFRESH_SEC)
st.rerun()
