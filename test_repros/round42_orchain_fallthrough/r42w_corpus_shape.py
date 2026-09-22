# -*- coding: utf-8 -*-
"""Round 42 G0 witnesses: an or-chain whose LAST operand falls through into the
chain's common exit (the `handle_exrights` shape)."""


def r42w_1_orchain_tail_fallthrough(sym, flds, dd, rd):
    if not dd or sym not in dd or len(dd[sym]) == 0:
        return rd if flds is None else rd[flds]
    v = dd[sym]
    out = []
    for i in v:
        if i:
            out.append(i)
    return out


def r42w_2_guard_break(sym, flds, dd, rd):
    if not dd or sym not in dd:
        return None
    v = dd[sym]
    if len(v) == 0:
        return rd
    return v[0]
