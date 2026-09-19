# Source Generated with Decompyle++ (Python version)
# File: r2_10_except_tail_loop_cond.pyc (Python 3.11)

__doc__ = """Repro: check_and_update_trade comparator R104b artifact.

Pattern: while-loop whose try/except handler is the LAST thing in the
loop body. Handler tail layout in CPython 3.11:
    ... POP_TOP, POP_EXCEPT, JUMP_FORWARD,
    RERAISE, COPY, POP_EXCEPT, RERAISE,      <- cleanup dead code
    LOAD_FAST count, LOAD_CONST 3, COMPARE_OP <,   <- rotated while
    POP_JUMP_BACKWARD_IF_TRUE,                     <- bottom back-edge
    LOAD_CONST None, RETURN_VALUE                  <- within 15 instrs
The decompiles to byte-identical code (raw difflib ratio 1.000 for the
original function), yet verification reports a mismatch because the
comparator's _remove_inlined_finally_in_except (R104b) trims the
decompiled side one-sidedly: it treats the POP_EXCEPT..return-None
window (which contains the loop back-edge) as an "inlined finally".
"""
import time
_app_log = print
def check_and_update(path, user_id):
    count = 1
    while count < 3:
        try:
            fh = open(path, 'r')
            data = fh.read()
            if len(data) == 0:
                _app_log('empty for {}'.format(user_id))
        except BaseException:
            if count == 2:
                _app_log('fail {} {}'.format(user_id, count))
            count += 1
            time.sleep(1)
    return None
