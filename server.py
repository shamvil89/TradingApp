import json
import subprocess
import sys
import threading
import time
from collections import deque
from typing import Any, Deque, Dict, Optional
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from breeze_client import BreezeClient
from rules import RuleEngine
from state import (
	get_position,
	set_position,
	clear_position,
	read_state,
	write_state,
	add_realized_pnl,
	get_total_pnl,
	get_last_sell_price,
	set_last_sell_price,
	get_trades_today,
	reset_state,
)
from quote_router import get_ltp as routed_ltp
from symbols import read_symbol_entry

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import yfinance as yf
import pandas as pd
import random

app = FastAPI(title="HERFOO_TRADES API")
app.mount("/web", StaticFiles(directory="web", html=True), name="web")


# ------------------- Trader Process Manager -------------------
_TRADER_PROC: Optional[subprocess.Popen] = None
_TRADER_LOCK = threading.Lock()
_TRADER_LOGS: Deque[str] = deque(maxlen=1000)
_TRADER_STATUS: str = "stopped"  # stopped | starting | running | stopping | error


def _append_log(line: str) -> None:
	try:
		_TRADER_LOGS.append(line.rstrip())
	except Exception:
		pass


def _reader_thread(proc: subprocess.Popen) -> None:
	global _TRADER_STATUS
	try:
		assert proc.stdout is not None
		assert proc.stderr is not None
		for line in iter(proc.stdout.readline, b""):
			if not line:
				break
			_append_log(line.decode(errors="ignore"))
		for line in iter(proc.stderr.readline, b""):
			if not line:
				break
			_append_log(line.decode(errors="ignore"))
	except Exception as e:
		_append_log(f"[manager] reader error: {e}")
	finally:
		code = proc.poll()
		_TRADER_STATUS = "stopped" if code == 0 else "error"
		_append_log(f"[manager] trader exited with code {code}")


def _python_exe() -> str:
	return sys.executable or "python"


def start_trader() -> None:
	global _TRADER_PROC, _TRADER_STATUS
	with _TRADER_LOCK:
		if _TRADER_PROC and _TRADER_PROC.poll() is None:
			raise RuntimeError("Trader already running")
		_TRADER_STATUS = "starting"
		_TRADER_LOGS.clear()
		cmd = [_python_exe(), "-u", "trader.py"]
		proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1)
		_TRADER_PROC = proc
		_TRADER_STATUS = "running"
		threading.Thread(target=_reader_thread, args=(proc,), daemon=True).start()
		_append_log("[manager] trader started")


def stop_trader() -> None:
	global _TRADER_PROC, _TRADER_STATUS
	with _TRADER_LOCK:
		if not _TRADER_PROC or _TRADER_PROC.poll() is not None:
			_TRADER_STATUS = "stopped"
			return
		_TRADER_STATUS = "stopping"
		try:
			_TRADER_PROC.terminate()
			_TRADER_PROC.wait(timeout=10)
		except Exception:
			try:
				_TRADER_PROC.kill()
			except Exception:
				pass
		finally:
			_TRADER_STATUS = "stopped"
			_append_log("[manager] trader stopped")


def trader_status() -> Dict[str, Any]:
	code = None
	if _TRADER_PROC is not None:
		code = _TRADER_PROC.poll()
	return {"status": _TRADER_STATUS, "exit_code": code}


def trader_logs(limit: int = 500) -> Dict[str, Any]:
	lines = list(_TRADER_LOGS)[-int(limit):]
	return {"lines": lines, "count": len(lines)}


def archive_and_clear_logs() -> Dict[str, Any]:
	lines = list(_TRADER_LOGS)
	count = len(lines)
	# Ensure archive directory exists
	archive_dir = Path("archive")
	archive_dir.mkdir(parents=True, exist_ok=True)
	# Create timestamped file
	stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
	file_path = archive_dir / f"logs_{stamp}.txt"
	try:
		with open(file_path, "w", encoding="utf-8", newline="\n") as f:
			f.write("\n".join(lines))
		_TRADER_LOGS.clear()
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Archive error: {e}")
	return {"archived": str(file_path), "lines": count}


# ------------------- API helpers -------------------

def _load_rules() -> RuleEngine:
	return RuleEngine()


def _breeze() -> BreezeClient:
	c = BreezeClient()
	c.connect()
	return c


def _convert_hhmm(from_tz: str, to_tz: str, hhmm: str) -> str:
	try:
		h, m = [int(x) for x in hhmm.split(":", 1)]
		now = datetime.now(ZoneInfo(from_tz))
		src_dt = now.replace(hour=h, minute=m, second=0, microsecond=0)
		dst_dt = src_dt.astimezone(ZoneInfo(to_tz))
		return f"{dst_dt.hour:02d}:{dst_dt.minute:02d}"
	except Exception:
		return hhmm


