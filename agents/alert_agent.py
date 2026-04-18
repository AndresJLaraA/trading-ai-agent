import requests
import os

PHASE_LABEL = {
    "london_open":      "🕐 London Open — Marcando rango",
    "london_expansion": "🕑 London Expansion — Setup activo",
    "ny_open":          "🕒 NY Open — Alta probabilidad",
}

def build_message(symbol: str, interval: str, signal: dict, risk: dict) -> str:
    phase    = signal.get("phase", "")
    strategy = signal.get("strategy", "").upper()
    direction = risk.get("direction", "BUY")
    arrow    = "🟢 BUY" if direction == "BUY" else "🔴 SELL"

    header = PHASE_LABEL.get(phase, f"📡 {strategy}")

    lines = [
        f"<b>{header}</b>",
        f"<b>{arrow} — {symbol} [{interval}]</b>",
        "",
        f"Estrategia : <code>{strategy}</code>",
    ]

    if phase:
        lines.append(f"Fase       : <code>{phase}</code>")

    if signal.get("signal") == "WATCH":
        lines += [
            "",
            f"Session High : <code>{signal.get('session_high', '—'):.2f}</code>",
            f"Session Low  : <code>{signal.get('session_low',  '—'):.2f}</code>",
            "",
            "<i>Sin entrada — esperando expansión</i>",
        ]
    else:
        lines += [
            "",
            f"Entry : <code>{risk['entry']:.2f}</code>",
            f"Stop  : <code>{risk['stop']:.2f}</code>",
            f"TP    : <code>{risk['tp']:.2f}</code>",
            f"R:R   : <code>{risk['rr']:.2f}</code>",
        ]

        if signal.get("sweep"):
            lines.append(f"Sweep : <code>{signal['sweep']}</code>")
        if signal.get("vwap_pos"):
            lines.append(f"VWAP  : <code>{signal['vwap_pos']}</code>")

    return "\n".join(lines)


def send_alert(symbol: str, interval: str, signal: dict, risk: dict) -> None:
    msg     = build_message(symbol, interval, signal, risk)
    token   = os.getenv("TG_TOKEN")
    chat_id = os.getenv("TG_CHAT_ID")

    if not token or not chat_id:
        print(msg)
        return

    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={
                "chat_id":    chat_id,
                "text":       msg,
                "parse_mode": "HTML",
            },
            timeout=10,
        )
        resp.raise_for_status()

    except requests.exceptions.RequestException as e:
        print(f"[alert_agent] Error enviando alerta {symbol}: {e}")
        print(msg)