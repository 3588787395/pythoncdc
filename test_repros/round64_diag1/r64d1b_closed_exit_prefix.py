# -*- coding: utf-8 -*-
# R64-diag1 cand_r64d1b_kbin: closed shared-exit and-prefix (v is not None / not
# v.empty -> SAME else block) immediately followed by a NESTED if/else in the then
# branch.  The landed chain walker absorbs the nested condition and emits
# `v is not None and v.empty or c == 6`, orphaning the nested else statement.
def kbin_repro(v, cols, c, wide, narrow):
    data = v.load(c)
    if data is not None and not data.empty:
        if c == 6:
            out = data[wide]
        else:
            out = data[narrow]
        out.columns = cols
    else:
        out = build(c)
    return out