# ------------------- Routes -------------------
@app.get("/")
async def root() -> FileResponse:
	return FileResponse("web/index.html")


@app.get("/api/state")
async def api_state() -> Dict[str, Any]:
	state = read_state()
	rules = _load_rules()
	return {
		**state,
		"max_quantity_per_trade": rules.quantity,
		"trades_today": get_trades_today(),
	}


@app.get("/api/rules")
async def api_rules_get() -> Dict[str, Any]:
	with open("rules.config", "r") as f:
		return json.load(f)


@app.post("/api/rules")
async def api_rules_post(payload: Dict[str, Any]) -> Dict[str, Any]:
	with open("rules.config", "r") as f:
		cfg = json.load(f)
	cfg.update(payload or {})
	with open("rules.config", "w") as f:
		json.dump(cfg, f, indent=2)
	return cfg


@app.get("/api/convert_time")
async def api_convert_time(from_tz: str, hhmm: str, to_tz: str = "Asia/Kolkata") -> Dict[str, Any]:
	return {"from_tz": from_tz, "to_tz": to_tz, "input": hhmm, "output": _convert_hhmm(from_tz, to_tz, hhmm)}


@app.get("/api/creds")
async def api_creds_get() -> Dict[str, Any]:
	try:
		with open("creds.config", "r") as f:
			return json.load(f)
	except FileNotFoundError:
		return {"api_key": "", "api_secret": "", "session_token": ""}


@app.post("/api/creds")
async def api_creds_post(payload: Dict[str, Any]) -> Dict[str, Any]:
	if payload is None:
		raise HTTPException(status_code=400, detail="Missing payload")
	data = {
		"api_key": str(payload.get("api_key", "")),
		"api_secret": str(payload.get("api_secret", "")),
		"session_token": str(payload.get("session_token", "")),
	}
	with open("creds.config", "w") as f:
		json.dump(data, f, indent=2)
	return data


@app.get("/api/symbol")
async def api_symbol_get() -> Dict[str, Any]:
	with open("stocksymbol.txt", "r") as f:
		line = f.read().strip()
	display, breeze = read_symbol_entry()
	return {"symbol_line": line, "display": display, "breeze_code": breeze}


@app.post("/api/symbol")
async def api_symbol_post(payload: Dict[str, Any]) -> Dict[str, Any]:
	line = str((payload or {}).get("symbol_line", "")).strip()
	if not line or "\n" in line or "\r" in line:
		raise HTTPException(status_code=400, detail="Invalid symbol format")
	with open("stocksymbol.txt", "w") as f:
		f.write(line + "\n")
	display, breeze = read_symbol_entry()
	return {"ok": True, "symbol_line": line, "display": display, "breeze_code": breeze}


@app.get("/api/ltp")
async def api_ltp() -> Dict[str, Any]:
	rules = _load_rules()
	display_symbol, breeze_code = read_symbol_entry()
	c = _breeze()
	if rules.quote_source == "breeze":
		ltp = c.get_ltp(breeze_code, rules.exchange_code)
	else:
		ltp = routed_ltp(display_symbol, rules.exchange_code, c)
	return {"symbol": display_symbol, "ltp": ltp}


