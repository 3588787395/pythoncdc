# Pattern Q repro: Constant string in FormattedValue + literal double-quotes.
# Source is valid Python 3.11: single-quoted f-string, double-quoted inner Constant.
# Decompiler renders Constant via repr() -> '1' (single-quoted). Content has both
# ' (from '1') and " (from literal "k"). Quote-selection falls back to single-quote
# delimiter -> {'1'!s} conflicts with f'...' -> SyntaxError.
x = f'"k": {"1"!s}'
