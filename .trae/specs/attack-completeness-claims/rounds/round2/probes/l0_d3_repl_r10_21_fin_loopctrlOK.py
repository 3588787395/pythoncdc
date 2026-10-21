# Source Generated with Decompyle++ (Python version)
# File: l0_d3_repl_r10_21_fin_loopctrl.pyc (Python 3.11)

__doc__ = '逐字复刻 r10_21_fin_loopctrl（finally 体含 continue/break）'
def fin_continue(rows):
    out = []
    for r in rows:
        try:
            if r < 0:
                raise ValueError(r)
        finally:
            if r < 0:
                continue
        out.append(r)
    return out
def fin_break(rows):
    total = 0
    for r in rows:
        try:
            total += r
        finally:
            if total > 100:
                break
    return total
def fin_continue_stmt(rows):
    out = []
    i = 0
    while i < len(rows):
        try:
            v = rows[i]
        finally:
            i += 1
            if v is None:
                continue
        out.append(v)
    return out
