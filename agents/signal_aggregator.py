def aggregate_signals(signals: list) -> dict | None:
    if not signals:
        return None

    # Filtra solo señales accionables (excluye WATCH de london_open)
    actionable = [s for s in signals if s.get("signal") not in (None, "WATCH")]
    if not actionable:
        return None

    # Prioriza por score, desempata por orden de llegada
    return sorted(actionable, key=lambda x: x.get("score", 1), reverse=True)[0]