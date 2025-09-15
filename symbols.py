from typing import Tuple


def read_symbol_entry(path: str = "stocksymbol.txt") -> Tuple[str, str]:
	with open(path, "r") as f:
		line = f.read().strip()
	# Accept formats:
	# - SYMBOL
	# - SYMBOL|BREEZE_CODE
	if "|" in line:
		display, breeze_code = line.split("|", 1)
		return display.strip().upper(), breeze_code.strip()
	return line.strip().upper(), line.strip().upper()
