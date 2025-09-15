## HERFOO_TRADES - Breeze API Single-Position Bot

This project buys one stock at a time (single position) using ICICIdirect Breeze API, based on simple rules: buy low and sell high.

### 1) Install
```bash
pip install -r requirements.txt
```

### 2) Configure
- Put your credentials in `creds.config` (JSON)
- Put rules in `rules.config` (JSON)
- Put the symbol mapping in `stocksymbol.txt` as `DISPLAY|BREEZE_CODE` (e.g., `RELIANCE|RELIANCE`). Left side is for display/3rd-party quotes, right side is Breeze stock_code.

### 3) Run (recommended)
```bash
python -u trader.py
```
This unified loop continuously buys and sells according to rules and re-enters when conditions allow.

### Notes
- Archived older scripts are in `archive/` (`buy.py`, `monitor.py`). Prefer `trader.py`.
- Orders are MARKET; execution price from Breeze is recorded when available.
- State is tracked in `state.json` with file locking.
- Market-hours guard prevents orders outside configured hours.
