# repro_14: jump-target renumbering (forward jump offset mismatch)
# Pattern: JUMP-TARGET renumber (conditional jump offset renumbered; structural NOP drop)
# Original failing function: get_kline_by_date_ndarray / get_kline_by_date_new (klinedata.pyc)
# Expected: forward conditional jump -> POP_JUMP_FORWARD_IF_TRUE with consistent target
# Actual diff summary: orig index 47 POP_JUMP_FORWARD_IF_TRUE arg=656 vs decomp arg=308
# Expected vs actual bytecode diff: index 47 same op, jump target offset differs (jump_diffs=3)
def f(x, y, z):
    if x is not None and y is not None:
        if z:
            return x
        return y
    return z
