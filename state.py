import json
import os
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, Optional

from filelock import FileLock

STATE_FILE = "state.json"
LOCK_FILE = "state.json.lock"


def _today_str() -> str:
	return datetime.now().strftime("%Y-%m-%d")


def _default_state() -> Dict[str, Any]:
	return {
		"position": None,  # or {symbol, qty, avg_price}
		"total_pnl": 0.0,
		"last_sell_price": None,
		"trades_today_date": _today_str(),
		"trades_today_count": 0,
	}


@contextmanager
def _locked_state():
	lock = FileLock(LOCK_FILE, timeout=10)
	with lock:
		yield


def read_state() -> Dict[str, Any]:
	if not os.path.exists(STATE_FILE):
		return _default_state()
	try:
		with open(STATE_FILE, "r") as f:
			state = json.load(f)
			# Backward compatibility defaults
			if "total_pnl" not in state:
				state["total_pnl"] = 0.0
			if "last_sell_price" not in state:
				state["last_sell_price"] = None
			if "position" not in state:
				state["position"] = None
			if "trades_today_date" not in state:
				state["trades_today_date"] = _today_str()
			if "trades_today_count" not in state:
				state["trades_today_count"] = 0
			# Rollover daily counter if date changed
			if state.get("trades_today_date") != _today_str():
				state["trades_today_date"] = _today_str()
				state["trades_today_count"] = 0
			return state
	except Exception:
		return _default_state()


def write_state(state: Dict[str, Any]) -> None:
	with open(STATE_FILE, "w") as f:
		json.dump(state, f, indent=2)


def reset_state() -> Dict[str, Any]:
	"""Reset state.json to defaults and return it."""
	with _locked_state():
		state = _default_state()
		write_state(state)
		return state


def get_position() -> Optional[Dict[str, Any]]:
	with _locked_state():
		state = read_state()
		return state.get("position")


def set_position(symbol: str, qty: int, avg_price: float) -> None:
	with _locked_state():
		state = read_state()
		state["position"] = {
			"symbol": symbol,
			"qty": int(qty),
			"avg_price": float(avg_price),
		}
		write_state(state)


def clear_position() -> None:
	with _locked_state():
		state = read_state()
		state["position"] = None
		write_state(state)


def add_realized_pnl(amount: float) -> float:
	with _locked_state():
		state = read_state()
		state["total_pnl"] = float(state.get("total_pnl", 0.0)) + float(amount)
		write_state(state)
		return state["total_pnl"]


def get_total_pnl() -> float:
	with _locked_state():
		state = read_state()
		return float(state.get("total_pnl", 0.0))


def set_last_sell_price(price: Optional[float]) -> None:
	with _locked_state():
		state = read_state()
		state["last_sell_price"] = None if price is None else float(price)
		write_state(state)


def get_last_sell_price() -> Optional[float]:
	with _locked_state():
		state = read_state()
		val = state.get("last_sell_price")
		return None if val is None else float(val)


def increment_trades_today() -> int:
	with _locked_state():
		state = read_state()
		state["trades_today_count"] = int(state.get("trades_today_count", 0)) + 1
		write_state(state)
		return state["trades_today_count"]


def get_trades_today() -> int:
	with _locked_state():
		state = read_state()
		return int(state.get("trades_today_count", 0))
