# Source Generated with Decompyle++ (Python version)
# File: r2_02_guard_early_return_dec_dec.pyc (Python 3.11)

__doc__ = """Repro: query_strategy_id / query_trade_strategy_info tail mismatch.

Pattern: `if not os.path.exists(p): return None` early-return guard
before a try/except whose handler falls through to a trailing
`return None`. CPython lays out two separate LOAD_CONST(None) blocks:
the guard-return block comes first, the after-try return last. The
decompiler instead wraps everything in `if os.path.exists(p):` and
puts `return None` inside the if, swapping which return block each
path targets (jump-target-only diff, but it also trips the
comparator's R104b trim -> reported as true_diffs).
"""
import os
import time
_system_log = print
def query_strategy_id(path, trade_id):
    try:
        if not os.path.exists(path):
            return None
        else:
            with open(path, mode='r') as fh:
                rows = fh.read().splitlines()
            for row in rows:
                cols = row.split(',')
                if len(cols) > 2 and cols[2] == trade_id:
                    return cols[0]
    except BaseException:
        _system_log('read error {}'.format(trade_id))
        time.sleep(1)
    return None
