from typing import Optional, List

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import yfinance as yf


_session: Optional[requests.Session] = None
_nse_session: Optional[requests.Session] = None


def _get_retry_session() -> requests.Session:
	global _session
	if _session is not None:
		return _session
	s = requests.Session()
	retry = Retry(
		total=3,
		read=3,
		connect=3,
		backoff_factor=0.6,
		status_forcelist=(429, 500, 502, 503, 504),
		allowed_methods=("GET", "POST"),
	)
	adapter = HTTPAdapter(max_retries=retry)
	s.mount("http://", adapter)
	s.mount("https://", adapter)
	_session = s
	return s


def _get_nse_session() -> requests.Session:
	global _nse_session
	if _nse_session is not None:
		return _nse_session
	s = requests.Session()
	s.headers.update({
		"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
		"Accept": "*/*",
		"Accept-Language": "en-US,en;q=0.9",
		"Connection": "keep-alive",
		"Referer": "https://www.nseindia.com/",
	})
	# Prime cookies by visiting homepage
	s.get("https://www.nseindia.com/", timeout=10)
	_nse_session = s
	return s


def resolve_yf_candidates(symbol: str, exchange_code: str) -> List[str]:
	# If user already provided a Yahoo-style ticker, use as-is first
	if "." in symbol:
		return [symbol]
	sym = symbol.upper().strip()
	if exchange_code.upper() == "NSE":
		return [f"{sym}.NS", sym]
	elif exchange_code.upper() == "BSE":
		return [f"{sym}.BO", sym]
	else:
		# Unknown exchange; try raw and NSE as best-effort
		return [sym, f"{sym}.NS"]


def _try_fast_info(ticker: yf.Ticker) -> Optional[float]:
	try:
		fi = ticker.fast_info
		val = getattr(fi, "last_price", None)
		if val is None and hasattr(fi, "last_traded_price"):
			val = getattr(fi, "last_traded_price")
		if val is None:
			# some versions expose mapping-like access
			val = (fi.get("last_price") if hasattr(fi, "get") else None)  # type: ignore[attr-defined]
		return float(val) if val is not None else None
	except Exception:
		return None


def _try_info_regular(ticker: yf.Ticker) -> Optional[float]:
	try:
		info = ticker.info
		val = info.get("regularMarketPrice") if isinstance(info, dict) else None
		return float(val) if val is not None else None
	except Exception:
		return None


def _try_history(ticker: yf.Ticker) -> Optional[float]:
	for period, interval, col in [("1d", "1m", "Close"), ("5d", "5m", "Close"), ("1d", "1m", "Adj Close")]:
		try:
			df = ticker.history(period=period, interval=interval)
			if not df.empty and col in df.columns:
				return float(df[col].iloc[-1])
		except Exception:
			continue
	return None


def get_ltp_yf(symbol: str, exchange_code: str = "NSE") -> Optional[float]:
	session = _get_retry_session()
	candidates = resolve_yf_candidates(symbol, exchange_code)
	for cand in candidates:
		t = yf.Ticker(cand, session=session)
		ltp = _try_fast_info(t)
		if ltp is None:
			ltp = _try_info_regular(t)
		if ltp is None:
			ltp = _try_history(t)
		if ltp is not None:
			return ltp
	return None


def get_ltp_nse(symbol: str) -> Optional[float]:
	try:
		s = _get_nse_session()
		url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol.upper()}"
		resp = s.get(url, timeout=10)
		if resp.status_code != 200:
			return None
		data = resp.json()
		price_info = data.get("priceInfo") or {}
		ltp = price_info.get("lastPrice")
		return float(ltp) if ltp is not None else None
	except Exception:
		return None
