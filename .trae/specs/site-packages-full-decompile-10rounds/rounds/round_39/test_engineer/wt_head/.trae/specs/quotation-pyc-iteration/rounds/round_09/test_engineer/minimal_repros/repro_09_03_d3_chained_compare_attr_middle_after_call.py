"""Repro 09-03: D3 variant — chained compare with LOAD_ATTR middle operand.

The quotation.pyc D3 site uses `400 <= e2.code <= 499` where the
middle operand is `e2.code` (LOAD_FAST + LOAD_ATTR). CPython 3.11
emits this as:
    LOAD_CONST 400 / LOAD_FAST e2 / LOAD_ATTR code / SWAP / COPY /
    COMPARE_OP '<=' / POP_JUMP_FORWARD_IF_FALSE /
    LOAD_CONST 499 / COMPARE_OP '<=' / POP_JUMP_FORWARD_IF_FALSE
The SWAP+COPY shape shares the middle operand (`e2.code`) between
two COMPARE_OP instructions across two basic blocks.

R8 repro_08_07 confirmed this is NOT-REPRO in isolation. This repro
adds a preceding call in the same except handler to test whether the
LOAD_ATTR middle operand triggers D3 in the compound context.

Expected defect: `if 499:` (chained compare lost) when preceded by
a call in the same except handler.
"""


def handler(e):
    try:
        do_work()
    except HTTPError as e2:
        log_error(get_traceback_message())
        if 400 <= e2.code <= 499:
            handle_4xx(e2)
        else:
            handle_other(e2)
