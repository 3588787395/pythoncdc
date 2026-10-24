"""B142 族探针 G3：双层/三层 finally 嵌套变体。"""


def g3_two_fin(rows):
    """B142 基形变体：双层 try/finally + continue。"""
    out = []
    for r in rows:
        try:
            try:
                if r == 0:
                    continue
            finally:
                out.append(10)
        finally:
            out.append(20)
        out.append(r)
    return out


def g3_three_fin(rows):
    """三层 try/finally + continue：内层副本链跨三个台账。"""
    out = []
    for r in rows:
        try:
            try:
                try:
                    if r == 0:
                        continue
                finally:
                    out.append(1)
            finally:
                out.append(2)
        finally:
            out.append(3)
        out.append(r)
    return out
