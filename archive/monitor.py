import time
from typing import Optional

from breeze_client import BreezeClient
from rules import RuleEngine
from state import get_position, clear_position
from quote_router import get_ltp
from symbols import read_symbol_entry


def main() -> None:
	client = BreezeClient()
	client.connect()
	rules = RuleEngine()
	display_symbol, breeze_code = read_symbol_entry()

	print(f"Monitor started (source={rules.quote_source}).")
	while True:
		pos = get_position()
		if not pos:
			print("No open position. Idle...")
			time.sleep(rules.poll_interval_sec)
			continue

		avg_buy = float(pos["avg_price"]) if "avg_price" in pos else 0.0
		ltp: Optional[float] = None
		if rules.quote_source in ("auto", "yf"):
			ltp = get_ltp(display_symbol, rules.exchange_code, client)
		elif rules.quote_source == "breeze":
			ltp = client.get_ltp(breeze_code, rules.exchange_code)
		else:
			ltp = get_ltp(display_symbol, rules.exchange_code, client)

		if ltp is None:
			print("Failed to fetch LTP. Retrying...")
			time.sleep(rules.poll_interval_sec)
			continue

		print(f"Position avg={avg_buy} LTP={ltp}")
		should_exit, reason = rules.should_sell(ltp, avg_buy)
		if should_exit:
			print(f"Exit signal {reason} at {ltp}")
			resp = client.place_market_order(
				stock_code=breeze_code,
				exchange_code=rules.exchange_code,
				action="SELL",
				quantity=rules.quantity,
			)
			clear_position()
			print(f"Sold {display_symbol} due to {reason} at approx {ltp}")
		else:
			print("Holding...")

		time.sleep(rules.poll_interval_sec)


if __name__ == "__main__":
	try:
		main()
	except Exception as e:
		print(f"Error: {e}")
		import traceback
		traceback.print_exc()
		raise

