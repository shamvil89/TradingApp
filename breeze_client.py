import json
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from breeze_connect import BreezeConnect


class BreezeClient:
	def __init__(self, creds_path: str = "creds.config") -> None:
		self.creds_path = creds_path
		self._breeze: Optional[BreezeConnect] = None

	def connect(self) -> None:
		with open(self.creds_path, "r") as f:
			creds = json.load(f)
		api_key = creds.get("api_key", "").strip()
		api_secret = creds.get("api_secret", "").strip()
		session_token = creds.get("session_token", "").strip()
		if not api_key or not api_secret or not session_token:
			raise ValueError("Missing api_key/api_secret/session_token in creds.config")

		breeze = BreezeConnect(api_key=api_key)
		breeze.generate_session(api_secret=api_secret, session_token=session_token)
		self._breeze = breeze

	def _ensure(self) -> BreezeConnect:
		if self._breeze is None:
			raise RuntimeError("BreezeClient not connected. Call connect().")
		return self._breeze

	def get_ltp(self, stock_code: str, exchange_code: str) -> Optional[float]:
		breeze = self._ensure()
		# 1) Try real-time quotes (cash)
		try:
			resp: Dict[str, Any] = breeze.get_quotes(
				stock_code=stock_code,
				exchange_code=exchange_code,
				product_type="cash",
			)
			data = resp.get("Success") or resp.get("data") or []
			if data:
				row = data[0]
				for key in ("ltp", "LTP", "last_traded_price"):
					if key in row and row[key] is not None:
						return float(row[key])
			else:
				print("Breeze get_quotes returned empty for cash product.")
		except Exception as e:
			print(f"Breeze get_quotes error (cash): {e}")
		# 1b) Try quotes without product_type
		try:
			resp2: Dict[str, Any] = breeze.get_quotes(
				stock_code=stock_code,
				exchange_code=exchange_code,
			)
			data2 = resp2.get("Success") or resp2.get("data") or []
			if data2:
				row = data2[0]
				for key in ("ltp", "LTP", "last_traded_price"):
					if key in row and row[key] is not None:
						return float(row[key])
			else:
				print("Breeze get_quotes returned empty (no product_type).")
		except Exception as e:
			print(f"Breeze get_quotes error: {e}")
		# 2) Fall back to short historical window (last 10–15 minutes)
		try:
			to_dt = datetime.now(timezone.utc)
			from_dt = to_dt - timedelta(minutes=15)
			resp3: Dict[str, Any] = breeze.get_historical_data(
				interval="1minute",
				from_date=from_dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
				to_date=to_dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
				stock_code=stock_code,
				exchange_code=exchange_code,
				product_type="cash",
			)
			data3 = resp3.get("Success") or resp3.get("data") or []
			if data3:
				row = data3[-1]
				for key in ("close", "Close", "ltp", "LTP"):
					if key in row and row[key] is not None:
						return float(row[key])
			else:
				print("Breeze historical returned empty.")
		except Exception as e:
			print(f"Breeze historical error: {e}")
		return None

	def place_market_order(self,
						 stock_code: str,
						 exchange_code: str,
						 action: str,
						 quantity: int,
						 product: str = "cash",
						 validity: str = "DAY") -> Dict[str, Any]:
		breeze = self._ensure()
		if action not in ("BUY", "SELL"):
			raise ValueError("action must be BUY or SELL")
		payload = {
			"stock_code": stock_code,
			"exchange_code": exchange_code,
			"product": product,
			"action": action,
			"order_type": "MARKET",
			"quantity": int(quantity),
			"validity": validity,
		}
		resp: Dict[str, Any] = breeze.place_order(**payload)
		return resp

	def get_order_status(self, order_id: str) -> Dict[str, Any]:
		breeze = self._ensure()
		return breeze.get_order_detail(exchange_code="NSE", order_id=order_id)
