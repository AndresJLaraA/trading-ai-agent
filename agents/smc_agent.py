import pandas as pd
from datetime import time

class MarketStructure:

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    def detect_swings(self, window=3):
        df = self.df
        df["pivot_high"] = df["high"].where(
            df["high"] == df["high"].rolling(window * 2 + 1, center=True).max()
        )
        df["pivot_low"] = df["low"].where(
            df["low"] == df["low"].rolling(window * 2 + 1, center=True).min()
        )
        self.df = df
        return df

    def classify_structure(self):
        df = self.df
        last_high = last_low = None
        structure = []

        for _, row in df.iterrows():
            label = None
            if not pd.isna(row.get("pivot_high", float("nan"))):
                if last_high is not None:
                    label = "HH" if row["pivot_high"] > last_high else "LH"
                last_high = row["pivot_high"]
            elif not pd.isna(row.get("pivot_low", float("nan"))):
                if last_low is not None:
                    label = "HL" if row["pivot_low"] > last_low else "LL"
                last_low = row["pivot_low"]
            structure.append(label)

        df["structure"] = structure
        self.df = df
        return df

    def detect_bos(self):
        df = self.df
        df["bos_up"]   = df["close"] > df["pivot_high"].shift(1)
        df["bos_down"] = df["close"] < df["pivot_low"].shift(1)
        self.df = df
        return df


def get_session(timestamp) -> str | None:
    """Retorna la sesión activa en hora UK (UTC+1 en verano)."""
    t = timestamp.time()
    if time(8, 0) <= t < time(10, 0):
        return "london_open"
    if time(10, 0) <= t < time(12, 0):
        return "london_expansion"
    if time(14, 30) <= t < time(16, 0):
        return "ny_open"
    return None


def get_vwap_position(close: float, vwap: float, atr: float) -> str:
    """Clasifica precio respecto al VWAP usando ATR como banda."""
    band = atr * 0.5
    if close < vwap - band:
        return "lower"
    if close > vwap + band:
        return "upper"
    return "mid"


def smc_signal(df: pd.DataFrame, logic: dict) -> dict | None:
    """
    Evalúa señal SMC en la última vela.
    Retorna dict con fase, dirección y metadata, o None si no hay setup.
    """
    ms = MarketStructure(df)
    ms.detect_swings()
    ms.classify_structure()
    ms.detect_bos()
    df = ms.df

    if len(df) < 5:
        return None

    last   = df.iloc[-1]
    prev   = df.iloc[-2]
    ts     = last.name

    session = get_session(ts)
    if session is None:
        return None

    # --- Fase 1: London Open — solo marcar rango, no operar ---
    if session == "london_open":
        return {
            "strategy":  "smc",
            "phase":     "london_open",
            "direction": None,
            "signal":    "WATCH",
            "note":      "Marcando rango institucional — sin entrada",
            "session_high": df.loc[df.index.time >= time(8, 0), "high"].max(),
            "session_low":  df.loc[df.index.time >= time(8, 0), "low"].min(),
        }

    vwap_pos = get_vwap_position(last["close"], last["vwap"], last["atr"])

    # Sweep: barre el mínimo previo pero cierra por encima (trampa bajista)
    is_sweep_low  = last["low"] < prev["low"] and last["close"] > prev["low"]
    # Sweep: barre el máximo previo pero cierra por debajo (trampa alcista)
    is_sweep_high = last["high"] > prev["high"] and last["close"] < prev["high"]

    # BOS confirmado por detect_bos
    bos_up   = bool(last.get("bos_up",   False))
    bos_down = bool(last.get("bos_down", False))

    # Último LH/LL en estructura
    last_lh = df[df["structure"] == "LH"]["pivot_high"].dropna().iloc[-1] \
              if "LH" in df["structure"].values else None
    last_hl = df[df["structure"] == "HL"]["pivot_low"].dropna().iloc[-1] \
              if "HL" in df["structure"].values else None

    structure_break_up   = last_lh is not None and last["close"] > last_lh
    structure_break_down = last_hl is not None and last["close"] < last_hl

    adx_ok = last.get("adx", 0) >= logic.get("adx_min", 20)

    # --- Fase 2: London Expansion ---
    if session == "london_expansion":
        if is_sweep_low and vwap_pos == "lower" and structure_break_up and adx_ok:
            return {
                "strategy":  "smc",
                "phase":     "london_expansion",
                "direction": "BUY",
                "signal":    "BUY",
                "sweep":     "low_swept",
                "vwap_pos":  vwap_pos,
                "bos_up":    bos_up,
                "score":     3,
            }
        if is_sweep_high and vwap_pos == "upper" and structure_break_down and adx_ok:
            return {
                "strategy":  "smc",
                "phase":     "london_expansion",
                "direction": "SELL",
                "signal":    "SELL",
                "sweep":     "high_swept",
                "vwap_pos":  vwap_pos,
                "bos_down":  bos_down,
                "score":     3,
            }

    # --- Fase 3: NY Open — mismo setup, mayor peso por volumen ---
    if session == "ny_open":
        if is_sweep_low and vwap_pos == "lower" and structure_break_up and adx_ok:
            return {
                "strategy":  "smc",
                "phase":     "ny_open",
                "direction": "BUY",
                "signal":    "BUY",
                "sweep":     "low_swept",
                "vwap_pos":  vwap_pos,
                "bos_up":    bos_up,
                "score":     4,
            }
        if is_sweep_high and vwap_pos == "upper" and structure_break_down and adx_ok:
            return {
                "strategy":  "smc",
                "phase":     "ny_open",
                "direction": "SELL",
                "signal":    "SELL",
                "sweep":     "high_swept",
                "vwap_pos":  vwap_pos,
                "bos_down":  bos_down,
                "score":     4,
            }

    return None