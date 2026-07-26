"""Repro 08-07: D3 variant — chained compare with LOAD_ATTR middle operand.

CPython 3.11 chained compare where the middle operand is an attribute
access (`a.x`). The bytecode is the same SWAP+COPY shape as D3:
    LOAD_CONST X / LOAD_FAST a / LOAD_ATTR x / SWAP / COPY /
    COMPARE_OP '<=' / POP_JUMP_FORWARD_IF_FALSE /
    LOAD_CONST Y / COMPARE_OP '<=' / POP_JUMP_FORWARD_IF_FALSE
The decompiler should emit `if X <= a.x <= Y:` but may emit `if Y:`.
The variant exercises whether the LOAD_ATTR middle operand changes
the failure mode.

Expected defect: `if Y:` (chained compare lost) instead of `if X <= a.x <= Y:`.
"""


def handler(obj):
    try:
        do_work()
    except HTTPError as e:
        if 400 <= e.code <= 499:
            handle_4xx(e)
        else:
            handle_other(e)
