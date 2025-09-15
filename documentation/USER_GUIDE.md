## HERFOO_TRADES - User Guide

This guide explains, in simple terms, how to set up and use the trading bot. It also lists every feature and configuration option so you can control the bot’s behavior without reading code.

### What this bot does
- Buys and sells exactly one stock at a time per running trader.
- You can run multiple traders in parallel (one per symbol) with a small orchestrator if desired.
- It reads live prices from public sources first (yfinance/NSE) and falls back to ICICIdirect Breeze quotes only when needed.
- All real orders are placed through ICICIdirect Breeze (MARKET orders only; price is omitted by design).
- It records the execution price returned by Breeze and tracks your total profit so far.
- It refuses to place orders outside market hours.

### Files you will see
- `creds.config`: Your ICICI Breeze credentials (API key, secret, session token).
- `rules.config`: All settings that control buying, selling, safety, and market hours.
- `stocksymbol.txt`: The stock you want to trade, one line as `DISPLAY|BREEZE_CODE` (e.g., `RELIANCE|RELIANCE`).
- `state.json`: Saves current position, last sell price, and total profit so far.
- `trader.py`: The main program. Runs the buy/sell/rebuy loop continuously.
- `archive/`: Older scripts kept for reference (not needed in normal use).

### One-time setup
1) Install Python 3.9+ and run:
```bash
pip install -r requirements.txt
```
2) Fill `creds.config` like this:
```json
{
  "api_key": "YOUR_API_KEY",
  "api_secret": "YOUR_API_SECRET",
  "session_token": "YOUR_SESSION_TOKEN"
}
```
3) Put your symbol mapping in `stocksymbol.txt`:
```
RELIANCE|RELIANCE
```
- Left side (`RELIANCE`) is used for public price feeds.
- Right side (`RELIANCE`) is the exact ICICI Breeze stock_code.

### How to run
In a terminal:
```bash
python -u trader.py
```
You will see messages like LTP (last traded price), buy/sell signals, and realized profit after sells.

### Features explained (in plain English)
- Single position rule: The bot can hold only one position at a time. It won’t buy again until it has sold the current position.
- Immediate first buy (optional): You can tell the bot to buy the first time it sees a price, so you don’t wait for a pattern.
- Buy on price drop: The bot watches the recent highest price and buys if the price drops by either:
  - A percentage you set, or
  - A fixed rupee amount you set.
- Buy below average (SMA) (optional): Instead of recent high logic, you can choose to buy when price falls below its recent moving average by a small percentage.
- Take profit: The bot will sell when either:
  - Your rupee profit per share reaches your target, or
  - Your percent profit reaches your target.
- Stop loss: The bot sells if the loss reaches your percent limit.
- Re-entry rule: After a sell, if the price drops below your last sell price and you have no position, the bot can buy again immediately.
- Market-hours guard: The bot will not place any orders when the market is closed.
- Safe MARKET orders: Orders are sent as MARKET (no price field) to avoid exchange rejections.
- Price sources with fallback: The bot tries public feeds first (yfinance, then NSE) and uses Breeze quotes if those are unavailable.
- Robust logs: The bot prints simple ASCII logs so they work reliably on Windows terminals.

### All configuration options (rules.config)
Put these in `rules.config` as JSON. You can keep only the ones you care about; defaults will apply for others.

- Exchange and quantity
  - "exchange_code": "NSE" — Which exchange to trade on.
  - "quantity": 1 — Number of shares per order.

- Buy triggers
  - "buy_immediate_on_start": true/false — Buy right away the first time a price comes in.
  - "buy_mode": "drop_from_high" or "below_sma"
    - drop_from_high: Buy when price drops from the recent high.
    - below_sma: Buy when price is below its moving average by a percentage.
  - "buy_drop_pct": 0.01 — Percent drop from recent high required to buy (1% = 0.01).
  - "buy_drop_abs": 0.2 — Rupee drop from recent high required to buy.
  - "sma_window": 20 — Number of recent prices to compute SMA (only if below_sma mode).
  - "sma_drop_pct": 0.003 — Percent below SMA required to buy (0.3% = 0.003).

- Sell triggers
  - "take_profit_abs": 0.1 — Rupees of profit per share to sell (e.g., 0.1 means sell after 10 paise gain).
  - "take_profit_pct": 0.02 — Percent profit to sell (2% = 0.02).
  - "stop_loss_pct": 0.01 — Percent loss to sell (1% = 0.01).

- Price polling and sources
  - "poll_interval_sec": 5 — Seconds between checks.
  - "quote_source": "auto" | "yf" | "breeze" — Where to get prices from.
    - auto/yf: Use yfinance, fall back to NSE, then Breeze.
    - breeze: Use Breeze quotes and historical short window.

- Market hours (India time)
  - "market_tz": "Asia/Kolkata" — Time zone.
  - "market_open": "09:15" — Market open time.
  - "market_close": "15:30" — Market close time.
  - "market_buffer_min": 1 — Minutes before close to stop placing new orders.

- Debugging
  - "debug": true/false — Print extra details to see why buys or sells are/aren’t triggered.
  - "min_warmup_samples": 3 — The bot waits for this many prices before using some buy modes (unless immediate buy is on).

### How profits are tracked
- After each sell, the bot calculates profit for that trade using the sell price and the recorded average buy price, updates `total_pnl` in `state.json`, and prints both the trade profit and the running total.
- `last_sell_price` is also stored to help with the “re-enter lower than last sell” rule.

### Running multiple symbols (parallel)
- `stocksymbol.txt` currently holds one line. To trade multiple symbols at once, run one `trader.py` per symbol in separate terminals or create a small `multi_trader.py` to launch them.
- Best practice for multiple symbols:
  - Keep one line per symbol like `RELIANCE|RELIANCE`, `TCS|TCS`.
  - Start each trader with its own symbol argument and its own state file (namespace).
  - Stagger start times by a few seconds to spread out API usage.

### Safety reminders
- Make sure your ICICI credentials are correct and production-enabled.
- Use small quantity in the beginning.
- Monitor logs until you’re confident in behavior.
- Avoid Unicode symbols in logs on Windows terminals to prevent encoding issues.

### Troubleshooting tips
- No buy? Enable debug in `rules.config` and look for lines showing recent high, SMA, and thresholds. Consider lowering thresholds or using `buy_immediate_on_start`.
- No prices? The bot will try yfinance, NSE, then Breeze. If all fail, it will print clear messages.
- Orders not visible? Double-check Breeze credentials and that `exchange_code`, `BREEZE_CODE`, and market hours are correct.

### What’s next (AI/ML)
- You can add a small ML model to score “buy/hold” based on recent prices and indicators. Keep it behind a config switch so if the model is missing or misbehaves, the bot falls back to rules.

If you need, we can extend this guide with multi-symbol orchestration and an example ML integration walkthrough.
