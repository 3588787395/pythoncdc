# Source Generated with Decompyle++ (Python version)
# File: r42w_corpus_shape.pyc (Python 3.11)

__doc__ = """Round 42 G0 witnesses: an or-chain whose LAST operand falls through into the
chain's common exit (the `handle_exrights` shape)."""
def r42w_1_orchain_tail_fallthrough(sym, flds, dd, rd):
    if dd and sym in dd:
        v = dd[sym]
        out = []
        for i in v:
            if i:
                out.append(i)
        return out
    return rd if flds is None else rd[flds]
def r42w_2_guard_break(sym, flds, dd, rd):
    if dd or sym not in dd:
        return None
    v = dd[sym]
    if len(v) == 0:
        return rd
    else:
        return v[0]
