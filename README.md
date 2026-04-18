# Trading AI Agent

> Modular multi-strategy trading signal engine with real-time Telegram alerts — runs fully automated on GitHub Actions at zero infrastructure cost.

```
SPY  ▸ 5m  ▸ ORB     → BUY  @ 589.42  SL 586.10  TP 595.06  R:R 2.0
NVDA ▸ 15m ▸ SMC/NY  → BUY  @ 134.87  SL 133.20  TP 137.87  R:R 2.4
TSLA ▸ 4h  ▸ VWAP    → SELL @ 178.33  SL 180.90  TP 173.19  R:R 2.0
```

---

## What it does

Analyzes equities and ETFs across three timeframes simultaneously, calculates six technical indicators, evaluates four independent trading strategies, and dispatches entry/exit alerts to Telegram — all without executing trades automatically.

Every signal passes through a 7-layer quality filter before reaching you:

```
Market data → Indicators → Strategy signals → Aggregation → Risk validation → Alert
```

No signal leaves the system unless it has volume confirmation, trend strength, a valid R:R ratio, and sufficient price movement to cover real-world friction.

---

## Architecture

The system is built as a pipeline of single-responsibility agents:

```
trading-ai-agent/
│
├── main.py                          # Entry point
│
├── core/
│   ├── config.py                    # Central config — symbols, intervals, thresholds
│   └── orchestrator.py              # Pipeline coordinator
│
├── agents/
│   ├── data_agent.py                # OHLCV download + 1h→4h resampling
│   ├── indicator_agent.py           # EMA · RSI · ATR · ADX · RVOL · VWAP
│   ├── smc_agent.py                 # Smart Money Concepts + session detection
│   │
│   ├── strategies/
│   │   ├── orb_agent.py             # Opening Range Breakout
│   │   ├── vwap_agent.py            # VWAP Reversion
│   │   └── momentum_agent.py        # Momentum Scalping
│   │
│   ├── signal_aggregator.py         # Score-based signal selection
│   ├── risk_agent.py                # SL · TP · R:R calculation
│   └── alert_agent.py               # Telegram formatter + sender
│
└── .github/
    └── workflows/
        └── trading_bot.yml          # Cron: */5 08-16 * * 1-5
```

Adding a new strategy takes exactly three steps: create the agent file, register it in `config.py`, add it to the orchestrator pipeline. The core never changes.

---

## Strategies

### ORB — Opening Range Breakout
Captures directional breakouts of the price range formed in the first 30 minutes of market open. Only fires with volume confirmation (RVOL ≥ 1.5×) and trend strength (ADX ≥ 20) to filter false breakouts.

```python
# BUY signal
close > orb_high AND rvol >= 1.5 AND adx >= 20

# SELL signal  
close < orb_low  AND rvol >= 1.5 AND adx >= 20
```

### VWAP Reversion
Identifies overextended deviations from the session VWAP combined with RSI exhaustion. Uses ATR-based dynamic bands instead of fixed percentages — adapts automatically to each asset's volatility profile.

```python
# BUY signal
close < vwap - (atr * 0.5) AND rsi < 40

# SELL signal
close > vwap + (atr * 0.5) AND rsi > 70
```

### Momentum Scalping
Captures strong directional moves backed by institutional volume. Requires price above/below EMA20 with both ADX and RVOL confirming active trend. Filters flat or low-volume markets entirely.

```python
# BUY signal
close > ema20 AND rvol >= 1.5 AND adx >= 20
```

### SMC — Smart Money Concepts
Three-phase institutional strategy aligned with London and New York liquidity windows. Combines liquidity sweeps, VWAP positioning, and Break of Structure (BOS) confirmation.

| Phase | Time (UK) | Action | Score |
|---|---|---|---|
| London Open | 08:00–10:00 | Mark session range — no entry | WATCH |
| London Expansion | 10:00–12:00 | Trade sweep + VWAP + BOS | 3 |
| NY Open | 14:30–16:00 | Same setup, higher weight | 4 |

```python
# BUY condition
session_active AND sweep_low AND vwap_position == "lower" AND structure_break_up AND adx >= 20
```

---

## Signal Quality Pipeline

Every signal passes 7 filters before dispatch:

| Layer | Filter | What gets dropped |
|---|---|---|
| 1 | Data sufficiency | Empty or undersized DataFrames |
| 2 | Indicator validity | Null RSI / ATR / ADX / RVOL values |
| 3 | Strategy condition | Failed entry condition |
| 4 | Quality gates | ADX < 20 or RVOL < 1.5 |
| 5 | Session gate | SMC outside active windows |
| 6 | Score aggregation | All signals below the best score |
| 7 | Risk validation | TP < 2% of entry price |

---

## Risk Management

Stop Loss and Take Profit are calculated dynamically using ATR — not fixed percentages. This means the system self-adjusts to current volatility without manual recalibration.

