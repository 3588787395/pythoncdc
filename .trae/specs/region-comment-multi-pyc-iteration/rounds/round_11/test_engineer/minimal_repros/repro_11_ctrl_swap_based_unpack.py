"""[R11 repro_11] CTRL: SWAP-based tuple unpack (must still work via SWAP path)."""

# At module scope, `a, b = c, d` emits SWAP 2 (not optimized away).
# This is the existing Pattern handled by the SWAP detection path.
a, b = 1, 2
