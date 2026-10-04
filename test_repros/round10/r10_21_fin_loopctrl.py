"""r10_21: R-1 观察项探针 — finally 体仅含 continue/break（B68 门控 machinery 集重叠面）"""


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