| Strategy | SL | TP | R:R target |
|---|---|---|---|
| ORB / SMC | ATR × 1.5 | ATR × 3.0 | 1:2 |
| VWAP | ATR × 1.0 | ATR × 1.5 | 1:1.5 |
| Momentum | ATR × 0.8 | ATR × 1.2 | 1:1.5 |

---

## Indicators

| Indicator | Config | Role |
|---|---|---|
| EMA 20 | span=20 | Trend reference for momentum signals |
| EMA 200 | span=200 | Macro trend filter on 15m and 4h |
| RSI | length=14 | Exhaustion confirmation in VWAP reversion |
| ATR | length=14 | Dynamic SL/TP sizing + VWAP band width |
| ADX | length=14 | Trend strength gate — rejects ranging markets |
| RVOL | rolling=20 | Volume confirmation — rejects low-conviction moves |
| VWAP | per session | Fair value reference — resets daily |

---

## Setup

**1. Clone and install**
```bash
git clone https://github.com/youruser/trading-ai-agent.git
cd trading-ai-agent
pip install -r requirements.txt
```

**2. Configure credentials**
```bash
cp .env.example .env
# Add your TG_TOKEN and TG_CHAT_ID
```

**3. Run locally**
```bash
python main.py
```

**4. Deploy to GitHub Actions**

Add `TG_TOKEN` and `TG_CHAT_ID` to your repository's `Settings → Secrets → Actions`. The workflow runs automatically Monday–Friday, every 5 minutes between 08:00–16:59 UTC.

---

## Configuration

All parameters live in `core/config.py`. No code changes needed to adjust behavior:

```python
CONFIG = {
    "symbols":   ["SPY", "NVDA", "TSLA"],
    "intervals": ["5m", "15m", "4h"],

    "strategies": {
        "orb":      {"enabled": True, "orb_minutes": 30},
        "vwap":     {"enabled": True},
        "momentum": {"enabled": True},
        "smc":      {"enabled": True},
    },

    "logic": {
        "adx_min":  20,
        "rsi_low":  40,
        "rsi_high": 70,
        "rvol_min": 1.5,
    },

    "risk": {
        "atr_mult":   1.5,
        "tp_min_pct": 0.02,
    }
}
```

To add a symbol: append to `symbols`. To disable a strategy: set `enabled: False`. To tighten quality filters: raise `adx_min` or `rvol_min`.

---

## Dependencies

```
yfinance==1.2.0       # Market data
pandas==2.3.3         # Time series manipulation
numpy==2.2.6          # Numerical operations
pandas-ta==0.4.71b0   # Technical indicators
requests==2.32.5      # Telegram API calls
python-dotenv==1.2.2  # Local environment variables
tenacity==9.1.4       # Retry logic for alert delivery
```

---

## Extending the system

**Add a new strategy**
1. Create `agents/strategies/your_strategy.py` returning a dict with `strategy`, `direction`, `signal`, `score`
2. Add `"your_strategy": {"enabled": True}` to `config.py`
3. Import and call it in `orchestrator.py`

**Add a new symbol**
Append to the `symbols` list in `config.py`. Done.

**Add a new timeframe**
Append to `intervals` and add a `PERIOD_MAP` entry in `data_agent.py` if needed. Non-native intervals (e.g. 4h) are resampled automatically from 1h data.

**Backtest a strategy**
`vectorbt` is available in the environment. The same indicators computed live are available for historical validation without any additional dependencies.

---

## Telegram alert format

```
🕒 NY Open — Alta probabilidad
🟢 BUY — NVDA [15m]

Estrategia : SMC
Fase       : ny_open

Entry : 134.87
Stop  : 133.20
TP    : 137.87
R:R   : 2.40
Sweep : low_swept
VWAP  : lower
```

---

## Infrastructure

Zero-cost, zero-maintenance deployment on GitHub Actions:

- **Schedule**: Every 5 minutes, Monday–Friday, 08:00–16:59 UTC
- **Runtime**: ~15–25 seconds per cycle
- **Cost**: Free within GitHub's 2,000 minutes/month limit
- **Dependency caching**: pip cache cuts install time from ~60s to ~3s
- **Secrets**: Credentials stored as GitHub Secrets, never in code

---

## Design principles

**Single responsibility** — each agent does exactly one thing and exposes one function. `data_agent` downloads data. `risk_agent` calculates risk. Nothing bleeds into anything else.

**Config-driven behavior** — thresholds, symbols, intervals, and strategy toggles are all in `config.py`. Tuning the system never requires touching logic code.

**Standardized contracts** — every strategy returns the same dict shape. The aggregator, risk agent, and alert agent don't know or care which strategy fired.

**Fail gracefully** — every agent returns `None` on failure. The orchestrator skips and continues. A bad data feed for one symbol never blocks alerts for others.

**Observable** — every alert includes full context: strategy, phase, sweep type, VWAP position, all price levels. No black box.

---

## License

MIT
