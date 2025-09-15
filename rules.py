import json
import time
from typing import Deque, Dict, Optional, Tuple
from collections import deque
from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo


class RuleEngine:
	def __init__(self, rules_path: str = "rules.config") -> None:
		with open(rules_path, "r") as f:
			cfg = json.load(f)
		self.exchange_code: str = cfg.get("exchange_code", "NSE")
		self.quantity: int = int(cfg.get("quantity", 1))
		self.buy_drop_pct: float = float(cfg.get("buy_drop_pct", 0.01))
		self.buy_drop_abs: float = float(cfg.get("buy_drop_abs", 0.0))
		self.take_profit_pct: float = float(cfg.get("take_profit_pct", 0.02))
		self.take_profit_abs: float = float(cfg.get("take_profit_abs", 0.0))
		self.stop_loss_pct: float = float(cfg.get("stop_loss_pct", 0.01))
		self.poll_interval_sec: int = int(cfg.get("poll_interval_sec", 5))
		self.quote_source: str = str(cfg.get("quote_source", "auto")).lower()
		self.debug: bool = bool(cfg.get("debug", False))
		self.min_warmup_samples: int = int(cfg.get("min_warmup_samples", 3))
		self.buy_immediate_on_start: bool = bool(cfg.get("buy_immediate_on_start", False))
		self.buy_mode: str = str(cfg.get("buy_mode", "drop_from_high")).lower()
		self.sma_window: int = int(cfg.get("sma_window", 20))
		self.sma_drop_pct: float = float(cfg.get("sma_drop_pct", 0.003))
		self.market_tz: str = str(cfg.get("market_tz", "Asia/Kolkata"))
		self.market_open: str = str(cfg.get("market_open", "09:15"))
		self.market_close: str = str(cfg.get("market_close", "15:30"))
		self.market_buffer_min: int = int(cfg.get("market_buffer_min", 1))

		self.window_prices: Deque[float] = deque(maxlen=60)

	def is_market_open(self) -> bool:
		try:
			tz = ZoneInfo(self.market_tz)
			now = datetime.now(tz)
			open_h, open_m = [int(x) for x in self.market_open.split(":")]
			close_h, close_m = [int(x) for x in self.market_close.split(":")]
			open_time = dtime(hour=open_h, minute=open_m)
			close_time = dtime(hour=close_h, minute=close_m)
			# apply buffer
			start_dt = now.replace(hour=open_time.hour, minute=open_time.minute, second=0, microsecond=0)
			end_dt = now.replace(hour=close_time.hour, minute=close_time.minute, second=0, microsecond=0)
			start_dt = start_dt + (0 * start_dt.tzinfo.utcoffset(start_dt))  # no-op to keep tz-aware
			end_dt = end_dt + (0 * end_dt.tzinfo.utcoffset(end_dt))  # no-op
			buffer = self.market_buffer_min
			start_dt = start_dt.replace(minute=start_dt.minute + 0)  # buffer on open is usually 0–1; controlled externally
			end_dt = end_dt.replace(minute=end_dt.minute - buffer if end_dt.minute >= buffer else 0)
			return start_dt <= now <= end_dt
		except Exception:
			return True

	def update_price(self, ltp: float) -> None:
		self.window_prices.append(ltp)
		if self.debug:
			print(f"[debug] price window size={len(self.window_prices)} high={max(self.window_prices) if self.window_prices else None} last={ltp}")

	def ready(self) -> bool:
		return len(self.window_prices) >= self.min_warmup_samples

	def _should_buy_drop_from_high(self, ltp: float) -> bool:
		recent_high = max(self.window_prices) if self.window_prices else ltp
		if recent_high <= 0:
			return False
		drop_abs = (recent_high - ltp)
		drop_pct = drop_abs / recent_high
		if self.debug:
			print(f"[debug] mode=drop_from_high recent_high={recent_high} ltp={ltp} drop_abs={drop_abs:.4f} drop_pct={drop_pct:.4f} thr_abs={self.buy_drop_abs} thr_pct={self.buy_drop_pct}")
		if self.buy_drop_abs > 0 and drop_abs >= self.buy_drop_abs:
			return True
		return drop_pct >= self.buy_drop_pct

	def _should_buy_below_sma(self, ltp: float) -> bool:
		if len(self.window_prices) < max(self.sma_window, self.min_warmup_samples):
			return False
		sma = sum(list(self.window_prices)[-self.sma_window:]) / float(self.sma_window)
		gap = (sma - ltp) / sma if sma > 0 else 0.0
		if self.debug:
			print(f"[debug] mode=below_sma sma={sma:.4f} ltp={ltp} gap={gap:.4f} threshold={self.sma_drop_pct}")
		return gap >= self.sma_drop_pct

	def should_buy(self, ltp: Optional[float]) -> bool:
		if ltp is None:
			return False
		if not self.is_market_open():
			if self.debug:
				print("[debug] market is closed; skipping buy checks")
			return False
		if not self.ready() and not self.buy_immediate_on_start:
			return False
		if self.buy_mode == "below_sma":
			return self._should_buy_below_sma(ltp)
		return self._should_buy_drop_from_high(ltp)

	def should_sell(self, ltp: Optional[float], avg_buy_price: float) -> Tuple[bool, str]:
		if ltp is None or avg_buy_price <= 0:
			return False, "no_price"
		pnl_abs = ltp - avg_buy_price
		pnl_pct = pnl_abs / avg_buy_price
		if self.debug:
			print(f"[debug] pnl_abs={pnl_abs:.4f} pnl_pct={pnl_pct:.4f} tp_abs={self.take_profit_abs} tp_pct={self.take_profit_pct} sl_pct={self.stop_loss_pct}")
		if self.take_profit_abs > 0 and pnl_abs >= self.take_profit_abs:
			return True, "take_profit_abs"
		if pnl_pct >= self.take_profit_pct:
			return True, "take_profit"
		if pnl_pct <= -self.stop_loss_pct:
			return True, "stop_loss"
		return False, "hold"
