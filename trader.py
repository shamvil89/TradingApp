import sys
import time
from typing import Optional

from breeze_client import BreezeClient
from rules import RuleEngine
from state import get_position, set_position, clear_position, add_realized_pnl, get_total_pnl, set_last_sell_price, get_last_sell_price, increment_trades_today
from quote_router import get_ltp
from symbols import read_symbol_entry


def main() -> None:
	client = BreezeClient()
	client.connect()
	rules = RuleEngine()
	display_symbol, breeze_code = read_symbol_entry()

	print(f"Trader started for {display_symbol} (source={rules.quote_source}).")
	immediate_bought = False
	while True:
		pos = get_position()
		ltp: Optional[float] = None

		# Fetch latest price
		if rules.quote_source == "breeze":
			ltp = client.get_ltp(breeze_code, rules.exchange_code)
		else:
			ltp = get_ltp(display_symbol, rules.exchange_code, client)

		print(f"[debug] LTP={ltp}")
		if ltp is None:
			print("No LTP yet...")
			time.sleep(rules.poll_interval_sec)
			continue

		if not rules.is_market_open():
			print("Market closed; no new orders.")
			time.sleep(rules.poll_interval_sec)
			continue

		if pos is None:
			last_sell = get_last_sell_price()
			if last_sell is not None and ltp < last_sell:
				print(f"BUY (price below last sell {last_sell}) at {ltp}")
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
				immediate_bought = True
			else:
				if rules.buy_immediate_on_start and not immediate_bought:
					print(f"BUY (immediate on start) at {ltp}")
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
					immediate_bought = True
				else:
					rules.update_price(ltp)
					if not rules.ready() and not rules.buy_immediate_on_start:
						print("[debug] warming up price window...")
					elif rules.should_buy(ltp):
						print(f"BUY signal at {ltp}")
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
					else:
						print("[debug] no buy trigger yet.")
		else:
			avg_buy = float(pos.get("avg_price", 0))
			should_exit, reason = rules.should_sell(ltp, avg_buy)
			if should_exit:
				print(f"SELL signal ({reason}) at {ltp}")
				client.place_market_order(
					stock_code=breeze_code,
					exchange_code=rules.exchange_code,
					action="SELL",
					quantity=rules.quantity,
				)
				pnl = (ltp - avg_buy) * float(pos.get("qty", 0) or 0)
				total = add_realized_pnl(pnl)
				set_last_sell_price(ltp)
				clear_position()
				increment_trades_today()
				print(f"Sold {display_symbol} due to {reason} at approx {ltp}; trade PnL={pnl:.2f}; total PnL={total:.2f}")
			else:
				print("[debug] holding; no exit trigger.")

		time.sleep(rules.poll_interval_sec)


if __name__ == "__main__":
	try:
		main()
	except Exception as e:
		print(f"Error: {e}")
		import traceback
		traceback.print_exc()
		sys.exit(1)
