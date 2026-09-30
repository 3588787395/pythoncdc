# Source Generated with Decompyle++ (Python version)
# File: w1_orchain_guard.pyc (Python 3.11)

def w1(sym, flds, dd, rd):
    if dd and sym not in dd or len(dd[sym]) == 0:
        return rd if flds is None else rd[flds]
    else:
        v = dd[sym]
        out = []
        for i in v:
            out.append(i)
        return out