@app.get("/api/chart/day")
async def api_chart_day() -> Dict[str, Any]:
	# Return last 1 day intraday series (timestamps ms + close) for the display symbol
	display_symbol, _ = read_symbol_entry()
	
	# Try to get real data for any symbol (including HERFOO)
	candidates = [f"{display_symbol.upper()}.NS", display_symbol.upper(), f"{display_symbol.upper()}.BO"]
	# Prefer 5m over 1m (yfinance reliability), and 5d over 1d so we can always
	# slice the most recent trading day even when the market is closed.
	intervals = ["5m", "1m"]
	periods = ["5d", "1d"]
	last_err: Optional[str] = None
	
	for tick in candidates:
		for per in periods:
			for iv in intervals:
				try:
					ticker = yf.Ticker(tick)
					df = ticker.history(period=per, interval=iv)
					if df is None or df.empty:
						continue
					# Slice to the most recent trading day so closed-market still shows full day
					try:
						# Determine the last calendar date present in the data (based on local timestamp)
						last_ts = df.index[-1]
						last_date = last_ts.to_pydatetime().date()
						day_df = df[df.index.to_series().apply(lambda x: x.to_pydatetime().date() == last_date)]
						if day_df is None or day_df.empty:
							day_df = df
					except Exception:
						day_df = df

					points = []
					for ts, row in day_df.iterrows():
						try:
							tp = int(ts.to_pydatetime().timestamp() * 1000)
						except Exception:
							tp = int(datetime.fromisoformat(str(ts)).timestamp() * 1000)
						open_val = row.get("Open")
						high_val = row.get("High") 
						low_val = row.get("Low")
						close_val = row.get("Close")
						volume_val = row.get("Volume", 0)
						
						if any(pd.isna(x) for x in [open_val, high_val, low_val, close_val]):
							continue
							
						points.append({
							"t": tp,
							"o": round(float(open_val), 2),
							"h": round(float(high_val), 2), 
							"l": round(float(low_val), 2),
							"c": round(float(close_val), 2),
							"v": int(volume_val) if not pd.isna(volume_val) else 0
						})
					if points:
						return {"symbol": display_symbol, "ticker": tick, "interval": iv, "period": per, "points": points, "real": True}
				except Exception as e:
					last_err = str(e)
					continue
	
	# If reached here, no real data available
	raise HTTPException(status_code=404, detail=f"no real market data available for {display_symbol} (tried: {', '.join(candidates)}) - {last_err}")


@app.post("/api/flatten")
async def api_flatten() -> Dict[str, Any]:
	rules = _load_rules()
	pos = get_position()
	if not pos:
		raise HTTPException(status_code=400, detail="No open position")
	if not rules.is_market_open():
		raise HTTPException(status_code=400, detail="Market closed")
	c = _breeze()
	display_symbol, breeze_code = read_symbol_entry()
	resp = c.place_market_order(
		stock_code=breeze_code,
		exchange_code=rules.exchange_code,
		action="SELL",
		quantity=rules.quantity,
	)
	ltp: Optional[float] = None
	if rules.quote_source == "breeze":
		ltp = c.get_ltp(breeze_code, rules.exchange_code)
	else:
		ltp = routed_ltp(display_symbol, rules.exchange_code, c)
	avg_buy = float(pos.get("avg_price", 0))
	pnl = (float(ltp) - avg_buy) * float(pos.get("qty", 0) or 0) if ltp is not None else 0.0
	total = add_realized_pnl(pnl)
	set_last_sell_price(ltp if ltp is not None else None)
	clear_position()
	return {"status": "flattened", "ltp": ltp, "trade_pnl": pnl, "total_pnl": total, "order": resp}


@app.post("/api/trader/start")
async def api_trader_start() -> Dict[str, Any]:
	try:
		start_trader()
		return trader_status()
	except Exception as e:
		_append_log(f"[manager] start error: {e}")
		raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/trader/stop")
async def api_trader_stop() -> Dict[str, Any]:
	stop_trader()
	return trader_status()


@app.get("/api/trader/status")
async def api_trader_status() -> Dict[str, Any]:
	return trader_status()


@app.get("/api/trader/logs")
async def api_trader_logs(limit: int = 500) -> Dict[str, Any]:
	return trader_logs(limit)


@app.post("/api/trader/logs/clear")
async def api_trader_logs_clear() -> Dict[str, Any]:
	return archive_and_clear_logs()


@app.post("/api/trader/logs/archive")
async def api_trader_logs_archive() -> Dict[str, Any]:
	return archive_and_clear_logs()


@app.get("/api/status")
async def api_status() -> Dict[str, Any]:
	return read_state()


@app.post("/api/status/reset")
async def api_status_reset() -> Dict[str, Any]:
	return reset_state()


# -------- API logs file reader --------
@app.get("/api/logs/api")
async def api_logs_api(file: str = Query(default="apiLogs_1305.log"), limit: int = Query(default=1000)) -> Dict[str, Any]:
	# only allow files that start with 'apiLogs' and end with '.log' to avoid path traversal
	name = file.strip()
	if not (name.startswith("apiLogs") and name.endswith(".log") and "/" not in name and "\\" not in name):
		raise HTTPException(status_code=400, detail="Invalid log filename")
	paths = [Path(name), Path("archive") / name, Path("logs") / name]
	lines = []
	used = None
	for p in paths:
		try:
			with open(p, "r", encoding="utf-8", errors="ignore") as f:
				lines = f.read().splitlines()
				used = str(p)
				break
		except FileNotFoundError:
			continue
	if used is None:
		return {"file": name, "lines": [], "count": 0, "path": None}
	# tail last N lines
	if limit is not None:
		lines = lines[-int(limit):]
	return {"file": name, "lines": lines, "count": len(lines), "path": used}
