# Pattern Q repro: mixed Constant string + variable in f-string with literal double-quotes.
var = 42
x = f'"k": {"1"!s}{var}suffix'
