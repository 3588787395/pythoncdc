# Pattern Q repro: Compare with Constant string in FormattedValue (backtest scenario:
# "enabled": {frequency != 'tick'!s}). Source uses double-quoted inner to be valid 3.11.
freq = 'tick'
x = f'"enabled": {freq != "tick"!s}'
