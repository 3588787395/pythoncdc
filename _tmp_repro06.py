# repro_06: compound None-check in try/except + return (POP_JUMP->EXTENDED_ARG)
# Pattern: CONDITIONAL region collapse (compound None-check jump replaced by EXTENDED_ARG)
# Original failing function: get_kline_by_count / get_price_common (klinedata.pyc)
# Expected: try: if x is None or y is None: return z -> POP_JUMP_FORWARD_IF_NONE chain
# Actual diff summary: orig index 2 POP_JUMP_FORWARD_IF_NONE vs decomp EXTENDED_ARG
# Expected vs actual bytecode diff: index 2 orig_op=POP_JUMP_FORWARD_IF_NONE decomp_op=EXTENDED_ARG
def f(x, y, z, default):
    try:
        if x is None or y is None:
            return z
        elif x == 0 and y == 0:
            return z + 1
        elif x > y:
            return x
    except BaseException:
        return default
    return y
