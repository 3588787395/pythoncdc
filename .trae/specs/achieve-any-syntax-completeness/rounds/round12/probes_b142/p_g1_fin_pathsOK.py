# Source Generated with Decompyle++ (Python version)
# File: p_g1_fin_paths.pyc (Python 3.11)

"""B142 族探针 G1：内层 finally 正常/异常路径（双层 try/finally 副本归属）"""
def g1_fin_normal(rows):
    """正常路径：内层 finally 副本（正常出口）与外层 finally 副本按序执行。"""
    out = []
    for r in rows:
        try:
            try:
                out.append(r)
            finally:
                out.append(1)
        finally:
            out.append(2)
    return out
def g1_fin_raise_in_try(rows):
    """异常路径：内层 try 体抛异常 → 内层 finally → 外层 finally → 传播。"""
    out = []
    for r in rows:
        try:
            try:
                if r < 0:
                    raise ValueError(r)
                out.append(r)
            finally:
                out.append(1)
        finally:
            out.append(2)
    return out
