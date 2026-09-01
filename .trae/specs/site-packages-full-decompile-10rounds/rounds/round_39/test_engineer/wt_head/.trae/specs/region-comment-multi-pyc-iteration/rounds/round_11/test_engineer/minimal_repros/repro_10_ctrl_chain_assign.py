"""[R11 repro_10] CTRL: chain assignment `a = b = c` (must NOT trigger C2).

Chain assignment uses COPY 1 (one value on stack, multiple stores).  This
is handled by the existing chain-assign detection.  Pattern C2 detection
must NOT fire here (no SWAP, but only one value on stack — guarded by
the stack-depth check).
"""


def f(c):
    a = b = c
    return a, b
