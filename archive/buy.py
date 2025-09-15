import json
import sys
import time
from typing import Optional

from breeze_client import BreezeClient
from rules import RuleEngine
from state import get_position, set_position
from quote_router import get_ltp
from symbols import read_symbol_entry


def main() -> None:
	client = BreezeClient()
	client.connect()
	display_symbol, breeze_code = read_symbol_entry()
	rules = RuleEngine()

	if get_position() is not None:
		print("Position already open. Not buying another.")
		return

	print(f"Monitoring {display_symbol} for buy (source={rules.quote_source})...")
	while True:
		ltp: Optional[float] = None
		if rules.quote_source in ("auto", "yf"):
			ltp = get_ltp(display_symbol, rules.exchange_code, client)
		elif rules.quote_source == "breeze":
			ltp = client.get_ltp(breeze_code, rules.exchange_code)
		else:
			ltp = get_ltp(display_symbol, rules.exchange_code, client)

		if ltp is not None:
			rules.update_price(ltp)
			if rules.should_buy(ltp):
				print(f"Buy signal at {ltp}")
				resp = client.place_market_order(
					stock_code=breeze_code,
					exchange_code=rules.exchange_code,
					action="BUY",
					quantity=rules.quantity,
				)
				avg_price = ltp
				try:
					odata = resp.get("Success") or resp.get("data") or {}
					avg_price = float(odata.get("average_price") or odata.get("avg_price") or avg_price)
				except Exception:
					pass
				set_position(display_symbol, rules.quantity, avg_price)
				print(f"Bought {display_symbol} qty={rules.quantity} avg_price={avg_price}")
				return
		else:
			print("No LTP yet...")
		time.sleep(rules.poll_interval_sec)


if __name__ == "__main__":
	try:
		main()
	except Exception as e:
		print(f"Error: {e}")
		import traceback
		traceback.print_exc()
		sys.exit(1)

