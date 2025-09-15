import os
import time
from typing import Optional

from prices import get_ltp_yf, get_ltp_nse

_YF_COOLDOWN_FILE = "yf.cooldown"
_YF_COOLDOWN_SEC = 600  # 10 minutes


def _yf_on_cooldown() -> bool:
	try:
		if not os.path.exists(_YF_COOLDOWN_FILE):
			return False
		with open(_YF_COOLDOWN_FILE, "r") as f:
			ts = float(f.read().strip() or "0")
		return (time.time() - ts) < _YF_COOLDOWN_SEC
	except Exception:
		return False


def _set_yf_cooldown() -> None:
	try:
		with open(_YF_COOLDOWN_FILE, "w") as f:
			f.write(str(time.time()))
	except Exception:
		pass


def get_ltp(symbol: str, exchange_code: str, breeze_client) -> Optional[float]:
	# 1) yfinance
	if not _yf_on_cooldown():
		ltp = get_ltp_yf(symbol, exchange_code)
		if ltp is not None:
			return ltp
		_set_yf_cooldown()
		print("yfinance unavailable; entering cooldown.")
	# 2) NSE India
	ltp = get_ltp_nse(symbol)
	if ltp is not None:
		return ltp
	# 3) Breeze fallback
	try:
		return breeze_client.get_ltp(symbol, exchange_code)
	except Exception:
		return None
