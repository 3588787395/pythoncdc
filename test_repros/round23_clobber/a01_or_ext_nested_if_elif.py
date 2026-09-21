# -*- coding: utf-8 -*-
# R23 battery case a01_or_ext_nested_if_elif
# SHAPE: or-extended if whose THEN arm reduces a nested IfRegion (sink = RETURN), then an elif arm of the parent.  Nested reduction is the clobber source.
# EXPECTED: parent keeps BOTH arms: `elif a < b: return 3` and the trailing `return 0`.
# ACTUAL-HEAD: FAIL |d|=2 f seq_len orig=28 decomp=26
# ACTUAL-C1A: FAIL |d|=2 f seq_len orig=28 decomp=26
# MARK: DIAG_OR_EXT_NOEFFECT
# MUST_CONTAIN: elif a < b:
# MUST_CONTAIN: return 0
def log(m):
    return None


def f(a, b, c, d, e):
    if a > b or c == d:
        if e:
            log(1)
            if a:
                return None
    elif a < b:
        return 3
    return 0
