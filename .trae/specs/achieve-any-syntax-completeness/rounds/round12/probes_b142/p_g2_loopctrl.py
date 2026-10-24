"""B142 族探针 G2：continue/break 穿双层 finally（回边保留 + 副本归属）"""


def g2_cont(rows):
    """continue 在内层 try 体：内层副本→外层副本→回边。"""
    out = []
    for r in rows:
        try:
            try:
                if r % 2 == 0:
                    continue
                out.append(r)
            finally:
                out.append(1)
        finally:
            out.append(2)
    return out


def g2_brk(rows):
    """break 在内层 try 体：出口跳转嵌在外层副本块尾。"""
    out = []
    for r in rows:
        try:
            try:
                if r > 10:
                    break
                out.append(r)
            finally:
                out.append(1)
        finally:
            out.append(2)
    return out
