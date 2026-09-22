def w1(sym, flds, dd, rd):
    if not dd or sym not in dd or len(dd[sym]) == 0:
        return rd if flds is None else rd[flds]
    v = dd[sym]
    out = []
    for i in v:
        out.append(i)
    return out
